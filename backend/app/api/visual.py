from flask import Blueprint, request, jsonify
from app.api.upload import uploaded_files
from app.services.visual_service import get_graph_layout, toggle_node, query_path, query_neighbors, query_subgraph, get_graph_stats

bp = Blueprint('visual', __name__)

@bp.route('/layout/<file_id>', methods=['GET'])
def get_layout(file_id):
    """获取图谱布局数据"""
    if file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    file_info = uploaded_files[file_id]
    if file_info.get('status') != 'graph_built':
        return jsonify({'success': False, 'message': 'Graph not built yet'})
    
    try:
        layout_type = request.args.get('type', 'force')
        layout_data = get_graph_layout(file_info, layout_type)
        return jsonify({'success': True, 'data': layout_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/toggle-node', methods=['POST'])
def toggle_node_route():
    """节点展开/折叠"""
    data = request.get_json()
    file_id = data.get('fileId')
    node_id = data.get('nodeId')
    
    if not file_id or file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    if not node_id:
        return jsonify({'success': False, 'message': 'Node ID is required'})
    
    try:
        result = toggle_node(uploaded_files[file_id], node_id)
        return jsonify({'success': True, 'message': 'Node toggled successfully', 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/query-path', methods=['POST'])
def query_path_route():
    """路径查询"""
    data = request.get_json()
    file_id = data.get('fileId')
    source_node_id = data.get('sourceNodeId')
    target_node_id = data.get('targetNodeId')
    
    if not file_id or file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    if not source_node_id or not target_node_id:
        return jsonify({'success': False, 'message': 'Source and target node IDs are required'})
    
    try:
        path_data = query_path(uploaded_files[file_id], source_node_id, target_node_id)
        return jsonify({'success': True, 'data': path_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/neighbors/<file_id>/<node_id>', methods=['GET'])
def get_neighbors(file_id, node_id):
    """邻居查询"""
    if file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    try:
        depth = int(request.args.get('depth', 1))
        neighbors = query_neighbors(uploaded_files[file_id], node_id, depth)
        return jsonify({'success': True, 'data': neighbors})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/subgraph', methods=['POST'])
def get_subgraph():
    """子图查询"""
    data = request.get_json()
    file_id = data.get('fileId')
    node_ids = data.get('nodeIds', [])
    
    if not file_id or file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    if not node_ids:
        return jsonify({'success': False, 'message': 'Node IDs are required'})
    
    try:
        subgraph = query_subgraph(uploaded_files[file_id], node_ids)
        return jsonify({'success': True, 'data': subgraph})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/stats/<file_id>', methods=['GET'])
def get_stats(file_id):
    """图谱统计信息"""
    if file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    file_info = uploaded_files[file_id]
    if file_info.get('status') != 'graph_built':
        return jsonify({'success': False, 'message': 'Graph not built yet'})
    
    try:
        stats = get_graph_stats(file_info)
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})