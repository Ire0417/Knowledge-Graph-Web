from flask import Blueprint, request, jsonify
from app.api.upload import uploaded_files
from app.services.extraction_service import extract_from_file, recognize_entities, extract_relations, parse_table

bp = Blueprint('extract', __name__)

# 存储抽取进度
extraction_progress = {}

@bp.route('/', methods=['POST'])
def extract():
    """从文件中抽取知识"""
    data = request.get_json()
    file_id = data.get('fileId')
    
    if not file_id or file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    file_info = uploaded_files[file_id]
    if file_info.get('status') != 'parsed':
        return jsonify({'success': False, 'message': 'File not parsed yet'})
    
    try:
        # 初始化抽取进度
        extraction_progress[file_id] = 0
        
        # 执行知识抽取
        extract_result = extract_from_file(file_info)
        file_info['extract_result'] = extract_result
        file_info['status'] = 'extracted'
        
        return jsonify({'success': True, 'message': 'Extraction completed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/progress/<file_id>', methods=['GET'])
def get_extract_progress(file_id):
    """获取抽取进度"""
    if file_id not in extraction_progress:
        return jsonify({'success': False, 'message': 'Extraction not started'})
    
    # 实际应用中应该返回真实的抽取进度
    return jsonify({'success': True, 'progress': 100, 'status': 'completed'})

@bp.route('/result/<file_id>', methods=['GET'])
def get_extract_result(file_id):
    """获取抽取结果"""
    if file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    file_info = uploaded_files[file_id]
    if 'extract_result' not in file_info:
        return jsonify({'success': False, 'message': 'Extraction not completed'})
    
    return jsonify({'success': True, 'result': file_info['extract_result']})

@bp.route('/entities', methods=['POST'])
def extract_entities():
    """实体识别"""
    data = request.get_json()
    text = data.get('text')
    
    if not text:
        return jsonify({'success': False, 'message': 'Text is required'})
    
    try:
        entities = recognize_entities(text)
        return jsonify({'success': True, 'entities': entities})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/relations', methods=['POST'])
def extract_relations_route():
    """关系抽取"""
    data = request.get_json()
    text = data.get('text')
    
    if not text:
        return jsonify({'success': False, 'message': 'Text is required'})
    
    try:
        relations = extract_relations(text)
        return jsonify({'success': True, 'relations': relations})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/table', methods=['POST'])
def extract_table():
    """表格数据解析"""
    data = request.get_json()
    file_id = data.get('fileId')
    table_index = data.get('tableIndex', 0)
    
    if not file_id or file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    try:
        table_data = parse_table(uploaded_files[file_id]['path'], table_index)
        return jsonify({'success': True, 'tableData': table_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})