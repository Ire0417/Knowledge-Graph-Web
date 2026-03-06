import spacy
import re
from app.data_processing.file_parser import ocr_image

# 加载Spacy模型
try:
    nlp = spacy.load('zh_core_web_sm')
except Exception as e:
    print(f'Error loading Spacy model: {e}')
    # 如果模型加载失败，使用一个简单的实体识别方法
    nlp = None

def extract_from_file(file_info):
    """从文件中抽取知识"""
    parse_result = file_info.get('parse_result', {})
    text = parse_result.get('text', '')
    tables = parse_result.get('tables', [])
    images = parse_result.get('images', [])
    
    # 抽取实体
    entities = recognize_entities(text)
    
    # 抽取关系
    relations = extract_relations(text)
    
    # 处理表格数据
    table_data = []
    for table in tables:
        if isinstance(table, dict) and 'data' in table:
            table_data.append(table['data'])
        else:
            table_data.append(table)
    
    # 处理图片OCR
    image_texts = []
    for image in images:
        if isinstance(image, str) and image.endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            ocr_result = ocr_image(image)
            if ocr_result:
                image_texts.append(ocr_result)
                # 从OCR结果中抽取实体和关系
                ocr_entities = recognize_entities(ocr_result)
                entities.extend(ocr_entities)
                ocr_relations = extract_relations(ocr_result)
                relations.extend(ocr_relations)
    
    return {
        'entities': entities,
        'relations': relations,
        'table_data': table_data,
        'image_texts': image_texts
    }

def recognize_entities(text):
    """实体识别"""
    entities = []
    
    if nlp:
        # 使用Spacy进行实体识别
        doc = nlp(text)
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'type': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
    else:
        # 简单的实体识别方法
        # 识别人名
        person_pattern = r'[\u4e00-\u9fa5]{2,4}'
        for match in re.finditer(person_pattern, text):
            entities.append({
                'text': match.group(),
                'type': 'PERSON',
                'start': match.start(),
                'end': match.end()
            })
        
        # 识别组织名
        org_pattern = r'[\u4e00-\u9fa5]+(公司|企业|机构|大学|学院|研究所)'
        for match in re.finditer(org_pattern, text):
            entities.append({
                'text': match.group(),
                'type': 'ORG',
                'start': match.start(),
                'end': match.end()
            })
    
    return entities

def extract_relations(text):
    """关系抽取"""
    relations = []
    
    # 简单的关系抽取规则，支持中文
    patterns = [
        (r'([\w\u4e00-\u9fa5]+)是([\w\u4e00-\u9fa5]+)', 'IS_A'),
        (r'([\w\u4e00-\u9fa5]+)在([\w\u4e00-\u9fa5]+)', 'LOCATED_IN'),
        (r'([\w\u4e00-\u9fa5]+)属于([\w\u4e00-\u9fa5]+)', 'PART_OF'),
        (r'([\w\u4e00-\u9fa5]+)包含([\w\u4e00-\u9fa5]+)', 'HAS_PART'),
        (r'([\w\u4e00-\u9fa5]+)创建([\w\u4e00-\u9fa5]+)', 'CREATED_BY'),
        (r'([\w\u4e00-\u9fa5]+)使用([\w\u4e00-\u9fa5]+)', 'USED_BY')
    ]
    
    for pattern, relation_type in patterns:
        for match in re.finditer(pattern, text):
            relations.append({
                'subject': match.group(1),
                'predicate': relation_type,
                'object': match.group(2)
            })
    
    return relations

def parse_table(filepath, table_index=0):
    """解析表格数据"""
    from app.data_processing.file_parser import parse_file
    parse_result = parse_file(filepath)
    tables = parse_result.get('tables', [])
    
    if table_index < len(tables):
        return tables[table_index]
    else:
        return []