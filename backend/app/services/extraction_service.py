import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

import jieba.posseg as pseg

from app.data_processing.file_parser import ocr_image

ORG_SUFFIXES = (
    '公司', '集团', '大学', '学院', '研究院', '研究所', '实验室', '银行', '医院', '协会',
    '委员会', '部', '局', '厅', '中心', '学校', '法院', '检察院', '事务所', '平台'
)

LOCATION_SUFFIXES = (
    '省', '市', '区', '县', '镇', '乡', '村', '路', '街', '大道', '园区', '新区', '中国', '北京', '上海',
    '广州', '深圳', '杭州', '南京', '武汉', '成都', '重庆', '天津'
)

RELATION_HINT_TOKENS = ('是', '在', '位于', '属于', '包含', '由', '使用')

STOPWORDS = {
    '我们', '你们', '他们', '以及', '其中', '一个', '一种', '这个', '那个', '可以', '进行',
    '通过', '因为', '所以', '如果', '或者', '然后', '已经', '表示', '相关', '问题', '数据', '系统'
}


def normalize_text(text: str) -> str:
    """清洗文本，减少噪声字符对抽取效果的影响。"""
    if not text:
        return ''
    text = text.replace('\u3000', ' ').replace('\xa0', ' ')
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'[\t ]+', ' ', text)
    return text.strip()


def flatten_table_rows(tables: Sequence[Any]) -> str:
    """把表格内容压平成文本，以便参与实体关系抽取。"""
    rows: List[str] = []
    for table in tables:
        table_data = table.get('data') if isinstance(table, dict) else table
        if not isinstance(table_data, list):
            continue
        for row in table_data:
            if isinstance(row, list):
                rows.append(' '.join(str(cell).strip() for cell in row if str(cell).strip()))
            elif isinstance(row, str) and row.strip():
                rows.append(row.strip())
    return '\n'.join(rows)


def extract_from_file(file_info: Dict[str, Any]) -> Dict[str, Any]:
    """从解析结果中抽取实体、关系、表格与OCR文本。"""
    parse_result = file_info.get('parse_result', {})
    base_text = normalize_text(parse_result.get('text', '') or '')
    tables = parse_result.get('tables', []) or []
    images = parse_result.get('images', []) or []

    table_text = normalize_text(flatten_table_rows(tables))
    merged_text = '\n'.join([part for part in [base_text, table_text] if part])

    image_texts: List[str] = []
    for image in images:
        if isinstance(image, str) and image.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff')):
            ocr_result = normalize_text(ocr_image(image))
            if ocr_result:
                image_texts.append(ocr_result)

    all_text_parts = [merged_text] + image_texts
    all_text = '\n'.join(part for part in all_text_parts if part)

    entities = recognize_entities(all_text)
    relations = extract_relations(all_text, entities)

    table_data = []
    for table in tables:
        if isinstance(table, dict) and 'data' in table:
            table_data.append(table['data'])
        else:
            table_data.append(table)

    return {
        'entities': entities,
        'relations': relations,
        'table_data': table_data,
        'image_texts': image_texts,
        'stats': {
            'text_length': len(all_text),
            'entity_count': len(entities),
            'relation_count': len(relations),
        },
    }


def _add_entity(
    entities: List[Dict[str, Any]],
    seen: set,
    text: str,
    entity_type: str,
    start: Optional[int] = None,
    end: Optional[int] = None,
) -> None:
    text = text.strip(' ,，。；;:：()（）[]【】"\'')
    text = re.sub(r'(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])', '', text)
    if len(text) < 2:
        return
    if text.isdigit():
        return
    if entity_type in {'ORG', 'LOCATION', 'ENTITY'} and any(token in text for token in RELATION_HINT_TOKENS):
        return
    if entity_type == 'PERSON' and any(s in text for s in ORG_SUFFIXES):
        return
    if entity_type == 'ORG' and len(text) > 20:
        return
    key = (text, entity_type)
    if key in seen:
        return
    seen.add(key)
    entities.append({
        'text': text,
        'type': entity_type,
        'start': start if start is not None else -1,
        'end': end if end is not None else -1,
    })


def recognize_entities(text: str) -> List[Dict[str, Any]]:
    """实体识别：规则 + jieba词性 的多策略融合。"""
    text = normalize_text(text)
    if not text:
        return []

    entities: List[Dict[str, Any]] = []
    seen = set()

    pattern_specs: List[Tuple[str, str]] = [
        (r'[\u4e00-\u9fa5A-Za-z0-9]{2,20}(?:' + '|'.join(ORG_SUFFIXES) + r')', 'ORG'),
        (r'(?:19|20)\d{2}年(?:\d{1,2}月)?(?:\d{1,2}日)?', 'TIME'),
        (r'[\u4e00-\u9fa5]{2,12}(?:' + '|'.join(LOCATION_SUFFIXES) + r')', 'LOCATION'),
        (r'《[^》]{2,40}》', 'WORK'),
    ]

    for pattern, entity_type in pattern_specs:
        for m in re.finditer(pattern, text):
            _add_entity(entities, seen, m.group(), entity_type, m.start(), m.end())

    # 基于常见称谓的中文人名匹配。
    person_patterns = [
        r'([\u4e00-\u9fa5]{2,4})(?:先生|女士|老师|教授|博士|主任|总裁|经理)',
        r'(?:由|与|和)([\u4e00-\u9fa5]{2,4})(?:共同)?(?:创建|提出|研发|负责)'
    ]
    for pattern in person_patterns:
        for m in re.finditer(pattern, text):
            _add_entity(entities, seen, m.group(1), 'PERSON', m.start(1), m.end(1))

    try:
        for token in pseg.cut(text):
            word = token.word.strip()
            flag = token.flag
            if not word or len(word) < 2:
                continue
            if word in STOPWORDS:
                continue
            if re.fullmatch(r'[\W_]+', word):
                continue
            if flag in {'nr'}:
                _add_entity(entities, seen, word, 'PERSON')
            elif flag in {'nt'}:
                _add_entity(entities, seen, word, 'ORG')
            elif flag in {'ns'}:
                _add_entity(entities, seen, word, 'LOCATION')
            elif flag in {'nz', 'n'}:
                _add_entity(entities, seen, word, 'ENTITY')
    except Exception:
        pass

    # 频次过滤，降低一次性噪声词。
    freq: Dict[str, int] = {}
    for e in entities:
        freq[e['text']] = freq.get(e['text'], 0) + 1

    filtered = []
    for e in entities:
        text_len = len(e['text'])
        etype = e['type']
        if etype == 'ENTITY' and freq[e['text']] < 2:
            continue
        if text_len > 24:
            continue
        filtered.append(e)

    return filtered


def _clean_relation_endpoint(value: str) -> str:
    value = value.strip(' ,，。；;:：()（）[]【】"\'')
    value = re.sub(r'\s+', '', value)
    return value


def extract_relations(text: str, entities: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, str]]:
    """关系抽取：规则模板 + 句子级实体配对。"""
    text = normalize_text(text)
    if not text:
        return []

    relations: List[Dict[str, str]] = []
    seen = set()

    patterns = [
        (r'([\u4e00-\u9fa5A-Za-z0-9]{2,30})是([\u4e00-\u9fa5A-Za-z0-9]{2,30})', 'IS_A'),
        (r'([\u4e00-\u9fa5A-Za-z0-9]{2,30})在([\u4e00-\u9fa5A-Za-z0-9]{2,30})', 'LOCATED_IN'),
        (r'([\u4e00-\u9fa5A-Za-z0-9]{2,30})位于([\u4e00-\u9fa5A-Za-z0-9]{2,30})', 'LOCATED_IN'),
        (r'([\u4e00-\u9fa5A-Za-z0-9]{2,30})属于([\u4e00-\u9fa5A-Za-z0-9]{2,30})', 'PART_OF'),
        (r'([\u4e00-\u9fa5A-Za-z0-9]{2,30})包含([\u4e00-\u9fa5A-Za-z0-9]{2,30})', 'HAS_PART'),
        (r'([\u4e00-\u9fa5A-Za-z0-9]{2,30})由([\u4e00-\u9fa5A-Za-z0-9]{2,30})创建', 'CREATED_BY'),
        (r'([\u4e00-\u9fa5A-Za-z0-9]{2,30})使用([\u4e00-\u9fa5A-Za-z0-9]{2,30})', 'USES'),
    ]

    for pattern, relation_type in patterns:
        for match in re.finditer(pattern, text):
            subject = _clean_relation_endpoint(match.group(1))
            obj = _clean_relation_endpoint(match.group(2))
            if len(subject) < 2 or len(obj) < 2 or subject == obj:
                continue
            key = (subject, relation_type, obj)
            if key in seen:
                continue
            seen.add(key)
            relations.append({'subject': subject, 'predicate': relation_type, 'object': obj})

    if entities:
        entity_texts = [e.get('text', '').strip() for e in entities if e.get('text')]
        sentence_list = [s.strip() for s in re.split(r'[。！？!?\n]', text) if s.strip()]
        sentence_patterns: List[Tuple[str, str]] = [
            ('LOCATED_IN', r'(在|位于)'),
            ('PART_OF', r'属于'),
            ('HAS_PART', r'包含|包括'),
            ('CREATED_BY', r'由.*(创建|提出|研发)'),
            ('USES', r'使用|采用|基于'),
        ]

        for sentence in sentence_list:
            present = [name for name in entity_texts if name and name in sentence]
            if len(present) < 2:
                continue
            for predicate, clue in sentence_patterns:
                if not re.search(clue, sentence):
                    continue
                subject = present[0]
                obj = present[-1]
                if subject == obj:
                    continue
                key = (subject, predicate, obj)
                if key in seen:
                    continue
                seen.add(key)
                relations.append({'subject': subject, 'predicate': predicate, 'object': obj})

    return relations


def parse_table(filepath: str, table_index: int = 0):
    """解析表格数据。"""
    from app.data_processing.file_parser import parse_file

    parse_result = parse_file(filepath)
    tables = parse_result.get('tables', [])

    if 0 <= table_index < len(tables):
        return tables[table_index]
    return []