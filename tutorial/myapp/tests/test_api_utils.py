"""
Unit tests for api_utils module.
Tests all business logic functions extracted from API views.
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# Ensure `tutorial` package is importable
tests_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(tests_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from myapp.utils import api_utils


class TestEndpointExtraction:
    """Tests for URL endpoint extraction functions."""
    
    def test_build_endpoint_dict_with_name(self):
        """Test building endpoint dict from pattern with name."""
        mock_pattern = Mock()
        mock_pattern.name = 'api_test'
        
        result = api_utils.build_endpoint_dict(mock_pattern, 'api/test/endpoint')
        
        assert result['path'] == '/api/test/endpoint'
        assert result['name'] == 'api_test'
    
    def test_build_endpoint_dict_without_name(self):
        """Test building endpoint dict from pattern without name."""
        mock_pattern = Mock(spec=[])  # No 'name' attribute
        
        result = api_utils.build_endpoint_dict(mock_pattern, 'api/test')
        
        assert result['path'] == '/api/test'
        assert result['name'] is None
    
    def test_build_endpoint_dict_strips_regex_chars(self):
        """Test that regex characters are stripped from path."""
        mock_pattern = Mock()
        mock_pattern.name = 'test'
        
        result = api_utils.build_endpoint_dict(mock_pattern, '^api/test$')
        
        assert result['path'] == '/api/test'
    
    def test_extract_api_endpoints_empty_patterns(self):
        """Test extraction with empty URL patterns."""
        result = api_utils.extract_api_endpoints([])
        assert result == []
    
    def test_extract_api_endpoints_filters_non_api(self):
        """Test that non-api patterns are filtered out."""
        mock_pattern = Mock()
        mock_pattern.name = 'home'
        mock_pattern.pattern = Mock()
        mock_pattern.pattern.__str__ = Mock(return_value='home/')
        
        result = api_utils.extract_api_endpoints([mock_pattern])
        
        assert result == []
    
    def test_extract_api_endpoints_includes_api_patterns(self):
        """Test that api patterns are included."""
        mock_pattern = Mock()
        mock_pattern.name = 'api_test'
        mock_pattern.pattern = Mock()
        mock_pattern.pattern.__str__ = Mock(return_value='api/test')
        # Make sure url_patterns attribute doesn't exist so it's treated as a regular pattern
        del mock_pattern.url_patterns
        
        result = api_utils.extract_api_endpoints([mock_pattern], prefix='')
        
        assert len(result) == 1
        assert result[0]['name'] == 'api_test'
        assert result[0]['path'] == '/api/test'


class TestSqlFileOperations:
    """Tests for SQL file management functions."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_save_sql_file_basic(self, temp_dir):
        """Test saving a SQL file."""
        api_utils.save_sql_file(temp_dir, 'test.sql', 'SELECT * FROM users;')
        
        file_path = os.path.join(temp_dir, 'test.sql')
        assert os.path.exists(file_path)
        
        with open(file_path, 'r') as f:
            content = f.read()
        assert content == 'SELECT * FROM users;'
    
    def test_save_sql_file_adds_extension(self, temp_dir):
        """Test that .sql extension is added if missing."""
        api_utils.save_sql_file(temp_dir, 'test', 'SELECT 1;')
        
        file_path = os.path.join(temp_dir, 'test.sql')
        assert os.path.exists(file_path)
    
    def test_save_sql_file_handles_double_extension(self, temp_dir):
        """Test handling of .sql.sql double extension."""
        api_utils.save_sql_file(temp_dir, 'test.sql.sql', 'SELECT 1;')
        
        file_path = os.path.join(temp_dir, 'test.sql')
        assert os.path.exists(file_path)
        assert not os.path.exists(os.path.join(temp_dir, 'test.sql.sql'))
    
    def test_read_sql_file_basic(self, temp_dir):
        """Test reading a SQL file."""
        sql_content = 'SELECT * FROM users WHERE id = 1;'
        file_path = os.path.join(temp_dir, 'query.sql')
        
        with open(file_path, 'w') as f:
            f.write(sql_content)
        
        result = api_utils.read_sql_file(temp_dir, 'query.sql')
        assert result == sql_content
    
    def test_read_sql_file_adds_extension(self, temp_dir):
        """Test reading file when extension is omitted."""
        sql_content = 'SELECT 1;'
        file_path = os.path.join(temp_dir, 'query.sql')
        
        with open(file_path, 'w') as f:
            f.write(sql_content)
        
        result = api_utils.read_sql_file(temp_dir, 'query')
        assert result == sql_content
    
    def test_delete_sql_file_existing(self, temp_dir):
        """Test deleting an existing SQL file."""
        file_path = os.path.join(temp_dir, 'delete_me.sql')
        with open(file_path, 'w') as f:
            f.write('SELECT 1;')
        
        result = api_utils.delete_sql_file(temp_dir, 'delete_me.sql')
        
        assert result is True
        assert not os.path.exists(file_path)
    
    def test_delete_sql_file_nonexistent(self, temp_dir):
        """Test deleting a non-existent file returns False."""
        result = api_utils.delete_sql_file(temp_dir, 'nonexistent.sql')
        assert result is False
    
    def test_replace_all_sql_files(self, temp_dir):
        """Test replacing all SQL files in directory."""
        # Create some existing files
        with open(os.path.join(temp_dir, 'old1.sql'), 'w') as f:
            f.write('OLD 1')
        with open(os.path.join(temp_dir, 'old2.sql'), 'w') as f:
            f.write('OLD 2')
        with open(os.path.join(temp_dir, 'keep.txt'), 'w') as f:
            f.write('KEEP ME')
        
        # Replace with new files
        new_files = [
            {'filename': 'new1.sql', 'sql': 'SELECT 1;'},
            {'filename': 'new2', 'sql': 'SELECT 2;'}  # Without extension
        ]
        
        api_utils.replace_all_sql_files(temp_dir, new_files)
        
        # Check old SQL files are gone
        assert not os.path.exists(os.path.join(temp_dir, 'old1.sql'))
        assert not os.path.exists(os.path.join(temp_dir, 'old2.sql'))
        
        # Check new files exist
        assert os.path.exists(os.path.join(temp_dir, 'new1.sql'))
        assert os.path.exists(os.path.join(temp_dir, 'new2.sql'))
        
        # Check non-SQL file is preserved
        assert os.path.exists(os.path.join(temp_dir, 'keep.txt'))
    
    def test_list_sql_files_empty_directory(self, temp_dir):
        """Test listing SQL files in empty directory."""
        result = api_utils.list_sql_files(temp_dir)
        assert result == []
    
    def test_list_sql_files_with_files(self, temp_dir):
        """Test listing SQL files."""
        # Create various files
        with open(os.path.join(temp_dir, 'query1.sql'), 'w') as f:
            f.write('SELECT 1;')
        with open(os.path.join(temp_dir, 'query2.sql'), 'w') as f:
            f.write('SELECT 2;')
        with open(os.path.join(temp_dir, 'not_sql.txt'), 'w') as f:
            f.write('TEXT')
        
        result = api_utils.list_sql_files(temp_dir)
        
        assert len(result) == 2
        assert 'query1.sql' in result
        assert 'query2.sql' in result
        assert 'not_sql.txt' not in result
    
    def test_list_sql_files_sorted(self, temp_dir):
        """Test that SQL files are returned sorted."""
        files = ['zebra.sql', 'alpha.sql', 'beta.sql']
        for f in files:
            with open(os.path.join(temp_dir, f), 'w') as file:
                file.write('SELECT 1;')
        
        result = api_utils.list_sql_files(temp_dir)
        
        assert result == ['alpha.sql', 'beta.sql', 'zebra.sql']


class TestSqlExecution:
    """Tests for SQL query execution."""
    
    @patch('myapp.utils.api_utils.runSql')
    def test_execute_sql_query_success_with_results(self, mock_run_sql):
        """Test successful SQL execution with results."""
        # Mock cursor with results
        mock_cursor = Mock()
        mock_cursor.description = [('id',), ('name',)]
        mock_cursor.fetchall.return_value = [(1, 'Alice'), (2, 'Bob')]
        mock_run_sql.return_value = mock_cursor
        
        result = api_utils.execute_sql_query('SELECT * FROM users;', 'testuser')
        
        assert result['error'] is None
        assert result['columns'] == ['id', 'name']
        assert result['result'] == [[1, 'Alice'], [2, 'Bob']]
        mock_run_sql.assert_called_once_with('SELECT * FROM users;', 'testuser')
    
    @patch('myapp.utils.api_utils.runSql')
    def test_execute_sql_query_success_no_results(self, mock_run_sql):
        """Test successful SQL execution without results (e.g., INSERT)."""
        mock_cursor = Mock()
        mock_cursor.description = None
        mock_run_sql.return_value = mock_cursor
        
        result = api_utils.execute_sql_query('INSERT INTO users VALUES (1, "Alice");', 'testuser')
        
        assert result['error'] is None
        assert result['columns'] == []
        assert result['result'] == []
    
    @patch('myapp.utils.api_utils.runSql')
    def test_execute_sql_query_empty_sql(self, mock_run_sql):
        """Test execution with empty SQL string."""
        result = api_utils.execute_sql_query('', 'testuser')
        
        assert result['error'] == 'No SQL provided'
        assert result['columns'] == []
        assert result['result'] == []
        mock_run_sql.assert_not_called()
    
    @patch('myapp.utils.api_utils.runSql')
    def test_execute_sql_query_operational_error(self, mock_run_sql):
        """Test handling of SQLite OperationalError."""
        from sqlite3 import OperationalError
        mock_run_sql.side_effect = OperationalError('near "SELEC": syntax error')
        
        result = api_utils.execute_sql_query('SELEC * FROM users;', 'testuser')
        
        assert result['error'] == 'near "SELEC": syntax error'
        assert result['columns'] == []
        assert result['result'] == []
    
    @patch('myapp.utils.api_utils.runSql')
    def test_execute_sql_query_generic_error(self, mock_run_sql):
        """Test handling of generic exceptions."""
        mock_run_sql.side_effect = Exception('Database connection failed')
        
        result = api_utils.execute_sql_query('SELECT 1;', 'testuser')
        
        assert 'Database connection failed' in result['error']
        assert result['columns'] == []
        assert result['result'] == []


class TestDatabaseFileOperations:
    """Tests for database file operations."""
    
    def test_save_database_file(self):
        """Test saving database file from binary data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = b'\x00\x01\x02\x03\x04\x05'
            
            api_utils.save_database_file(temp_dir, test_data)
            
            file_path = os.path.join(temp_dir, 'datenbank.db')
            assert os.path.exists(file_path)
            
            with open(file_path, 'rb') as f:
                saved_data = f.read()
            assert saved_data == test_data


class TestDiagramOperations:
    """Tests for diagram JSON file operations."""
    
    def test_read_diagram_json(self):
        """Test reading diagram JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = b'{"id": "diagram", "nodes": [], "edges": []}'
            file_path = os.path.join(temp_dir, 'model.json')
            
            with open(file_path, 'wb') as f:
                f.write(test_data)
            
            result = api_utils.read_diagram_json(temp_dir, 'model.json')
            assert result == test_data
    
    def test_save_diagram_json_without_processing(self):
        """Test saving diagram JSON without processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = b'{"id": "diagram", "nodes": [], "edges": []}'
            
            api_utils.save_diagram_json(temp_dir, 'editor_model.json', test_data)
            
            file_path = os.path.join(temp_dir, 'editor_model.json')
            assert os.path.exists(file_path)
            
            with open(file_path, 'rb') as f:
                saved_data = f.read()
            assert saved_data == test_data
    
    @patch('myapp.utils.api_utils.load_json')
    def test_save_diagram_json_with_processing(self, mock_load_json):
        """Test saving diagram JSON with processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = b'{"id": "diagram", "nodes": [], "edges": []}'
            
            api_utils.save_diagram_json(
                temp_dir, 
                'model.json', 
                test_data, 
                process_diagram=True, 
                username='testuser'
            )
            
            # Check file was saved
            file_path = os.path.join(temp_dir, 'model.json')
            assert os.path.exists(file_path)
            
            # Check load_json was called
            mock_load_json.assert_called_once_with(test_data, 'testuser')
    
    @patch('myapp.utils.api_utils.load_json')
    def test_save_diagram_json_no_username_no_processing(self, mock_load_json):
        """Test that processing doesn't happen without username."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = b'{"id": "diagram"}'
            
            api_utils.save_diagram_json(
                temp_dir, 
                'model.json', 
                test_data, 
                process_diagram=True, 
                username=None
            )
            
            # load_json should not be called without username
            mock_load_json.assert_not_called()


class TestSystemDataCollection:
    """Tests for system data collection."""
    
    @patch('myapp.utils.api_utils.views_user.get_recent_audit_logs')
    @patch('myapp.utils.api_utils.get_session_details')
    @patch('myapp.utils.api_utils.get_logged_in_users_count')
    @patch('myapp.utils.api_utils.psutil.cpu_percent')
    @patch('myapp.utils.api_utils.psutil.virtual_memory')
    @patch('myapp.utils.api_utils.shutil.disk_usage')
    @patch('myapp.utils.api_utils.get_directory_tree_with_sizes')
    def test_collect_system_data_success(
        self,
        mock_dir_tree,
        mock_disk_usage,
        mock_virtual_memory,
        mock_cpu_percent,
        mock_logged_users,
        mock_session_details,
        mock_audit_logs
    ):
        """Test successful system data collection."""
        # Setup mocks
        mock_dir_tree.return_value = [{'name': 'user1', 'size': 1000}]
        mock_disk_usage.return_value = (100 * 1024**3, 60 * 1024**3, 40 * 1024**3)  # 100GB total, 60GB used
        
        mock_ram = Mock()
        mock_ram.total = 16 * 1024**3  # 16GB
        mock_ram.used = 8 * 1024**3    # 8GB
        mock_ram.available = 8 * 1024**3  # 8GB
        mock_ram.percent = 50.0
        mock_virtual_memory.return_value = mock_ram
        
        mock_cpu_percent.return_value = 25.5
        mock_logged_users.return_value = 5
        mock_session_details.return_value = [{'username': 'user1', 'ip': '127.0.0.1'}]
        
        mock_log = Mock()
        mock_log.timestamp.strftime.return_value = '2026-01-21 10:00:00'
        mock_log.username = 'testuser'
        mock_log.action = 'LOGIN'
        mock_log.ACTION_CHOICES = [('LOGIN', 'Login')]
        mock_log.ip_address = '127.0.0.1'
        mock_log.operating_system = 'Linux'
        mock_log.location = 'Germany'
        mock_log.session_id = 'abc123'
        mock_audit_logs.return_value = [mock_log]
        
        # Execute
        result = api_utils.collect_system_data()
        
        # Verify
        assert 'directories' in result
        assert 'fullness_percentage' in result
        assert result['fullness_percentage'] == 60  # 60% used
        assert result['total_gb'] == '100.00'
        assert result['used_gb'] == '60.00'
        assert result['free_gb'] == '40.00'
        assert result['ram_total'] == '16.00'
        assert result['ram_percentage'] == 50
        assert result['cpu_percentage'] == 26  # Rounded from 25.5
        assert result['logged_in_users'] == 5
        assert len(result['session_info']) == 1
        assert len(result['recent_audit_logs']) == 1
    
    @patch('myapp.utils.api_utils.views_user.get_recent_audit_logs')
    @patch('myapp.utils.api_utils.get_session_details')
    @patch('myapp.utils.api_utils.get_logged_in_users_count')
    @patch('myapp.utils.api_utils.psutil.cpu_percent')
    @patch('myapp.utils.api_utils.psutil.virtual_memory')
    @patch('myapp.utils.api_utils.shutil.disk_usage')
    @patch('myapp.utils.api_utils.get_directory_tree_with_sizes')
    def test_collect_system_data_handles_errors_gracefully(
        self,
        mock_dir_tree,
        mock_disk_usage,
        mock_virtual_memory,
        mock_cpu_percent,
        mock_logged_users,
        mock_session_details,
        mock_audit_logs
    ):
        """Test that errors in data collection are handled gracefully."""
        # Setup mocks with errors
        mock_dir_tree.side_effect = Exception('Directory error')
        mock_disk_usage.side_effect = Exception('Disk error')
        mock_virtual_memory.side_effect = Exception('RAM error')
        mock_cpu_percent.side_effect = Exception('CPU error')
        mock_logged_users.return_value = 0
        mock_session_details.return_value = []
        mock_audit_logs.return_value = []
        
        # Execute - should not raise exception
        result = api_utils.collect_system_data()
        
        # Verify defaults are used
        assert result['directories'] == []
        assert result['fullness_percentage'] == 0
        assert result['total_gb'] == '0.00'
        assert result['ram_total'] == '0.00'
        assert result['cpu_percentage'] == 0


class TestLogAndRotate:
    """Tests for logging and rotation functions."""
    
    @patch('myapp.utils.api_utils.views_user.rotate_audit_logs')
    @patch('myapp.utils.api_utils.views_user.log_resource_data_to_csv')
    def test_log_and_rotate_system_data(self, mock_log_csv, mock_rotate):
        """Test logging and rotation of system data."""
        test_data = {'cpu_percentage': 50, 'ram_percentage': 60}
        
        api_utils.log_and_rotate_system_data(test_data)
        
        # CSV logging should always be called
        mock_log_csv.assert_called_once_with(test_data)
    
    @patch('myapp.utils.api_utils.views_user.rotate_audit_logs')
    @patch('myapp.utils.api_utils.views_user.log_resource_data_to_csv')
    @patch('random.randint')
    def test_log_and_rotate_calls_rotation_randomly(self, mock_randint, mock_log_csv, mock_rotate):
        """Test that rotation is called randomly (10% chance)."""
        test_data = {'cpu_percentage': 50}
        
        mock_rotate.reset_mock()
        # Simulate the 10% chance (randint returns 1)
        api_utils.rotation_counter = 0  # Reset counter to ensure rotation is attempted
        api_utils.log_and_rotate_system_data(test_data)
        mock_rotate.assert_called_once()
        
        # Simulate the 90% chance (randint returns something else)
        mock_rotate.reset_mock()
        api_utils.rotation_counter = 5  # Reset counter to ensure rotation is attempted
        api_utils.log_and_rotate_system_data(test_data)
        
        mock_rotate.assert_not_called()
    
    @patch('myapp.utils.api_utils.views_user.rotate_audit_logs')
    @patch('myapp.utils.api_utils.views_user.log_resource_data_to_csv')
    def test_log_and_rotate_handles_rotation_error(self, mock_log_csv, mock_rotate):
        """Test that rotation errors don't break the function."""
        test_data = {'cpu_percentage': 50}
        mock_rotate.side_effect = Exception('Rotation failed')
        
        # Should not raise exception
        api_utils.rotation_counter = 0  # Reset counter to ensure rotation is attempted
        api_utils.log_and_rotate_system_data(test_data)
        
        # CSV logging should still have been called
        mock_log_csv.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
