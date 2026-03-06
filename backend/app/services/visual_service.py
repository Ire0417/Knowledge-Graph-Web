import math

def get_graph_layout(file_info, layout_type='force'):
    """获取图谱布局数据"""
    graph_result = file_info.get('graph_result', {})
    nodes = graph_result.get('nodes', [])
    edges = graph_result.get('edges', [])
    
    # 根据布局类型计算节点位置
    if layout_type == 'force':
        # 简单的力导向布局
        layout_nodes = force_layout(nodes, edges)
    elif layout_type == 'circle':
        # 环形布局
        layout_nodes = circle_layout(nodes)
    elif layout_type == 'radial':
        # 辐射布局
        layout_nodes = radial_layout(nodes, edges)
    elif layout_type == 'tree':
        # 树形布局
        layout_nodes = tree_layout(nodes, edges)
    else:
        # 默认使用力导向布局
        layout_nodes = force_layout(nodes, edges)
    
    return {
        'nodes': layout_nodes,
        'links': edges
    }

def force_layout(nodes, edges):
    """力导向布局"""
    # 简单的力导向布局实现
    # 实际应用中应该使用更复杂的算法
    for i, node in enumerate(nodes):
        node['x'] = 100 + (i % 5) * 200
        node['y'] = 100 + (i // 5) * 200
    return nodes

def circle_layout(nodes):
    """环形布局"""
    num_nodes = len(nodes)
    radius = 300
    
    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / num_nodes
        node['x'] = 400 + radius * math.cos(angle)
        node['y'] = 300 + radius * math.sin(angle)
    return nodes

def radial_layout(nodes, edges):
    """辐射布局"""
    # 简单的辐射布局实现
    # 实际应用中应该使用更复杂的算法
    if not nodes:
        return []
    
    # 中心节点
    center_node = nodes[0]
    center_node['x'] = 400
    center_node['y'] = 300
    
    # 其他节点围绕中心
    for i, node in enumerate(nodes[1:]):
        angle = 2 * math.pi * i / (len(nodes) - 1)
        radius = 200
        node['x'] = 400 + radius * math.cos(angle)
        node['y'] = 300 + radius * math.sin(angle)
    
    return nodes

def tree_layout(nodes, edges):
    """树形布局"""
    # 简单的树形布局实现
    # 实际应用中应该使用更复杂的算法
    if not nodes:
        return []
    
    # 根节点
    root_node = nodes[0]
    root_node['x'] = 400
    root_node['y'] = 100
    
    # 构建树结构
    tree = {root_node['id']: []}
    for edge in edges:
        if edge['source'] not in tree:
            tree[edge['source']] = []
        tree[edge['source']].append(edge['target'])
    
    # 递归计算节点位置
    def calculate_positions(node_id, x, y, level):
        children = tree.get(node_id, [])
        if not children:
            return
        
        child_count = len(children)
        spacing = 800 / (child_count + 1)
        
        for i, child_id in enumerate(children):
            child_x = x - 400 + (i + 1) * spacing
            child_y = y + 150
            
            for node in nodes:
                if node['id'] == child_id:
                    node['x'] = child_x
                    node['y'] = child_y
                    calculate_positions(child_id, child_x, child_y, level + 1)
                    break
    
    calculate_positions(root_node['id'], 400, 100, 0)
    
    # 为未定位的节点设置默认位置
    for node in nodes:
        if 'x' not in node:
            node['x'] = 400
            node['y'] = 300
    
    return nodes

def toggle_node(file_info, node_id):
    """节点展开/折叠"""
    # 简单的节点展开/折叠实现
    # 实际应用中应该根据图谱结构进行更复杂的处理
    return {
        'node_id': node_id,
        'status': 'toggled'
    }

def query_path(file_info, source_node_id, target_node_id):
    """路径查询"""
    graph_result = file_info.get('graph_result', {})
    nodes = graph_result.get('nodes', [])
    edges = graph_result.get('edges', [])
    
    # 简单的路径查询实现
    # 实际应用中应该使用更复杂的算法，如Dijkstra算法
    path_nodes = []
    path_edges = []
    
    # 查找源节点和目标节点
    source_node = None
    target_node = None
    for node in nodes:
        if node['id'] == source_node_id:
            source_node = node
        if node['id'] == target_node_id:
            target_node = node
    
    if source_node and target_node:
        path_nodes.append(source_node)
        path_nodes.append(target_node)
        
        # 查找连接源节点和目标节点的边
        for edge in edges:
            if (edge['source'] == source_node_id and edge['target'] == target_node_id) or \
               (edge['source'] == target_node_id and edge['target'] == source_node_id):
                path_edges.append(edge)
                break
    
    return {
        'nodes': path_nodes,
        'links': path_edges
    }

def query_neighbors(file_info, node_id, depth=1):
    """邻居查询"""
    graph_result = file_info.get('graph_result', {})
    nodes = graph_result.get('nodes', [])
    edges = graph_result.get('edges', [])
    
    # 查找节点的邻居
    neighbor_nodes = []
    neighbor_edges = []
    
    # 查找目标节点
    target_node = None
    for node in nodes:
        if node['id'] == node_id:
            target_node = node
            neighbor_nodes.append(node)
            break
    
    if target_node:
        # 查找直接邻居
        for edge in edges:
            if edge['source'] == node_id:
                # 查找目标节点
                for node in nodes:
                    if node['id'] == edge['target']:
                        neighbor_nodes.append(node)
                        neighbor_edges.append(edge)
                        break
            elif edge['target'] == node_id:
                # 查找源节点
                for node in nodes:
                    if node['id'] == edge['source']:
                        neighbor_nodes.append(node)
                        neighbor_edges.append(edge)
                        break
    
    return {
        'nodes': neighbor_nodes,
        'links': neighbor_edges
    }

def query_subgraph(file_info, node_ids):
    """子图查询"""
    graph_result = file_info.get('graph_result', {})
    nodes = graph_result.get('nodes', [])
    edges = graph_result.get('edges', [])
    
    # 查找指定节点及其相关边
    subgraph_nodes = []
    subgraph_edges = []
    
    # 查找指定节点
    for node in nodes:
        if node['id'] in node_ids:
            subgraph_nodes.append(node)
    
    # 查找连接这些节点的边
    for edge in edges:
        if edge['source'] in node_ids and edge['target'] in node_ids:
            subgraph_edges.append(edge)
    
    return {
        'nodes': subgraph_nodes,
        'links': subgraph_edges
    }

def get_graph_stats(file_info):
    """图谱统计信息"""
    graph_result = file_info.get('graph_result', {})
    nodes = graph_result.get('nodes', [])
    edges = graph_result.get('edges', [])
    
    # 计算统计信息
    node_count = len(nodes)
    edge_count = len(edges)
    
    # 计算节点类型分布
    type_distribution = {}
    for node in nodes:
        node_type = node.get('type', 'UNKNOWN')
        if node_type not in type_distribution:
            type_distribution[node_type] = 0
        type_distribution[node_type] += 1
    
    # 计算关系类型分布
    relation_distribution = {}
    for edge in edges:
        relation_type = edge.get('relationship', 'UNKNOWN')
        if relation_type not in relation_distribution:
            relation_distribution[relation_type] = 0
        relation_distribution[relation_type] += 1
    
    return {
        'node_count': node_count,
        'edge_count': edge_count,
        'type_distribution': type_distribution,
        'relation_distribution': relation_distribution
    }