from flask import Blueprint, request, jsonify
import os
import uuid
from datetime import datetime
from app.config import Config
from app.data_processing.file_parser import parse_file
from app.services.rag_service import build_file_vector_store

bp = Blueprint('upload', __name__)

# 存储上传的文件信息
uploaded_files = {}

# 检查文件扩展名是否允许
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

import traceback

@bp.route('', methods=['POST'])
def upload_file():
    """文件上传接口"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'})
        
        if file and allowed_file(file.filename):
            # 生成唯一文件名
            file_id = str(uuid.uuid4())
            filename = f"{file_id}_{file.filename}"
            
            # 使用 os.path.normpath 规范化路径，避免 Windows 下路径问题
            upload_folder = os.path.normpath(Config.UPLOAD_FOLDER)
            filepath = os.path.join(upload_folder, filename)
            
            # 确保上传目录存在
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            file.save(filepath)
            
            # 存储文件信息
            uploaded_files[file_id] = {
                'id': file_id,
                'name': file.filename,
                'path': filepath,
                'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'uploaded'
            }
            
            return jsonify({'success': True, 'fileId': file_id, 'message': 'File uploaded successfully'})
        else:
            return jsonify({'success': False, 'message': 'File type not allowed'})
            
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server Error: {str(e)}'}), 500

@bp.route('/parse', methods=['POST'])
def parse_uploaded_file():
    """解析上传的文件"""
    data = request.get_json(silent=True) or {}
    file_id = data.get('fileId')
    
    if not file_id or file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    file_info = uploaded_files[file_id]
    try:
        # 检查文件是否存在
        if not os.path.exists(file_info['path']):
            return jsonify({'success': False, 'message': 'File does not exist on server'})
        
        # 检查文件大小
        file_size = os.path.getsize(file_info['path'])
        if file_size > 100 * 1024 * 1024:  # 100MB限制
            return jsonify({'success': False, 'message': 'File too large (max 100MB)'})
        
        # 解析文件
        print(f"开始解析文件: {file_info['path']}")
        parse_result = parse_file(file_info['path'])
        file_info['parse_result'] = parse_result
        file_info['status'] = 'parsed'
        file_info['parse_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        vector_result = {'chunk_count': 0, 'vector_store_path': ''}
        vector_warning = ''

        # 解析后尝试向量化；若失败，不影响解析成功状态。
        try:
            vector_result = build_file_vector_store(file_id, file_info)
            file_info['rag_ready'] = True
            file_info.pop('rag_error', None)
        except Exception as vector_err:
            file_info['rag_ready'] = False
            vector_warning = f'Vector build skipped: {str(vector_err)}'
            file_info['rag_error'] = vector_warning
            print(f"Vector build failed for {file_id}: {vector_warning}")
        
        print(f"文件解析成功: {file_info['name']}")
        return jsonify({
            'success': True,
            'message': 'File parsed successfully',
            'chunkCount': vector_result.get('chunk_count', 0),
            'ragReady': bool(file_info.get('rag_ready')),
            'warning': vector_warning,
        })
    except Exception as e:
        print(f"Error parsing file: {str(e)}")
        traceback.print_exc()
        # 提供更详细的错误信息
        error_msg = f'Parse error: {str(e)}'
        # 常见错误处理
        if 'Unsupported file format' in str(e):
            error_msg = 'Unsupported file format. Please upload PDF, DOCX, Excel, TXT, Markdown, or image files.'
        elif 'No such file or directory' in str(e):
            error_msg = 'File not found on server. Please upload the file again.'
        elif 'Permission denied' in str(e):
            error_msg = 'Server permission error. Please contact administrator.'
        elif 'Legacy .doc is not supported' in str(e):
            error_msg = 'Legacy .doc is not supported yet. Please convert it to .docx and retry.'
        
        file_info['status'] = 'parse_failed'
        file_info['parse_error'] = error_msg
        return jsonify({'success': False, 'message': error_msg})

@bp.route('/parse/progress/<file_id>', methods=['GET'])
def get_parse_progress(file_id):
    """获取解析进度"""
    if file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    # 实际应用中应该返回真实的解析进度
    return jsonify({'success': True, 'progress': 100, 'status': 'completed'})

@bp.route('/files', methods=['GET'])
def get_file_list():
    """获取文件列表"""
    files = []
    for file_id, file_info in uploaded_files.items():
        files.append({
            'id': file_id,
            'name': file_info['name'],
            'size': os.path.getsize(file_info['path']) if 'path' in file_info else 0,
            'uploadTime': file_info.get('upload_time', ''),
            'status': file_info.get('status', 'uploaded')
        })
    return jsonify({'success': True, 'files': files})

@bp.route('/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """删除文件"""
    if file_id not in uploaded_files:
        return jsonify({'success': False, 'message': 'File not found'})
    
    file_info = uploaded_files[file_id]
    if 'path' in file_info and os.path.exists(file_info['path']):
        os.remove(file_info['path'])
    
    del uploaded_files[file_id]
    return jsonify({'success': True, 'message': 'File deleted successfully'})