"""
Unit tests for api.py view functions.
Tests all HTTP request handling for API endpoints.
"""

import pytest
import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse

# Ensure `tutorial` package is importable
tests_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(tests_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from myapp.views import api


class TestApiEndpoints:
    """Tests for api_endpoints view."""
    
    def test_api_endpoints_success(self):
        """Test successful retrieval of API endpoints."""
        request = RequestFactory().get('/api/endpoints', SERVER_NAME='testserver')
        
        with patch('myapp.views.api.get_resolver') as _, \
             patch('myapp.views.api.api_utils.extract_api_endpoints') as mock_extract:
            mock_extract.return_value = [
                {'path': '/api/sql', 'name': 'api_sql'},
                {'path': '/api/run', 'name': 'api_run_sql'}
            ]
            
            response = api.api_endpoints(request)
            
            assert response.status_code == 200
            data = json.loads(response.content)
            assert 'endpoints' in data
            assert 'count' in data
            assert data['count'] == 2
    
    def test_api_endpoints_handles_exception(self):
        """Test error handling when endpoint extraction fails."""
        request = RequestFactory().get('/api/endpoints', SERVER_NAME='testserver')
        
        with patch('myapp.views.api.get_resolver') as mock_resolver:
            mock_resolver.side_effect = Exception('Resolver error')
            
            response = api.api_endpoints(request)
            
            assert response.status_code == 500
            assert b"Could not get endpoints" in response.content


class TestApiSql:
    """Tests for api_sql view (single SQL file operations)."""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = Mock(spec=User)
        user.username = 'testuser_admin'
        user.is_authenticated = True
        return user
    
    @pytest.fixture
    def authenticated_request(self, mock_user):
        """Create an authenticated request."""
        factory = RequestFactory()
        request = factory.get('/api/sql/test.sql')
        request.user = mock_user
        return request
    
    @patch('myapp.views.api.sqllock_release')
    @patch('myapp.views.api.get_user_directory')
    @patch('myapp.views.api.api_utils.save_sql_file')
    def test_api_sql_post_success(self, mock_save, mock_get_dir, mock_unlock, mock_user):
        """Test POST request to save SQL file."""
        mock_get_dir.return_value = '/tmp/testuser_admin'
        
        request = RequestFactory().post(
            '/api/sql/test.sql',
            data=json.dumps({'sql': 'SELECT 1;'}),
            content_type='application/json'
        )
        request.user = mock_user
        
        response = api.api_sql(request, 'test.sql')
        
        assert response.status_code == 200
        assert b"File saved successfully" in response.content
        mock_save.assert_called_once_with('/tmp/testuser_admin', 'test.sql', 'SELECT 1;')
        mock_unlock.assert_called()
    
    @patch('myapp.views.api.sqllock_release')
    @patch('myapp.views.api.get_user_directory')
    @patch('myapp.views.api.api_utils.read_sql_file')
    def test_api_sql_get_success(self, mock_read, mock_get_dir, mock_unlock, mock_user):
        """Test GET request to read SQL file."""
        mock_get_dir.return_value = '/tmp/testuser_admin'
        mock_read.return_value = 'SELECT * FROM users;'
        
        request = RequestFactory().get('/api/sql/query.sql')
        request.user = mock_user
        
        response = api.api_sql(request, 'query.sql')
        
        assert response.status_code == 200
        assert response.content == b'SELECT * FROM users;'
        assert response['Content-Type'] == 'text/sql'
        mock_read.assert_called_once_with('/tmp/testuser_admin', 'query.sql')
    
    @patch('myapp.views.api.sqllock_release')
    @patch('myapp.views.api.get_user_directory')
    @patch('myapp.views.api.api_utils.delete_sql_file')
    def test_api_sql_delete_success(self, mock_delete, mock_get_dir, mock_unlock, mock_user):
        """Test DELETE request to remove SQL file."""
        mock_get_dir.return_value = '/tmp/testuser_admin'
        mock_delete.return_value = True
        
        request = RequestFactory().delete('/api/sql/old.sql')
        request.user = mock_user
        
        response = api.api_sql(request, 'old.sql')
        
        assert response.status_code == 200
        assert b"File deleted successfully" in response.content
        mock_delete.assert_called_once_with('/tmp/testuser_admin', 'old.sql')
    
    @patch('myapp.views.api.sqllock_release')
    @patch('myapp.views.api.get_user_directory')
    @patch('myapp.views.api.api_utils.delete_sql_file')
    def test_api_sql_delete_not_found(self, mock_delete, mock_get_dir, mock_unlock, mock_user):
        """Test DELETE request for non-existent file."""
        mock_get_dir.return_value = '/tmp/testuser_admin'
        mock_delete.return_value = False
        
        request = RequestFactory().delete('/api/sql/nonexistent.sql')
        request.user = mock_user
        
        response = api.api_sql(request, 'nonexistent.sql')
        
        assert response.status_code == 404
        assert b"File not found" in response.content
    
    @patch('myapp.views.api.sqllock_release')
    @patch('myapp.views.api.get_user_directory')
    @patch('myapp.views.api.api_utils.read_sql_file')
    def test_api_sql_handles_exception(self, mock_read, mock_get_dir, mock_unlock, mock_user):
        """Test error handling in api_sql."""
        mock_get_dir.return_value = '/tmp/testuser_admin'
        mock_read.side_effect = Exception('Read error')
        
        request = RequestFactory().get('/api/sql/test.sql')
        request.user = mock_user
        
        response = api.api_sql(request, 'test.sql')
        
        assert response.status_code == 500
        assert b"Unknown request" in response.content
        mock_unlock.assert_called()


class TestApiSqlAll:
    """Tests for api_sql_all view (replace all SQL files)."""
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.username = 'testuser_admin'
        return user
    
    @patch('myapp.views.api.sqllock_release')
    @patch('myapp.utils.directories.sqllock_get')
    @patch('myapp.views.api.get_user_directory')
    @patch('myapp.views.api.api_utils.replace_all_sql_files')
    def test_api_sql_all_post_success(self, mock_replace, mock_get_dir, mock_lock, mock_unlock, mock_user):
        """Test POST request to replace all SQL files."""
        mock_get_dir.return_value = '/tmp/testuser'
        
        files_data = [
            {'filename': 'query1.sql', 'sql': 'SELECT 1;'},
            {'filename': 'query2.sql', 'sql': 'SELECT 2;'}
        ]
        
        request = RequestFactory().post(
            '/api/sql/all',
            data=json.dumps({'files': files_data}),
            content_type='application/json'
        )
        request.user = mock_user
        
        response = api.api_sql_all(request)
        
        assert response.status_code == 200
        assert b"Files saved successfully" in response.content
        mock_replace.assert_called_once_with('/tmp/testuser', files_data)
        mock_lock.assert_called_once()
        mock_unlock.assert_called()
    
    @patch('myapp.views.api.sqllock_release')
    @patch('myapp.utils.directories.sqllock_get')
    @patch('myapp.views.api.get_user_directory')
    @patch('myapp.views.api.api_utils.replace_all_sql_files')
    def test_api_sql_all_handles_exception(self, mock_replace, mock_get_dir, mock_lock, mock_unlock, mock_user):
        """Test error handling in api_sql_all."""
        mock_get_dir.return_value = '/tmp/testuser_admin'
        mock_replace.side_effect = Exception('Replace error')
        
        request = RequestFactory().post(
            '/api/sql/all',
            data=json.dumps({'files': []}),
            content_type='application/json'
        )
        request.user = mock_user
        
        response = api.api_sql_all(request)
        
        assert response.status_code == 500
        assert b"Internal error while saving SQL files" in response.content


class TestApiSqlList:
    """Tests for api_sql_list view (list SQL files)."""
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.username = 'testuser_admin'
        return user
    
    @patch('myapp.views.api.sqllock_release')
    @patch('myapp.utils.directories.sqllock_get')
    @patch('myapp.views.api.get_user_directory')
    @patch('myapp.views.api.api_utils.list_sql_files')
    def test_api_sql_list_success(self, mock_list, mock_get_dir, mock_lock, mock_unlock, mock_user):
        """Test successful listing of SQL files."""
        mock_get_dir.return_value = '/tmp/testuser'
        mock_list.return_value = ['query1.sql', 'query2.sql', 'query3.sql']
        
        request = RequestFactory().get('/api/sql/list')
        request.user = mock_user
        
        response = api.api_sql_list(request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'files' in data
        assert len(data['files']) == 3
        assert 'query1.sql' in data['files']
    
    @patch('myapp.views.api.sqllock_release')
    @patch('myapp.utils.directories.sqllock_get')
    @patch('myapp.views.api.get_user_directory')
    @patch('myapp.views.api.api_utils.list_sql_files')
    def test_api_sql_list_handles_exception(self, mock_list, mock_get_dir, mock_lock, mock_unlock, mock_user):
        """Test error handling in api_sql_list."""
        mock_get_dir.return_value = '/tmp/testuser_admin'
        mock_list.side_effect = Exception('List error')
        
        request = RequestFactory().get('/api/sql/list')
        request.user = mock_user
        
        response = api.api_sql_list(request)
        
        assert response.status_code == 500
        assert b"Internal error while listing user's SQL files" in response.content


class TestApiRunSql:
    """Tests for api_run_sql view (execute SQL)."""
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.username = 'testuser_admin'
        return user
    
    @patch('myapp.views.api.api_utils.execute_sql_query')
    def test_api_run_sql_success(self, mock_execute, mock_user):
        """Test successful SQL execution."""
        mock_execute.return_value = {
            'columns': ['id', 'name'],
            'result': [[1, 'Alice'], [2, 'Bob']],
            'error': None
        }
        
        request = RequestFactory().post(
            '/api/run',
            data=json.dumps({'sql': 'SELECT * FROM users;'}),
            content_type='application/json'
        )
        request.user = mock_user
        
        response = api.api_run_sql(request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['columns'] == ['id', 'name']
        assert len(data['result']) == 2
        assert data['error'] is None
    
    @patch('myapp.views.api.api_utils.execute_sql_query')
    def test_api_run_sql_empty_sql(self, mock_execute, mock_user):
        """Test execution with empty SQL."""
        mock_execute.return_value = {
            'columns': [],
            'result': [],
            'error': 'No SQL provided'
        }
        
        request = RequestFactory().post(
            '/api/run',
            data=json.dumps({'sql': ''}),
            content_type='application/json'
        )
        request.user = mock_user
        
        response = api.api_run_sql(request)
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert data['error'] == 'No SQL provided'
    
    @patch('myapp.views.api.api_utils.execute_sql_query')
    def test_api_run_sql_syntax_error(self, mock_execute, mock_user):
        """Test execution with SQL syntax error."""
        mock_execute.return_value = {
            'columns': [],
            'result': [],
            'error': 'near "SELEC": syntax error'
        }
        
        request = RequestFactory().post(
            '/api/run',
            data=json.dumps({'sql': 'SELEC * FROM users;'}),
            content_type='application/json'
        )
        request.user = mock_user
        
        response = api.api_run_sql(request)
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'syntax error' in data['error']
    
    @patch('myapp.views.api.api_utils.execute_sql_query')
    def test_api_run_sql_handles_exception(self, mock_execute, mock_user):
        """Test error handling when execution fails."""
        mock_execute.side_effect = Exception('Database connection failed')
        
        request = RequestFactory().post(
            '/api/run',
            data=json.dumps({'sql': 'SELECT 1;'}),
            content_type='application/json'
        )
        request.user = mock_user
        
        response = api.api_run_sql(request)
        
        assert response.status_code == 500
        data = json.loads(response.content)
        assert 'error' in data
        assert 'Database connection failed' in data['error']


class TestApiUploadDb:
    """Tests for api_upload_db view (upload database file)."""
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.username = 'testuser_admin'
        return user
    
    @patch('myapp.views.api.get_user_directory')
    @patch('myapp.views.api.api_utils.save_database_file')
    def test_api_upload_db_success(self, mock_save, mock_get_dir, mock_user):
        """Test successful database upload."""
        mock_get_dir.return_value = '/tmp/testuser_admin'
        
        db_data = b'\x00\x01\x02\x03\x04\x05'
        request = RequestFactory().post(
            '/api/upload/db',
            data=db_data,
            content_type='application/octet-stream'
        )
        request.user = mock_user
        
        response = api.api_upload_db(request)
        
        assert response.status_code == 201
        assert b"File saved successfully" in response.content
        mock_save.assert_called_once_with('/tmp/testuser_admin', db_data)
    
    @patch('myapp.views.api.get_user_directory')
    @patch('myapp.views.api.api_utils.save_database_file')
    def test_api_upload_db_handles_exception(self, mock_save, mock_get_dir, mock_user):
        """Test error handling in api_upload_db."""
        mock_get_dir.return_value = '/tmp/testuser_admin'
        mock_save.side_effect = Exception('Save error')
        
        request = RequestFactory().post('/api/upload/db', data=b'data', content_type='application/octet-stream')
        request.user = mock_user
        
        response = api.api_upload_db(request)
        
        assert response.status_code == 500
        assert b"Internal error while uploading database" in response.content


class TestApiDbDiagramJson:
    """Tests for api_db_diagram_json view (database diagram)."""
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.username = 'testuser_admin'
        return user
    
    @patch('myapp.views.api.sqllock_release')
    @patch('myapp.utils.directories.sqllock_get')
    @patch('myapp.views.api.get_user_directory')
    @patch('myapp.views.api.api_utils.read_diagram_json')
    def test_api_db_diagram_json_get(self, mock_read, mock_get_dir, mock_lock, mock_unlock, mock_user):
        """Test GET request for database diagram."""
        mock_get_dir.return_value = '/tmp/testuser_admin'
        mock_read.return_value = b'{"id": "diagram", "nodes": []}'
        
        request = RequestFactory().get('/api/diagram/db')
        request.user = mock_user
        
        response = api.api_db_diagram_json(request)
        
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'
        mock_read.assert_called_once_with('/tmp/testuser_admin', 'model.json')
    
    @patch('myapp.views.api.sqllock_release')
    @patch('myapp.utils.directories.sqllock_get')
    @patch('myapp.views.api.get_user_directory')
    @patch('myapp.views.api.api_utils.save_diagram_json')
    def test_api_db_diagram_json_post(self, mock_save, mock_get_dir, mock_lock, mock_unlock, mock_user):
        """Test POST request to save database diagram."""
        mock_get_dir.return_value = '/tmp/testuser_admin'
        
        diagram_data = b'{"id": "diagram", "nodes": []}'
        request = RequestFactory().post(
            '/api/diagram/db',
            data=diagram_data,
            content_type='application/json'
        )
        request.user = mock_user
        
        response = api.api_db_diagram_json(request)
        
        assert response.status_code == 200
        mock_save.assert_called_once_with(
            '/tmp/testuser_admin', 
            'model.json', 
            diagram_data,
            process_diagram=True,
            username='testuser_admin'
        )


class TestApiEditorDiagramJson:
    """Tests for api_editor_diagram_json view (editor diagram)."""
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.username = 'testuser_admin'
        return user
    
    @patch('myapp.views.api.sqllock_release')
    @patch('myapp.utils.directories.sqllock_get')
    @patch('myapp.views.api.get_user_directory')
    @patch('myapp.views.api.api_utils.read_diagram_json')
    def test_api_editor_diagram_json_get(self, mock_read, mock_get_dir, mock_lock, mock_unlock, mock_user):
        """Test GET request for editor diagram."""
        mock_get_dir.return_value = '/tmp/testuser_admin'
        mock_read.return_value = b'{"id": "editor", "nodes": []}'
        
        request = RequestFactory().get('/api/diagram/editor')
        request.user = mock_user
        
        response = api.api_editor_diagram_json(request)
        
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'
        mock_read.assert_called_once_with('/tmp/testuser_admin', 'editor_model.json')
    
    @patch('myapp.views.api.sqllock_release')
    @patch('myapp.utils.directories.sqllock_get')
    @patch('myapp.views.api.get_user_directory')
    @patch('myapp.views.api.api_utils.save_diagram_json')
    def test_api_editor_diagram_json_post(self, mock_save, mock_get_dir, mock_lock, mock_unlock, mock_user):
        """Test POST request to save editor diagram."""
        mock_get_dir.return_value = '/tmp/testuser_admin'
        
        diagram_data = b'{"id": "editor", "nodes": []}'
        request = RequestFactory().post(
            '/api/diagram/editor',
            data=diagram_data,
            content_type='application/json'
        )
        request.user = mock_user
        
        response = api.api_editor_diagram_json(request)
        
        assert response.status_code == 200
        # Editor diagram doesn't process, just saves
        mock_save.assert_called_once_with('/tmp/testuser_admin', 'editor_model.json', diagram_data)


class TestGetSystemData:
    """Tests for get_system_data view (system monitoring)."""
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.username = 'admin'
        return user
    
    @patch('myapp.views.api.api_utils.log_and_rotate_system_data')
    @patch('myapp.views.api.api_utils.collect_system_data')
    def test_get_system_data_success(self, mock_collect, mock_log, mock_user):
        """Test successful system data collection."""
        mock_collect.return_value = {
            'cpu_percentage': 45,
            'ram_percentage': 60,
            'fullness_percentage': 70,
            'logged_in_users': 3
        }
        
        request = RequestFactory().get('/api/system')
        request.user = mock_user
        
        response = api.get_system_data(request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['cpu_percentage'] == 45
        assert data['ram_percentage'] == 60
        assert data['logged_in_users'] == 3
        mock_log.assert_called_once()
    
    @patch('myapp.views.api.api_utils.collect_system_data')
    def test_get_system_data_handles_exception(self, mock_collect, mock_user):
        """Test error handling in get_system_data."""
        mock_collect.side_effect = Exception('System data collection failed')
        
        request = RequestFactory().get('/api/system')
        request.user = mock_user
        
        response = api.get_system_data(request)
        
        assert response.status_code == 500
        assert b"Internal error while collecting system data" in response.content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
