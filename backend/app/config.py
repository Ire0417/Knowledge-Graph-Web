from pydantic_settings import BaseSettings
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Settings(BaseSettings):
    base_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    upload_folder: str = ''
    max_content_length: int = 100 * 1024 * 1024
    allowed_extensions: set = {'pdf', 'docx', 'doc', 'txt', 'md', 'xlsx', 'xls', 'jpg', 'jpeg', 'png', 'bmp', 'tif', 'tiff'}
    vector_db_path: str = ''
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    rag_top_k: int = 4
    qwen_api_key: str = ''
    qwen_base_url: str = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    qwen_model: str = 'qwen-plus'
    qwen_embedding_model: str = 'text-embedding-v3'
    log_level: str = 'INFO'
    secret_key: str = 'your-secret-key-change-in-production'
    auto_cleanup_enabled: bool = True
    auto_cleanup_expire_days: int = 3
    auto_cleanup_interval_hours: int = 6

    class Config:
        env_file = '.env'
        extra = 'ignore'


settings = Settings()

for p in [settings.upload_folder, settings.vector_db_path]:
    if p and not os.path.exists(p):
        try:
            os.makedirs(p, exist_ok=True)
        except Exception:
            pass


class Config:
    BASE_DIR = settings.base_dir
    UPLOAD_FOLDER = settings.upload_folder or os.path.join(settings.base_dir, 'uploads')
    MAX_CONTENT_LENGTH = settings.max_content_length
    ALLOWED_EXTENSIONS = settings.allowed_extensions
    VECTOR_DB_PATH = settings.vector_db_path or os.path.join(settings.base_dir, 'vector_db')
    RAG_CHUNK_SIZE = settings.rag_chunk_size
    RAG_CHUNK_OVERLAP = settings.rag_chunk_overlap
    RAG_TOP_K = settings.rag_top_k
    QWEN_API_KEY = settings.qwen_api_key or os.getenv('QWEN_API_KEY', 'sk-05a6800100264672ae32b6015f6db83b')
    QWEN_BASE_URL = settings.qwen_base_url or os.getenv('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    QWEN_MODEL = settings.qwen_model or os.getenv('QWEN_MODEL', 'qwen-plus')
    QWEN_EMBEDDING_MODEL = settings.qwen_embedding_model or os.getenv('QWEN_EMBEDDING_MODEL', 'text-embedding-v3')
    LOG_LEVEL = settings.log_level
    SECRET_KEY = settings.secret_key
    AUTO_CLEANUP_ENABLED = settings.auto_cleanup_enabled
    AUTO_CLEANUP_EXPIRE_DAYS = settings.auto_cleanup_expire_days
    AUTO_CLEANUP_INTERVAL_HOURS = settings.auto_cleanup_interval_hours
