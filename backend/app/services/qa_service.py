import logging
from app.services.rag_service import rag_answer
from app.services.graph_rag_service import graph_rag_answer
from app.database.mysql import save_qa_history as db_save_qa_history, get_qa_history as db_get_qa_history
from app.database.redis_client import (
    get_cache, set_cache, delete_cache, CACHE_PREFIXES, CACHE_TTL
)
from datetime import datetime

logger = logging.getLogger(__name__)


def ask_question(question, file_id, file_info, use_graph: bool = True):
    """基于 GraphRAG（知识图谱 + 四路向量召回）的智能问答。

    若 use_graph=True 且文件存在抽取结果，则优先使用 graph_rag_answer。
    """
    try:
        if use_graph:
            logger.info("[QA] using graph_rag_answer for file=%s", file_id)
            return graph_rag_answer(question=question, file_id=file_id, file_info=file_info, enable_graph=True)
    except Exception as e:
        logger.warning("[QA] graph_rag_answer failed, fallback to rag_answer: %s", e)

    logger.info("[QA] fallback to rag_answer for file=%s", file_id)
    result = rag_answer(question=question, file_id=file_id, file_info=file_info)
    # 对齐字段，保证前端一致处理
    result.setdefault("used_graph", False)
    result.setdefault("graph_context", {"triplets": [], "entities": [], "communities": []})
    return result

def get_qa_history(file_info):
    """获取问答历史（带Redis缓存）"""
    if not file_info or not file_info.get('id'):
        return []
    file_id = file_info.get('id')
    # 先查缓存
    history_cache_key = f"{CACHE_PREFIXES['qa_history']}{file_id}"
    cached = get_cache(history_cache_key)
    if cached is not None:
        logger.debug("[Redis] QA history cache HIT for file=%s", file_id)
        return cached
    # 缓存未命中，查MySQL
    try:
        result = db_get_qa_history(file_id)
        set_cache(history_cache_key, result, CACHE_TTL['qa_history'])
        return result
    except Exception:
        return []

def clear_qa_history(file_info):
    """清除问答历史"""
    # 实际应用中应该从数据库或文件中清除历史记录
    return {'status': 'success'}

def save_qa_result(question, answer, file_info):
    """保存问答结果"""
    try:
        file_id = file_info.get('id') if file_info else ''
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if file_id:
            db_save_qa_history(file_id, question, answer, ts)
            # 清除问答历史缓存，下次读取时重新从MySQL加载
            delete_cache(f"{CACHE_PREFIXES['qa_history']}{file_id}")
        return {
            'question': question,
            'answer': answer,
            'status': 'saved',
            'timestamp': ts,
        }
    except Exception:
        return {
            'question': question,
            'answer': answer,
            'status': 'error'
        }

def get_related_questions(question, file_info):
    """获取相关问题推荐"""
    # 简单的相关问题推荐实现
    # 实际应用中应该使用更复杂的算法
    related_questions = [
        f"{question}的定义是什么？",
        f"{question}有哪些相关实体？",
        f"{question}与其他实体的关系是什么？",
        f"{question}的属性有哪些？"
    ]
    return related_questions