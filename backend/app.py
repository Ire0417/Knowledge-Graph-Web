from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from app.api import upload, extract, graph, visual, qa
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)

# 配置CORS，允许来自http://localhost:3004和http://localhost:3006的跨域请求
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3004", "http://localhost:3006", "http://127.0.0.1:3004", "http://127.0.0.1:3006"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "supports_credentials": True
    }
})

# 注册API蓝图
app.register_blueprint(upload.bp, url_prefix='/upload')
app.register_blueprint(extract.bp, url_prefix='/extract')
app.register_blueprint(graph.bp, url_prefix='/graph')
app.register_blueprint(visual.bp, url_prefix='/visual')
app.register_blueprint(qa.bp, url_prefix='/qa')

# 健康检查
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)