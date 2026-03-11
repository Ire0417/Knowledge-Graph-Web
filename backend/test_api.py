import importlib.util
import io
import os
import sys

import pytest

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_flask_app():
    """从 backend/app.py 动态加载 Flask app，避免与 app 包同名冲突。"""
    app_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
    spec = importlib.util.spec_from_file_location('backend_entry_app', app_file)
    if spec is None or spec.loader is None:
        raise RuntimeError('Unable to load backend/app.py for testing')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app


@pytest.fixture(scope='module')
def client():
    app = _load_flask_app()
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture()
def file_id(client):
    from app.api.upload import uploaded_files

    uploaded_files.clear()
    data = {
        'file': (
            io.BytesIO(
                '张三是北京大学校长\n李四是清华大学教授\n北京位于中国\n北京大学包含数学学院和物理学院\n'.encode('utf-8')
            ),
            'test_file.txt',
        )
    }
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    payload = response.get_json()
    assert payload is not None
    assert payload.get('success') is True
    return payload['fileId']


def test_upload_file(client):
    data = {'file': (io.BytesIO('测试上传文件'.encode('utf-8')), 'upload_only.txt')}
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    payload = response.get_json()

    assert response.status_code == 200
    assert payload is not None
    assert payload.get('success') is True
    assert payload.get('fileId')


def test_parse_file(client, file_id, monkeypatch):
    import app.api.upload as upload_api

    monkeypatch.setattr(
        upload_api,
        'build_file_vector_store',
        lambda *_args, **_kwargs: {'chunk_count': 1, 'vector_store_path': 'mock'},
    )

    response = client.post('/upload/parse', json={'fileId': file_id})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload is not None
    assert payload.get('success') is True


def test_extract(client, file_id, monkeypatch):
    import app.api.extract as extract_api
    import app.api.upload as upload_api

    monkeypatch.setattr(
        upload_api,
        'build_file_vector_store',
        lambda *_args, **_kwargs: {'chunk_count': 1, 'vector_store_path': 'mock'},
    )
    monkeypatch.setattr(
        extract_api,
        'extract_from_file',
        lambda _file_info: {
            'entities': [{'text': '张三', 'type': 'PERSON'}],
            'relations': [{'subject': '张三', 'predicate': '是', 'object': '北京大学校长'}],
        },
    )

    parse_response = client.post('/upload/parse', json={'fileId': file_id})
    assert parse_response.get_json().get('success') is True

    extract_response = client.post('/extract/', json={'fileId': file_id})
    extract_payload = extract_response.get_json()
    assert extract_response.status_code == 200
    assert extract_payload is not None
    assert extract_payload.get('success') is True

    result_response = client.get(f'/extract/result/{file_id}')
    result_payload = result_response.get_json()
    assert result_response.status_code == 200
    assert result_payload is not None
    assert result_payload.get('success') is True


def test_build_graph(client, file_id, monkeypatch):
    import app.api.extract as extract_api
    import app.api.graph as graph_api
    import app.api.upload as upload_api

    monkeypatch.setattr(
        upload_api,
        'build_file_vector_store',
        lambda *_args, **_kwargs: {'chunk_count': 1, 'vector_store_path': 'mock'},
    )
    monkeypatch.setattr(
        extract_api,
        'extract_from_file',
        lambda _file_info: {
            'entities': [{'text': '张三', 'type': 'PERSON'}],
            'relations': [{'subject': '张三', 'predicate': '是', 'object': '北京大学校长'}],
        },
    )
    monkeypatch.setattr(
        graph_api,
        'build_graph',
        lambda _file_info: {
            'nodes': [{'id': '张三', 'label': '张三'}],
            'links': [{'source': '张三', 'target': '北京大学校长', 'label': '是'}],
        },
    )
    monkeypatch.setattr(
        graph_api,
        'get_graph_data',
        lambda file_info: file_info.get('graph_result', {'nodes': [], 'links': []}),
    )

    assert client.post('/upload/parse', json={'fileId': file_id}).get_json().get('success') is True
    assert client.post('/extract/', json={'fileId': file_id}).get_json().get('success') is True

    build_response = client.post('/graph/build', json={'fileId': file_id})
    build_payload = build_response.get_json()
    assert build_response.status_code == 200
    assert build_payload is not None
    assert build_payload.get('success') is True

    data_response = client.get(f'/graph/data/{file_id}')
    data_payload = data_response.get_json()
    assert data_response.status_code == 200
    assert data_payload is not None
    assert data_payload.get('success') is True
