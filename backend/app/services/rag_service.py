import json
import os
import shutil
from typing import Any, Dict, List, Optional

import numpy as np
from flask import current_app
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


def _get_config() -> Dict[str, Any]:
    cfg = current_app.config
    return {
        'vector_db_path': cfg.get('VECTOR_DB_PATH'),
        'chunk_size': cfg.get('RAG_CHUNK_SIZE', 800),
        'chunk_overlap': cfg.get('RAG_CHUNK_OVERLAP', 120),
        'top_k': cfg.get('RAG_TOP_K', 4),
        'qwen_api_key': cfg.get('QWEN_API_KEY', ''),
        'qwen_base_url': cfg.get('QWEN_BASE_URL', ''),
        'qwen_model': cfg.get('QWEN_MODEL', 'qwen-plus'),
        'qwen_embedding_model': cfg.get('QWEN_EMBEDDING_MODEL', 'text-embedding-v3'),
    }


def _ensure_api_key(api_key: str) -> None:
    if not api_key:
        raise RuntimeError('QWEN_API_KEY is empty. Please set it in environment or config.')


def _ensure_vector_db_path(path: str) -> None:
    if not path:
        raise RuntimeError('VECTOR_DB_PATH is empty. Please set it in config.')
    os.makedirs(path, exist_ok=True)


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
    text_parts: List[str] = []

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

    merged_text = '\n\n'.join(text_parts).strip()
    if not merged_text:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=current_app.config.get('RAG_CHUNK_SIZE', 800),
        chunk_overlap=current_app.config.get('RAG_CHUNK_OVERLAP', 120),
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


def _save_simple_vector_store(persist_dir: str, docs: List[Document], vectors: List[List[float]]) -> None:
    os.makedirs(persist_dir, exist_ok=True)
    with open(_simple_docs_path(persist_dir), 'w', encoding='utf-8') as f:
        json.dump(
            [
                {
                    'page_content': doc.page_content,
                    'metadata': doc.metadata or {},
                }
                for doc in docs
            ],
            f,
            ensure_ascii=False,
        )

    np.save(_simple_vectors_path(persist_dir), np.asarray(vectors, dtype=np.float32))


def _load_simple_vector_store(persist_dir: str) -> Dict[str, Any]:
    docs_path = _simple_docs_path(persist_dir)
    vectors_path = _simple_vectors_path(persist_dir)
    if not os.path.exists(docs_path) or not os.path.exists(vectors_path):
        raise RuntimeError('Simple vector store files are missing. Please parse the file again.')

    with open(docs_path, 'r', encoding='utf-8') as f:
        raw_docs = json.load(f)

    docs = [
        Document(
            page_content=item.get('page_content', ''),
            metadata=item.get('metadata', {}),
        )
        for item in raw_docs
    ]
    vectors = np.load(vectors_path)
    return {'docs': docs, 'vectors': vectors}


def _similarity_search_simple(embeddings: DashScopeEmbeddings, persist_dir: str, question: str, k: int) -> List[Document]:
    store = _load_simple_vector_store(persist_dir)
    docs: List[Document] = store['docs']
    vectors: np.ndarray = store['vectors']

    if len(docs) == 0 or vectors.size == 0:
        return []

    query_vec = np.asarray(embeddings.embed_query(question), dtype=np.float32)
    doc_norms = np.linalg.norm(vectors, axis=1) + 1e-12
    query_norm = float(np.linalg.norm(query_vec) + 1e-12)
    scores = (vectors @ query_vec) / (doc_norms * query_norm)

    top_indices = np.argsort(-scores)[: max(1, int(k))]
    return [docs[int(i)] for i in top_indices]


def build_file_vector_store(file_id: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
    """将解析内容切片并写入文件级向量库。"""
    docs = _build_documents(file_id, file_info)
    if not docs:
        raise RuntimeError('No valid content extracted from file for vectorization.')

    config = _get_config()
    persist_dir = _vector_dir(file_id)

    # 每次重新解析后重建该文件向量库，避免旧分片残留。
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir, ignore_errors=True)

    try:
        embeddings = _get_embedding_model(config)
        vectors = embeddings.embed_documents([doc.page_content for doc in docs])
        _save_simple_vector_store(persist_dir, docs, vectors)
    except Exception as e:
        raise RuntimeError(f'Failed to build vector store: {str(e)}') from e

    file_info['rag_ready'] = True
    file_info['vector_store_path'] = persist_dir
    file_info['vector_chunk_count'] = len(docs)

    return {
        'vector_store_path': persist_dir,
        'chunk_count': len(docs),
    }


def _load_vector_store(file_id: str) -> Dict[str, Any]:
    config = _get_config()
    persist_dir = _vector_dir(file_id)
    if not os.path.exists(persist_dir):
        raise RuntimeError('Vector store not found for this file. Please parse the file first.')

    try:
        embeddings = _get_embedding_model(config)
        _load_simple_vector_store(persist_dir)
        return {'persist_dir': persist_dir, 'embeddings': embeddings}
    except Exception as e:
        raise RuntimeError(f'Failed to load vector store: {str(e)}') from e


def rag_answer(question: str, file_id: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
    """基于LangChain+RAG的千问问答。"""
    config = _get_config()

    if not file_info.get('rag_ready'):
        if file_info.get('parse_result'):
            try:
                build_file_vector_store(file_id, file_info)
            except Exception as e:
                raise RuntimeError(f'RAG index is not ready: {str(e)}') from e
        else:
            raise RuntimeError('File is not parsed yet. Please parse the file before asking questions.')

    vector_store = _load_vector_store(file_id)
    try:
        docs = _similarity_search_simple(
            embeddings=vector_store['embeddings'],
            persist_dir=vector_store['persist_dir'],
            question=question,
            k=config['top_k'],
        )
    except Exception as e:
        raise RuntimeError(f'Failed to retrieve relevant chunks: {str(e)}') from e

    context = '\n\n'.join([doc.page_content for doc in docs])
    if not context.strip():
        return {
            'answer': '未检索到与问题相关的文本内容，请尝试换一种问法。',
            'sources': [],
        }

    llm = _get_llm(config)
    prompt = ChatPromptTemplate.from_template(
        """
你是一个知识库问答助手。请严格依据给定上下文回答问题。
要求：
1. 仅根据上下文作答，不要编造事实。
2. 如果上下文不足，请明确说明“根据当前文档无法确定”。
3. 用中文回答，条理清晰。

问题：{question}

上下文：
{context}
""".strip()
    )
    chain = prompt | llm | StrOutputParser()
    try:
        answer = chain.invoke({'question': question, 'context': context})
    except Exception as e:
        raise RuntimeError(f'LLM invocation failed: {str(e)}') from e

    return {
        'answer': answer,
        'sources': [doc.metadata for doc in docs],
    }


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
        report['file'] = {
            'rag_ready': bool(file_info.get('rag_ready')),
            'status': file_info.get('status', ''),
            'rag_error': file_info.get('rag_error', ''),
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
