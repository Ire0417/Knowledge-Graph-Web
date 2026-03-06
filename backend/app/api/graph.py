from flask import Blueprint, request, jsonify, send_file
import os
import tempfile
from app.api.upload import uploaded_files
from app.services.graph_service import build_graph, align_entities, merge_relations, optimize_graph, get_graph_data

bp = Blueprint('graph', __name__)

# 存储构建进度
build_progress = {}

@bp.route('/build', methods=['POST'])
def build():
    """构建知识图谱"""
    data = request.get_json()
    file_id = data.get('fileId')
    
    if not file_id or file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    file_info = uploaded_files[file_id]
    if file_info.get('status') != 'extracted':
        return jsonify({'success': False, 'message': 'Extraction not completed'})
    
    try:
        # 初始化构建进度
        build_progress[file_id] = 0
        
        # 执行图谱构建
        graph_result = build_graph(file_info)
        file_info['graph_result'] = graph_result
        file_info['status'] = 'graph_built'
        
        return jsonify({'success': True, 'message': 'Graph built successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/build/progress/<file_id>', methods=['GET'])
def get_build_progress(file_id):
    """获取构建进度"""
    if file_id not in build_progress:
        return jsonify({'success': False, 'message': 'Build not started'})
    
    # 实际应用中应该返回真实的构建进度
    return jsonify({'success': True, 'progress': 100, 'status': 'completed'})

@bp.route('/data/<file_id>', methods=['GET'])
def get_graph_data_route(file_id):
    """获取图谱数据"""
    if file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    file_info = uploaded_files[file_id]
    if file_info.get('status') != 'graph_built':
        return jsonify({'success': False, 'message': 'Graph not built yet'})
    
    try:
        graph_data = get_graph_data(file_info)
        return jsonify({'success': True, 'data': graph_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/align', methods=['POST'])
def align():
    """实体对齐"""
    data = request.get_json()
    file_id = data.get('fileId')
    
    if not file_id or file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    try:
        align_result = align_entities(uploaded_files[file_id])
        return jsonify({'success': True, 'message': 'Entities aligned successfully', 'result': align_result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/merge', methods=['POST'])
def merge():
    """关系合并"""
    data = request.get_json()
    file_id = data.get('fileId')
    
    if not file_id or file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    try:
        merge_result = merge_relations(uploaded_files[file_id])
        return jsonify({'success': True, 'message': 'Relations merged successfully', 'result': merge_result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/optimize', methods=['POST'])
def optimize():
    """图谱优化"""
    data = request.get_json()
    file_id = data.get('fileId')
    
    if not file_id or file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    try:
        optimize_result = optimize_graph(uploaded_files[file_id])
        return jsonify({'success': True, 'message': 'Graph optimized successfully', 'result': optimize_result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/export/<file_id>', methods=['GET'])
def export_graph(file_id):
    """导出图谱数据"""
    if file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    file_info = uploaded_files[file_id]
    if file_info.get('status') != 'graph_built':
        return jsonify({'success': False, 'message': 'Graph not built yet'})
    
    try:
        format = request.args.get('format', 'json')
        
        # 生成临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format}', delete=False) as f:
            if format == 'json':
                import json
                json.dump(file_info.get('graph_result', {}), f)
            elif format == 'csv':
                # 生成CSV格式
                pass
        
        # 发送文件
        return send_file(f.name, as_attachment=True, download_name=f'graph_{file_id}.{format}')
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})