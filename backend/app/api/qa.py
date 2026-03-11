from flask import Blueprint, request, jsonify
from datetime import datetime
from app.api.upload import uploaded_files
from app.services.qa_service import ask_question, get_qa_history, clear_qa_history, save_qa_result, get_related_questions
from app.services.rag_service import check_rag_health

bp = Blueprint('qa', __name__)

# 存储问答历史
qa_history = {}


@bp.route('/health', methods=['GET'])
def health():
    """问答/RAG健康检查。"""
    file_id = request.args.get('fileId', '')
    file_info = uploaded_files.get(file_id) if file_id else None

    report = check_rag_health(file_info=file_info)
    return jsonify({'success': report.get('ok', False), 'health': report})

@bp.route('/ask', methods=['POST'])
def ask():
    """智能问答"""
    data = request.get_json(silent=True) or {}
    question = data.get('question')
    file_id = data.get('fileId')
    
    if not question:
        return jsonify({'success': False, 'message': 'Question is required'})
    
    if not file_id or file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    file_info = uploaded_files[file_id]
    if file_info.get('status') not in ['parsed', 'extracted', 'graph_built'] and not file_info.get('rag_ready'):
        parse_error = file_info.get('parse_error')
        msg = 'File is not parsed yet'
        if parse_error:
            msg = f'File parse failed: {parse_error}'
        return jsonify({'success': False, 'message': msg})
    
    try:
        rag_result = ask_question(question, file_id, file_info)
        answer = rag_result.get('answer', '')
        sources = rag_result.get('sources', [])
        
        # 保存问答历史
        if file_id not in qa_history:
            qa_history[file_id] = []
        qa_history[file_id].append({
            'question': question,
            'answer': answer,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        return jsonify({'success': True, 'answer': answer, 'sources': sources})
    except Exception as e:
        return jsonify({'success': False, 'message': f'QA failed: {str(e)}'})

@bp.route('/history/<file_id>', methods=['GET'])
def get_history(file_id):
    """获取问答历史"""
    if file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    history = qa_history.get(file_id, [])
    return jsonify({'success': True, 'history': history})

@bp.route('/history/<file_id>', methods=['DELETE'])
def clear_history(file_id):
    """清除问答历史"""
    if file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    if file_id in qa_history:
        del qa_history[file_id]
    
    return jsonify({'success': True, 'message': 'History cleared successfully'})

@bp.route('/save', methods=['POST'])
def save():
    """保存问答结果"""
    data = request.get_json()
    question = data.get('question')
    answer = data.get('answer')
    file_id = data.get('fileId')
    
    if not question or not answer:
        return jsonify({'success': False, 'message': 'Question and answer are required'})
    
    if not file_id or file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    try:
        result = save_qa_result(question, answer, uploaded_files[file_id])
        return jsonify({'success': True, 'message': 'Q&A result saved successfully', 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/related', methods=['POST'])
def get_related():
    """相关问题推荐"""
    data = request.get_json()
    question = data.get('question')
    file_id = data.get('fileId')
    
    if not question:
        return jsonify({'success': False, 'message': 'Question is required'})
    
    if not file_id or file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    try:
        related = get_related_questions(question, uploaded_files[file_id])
        return jsonify({'success': True, 'questions': related})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})