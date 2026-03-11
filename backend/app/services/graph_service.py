import uuid

def build_graph(file_info):
    """构建知识图谱"""
    extract_result = file_info.get('extract_result', {})
    entities = extract_result.get('entities', [])
    relations = extract_result.get('relations', [])
    
    print(f"Entities count: {len(entities)}")
    print(f"Relations count: {len(relations)}")
    
    # 构建图谱数据结构
    nodes = []
    edges = []
    
    # 处理实体
    entity_map = {}
    for entity in entities:
        node_id = str(uuid.uuid4())
        entity_map[entity['text']] = node_id
        nodes.append({
            'id': node_id,
            'name': entity['text'],
            'type': entity.get('type', 'ENTITY')
        })
    
    # 处理关系
    for relation in relations:
        if relation['subject'] in entity_map and relation['object'] in entity_map:
            edges.append({
                'source': entity_map[relation['subject']],
                'target': entity_map[relation['object']],
                'relationship': relation['predicate']
            })
        else:
            print(f"Skipping relation: {relation['subject']} {relation['predicate']} {relation['object']}")
            print(f"Subject in entity_map: {relation['subject'] in entity_map}")
            print(f"Object in entity_map: {relation['object'] in entity_map}")
    
    print(f"Final nodes: {len(nodes)}")
    print(f"Final edges: {len(edges)}")
    
    return {
        'nodes': nodes,
        'edges': edges
    }

def get_graph_data(file_info):
    """获取图谱数据"""
    graph_result = file_info.get('graph_result', {})
    return {
        'nodes': graph_result.get('nodes', []),
        'links': graph_result.get('edges', [])
    }

def align_entities(file_info):
    """实体对齐"""
    # 简单的实体对齐实现
    # 实际应用中应该使用更复杂的算法
    graph_result = file_info.get('graph_result', {})
    nodes = graph_result.get('nodes', [])
    
    # 合并相同名称的实体
    entity_map = {}
    aligned_nodes = []
    
    for node in nodes:
        if node['name'] not in entity_map:
            entity_map[node['name']] = node
            aligned_nodes.append(node)
    
    # 更新图谱数据
    file_info['graph_result']['nodes'] = aligned_nodes
    
    return {
        'original_count': len(nodes),
        'aligned_count': len(aligned_nodes),
        'aligned_nodes': aligned_nodes
    }

def merge_relations(file_info):
    """关系合并"""
    graph_result = file_info.get('graph_result', {})
    edges = graph_result.get('edges', [])
    
    # 合并相同的关系
    relation_map = {}
    merged_edges = []
    
    for edge in edges:
        key = f"{edge['source']}-{edge['target']}-{edge['relationship']}"
        if key not in relation_map:
            relation_map[key] = edge
            merged_edges.append(edge)
    
    # 更新图谱数据
    file_info['graph_result']['edges'] = merged_edges
    
    return {
        'original_count': len(edges),
        'merged_count': len(merged_edges),
        'merged_edges': merged_edges
    }

def optimize_graph(file_info):
    """图谱优化"""
    # 简单的图谱优化实现
    # 实际应用中应该使用更复杂的算法
    graph_result = file_info.get('graph_result', {})
    nodes = graph_result.get('nodes', [])
    edges = graph_result.get('edges', [])
    
    # 计算节点度
    node_degree = {}
    for edge in edges:
        if edge['source'] not in node_degree:
            node_degree[edge['source']] = 0
        if edge['target'] not in node_degree:
            node_degree[edge['target']] = 0
        node_degree[edge['source']] += 1
        node_degree[edge['target']] += 1
    
    # 为节点添加度属性
    for node in nodes:
        node['degree'] = node_degree.get(node['id'], 0)
    
    return {
        'node_count': len(nodes),
        'edge_count': len(edges),
        'average_degree': sum(node_degree.values()) / len(node_degree) if node_degree else 0
    }