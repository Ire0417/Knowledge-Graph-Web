import re

def ask_question(question, file_info):
    """智能问答"""
    graph_result = file_info.get('graph_result', {})
    nodes = graph_result.get('nodes', [])
    edges = graph_result.get('edges', [])
    
    # 简单的问答实现
    # 实际应用中应该使用更复杂的NLP算法
    
    # 提取问题中的实体
    question_entities = extract_entities_from_question(question)
    
    # 基于实体查找相关信息
    if question_entities:
        # 查找包含这些实体的节点
        related_nodes = []
        for entity in question_entities:
            for node in nodes:
                if entity in node['name']:
                    related_nodes.append(node)
        
        if related_nodes:
            # 查找与这些节点相关的关系
            related_edges = []
            for node in related_nodes:
                for edge in edges:
                    if edge['source'] == node['id'] or edge['target'] == node['id']:
                        related_edges.append(edge)
            
            # 构建答案
            answer = build_answer(question, related_nodes, related_edges, nodes)
            return answer
    
    # 默认回答
    return '抱歉，我无法回答这个问题。请尝试提供更具体的问题，或者确保您已经上传并处理了相关文件。'

def extract_entities_from_question(question):
    """从问题中提取实体"""
    # 简单的实体提取实现
    # 实际应用中应该使用更复杂的NLP算法
    entities = []
    
    # 提取中文实体
    chinese_pattern = r'[\u4e00-\u9fa5]{2,}'
    for match in re.finditer(chinese_pattern, question):
        entity = match.group()
        if len(entity) >= 2:
            entities.append(entity)
    
    return entities

def build_answer(question, related_nodes, related_edges, all_nodes):
    """构建答案"""
    # 简单的答案构建实现
    # 实际应用中应该使用更复杂的算法
    
    if '是什么' in question or '定义' in question:
        # 回答定义类问题
        if related_nodes:
            node = related_nodes[0]
            answer = f"{node['name']}是一个{node.get('type', '实体')}。"
            
            # 添加相关关系
            for edge in related_edges:
                if edge['source'] == node['id']:
                    target_node = next((n for n in all_nodes if n['id'] == edge['target']), None)
                    if target_node:
                        answer += f"它{get_relation_description(edge['relationship'])} {target_node['name']}。"
                elif edge['target'] == node['id']:
                    source_node = next((n for n in all_nodes if n['id'] == edge['source']), None)
                    if source_node:
                        answer += f"{source_node['name']} {get_relation_description(edge['relationship'])} 它。"
            
            return answer
    
    elif '关系' in question or '联系' in question:
        # 回答关系类问题
        if len(related_nodes) >= 2:
            node1 = related_nodes[0]
            node2 = related_nodes[1]
            
            # 查找两个节点之间的关系
            for edge in related_edges:
                if (edge['source'] == node1['id'] and edge['target'] == node2['id']) or \
                   (edge['source'] == node2['id'] and edge['target'] == node1['id']):
                    return f"{node1['name']}和{node2['name']}之间存在{get_relation_description(edge['relationship'])}的关系。"
            
            return f"{node1['name']}和{node2['name']}之间没有直接关系。"
    
    # 默认回答
    answer = "根据图谱数据，我了解到以下信息："
    for node in related_nodes[:3]:  # 只显示前3个相关节点
        answer += f"\n- {node['name']}（{node.get('type', '实体')}）"
    
    if related_edges:
        answer += "\n\n相关关系："
        for edge in related_edges[:3]:  # 只显示前3个相关关系
            source_node = next((n for n in all_nodes if n['id'] == edge['source']), None)
            target_node = next((n for n in all_nodes if n['id'] == edge['target']), None)
            if source_node and target_node:
                answer += f"\n- {source_node['name']} {get_relation_description(edge['relationship'])} {target_node['name']}"
    
    return answer

def get_relation_description(relation_type):
    """获取关系类型的描述"""
    relation_map = {
        'IS_A': '是',
        'PART_OF': '属于',
        'HAS_PART': '包含',
        'LOCATED_IN': '位于',
        'CREATED_BY': '由...创建',
        'USED_BY': '被...使用'
    }
    return relation_map.get(relation_type, relation_type)

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