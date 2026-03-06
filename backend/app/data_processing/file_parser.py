import os
import PyPDF2
from docx import Document
import pandas as pd
from PIL import Image
import pytesseract

def parse_file(filepath):
    """解析不同格式的文件"""
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.pdf':
        return parse_pdf(filepath)
    elif ext in ['.docx', '.doc']:
        return parse_docx(filepath)
    elif ext == '.txt':
        return parse_txt(filepath)
    elif ext == '.md':
        return parse_md(filepath)
    elif ext in ['.xlsx', '.xls']:
        return parse_excel(filepath)
    else:
        raise Exception(f'Unsupported file format: {ext}')

def parse_pdf(filepath):
    """解析PDF文件"""
    text = ''
    images = []
    tables = []
    
    with open(filepath, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        num_pages = len(reader.pages)
        
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            text += page.extract_text() + '\n'
            # 实际应用中，还需要提取图片和表格
    
    return {
        'text': text,
        'images': images,
        'tables': tables,
        'page_count': num_pages
    }

def parse_docx(filepath):
    """解析Word文件"""
    text = ''
    images = []
    tables = []
    
    try:
        doc = Document(filepath)
        
        # 验证文档结构
        if not hasattr(doc, 'paragraphs'):
            raise Exception('Invalid Word document structure')
        
        # 检查是否有实际内容
        if len(doc.paragraphs) == 0 and len(doc.tables) == 0:
            # 可能是Office主题文件或空文档
            raise Exception('Empty or non-standard Word document (possibly Office theme file)')
        
        # 提取文本
        for paragraph in doc.paragraphs:
            text += paragraph.text + '\n'
        
        # 提取表格
        for table in doc.tables:
            table_data = []
            for row in table.rows:
                row_data = [cell.text for cell in row.cells]
                table_data.append(row_data)
            tables.append(table_data)
        
        # 实际应用中，还需要提取图片
        
        return {
            'text': text,
            'images': images,
            'tables': tables,
            'paragraph_count': len(doc.paragraphs),
            'table_count': len(doc.tables)
        }
    except Exception as e:
        # 检查是否是Office主题文件
        import zipfile
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                # 检查Word文档的标准结构
                required_files = ['word/document.xml', 'word/body.xml']
                has_required_files = any(file in zf.namelist() for file in required_files)
                
                # 检查是否包含themeManager.xml
                has_theme_manager = 'word/themeManager.xml' in zf.namelist()
                
                if has_theme_manager and not has_required_files:
                    raise Exception('File appears to be an Office theme file, not a standard Word document')
        except:
            pass
        
        raise Exception(f'Failed to parse Word document: {str(e)}')

def parse_txt(filepath):
    """解析文本文件"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    return {
        'text': text,
        'line_count': len(text.split('\n'))
    }

def parse_md(filepath):
    """解析Markdown文件"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    return {
        'text': text,
        'line_count': len(text.split('\n'))
    }

def parse_excel(filepath):
    """解析Excel文件"""
    tables = []
    
    # 读取所有工作表
    xl = pd.ExcelFile(filepath)
    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name)
        # 处理空DataFrame
        if df.empty:
            continue
            
        # 将NaN替换为空字符串
        df = df.fillna('')
        
        table_data = df.values.tolist()
        # 添加表头
        headers = df.columns.tolist()
        table_data.insert(0, headers)
        tables.append({
            'sheet_name': sheet_name,
            'data': table_data
        })
    
    return {
        'tables': tables,
        'sheet_count': len(tables)
    }

def ocr_image(image_path):
    """OCR识别图片中的文字"""
    image = Image.open(image_path)
    # 确保 Tesseract 路径配置正确，这里允许抛出异常以便上层捕获
    text = pytesseract.image_to_string(image, lang='chi_sim')
    return text