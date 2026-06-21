import hashlib
import logging
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.utils.file import ocr_image
from app.services.inference.ner_engine import run_ner
from app.services.inference.relation_engine import run_relation_extraction
from app.database.redis_client import (
    get_cache, set_cache, CACHE_PREFIXES, CACHE_TTL
)

logger = logging.getLogger(__name__)


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


def _text_hash(text: str) -> str:
    """Generate a short hash for text content."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:16]


def extract_from_file(file_info: Dict[str, Any]) -> Dict[str, Any]:
    """从解析结果中抽取实体、关系、表格与OCR文本（带Redis缓存）。"""
    # 尝试从缓存获取文件级抽取结果
    file_id = file_info.get('id', '')
    if file_id:
        extract_cache_key = f"{CACHE_PREFIXES['extract_file']}{file_id}"
        cached_result = get_cache(extract_cache_key)
        if cached_result is not None:
            logger.info("[Redis] Extract result cache HIT for file=%s", file_id)
            return cached_result

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

    # 使用新的推理引擎
    ner_entities = run_ner(all_text)
    triplets = run_relation_extraction(all_text, ner_entities)

    # 转换为旧的数据结构格式
    entities = []
    seen_entities = set()
    for e in ner_entities:
        key = (e.text, e.label)
        if key not in seen_entities:
            seen_entities.add(key)
            entities.append({
                'text': e.text,
                'type': e.label,
                'start': e.start,
                'end': e.end,
            })

    relations = []
    seen_relations = set()
    for t in triplets:
        key = (t.head, t.relation, t.tail)
        if key not in seen_relations:
            seen_relations.add(key)
            relations.append({
                'subject': t.head,
                'predicate': t.relation,
                'object': t.tail,
            })

    table_data = []
    for table in tables:
        if isinstance(table, dict) and 'data' in table:
            table_data.append(table['data'])
        else:
            table_data.append(table)

    result = {
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

    # 缓存抽取结果
    _cache_extract_result(file_id, result)
    return result


def _cache_extract_result(file_id: str, result: Dict[str, Any]) -> None:
    """缓存抽取结果（内部辅助函数）。"""
    if file_id:
        extract_cache_key = f"{CACHE_PREFIXES['extract_file']}{file_id}"
        set_cache(extract_cache_key, result, CACHE_TTL['extract_file'])
        logger.info("[Redis] Extract result cached for file=%s", file_id)


def recognize_entities(text: str) -> List[Dict[str, Any]]:
    """实体识别：使用新的推理引擎。"""
    text = normalize_text(text)
    if not text:
        return []

    ner_entities = run_ner(text)
    
    entities = []
    seen = set()
    for e in ner_entities:
        key = (e.text, e.label)
        if key not in seen:
            seen.add(key)
            entities.append({
                'text': e.text,
                'type': e.label,
                'start': e.start,
                'end': e.end,
            })
    return entities


def extract_relations(text: str, entities: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, str]]:
    """关系抽取：使用新的推理引擎。"""
    text = normalize_text(text)
    if not text:
        return []

    # 转换entities为新引擎的格式
    from app.services.inference.schemas import EntityItem
    ner_entities = []
    if entities:
        for e in entities:
            ner_entities.append(
                EntityItem(
                    text=e.get('text', ''),
                    label=e.get('type', 'ENTITY'),
                    start=e.get('start', -1),
                    end=e.get('end', -1),
                    confidence=0.85
                )
            )
    
    triplets = run_relation_extraction(text, ner_entities)
    
    relations = []
    seen = set()
    for t in triplets:
        key = (t.head, t.relation, t.tail)
        if key not in seen:
            seen.add(key)
            relations.append({
                'subject': t.head,
                'predicate': t.relation,
                'object': t.tail,
            })
    return relations


def parse_table(filepath: str, table_index: int = 0):
    """解析表格数据。"""
    from app.utils.file import parse_file

    parse_result = parse_file(filepath)
    tables = parse_result.get('tables', [])

    if 0 <= table_index < len(tables):
        return tables[table_index]
    return []