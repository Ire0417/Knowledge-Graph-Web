import json
import hashlib
import logging
import os
import re
import shutil
import threading
import time
from collections import defaultdict
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import chromadb
import numpy as np
from app.config import Config
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.database.redis_client import (
    get_cache, set_cache, CACHE_PREFIXES, CACHE_TTL
)
from app.services.observability import (
    new_trace, save_trace, record_request, record_llm, record_cache,
    record_error, record_step,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 分词 & 停用词
# ---------------------------------------------------------------------------
# 常用中文停用词（覆盖最高频、对语义贡献低的字/词）
_CN_STOPWORDS = {
    "的", "了", "和", "是", "在", "有", "我", "也", "就", "都", "而",
    "及", "与", "或", "但", "不", "没", "很", "这", "那", "这些", "那些",
    "这个", "那个", "一个", "上", "下", "等", "为", "以", "于", "由",
    "自", "之", "从", "到", "向", "把", "被", "给", "让", "将", "会",
    "可以", "能", "能够", "可", "需", "需要", "应", "应该", "必须",
    "对", "对于", "关于", "以及", "还有", "其中", "其", "该", "此",
    "如", "若", "如果", "则", "因此", "所以", "因为", "由于", "从而",
    "即", "亦即", "也就是", "等等", "等", "等", "使", "使得", "做",
    "进行", "具有", "拥有", "含", "包含", "包括", "的话", "是否", "不是",
    "没有", "非", "无法", "不能", "不会", "不可",
    "a", "an", "the", "and", "or", "is", "are", "was", "were", "be",
    "of", "to", "in", "on", "for", "with", "by", "from", "at", "as",
    "it", "its", "this", "that", "these", "those", "we", "you", "they",
    "our", "your", "their", "i", "me", "my", "he", "she", "him", "her",
}

# 英文/数字的正则
_EN_NUM_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
# 中文字符（单个）
_CN_RE = re.compile(r"[\u4e00-\u9fa5]")

# 分词用的线程锁（jieba 内部不是 100% 线程安全的首次加载）
_tokenizer_lock = threading.Lock()
_jieba_available: Optional[bool] = None


def _ensure_jieba() -> bool:
    """惰性检查并初始化 jieba。返回是否可用。"""
    global _jieba_available
    if _jieba_available is not None:
        return _jieba_available
    with _tokenizer_lock:
        if _jieba_available is not None:
            return _jieba_available
        try:
            import jieba  # noqa: F401
            # 关闭 jieba 默认日志
            jieba.setLogLevel(60)
            _jieba_available = True
            logger.info("[BM25] jieba 分词器已启用")
        except ImportError:
            _jieba_available = False
            logger.warning("[BM25] jieba 不可用，回退到字符级分词")
    return _jieba_available


def tokenize_text(text: str) -> List[str]:
    """改进版分词：
    - 中文：jieba 分词（若可用），否则按单字拆分（unigram）
    - 英文/数字：独立保留小写 token
    - 过滤停用词 + 长度<=1 的纯中文 token（避免"的"之类污染）
    """
    if not text:
        return []
    tokens: List[str] = []

    # 把文本切分为"中文段"和"英文/数字段"，分别处理
    # 1) 英文和数字：按原逻辑直接提取
    en_tokens = [t.lower() for t in _EN_NUM_RE.findall(text)]

    # 2) 中文部分：逐段分词
    # 先提取所有中文字符段（连续中文作为一个待分词片段）
    cn_segments = re.findall(r"[\u4e00-\u9fa5]+", text)

    if _ensure_jieba():
        import jieba
        for seg in cn_segments:
            # jieba 精确模式
            for w in jieba.cut(seg, cut_all=False):
                w = w.strip()
                if w:
                    tokens.append(w)
    else:
        # 回退：字符级 unigram（对中文短查询仍然比原方案好得多）
        for seg in cn_segments:
            for ch in seg:
                tokens.append(ch)

    tokens.extend(en_tokens)

    # 过滤：去停用词 + 长度
    filtered: List[str] = []
    for t in tokens:
        if not t:
            continue
        # 过滤停用词（中文 2 字以上才检查，避免误删；英文全部检查）
        if _CN_RE.fullmatch(t[0]) if t else False:
            # 是中文 token
            if t in _CN_STOPWORDS:
                continue
            if len(t) <= 1:
                # 单字中文也过滤（单字中文对 BM25 贡献不稳定，保留词也在停用表里）
                continue
        else:
            # 英文/数字 token
            if t in _CN_STOPWORDS:
                continue
            if len(t) <= 2:
                # 2 字符及以下的英文/数字通常无意义（"of","to","is","a","1"）
                continue
        filtered.append(t)

    return filtered


# ---------------------------------------------------------------------------
# BM25 核心
# ---------------------------------------------------------------------------
class BM25:
    """改进版 BM25Okapi（Okapi BM25）。

    主要改进：
    - 中文 jieba 分词（不可用时回退到字符级）
    - 停用词 + 短 token 过滤
    - 查询侧词频上限（避免同一个查询词重复出现被放大）
    - 更稳定的 IDF（防止除零）

    BM25 得分公式：
        score(d, q) = Σ_{t in q}  idf(t) * [ tf(t,d) * (k1 + 1) ]
                                          / [ tf(t,d) + k1 * (1 - b + b * |d| / avgdl) ]

    默认：k1=1.5, b=0.75（广泛认可的经验值）
    """

    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75,
                 eps_tf: float = 0.0, query_k_cap: int = 3):
        self.k1 = float(k1)
        self.b = float(b)
        self.eps_tf = float(eps_tf)  # 预留，未来可做平滑
        self.query_k_cap = int(query_k_cap)  # 查询词重复次数上限
        self.doc_count = len(corpus)
        self.avg_doc_len = 0.0
        self.doc_freqs: List[Dict[str, int]] = []
        self.idf: Dict[str, float] = {}
        self.doc_len: List[int] = []
        self._initialize(corpus)

    def _initialize(self, corpus: List[str]) -> None:
        if self.doc_count == 0:
            self.avg_doc_len = 1.0
            return

        df: Dict[str, int] = defaultdict(int)
        total_words = 0

        for doc in corpus:
            words = tokenize_text(doc)
            n = len(words)
            self.doc_len.append(n)
            total_words += n

            freq: Dict[str, int] = defaultdict(int)
            for word in words:
                freq[word] += 1
            self.doc_freqs.append(dict(freq))

            for word in freq:
                df[word] += 1

        self.avg_doc_len = float(total_words) / self.doc_count if self.doc_count > 0 else 1.0
        if self.avg_doc_len <= 0:
            self.avg_doc_len = 1.0

        # IDF：Robertson-Sparck Jones 形式
        for word, freq in df.items():
            # 经典形式：log( (N - f + 0.5) / (f + 0.5) + 1 )
            # 在某些变体里用 log( (N - f + 0.5) / (f + 0.5) )；这里与原实现一致保留 +1 更稳定
            self.idf[word] = float(
                np.log((self.doc_count - freq + 0.5) / (freq + 0.5) + 1.0)
            )

    def get_scores(self, query: str) -> List[float]:
        """计算每个文档对 query 的 BM25 得分。"""
        query_words = tokenize_text(query)
        if not query_words:
            return [0.0] * self.doc_count

        # 查询侧词频统计 & 限制，防止"aaaaa"类查询失真
        qf: Dict[str, int] = defaultdict(int)
        for w in query_words:
            qf[w] += 1
        unique_query_words = list(qf.keys())

        scores = np.zeros(self.doc_count, dtype=np.float64)
        avg_dl = self.avg_doc_len

        for word in unique_query_words:
            idf = self.idf.get(word, 0.0)
            if idf <= 0:
                continue
            qt = min(qf[word], self.query_k_cap)

            for i in range(self.doc_count):
                tf = self.doc_freqs[i].get(word, 0)
                if tf <= 0:
                    continue
                doc_len = self.doc_len[i]
                # BM25 核心公式
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / avg_dl))
                scores[i] += idf * (tf * (self.k1 + 1.0)) / denom * qt

        return scores.tolist()

    def top_k(self, query: str, k: int) -> List[Tuple[int, float]]:
        """返回 (doc_index, score) 的 top-k 列表（降序）。"""
        scores = self.get_scores(query)
        # 过滤零分 + 排序
        indexed = [(i, s) for i, s in enumerate(scores) if s > 0]
        indexed.sort(key=lambda x: x[1], reverse=True)
        return indexed[: max(1, int(k))]


# ---------------------------------------------------------------------------
# BM25 索引缓存（进程内 LRU）
# ---------------------------------------------------------------------------
_BM25_CACHE_LOCK = threading.Lock()
_BM25_CACHE: Dict[str, Dict[str, Any]] = {}
_BM25_CACHE_MAX = 16  # 最多缓存 16 个文件的 BM25 索引


def _bm25_cache_key(docs: List[Document]) -> str:
    """基于文档内容 hash 生成缓存 key。"""
    h = hashlib.md5()
    # 只取前 80 个字符的前若干份 + 总数，避免对大文档做完整 hash
    sample_count = min(len(docs), 32)
    for i in range(sample_count):
        h.update(docs[i].page_content[:120].encode("utf-8", errors="ignore"))
    h.update(str(len(docs)).encode())
    h.update(str(len(docs[-1].page_content) if docs else 0).encode())
    return h.hexdigest()


def _get_or_create_bm25(docs: List[Document]) -> BM25:
    """从缓存取或新建 BM25 索引。"""
    if not docs:
        return BM25([])
    key = _bm25_cache_key(docs)
    with _BM25_CACHE_LOCK:
        entry = _BM25_CACHE.get(key)
        if entry is not None:
            entry["last_used"] = time.time()
            return entry["bm25"]
    # 在锁外构建（BM25 初始化是纯 CPU，不应该持有全局锁）
    corpus = [doc.page_content for doc in docs]
    bm25 = BM25(corpus)
    with _BM25_CACHE_LOCK:
        # 淘汰最旧的，直到 <= 上限
        while len(_BM25_CACHE) >= _BM25_CACHE_MAX:
            oldest_key = min(_BM25_CACHE, key=lambda k: _BM25_CACHE[k]["last_used"])
            _BM25_CACHE.pop(oldest_key, None)
        _BM25_CACHE[key] = {"bm25": bm25, "last_used": time.time(), "doc_count": len(docs)}
    return bm25


def _reset_bm25_cache() -> None:
    """调试/测试用：清空索引缓存。"""
    with _BM25_CACHE_LOCK:
        _BM25_CACHE.clear()


def _bm25_search(docs: List[Document], question: str, k: int) -> List[Document]:
    """BM25 关键词召回（改进版）。

    - 使用 jieba 中文分词
    - 停用词 & 短 token 过滤
    - 进程内 LRU 缓存（避免每次重建）
    - 仅返回得分 > 0 的文档（若无则回退到按位置取首段）
    """
    if not docs:
        return []

    bm25 = _get_or_create_bm25(docs)
    top = bm25.top_k(question, k)

    if top:
        return [docs[i] for i, _ in top]

    # 回退：没有任何 token 命中（比如查询词全在停用表里）
    # 返回文档开头若干段作为兜底，保证四路融合层仍然有数据
    fallback_count = max(1, min(int(k), len(docs)))
    return list(docs[:fallback_count])


def _entity_relation_search(docs: List[Document], question: str, k: int, extract_result: Dict[str, Any]) -> List[Document]:
    relevant_docs = []
    if not extract_result:
        return []
    
    entities = extract_result.get('entities', [])
    triplets = extract_result.get('triplets', []) or extract_result.get('relations', [])
    
    entity_names = set()
    for ent in entities:
        name = ent.get('text', ent.get('name', ''))
        if name:
            entity_names.add(name)
    
    question_lower = question.lower()
    for doc in docs:
        content = doc.page_content.lower()
        score = 0
        for name in entity_names:
            if name.lower() in question_lower and name.lower() in content:
                score += 1
        for trip in triplets:
            head = trip.get('head', trip.get('subject', ''))
            tail = trip.get('tail', trip.get('object', ''))
            if (head and head.lower() in question_lower and head.lower() in content) or \
               (tail and tail.lower() in question_lower and tail.lower() in content):
                score += 1
        if score > 0:
            relevant_docs.append(doc)
    
    relevant_docs.sort(key=lambda x: len(x.page_content), reverse=True)
    return relevant_docs[:k]


def _position_search(docs: List[Document], k: int) -> List[Document]:
    if not docs:
        return []
    n = len(docs)
    top_positions = []
    start_count = min(k // 2, n)
    end_count = min(k - start_count, n - start_count)
    top_positions.extend(docs[:start_count])
    if end_count > 0:
        top_positions.extend(docs[-end_count:])
    seen = set()
    result = []
    for doc in top_positions:
        doc_id = id(doc)
        if doc_id not in seen:
            seen.add(doc_id)
            result.append(doc)
    return result[:k]


def _fuse_and_rerank(
    vector_docs: List[Document],
    bm25_docs: List[Document],
    er_docs: List[Document],
    pos_docs: List[Document],
    k: int
) -> List[Document]:
    doc_scores = defaultdict(float)
    doc_map = {}
    
    for i, doc in enumerate(vector_docs):
        doc_map[id(doc)] = doc
        doc_scores[id(doc)] += (k - i) * 1.0
    
    for i, doc in enumerate(bm25_docs):
        doc_map[id(doc)] = doc
        doc_scores[id(doc)] += (k - i) * 0.8
    
    for i, doc in enumerate(er_docs):
        doc_map[id(doc)] = doc
        doc_scores[id(doc)] += (k - i) * 0.9
    
    for i, doc in enumerate(pos_docs):
        doc_map[id(doc)] = doc
        doc_scores[id(doc)] += (k - i) * 0.7
    
    sorted_doc_ids = sorted(
        doc_scores.keys(), 
        key=lambda x: (-doc_scores[x], -len(doc_map[x].page_content))
    )
    result = [doc_map[doc_id] for doc_id in sorted_doc_ids]
    return result[:k]


def _get_config() -> Dict[str, Any]:
    return {
        'vector_db_path': Config.VECTOR_DB_PATH,
        'chunk_size': Config.RAG_CHUNK_SIZE,
        'chunk_overlap': Config.RAG_CHUNK_OVERLAP,
        'top_k': Config.RAG_TOP_K,
        'qwen_api_key': Config.QWEN_API_KEY,
        'qwen_base_url': Config.QWEN_BASE_URL,
        'qwen_model': Config.QWEN_MODEL,
        'qwen_embedding_model': Config.QWEN_EMBEDDING_MODEL,
        'chroma_api_key': os.getenv(
            'CHROMA_API_KEY',
            'ck-G24QwJTV3KbGg2DhQNCw5Uk5AKdZFG96qiWjb8p3CuUu',
        ),
        'chroma_tenant': os.getenv(
            'CHROMA_TENANT',
            'f1f1fce9-306c-4c9b-af5c-4b746e7cc78d',
        ),
        'chroma_database': os.getenv('CHROMA_DATABASE', 'zs2'),
    }


def _ensure_api_key(api_key: str) -> None:
    if not api_key:
        raise RuntimeError('QWEN_API_KEY is empty. Please set it in environment or config.')


def _ensure_vector_db_path(path: str) -> None:
    if not path:
        raise RuntimeError('VECTOR_DB_PATH is empty. Please set it in config.')
    os.makedirs(path, exist_ok=True)


_chroma_client_cache: Dict[str, 'chromadb.ClientAPI'] = {}


def _get_chroma_client(config: Dict[str, Any]) -> 'chromadb.ClientAPI':
    """懒加载单例：返回 ChromaDB CloudClient。"""
    key = f"{config['chroma_tenant']}|{config['chroma_database']}"
    if key not in _chroma_client_cache:
        try:
            _chroma_client_cache[key] = chromadb.CloudClient(
                api_key=config['chroma_api_key'],
                tenant=config['chroma_tenant'],
                database=config['chroma_database'],
            )
            logger.info(
                "[ChromaDB] CloudClient connected: tenant=%s database=%s",
                config['chroma_tenant'],
                config['chroma_database'],
            )
        except Exception as e:
            raise RuntimeError(f'Failed to connect to ChromaDB Cloud: {e}') from e
    return _chroma_client_cache[key]


def _collection_name(file_id: str) -> str:
    """把文件 id 映射为合法的 ChromaDB 集合名。"""
    safe = re.sub(r'[^a-zA-Z0-9_\-]', '_', str(file_id))
    return f"file_{safe}"


def _get_embedding_model(config: Dict[str, Any]) -> DashScopeEmbeddings:
    _ensure_api_key(config['qwen_api_key'])
    return DashScopeEmbeddings(
        model=config['qwen_embedding_model'],
        dashscope_api_key=config['qwen_api_key'],
    )


def _get_llm(config: Dict[str, Any]) -> ChatOpenAI:
    _ensure_api_key(config['qwen_api_key'])
    return ChatOpenAI(
        model=config['qwen_model'],
        api_key=config['qwen_api_key'],
        base_url=config['qwen_base_url'],
        temperature=0.2,
    )


def _flatten_tables(tables: List[Any]) -> str:
    rows: List[str] = []
    for table in tables:
        table_data = table.get('data') if isinstance(table, dict) else table
        if not isinstance(table_data, list):
            continue
        for row in table_data:
            if isinstance(row, list):
                cells = [str(cell).strip() for cell in row if str(cell).strip()]
                if cells:
                    rows.append(' | '.join(cells))
            elif isinstance(row, str) and row.strip():
                rows.append(row.strip())
    return '\n'.join(rows)


def _build_documents(file_id: str, file_info: Dict[str, Any]) -> List[Document]:
    parse_result = file_info.get('parse_result', {}) or {}
    extract_result = file_info.get('extract_result', {}) or {}
    text_parts: List[str] = []

    # 添加原始文本内容
    base_text = str(parse_result.get('text', '') or '').strip()
    if base_text:
        text_parts.append(base_text)

    table_text = _flatten_tables(parse_result.get('tables', []) or [])
    if table_text:
        text_parts.append(table_text)

    image_texts = parse_result.get('image_texts', []) or []
    for image_text in image_texts:
        if isinstance(image_text, str) and image_text.strip():
            text_parts.append(image_text.strip())

    # 添加知识抽取结果作为结构化知识片段
    if extract_result:
        # 处理实体
        entities = extract_result.get('entities', [])
        if entities:
            entity_texts = []
            for ent in entities:
                ent_text = ent.get('text', ent.get('name', ''))
                ent_type = ent.get('label', ent.get('type', '概念'))
                if ent_text:
                    entity_texts.append(f"实体：{ent_text}，类型：{ent_type}")
            if entity_texts:
                text_parts.append("\n".join(entity_texts))

        # 处理三元组/关系
        triplets = extract_result.get('triplets', []) or extract_result.get('relations', [])
        if triplets:
            triplet_texts = []
            for trip in triplets:
                head = trip.get('head', trip.get('subject', ''))
                relation = trip.get('relation', trip.get('predicate', ''))
                tail = trip.get('tail', trip.get('object', ''))
                if head and relation and tail:
                    triplet_texts.append(f"关系：{head} {relation} {tail}")
            if triplet_texts:
                text_parts.append("\n".join(triplet_texts))

    merged_text = '\n\n'.join(text_parts).strip()
    if not merged_text:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=Config.RAG_CHUNK_SIZE,
        chunk_overlap=Config.RAG_CHUNK_OVERLAP,
        separators=['\n\n', '\n', '。', '！', '？', '.', '!', '?', '；', ';', '，', ',', ' '],
    )

    chunks = splitter.split_text(merged_text)
    docs: List[Document] = []
    for idx, chunk in enumerate(chunks):
        docs.append(
            Document(
                page_content=chunk,
                metadata={
                    'file_id': file_id,
                    'file_name': file_info.get('name', ''),
                    'chunk_index': idx,
                    'has_extraction': bool(extract_result),
                },
            )
        )
    return docs


def _vector_dir(file_id: str) -> str:
    config = _get_config()
    _ensure_vector_db_path(config['vector_db_path'])
    return os.path.join(config['vector_db_path'], file_id)


def _simple_docs_path(persist_dir: str) -> str:
    return os.path.join(persist_dir, 'docs.json')


def _simple_vectors_path(persist_dir: str) -> str:
    return os.path.join(persist_dir, 'vectors.npy')


def _save_simple_vector_store(file_id: str, docs: List[Document], vectors: List[List[float]]) -> None:
    """使用 ChromaDB Cloud 存储文档与向量（替换原 JSON+npy 本地文件方案）。"""
    config = _get_config()
    client = _get_chroma_client(config)
    col_name = _collection_name(file_id)

    # 若该文件集合已存在，先删除（重新解析后重建，避免旧分片残留）。
    try:
        existing = client.get_collection(col_name)
        if existing is not None:
            client.delete_collection(col_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=col_name,
        metadata={'file_id': file_id},
    )

    ids = [f"{file_id}_{i}" for i in range(len(docs))]
    texts = [doc.page_content for doc in docs]
    metas = [dict(doc.metadata) if doc.metadata else {} for doc in docs]

    # ChromaDB 接受 List[List[float]]，直接传即可。
    collection.add(
        ids=ids,
        documents=texts,
        metadatas=metas,
        embeddings=vectors,
    )
    logger.info(
        "[ChromaDB] saved %d chunks to collection=%s (file=%s)",
        len(docs), col_name, file_id,
    )


def _load_simple_vector_store(file_id: str) -> Dict[str, Any]:
    """从 ChromaDB Cloud 读取指定文件的全部文档与向量。"""
    config = _get_config()
    client = _get_chroma_client(config)
    col_name = _collection_name(file_id)

    try:
        collection = client.get_collection(col_name)
    except Exception as e:
        raise RuntimeError(
            f'ChromaDB collection not found for file={file_id}: {e}'
        ) from e

    # 读取全部文档（按 chunk_index 排序），保持与旧版 JSON+npy 一致的接口。
    try:
        res = collection.get(include=['documents', 'metadatas', 'embeddings'])
    except Exception as e:
        raise RuntimeError(f'Failed to read from ChromaDB: {e}') from e

    raw_docs = res.get('documents') or []
    raw_metas = res.get('metadatas') or []
    raw_embs = res.get('embeddings') or []

    if not raw_docs:
        raise RuntimeError(f'ChromaDB collection for file={file_id} is empty.')

    docs: List[Document] = []
    for text, meta in zip(raw_docs, raw_metas):
        docs.append(
            Document(
                page_content=text or '',
                metadata=dict(meta) if isinstance(meta, dict) else {},
            )
        )

    # 按 chunk_index 排序，保证 BM25 / 位置召回与原逻辑一致。
    try:
        docs.sort(key=lambda d: int(d.metadata.get('chunk_index', 0)))
    except Exception:
        pass

    vectors = np.asarray(raw_embs, dtype=np.float32) if raw_embs else np.zeros((len(docs), 0), dtype=np.float32)
    return {'docs': docs, 'vectors': vectors}


def _text_hash(text: str) -> str:
    """Generate a short hash for text content (used as cache key suffix)."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:16]


def _similarity_search_simple(embeddings: DashScopeEmbeddings, file_id: str, question: str, k: int) -> List[Document]:
    """基于 ChromaDB Cloud 的向量召回（余弦相似度，返回 top-k 文档）。"""
    config = _get_config()
    client = _get_chroma_client(config)
    col_name = _collection_name(file_id)

    try:
        collection = client.get_collection(col_name)
    except Exception as e:
        raise RuntimeError(f'ChromaDB collection not found for file={file_id}: {e}') from e

    # 尝试从缓存获取 Embedding 向量
    embed_cache_key = f"{CACHE_PREFIXES['qa_embed']}{_text_hash(question)}"
    cached_vec = get_cache(embed_cache_key)
    if cached_vec is not None:
        query_vec = [float(x) for x in cached_vec]
        logger.debug("[Redis] Embedding cache HIT for question hash=%s", _text_hash(question))
    else:
        query_vec = embeddings.embed_query(question)
        set_cache(embed_cache_key, list(query_vec), CACHE_TTL['qa_embed'])
        logger.debug("[Redis] Embedding cache MISS, cached for question hash=%s", _text_hash(question))

    result = collection.query(
        query_embeddings=[query_vec],
        n_results=max(1, int(k)),
    )

    # ChromaDB 返回结构：{'ids': [[...]], 'documents': [[...]], 'metadatas': [[...]], 'distances': [[...]]}
    ids_list = (result.get('ids') or [[]])[0]
    docs_list = (result.get('documents') or [[]])[0]
    metas_list = (result.get('metadatas') or [[]])[0]

    out: List[Document] = []
    for _cid, text, meta in zip(ids_list, docs_list, metas_list):
        out.append(
            Document(
                page_content=text or '',
                metadata=dict(meta) if isinstance(meta, dict) else {},
            )
        )
    return out


def build_file_vector_store(file_id: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
    """将解析内容切片并写入 ChromaDB Cloud 向量库。"""
    docs = _build_documents(file_id, file_info)
    if not docs:
        raise RuntimeError('No valid content extracted from file for vectorization.')

    config = _get_config()

    try:
        embeddings = _get_embedding_model(config)
        vectors = embeddings.embed_documents([doc.page_content for doc in docs])
        _save_simple_vector_store(file_id, docs, vectors)
    except Exception as e:
        raise RuntimeError(f'Failed to build vector store: {str(e)}') from e

    file_info['rag_ready'] = True
    file_info['vector_store_path'] = f'chroma://{_collection_name(file_id)}'
    file_info['vector_chunk_count'] = len(docs)

    return {
        'vector_store_path': f'chroma://{_collection_name(file_id)}',
        'chunk_count': len(docs),
    }


def delete_file_vector_store(file_id: str) -> None:
    """删除指定文件在 ChromaDB Cloud 中的集合。"""
    config = _get_config()
    client = _get_chroma_client(config)
    col_name = _collection_name(file_id)
    try:
        client.delete_collection(col_name)
        logger.info("[ChromaDB] deleted collection=%s (file=%s)", col_name, file_id)
    except Exception as e:
        logger.warning(
            "[ChromaDB] failed to delete collection=%s: %s", col_name, e,
        )


def _load_vector_store(file_id: str) -> Dict[str, Any]:
    config = _get_config()
    client = _get_chroma_client(config)
    col_name = _collection_name(file_id)

    try:
        client.get_collection(col_name)
    except Exception as e:
        raise RuntimeError(
            f'Vector store not found for this file (collection={col_name}): {e}'
        ) from e

    try:
        embeddings = _get_embedding_model(config)
        _load_simple_vector_store(file_id)
        return {'file_id': file_id, 'embeddings': embeddings}
    except Exception as e:
        raise RuntimeError(f'Failed to load vector store: {str(e)}') from e


def rag_answer(question: str, file_id: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
    """基于四路召回策略的千问问答（带Redis缓存 + 可观测性追踪）。

    返回 dict 中额外字段：
      - trace_id: 本次请求的追踪 ID
      - used_graph: bool（普通 rag_answer 始终为 False）
    """
    from app.services.observability import TraceContext  # noqa: F401

    config = _get_config()
    trace = new_trace(file_id=file_id, question=question[:80], mode="text_rag")
    _finalized = [False]

    def _finalize(success: bool, **extra) -> Dict[str, Any]:
        """在 trace 上补全成功/失败信息并归档。"""
        if _finalized[0]:
            return {}
        _finalized[0] = True
        trace.finish(success, **extra)
        # 把各 step 的耗时同步到全局聚合
        for s in trace.steps:
            record_step(s["step"], s["elapsed_ms"])
        record_request(
            success=success,
            total_ms=trace.duration_ms,
            use_graph=trace.attrs.get("use_graph", False),
            used_graph=trace.attrs.get("used_graph", False),
        )
        save_trace(trace)
        trace.log_summary()
        return {}

    try:
        # 如果知识抽取完成但RAG未就绪，自动构建向量库
        if not file_info.get('rag_ready'):
            if file_info.get('extract_result') or file_info.get('parse_result'):
                with trace.timer("build_vector_store"):
                    try:
                        build_file_vector_store(file_id, file_info)
                    except Exception as e:
                        raise RuntimeError(f'RAG index is not ready: {str(e)}') from e
            else:
                raise RuntimeError('File is not parsed or extracted yet. Please parse or extract the file before asking questions.')

        # 尝试从缓存获取问答结果
        qa_cache_key = f"{CACHE_PREFIXES['qa_answer']}{file_id}:{_text_hash(question)}"
        cached_answer = get_cache(qa_cache_key)
        if cached_answer is not None:
            logger.info("[Redis] QA answer cache HIT for file=%s question_hash=%s", file_id, _text_hash(question))
            record_cache(True)
            trace.set("cache_hit", True)
            _finalize(True, retrieved_docs=len(cached_answer.get("sources", [])))
            result = dict(cached_answer)
            result["trace_id"] = trace.trace_id
            result.setdefault("used_graph", False)
            return result
        record_cache(False)
        trace.set("cache_hit", False)

        with trace.timer("load_vector_store"):
            vector_store = _load_vector_store(file_id)
            store = _load_simple_vector_store(file_id)
        all_docs = store['docs']
        extract_result = file_info.get('extract_result', {})
        has_extraction = bool(extract_result)
        trace.set("has_extraction", has_extraction)
        trace.set("doc_count", len(all_docs))

        k = config['top_k']
        try:
            with trace.timer("retrieve_vector"):
                vector_docs = _similarity_search_simple(
                    embeddings=vector_store['embeddings'],
                    file_id=file_id,
                    question=question,
                    k=k,
                )
            with trace.timer("retrieve_bm25"):
                bm25_docs = _bm25_search(all_docs, question, k)
            with trace.timer("retrieve_entity_relation"):
                er_docs = _entity_relation_search(all_docs, question, k, extract_result)
            with trace.timer("retrieve_position"):
                pos_docs = _position_search(all_docs, k)
            with trace.timer("fuse_and_rerank"):
                docs = _fuse_and_rerank(vector_docs, bm25_docs, er_docs, pos_docs, k)
        except Exception as e:
            raise RuntimeError(f'Failed to retrieve relevant chunks: {str(e)}') from e

        trace.set("retrieved_docs", len(docs))

        context = '\n\n'.join([doc.page_content for doc in docs])
        if not context.strip():
            _finalize(True)
            return {
                'answer': '未检索到与问题相关的文本内容，请尝试换一种问法。',
                'sources': [],
                'trace_id': trace.trace_id,
                'used_graph': False,
                'used_extraction': has_extraction,
            }

        llm = _get_llm(config)

        # 根据是否有知识抽取结果，使用不同的提示词
        if has_extraction:
            prompt = ChatPromptTemplate.from_template(
                """
你是一个知识库问答助手。请严格依据给定上下文回答问题。
上下文包含：
1. 原始文档文本
2. 从文档中提取的实体和关系知识（结构化知识）

【回答要求】
1. 优先利用结构化知识回答问题，结构化知识以"实体："或"关系："开头
2. 如果结构化知识不够，再参考原始文档文本
3. 仅根据上下文作答，不要编造事实
4. 如果上下文不足，请明确说明"根据当前文档无法确定"
5. 用中文回答，回答要简洁、清晰、易读
6. 使用纯文本格式，不要使用Markdown（如#、##、**等格式标记）
7. 可以用数字编号（1.、2.、3.）或短横线（-）分点组织内容
8. 突出关键信息，避免冗长啰嗦
9. 每个论点用1-2句话说明
10.【重要】回答要清晰分段，段落之间空一行，结构更清晰
11. 开头可以用醒目的标识区分不同部分

【输出格式示例】

答案要点：
- 要点1：简要说明
- 要点2：简要说明

详细说明：
详细但简洁地展开说明...

（段落之间要空一行，让结构更清晰）

问题：{question}

上下文：
{context}
""".strip()
            )
        else:
            prompt = ChatPromptTemplate.from_template(
                """
你是一个知识库问答助手。请严格依据给定上下文回答问题。

【回答要求】
1. 仅根据上下文作答，不要编造事实
2. 如果上下文不足，请明确说明"根据当前文档无法确定"
3. 用中文回答，回答要简洁、清晰、易读
4. 使用纯文本格式，不要使用Markdown（如#、##、**等格式标记）
5. 可以用数字编号（1.、2.、3.）或短横线（-）分点组织内容
6. 突出关键信息，避免冗长啰嗦
7. 每个论点用1-2句话说明
8.【重要】回答要清晰分段，段落之间空一行，结构更清晰
9. 开头可以用醒目的标识区分不同部分

【输出格式示例】

答案要点：
- 要点1：简要说明
- 要点2：简要说明

详细说明：
详细但简洁地展开说明...

（段落之间要空一行，让结构更清晰）

问题：{question}

上下文：
{context}
""".strip()
            )

        chain = prompt | llm | StrOutputParser()
        try:
            with trace.timer("llm_invoke"):
                answer = chain.invoke({'question': question, 'context': context})
            record_llm(True)
        except Exception as e:
            record_llm(False)
            raise RuntimeError(f'LLM invocation failed: {str(e)}') from e

        result = {
            'answer': answer,
            'sources': [doc.metadata for doc in docs],
            'used_extraction': has_extraction,
            'used_graph': False,
            'trace_id': trace.trace_id,
        }

        # 缓存问答结果
        set_cache(qa_cache_key, result, CACHE_TTL['qa_answer'])
        logger.info("[Redis] QA answer cached for file=%s question_hash=%s", file_id, _text_hash(question))

        _finalize(True)
        return result

    except Exception as e:
        trace.record_error(e)
        record_error(e, trace=trace, file_id=file_id)
        _finalize(False, error_type=type(e).__name__, error_message=str(e))
        raise


def check_rag_health(file_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """检查RAG可用性：配置、Embedding连通性、LLM连通性。"""
    config = _get_config()
    report: Dict[str, Any] = {
        'ok': True,
        'checks': {
            'api_key': {'ok': True, 'message': 'ok'},
            'vector_db_path': {'ok': True, 'message': 'ok'},
            'embedding': {'ok': True, 'message': 'ok'},
            'llm': {'ok': True, 'message': 'ok'},
        },
        'models': {
            'llm': config.get('qwen_model', ''),
            'embedding': config.get('qwen_embedding_model', ''),
        },
    }

    if file_info is not None:
        extract_result = file_info.get('extract_result', {})
        has_extraction = bool(extract_result)
        entity_count = extract_result.get('stats', {}).get('entity_count', 0) if has_extraction else 0
        relation_count = extract_result.get('stats', {}).get('relation_count', 0) if has_extraction else 0
        
        report['file'] = {
            'rag_ready': bool(file_info.get('rag_ready')),
            'status': file_info.get('status', ''),
            'rag_error': file_info.get('rag_error', ''),
            'has_extraction': has_extraction,
            'entity_count': entity_count,
            'relation_count': relation_count,
        }

    try:
        _ensure_api_key(config['qwen_api_key'])
    except Exception as e:
        report['checks']['api_key'] = {'ok': False, 'message': str(e)}

    try:
        _ensure_vector_db_path(config['vector_db_path'])
    except Exception as e:
        report['checks']['vector_db_path'] = {'ok': False, 'message': str(e)}

    if report['checks']['api_key']['ok']:
        try:
            embeddings = _get_embedding_model(config)
            embeddings.embed_query('health check')
        except Exception as e:
            report['checks']['embedding'] = {'ok': False, 'message': str(e)}

        try:
            llm = _get_llm(config)
            llm.invoke('请仅回复: OK')
        except Exception as e:
            report['checks']['llm'] = {'ok': False, 'message': str(e)}
    else:
        report['checks']['embedding'] = {'ok': False, 'message': 'Skipped because API key is invalid'}
        report['checks']['llm'] = {'ok': False, 'message': 'Skipped because API key is invalid'}

    report['ok'] = all(item.get('ok') for item in report['checks'].values())
    return report
