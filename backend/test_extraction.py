import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.extraction_service import recognize_entities, extract_relations

def test_extraction():
    """测试实体和关系提取"""
    # 测试文本
    test_text = "张三是北京大学校长，李四是清华大学教授。北京位于中国。北京大学包含数学学院和物理学院。"
    
    print("测试文本:")
    print(test_text)
    print("\n实体识别结果:")
    
    # 测试实体识别
    entities = recognize_entities(test_text)
    for entity in entities:
        print(f"{entity['text']} ({entity['type']})")
    
    print("\n关系提取结果:")
    # 测试关系提取
    relations = extract_relations(test_text, entities)
    for relation in relations:
        print(f"{relation['subject']} {relation['predicate']} {relation['object']}")
    
    print(f"\n实体数量: {len(entities)}")
    print(f"关系数量: {len(relations)}")

if __name__ == "__main__":
    test_extraction()
