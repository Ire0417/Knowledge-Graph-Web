from app.services.rag_service import rag_answer


def ask_question(question, file_id, file_info):
    """基于LangChain + RAG + 千问的智能问答。"""
    result = rag_answer(question=question, file_id=file_id, file_info=file_info)
    return result

def get_qa_history(file_info):
    """获取问答历史"""
    # 实际应用中应该从数据库或文件中获取历史记录
    return []

def clear_qa_history(file_info):
    """清除问答历史"""
    # 实际应用中应该从数据库或文件中清除历史记录
    return {'status': 'success'}

def save_qa_result(question, answer, file_info):
    """保存问答结果"""
    # 实际应用中应该将结果保存到数据库或文件中
    return {
        'question': question,
        'answer': answer,
        'status': 'saved'
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