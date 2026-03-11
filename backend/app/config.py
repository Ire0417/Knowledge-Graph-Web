import os

class Config:
    # 上传文件配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'md', 'xlsx', 'xls', 'jpg', 'jpeg', 'png', 'bmp', 'tif', 'tiff'}
    
    # 向量数据库配置
    VECTOR_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vector_db')
    RAG_CHUNK_SIZE = 800
    RAG_CHUNK_OVERLAP = 120
    RAG_TOP_K = 4
    
    # 千问API配置
    QWEN_API_KEY = os.getenv('QWEN_API_KEY', 'sk-7a92829b0af2483ca132fdaf6359a10d')
    QWEN_BASE_URL = os.getenv('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    QWEN_MODEL = os.getenv('QWEN_MODEL', 'qwen-plus')
    QWEN_EMBEDDING_MODEL = os.getenv('QWEN_EMBEDDING_MODEL', 'text-embedding-v3')
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    
    # 其他配置
    SECRET_KEY = 'your-secret-key'
    
    # 确保上传目录存在
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # 确保向量数据库目录存在
    if not os.path.exists(VECTOR_DB_PATH):
        os.makedirs(VECTOR_DB_PATH)