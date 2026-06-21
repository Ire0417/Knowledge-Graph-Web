import uuid

def build_graph(file_info):
    """构建知识图谱 - 完全使用知识抽取结果"""
    extract_result = file_info.get('extract_result', {})
    
    # 优先从 extract_result 中获取原始抽取结果
    entities = extract_result.get('entities', [])
    relations = extract_result.get('relations', [])
    triplets = extract_result.get('triplets', [])
    
    # 如果有原始 triplets 但没有 relations，转换一下
    if not relations and triplets:
        relations = [
            {"subject": t.get("head", ""), "predicate": t.get("relation", ""), "object": t.get("tail", "")}
            for t in triplets
        ]
    
    print(f"Entities count: {len(entities)}")
    print(f"Relations count: {len(relations)}")
    
    # 构建图谱数据结构
    nodes = []
    edges = []
    
    # 处理实体 - 兼容两种格式
    entity_map = {}
    for entity in entities:
        # 兼容两种格式：{'text': ..., 'label': ...} 或 {'text': ..., 'type': ...}
        entity_text = entity.get('text', entity.get('name', ''))
        entity_type = entity.get('label', entity.get('type', 'ENTITY'))
        node_id = str(uuid.uuid4())
        entity_map[entity_text] = node_id
        nodes.append({
            'id': node_id,
            'name': entity_text,
            'type': entity_type
        })
    
    # 处理关系
    for relation in relations:
        subject = relation.get('subject', '')
        predicate = relation.get('predicate', '')
        object_ = relation.get('object', '')
        
        # 同时兼容从 triplets 格式
        if not subject and 'head' in relation:
            subject = relation['head']
        if not predicate and 'relation' in relation:
            predicate = relation['relation']
        if not object_ and 'tail' in relation:
            object_ = relation['tail']
        
        if subject in entity_map and object_ in entity_map:
            edges.append({
                'source': entity_map[subject],
                'target': entity_map[object_],
                'relationship': predicate
            })
        else:
            print(f"Skipping relation: {subject} {predicate} {object_}")
            print(f"Subject in entity_map: {subject in entity_map}")
            print(f"Object in entity_map: {object_ in entity_map}")
    
    print(f"Final nodes: {len(nodes)}")
    print(f"Final edges: {len(edges)}")
    
    return {
        'nodes': nodes,
        'edges': edges
    }


# 尝试把构建好的图谱保存到 Neo4j（如果可用）
try:
    from app.database.neo4j import save_graph
except Exception:
    save_graph = None


def build_and_persist_graph(file_info):
    graph = build_graph(file_info)
    file_info['graph_result'] = graph
    # 若 Neo4j 可用，尝试保存
    if save_graph and file_info.get('id'):
        try:
            save_graph(file_info.get('id'), graph)
        except Exception:
            pass
    return graph

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