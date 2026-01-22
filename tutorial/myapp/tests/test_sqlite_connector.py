"""
Unit tests for sqlite_connector module.
Tests database operations, SQL parsing, and HTML generation functionality.
"""

import pytest
import sqlite3
import os
import tempfile
import unittest
from unittest.mock import patch

# Import after setting up Django (conftest.py does this)
from myapp.utils import sqlite_connector

# Disable autouse fixtures for this module to prevent interference with mocking
pytestmark = pytest.mark.no_auth_bypass


class TestGetDbName(unittest.TestCase):
    """Test suite for get_db_name function."""
    
    @patch('myapp.utils.sqlite_connector.get_user_directory')
    def test_get_db_name_valid_user(self, mock_get_user_dir):
        """Test getting database name for valid user."""
        mock_get_user_dir.return_value = '/tmp/testuser_admin'
        
        result = sqlite_connector.get_db_name('testuser_admin')
        
        assert result == '/tmp/testuser_admin/datenbank.db'
        mock_get_user_dir.assert_called_once_with('testuser_admin')
    
    def test_get_db_name_none_user(self):
        """Test getting database name with None username."""
        result = sqlite_connector.get_db_name(None)
        assert result == ""
    
    def test_get_db_name_empty_user(self):
        """Test getting database name with empty username."""
        result = sqlite_connector.get_db_name('')
        assert result == ""


class TestDeleteDb(unittest.TestCase):
    """Test suite for delete_db function."""
    
    def test_delete_db_existing_file(self):
        """Test deleting an existing database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'datenbank.db')
            backup_path = db_path + '.bak'
            
            # Create a dummy database file
            with open(db_path, 'w') as f:
                f.write('dummy db')
            
            with patch('myapp.utils.sqlite_connector.get_db_name', return_value=db_path):
                sqlite_connector.delete_db('testuser')
            
            assert not os.path.exists(db_path)
            assert os.path.exists(backup_path)
    
    def test_delete_db_nonexistent_file(self):
        """Test deleting a non-existent database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'nonexistent.db')
            
            with patch('myapp.utils.sqlite_connector.get_db_name', return_value=db_path):
                # Should not raise an error
                sqlite_connector.delete_db('testuser')


class TestCreateDb(unittest.TestCase):
    """Test suite for create_db function."""
    
    def test_create_db_simple_table(self):
        """Test creating a database with a simple table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'datenbank.db')
            
            sql = "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);"
            
            with patch('myapp.utils.sqlite_connector.get_user_directory', return_value=tmpdir):
                result = sqlite_connector.create_db(sql, 'testuser')
            
            assert result is not None
            assert isinstance(result, bytes)
            assert os.path.exists(db_path)
            
            # Verify table was created
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                assert cursor.fetchone() is not None
    
    def test_create_db_multiple_statements(self):
        """Test creating a database with multiple SQL statements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'datenbank.db')
            
            sql = """
            CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE posts (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT);
            """
            
            with patch('myapp.utils.sqlite_connector.get_user_directory', return_value=tmpdir):
                result = sqlite_connector.create_db(sql, 'testuser')
            
            assert result is not None
            
            # Verify both tables were created
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                assert 'users' in tables
                assert 'posts' in tables
    
    def test_create_db_with_empty_statements(self):
        """Test creating database with empty statements (should be skipped)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            
            sql = "CREATE TABLE test (id INTEGER); ; ; "
            
            with patch('myapp.utils.sqlite_connector.get_user_directory', return_value=tmpdir):
                result = sqlite_connector.create_db(sql, 'testuser')
            
            assert result is not None
    
    def test_create_db_invalid_sql(self):
        """Test creating database with invalid SQL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'datenbank.db')
            
            sql = "INVALID SQL STATEMENT"
            
            with patch('myapp.utils.sqlite_connector.get_user_directory', return_value=tmpdir):
                with pytest.raises(sqlite3.DatabaseError):
                    sqlite_connector.create_db(sql, 'testuser')
    
    def test_create_db_none_dbname(self):
        """Test creating database when username is None (returns empty dbname)."""
        # When username is None, get_db_name returns "", not None
        # create_db will try to create a database with empty path which causes FileNotFoundError
        with pytest.raises(FileNotFoundError):
            result = sqlite_connector.create_db('CREATE TABLE test (id INTEGER);', None)


class TestRunSql(unittest.TestCase):
    """Test suite for runSql function."""
    
    def test_run_sql_select(self):
        """Test running a SELECT statement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'datenbank.db')
            
            # Create database with data
            with sqlite3.connect(db_path) as conn:
                conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
                conn.execute("INSERT INTO users VALUES (1, 'Alice')")
                conn.commit()
            
            with patch('myapp.utils.sqlite_connector.get_user_directory', return_value=tmpdir):
                cursor = sqlite_connector.runSql("SELECT * FROM users", 'testuser')
                results = cursor.fetchall()
            
            assert len(results) == 1
            assert results[0] == (1, 'Alice')
    
    def test_run_sql_insert(self):
        """Test running an INSERT statement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'datenbank.db')
            
            with sqlite3.connect(db_path) as conn:
                conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
                conn.commit()
            
            with patch('myapp.utils.sqlite_connector.get_user_directory', return_value=tmpdir):
                sqlite_connector.runSql("INSERT INTO users VALUES (1, 'Bob')", 'testuser')
            
            # Verify data was inserted
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT * FROM users")
                results = cursor.fetchall()
            
            assert len(results) == 1
            assert results[0] == (1, 'Bob')
    
    def test_run_sql_multiple_statements(self):
        """Test running multiple SQL statements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'datenbank.db')
            
            with sqlite3.connect(db_path) as conn:
                conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
                conn.commit()
            
            sql = "INSERT INTO users VALUES (1, 'Alice'); INSERT INTO users VALUES (2, 'Bob');"
            
            with patch('myapp.utils.sqlite_connector.get_user_directory', return_value=tmpdir):
                sqlite_connector.runSql(sql, 'testuser')
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM users")
                count = cursor.fetchone()[0]
            
            assert count == 2
    
    def test_run_sql_empty_statements(self):
        """Test running SQL with empty statements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'datenbank.db')
            
            with sqlite3.connect(db_path) as conn:
                conn.execute("CREATE TABLE test (id INTEGER)")
                conn.commit()
            
            with patch('myapp.utils.sqlite_connector.get_user_directory', return_value=tmpdir):
                # Should not raise error
                sqlite_connector.runSql("SELECT 1; ; ; ", 'testuser')
    
    def test_run_sql_none_dbname(self):
        """Test running SQL when username is None (returns empty dbname)."""
        # When username is None, get_db_name returns "", which is not None
        # The check in runSql is 'if dbname is None', so empty string passes through
        # SQLite actually allows empty string as database name (creates in-memory or current dir)
        # So this doesn't raise an error - it just creates a temporary database
        result = sqlite_connector.runSql('SELECT 1', None)
        # Just verify it returns a cursor
        assert result is not None


class TestParseTableSchema(unittest.TestCase):
    """Test suite for parse_table_schema function."""
    
    def test_parse_simple_table(self):
        """Test parsing a simple table schema."""
        sql = "CREATE TABLE users (id INTEGER, name TEXT)"
        
        columns, pks, fks = sqlite_connector.parse_table_schema(sql)
        
        assert len(columns) == 2
        assert ('id', 'INTEGER') in columns
        assert ('name', 'TEXT') in columns
        assert len(pks) == 0
        assert len(fks) == 0
    
    def test_parse_table_with_inline_primary_key(self):
        """Test parsing table with inline PRIMARY KEY."""
        sql = "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
        
        columns, pks, fks = sqlite_connector.parse_table_schema(sql)
        
        assert ('id', 'INTEGER') in columns
        assert 'id' in pks
        assert len(fks) == 0
    
    def test_parse_table_with_separate_primary_key(self):
        """Test parsing table with separate PRIMARY KEY constraint."""
        sql = "CREATE TABLE users (id INTEGER, name TEXT, PRIMARY KEY (id))"
        
        columns, pks, fks = sqlite_connector.parse_table_schema(sql)
        
        assert len(columns) == 2
        assert 'id' in pks
    
    def test_parse_table_with_composite_primary_key(self):
        """Test parsing table with composite PRIMARY KEY."""
        sql = "CREATE TABLE enrollments (student_id INTEGER, course_id INTEGER, PRIMARY KEY (student_id, course_id))"
        
        columns, pks, fks = sqlite_connector.parse_table_schema(sql)
        
        assert len(columns) == 2
        assert 'student_id' in pks
        assert 'course_id' in pks
    
    def test_parse_table_with_foreign_key(self):
        """Test parsing table with FOREIGN KEY."""
        sql = "CREATE TABLE posts (id INTEGER, user_id INTEGER, FOREIGN KEY (user_id) REFERENCES users(id))"
        
        columns, pks, fks = sqlite_connector.parse_table_schema(sql)
        
        assert len(columns) == 2
        assert 'user_id' in fks
    
    def test_parse_table_with_quoted_columns(self):
        """Test parsing table with quoted column names."""
        sql = 'CREATE TABLE "users" ("id" INTEGER, "name" TEXT)'
        
        columns, pks, fks = sqlite_connector.parse_table_schema(sql)
        
        assert ('id', 'INTEGER') in columns
        assert ('name', 'TEXT') in columns
    
    def test_parse_table_with_types_containing_parentheses(self):
        """Test parsing table with types that have parentheses."""
        sql = "CREATE TABLE users (id INTEGER, name VARCHAR(255))"
        
        columns, pks, fks = sqlite_connector.parse_table_schema(sql)
        
        assert len(columns) == 2
        assert ('name', 'VARCHAR(255)') in columns
    
    def test_parse_table_no_parentheses(self):
        """Test parsing SQL without parentheses."""
        sql = "CREATE TABLE users"
        
        columns, pks, fks = sqlite_connector.parse_table_schema(sql)
        
        assert len(columns) == 0
        assert len(pks) == 0
        assert len(fks) == 0


class TestGetTableDict(unittest.TestCase):
    """Test suite for get_table_dict function."""
    
    def test_get_table_dict_single_table(self):
        """Test getting table dictionary for single table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'datenbank.db')
            
            with sqlite3.connect(db_path) as conn:
                conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
                conn.commit()
            
            with patch('myapp.utils.sqlite_connector.get_user_directory', return_value=tmpdir):
                result = sqlite_connector.get_table_dict('testuser')
            
            assert 'users' in result
            assert 'id' in result['users']
            assert result['users']['id']['type'] == 'INTEGER'
            assert result['users']['id']['primary_key'] is True
            assert 'name' in result['users']
    
    def test_get_table_dict_multiple_tables(self):
        """Test getting table dictionary for multiple tables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'datenbank.db')
            
            with sqlite3.connect(db_path) as conn:
                conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
                conn.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY, title TEXT)")
                conn.commit()
            
            with patch('myapp.utils.sqlite_connector.get_user_directory', return_value=tmpdir):
                result = sqlite_connector.get_table_dict('testuser')
            
            assert 'users' in result
            assert 'posts' in result
    
    def test_get_table_dict_with_foreign_key(self):
        """Test getting table dictionary with foreign keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'datenbank.db')
            
            with sqlite3.connect(db_path) as conn:
                conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
                conn.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY, user_id INTEGER, FOREIGN KEY (user_id) REFERENCES users(id))")
                conn.commit()
            
            with patch('myapp.utils.sqlite_connector.get_user_directory', return_value=tmpdir):
                result = sqlite_connector.get_table_dict('testuser')
            
            assert result['posts']['user_id']['is_foreign_key'] is True


class TestGenerateHtmlTable(unittest.TestCase):
    """Test suite for generate_html_table function."""
    
    def test_generate_html_simple_table(self):
        """Test generating HTML for simple table."""
        columns = [('id', 'INTEGER'), ('name', 'TEXT')]
        pks = set()
        fks = set()
        
        result = sqlite_connector.generate_html_table('users', columns, pks, fks)
        
        assert 'users' in result
        assert 'id : INTEGER' in result
        assert 'name : TEXT' in result
    
    def test_generate_html_with_primary_key(self):
        """Test generating HTML with primary key (underlined)."""
        columns = [('id', 'INTEGER'), ('name', 'TEXT')]
        pks = {'id'}
        fks = set()
        
        result = sqlite_connector.generate_html_table('users', columns, pks, fks)
        
        assert '<u>id : INTEGER</u>' in result
        assert 'name : TEXT' in result
    
    def test_generate_html_with_foreign_key(self):
        """Test generating HTML with foreign key (dotted underline)."""
        columns = [('id', 'INTEGER'), ('user_id', 'INTEGER')]
        pks = set()
        fks = {'user_id'}
        
        result = sqlite_connector.generate_html_table('posts', columns, pks, fks)
        
        assert "<u class='dotted'>user_id : INTEGER</u>" in result
    
    def test_generate_html_escapes_special_chars(self):
        """Test that HTML special characters are escaped."""
        columns = [('id', 'INTEGER'), ('<script>', 'TEXT')]
        pks = set()
        fks = set()
        
        result = sqlite_connector.generate_html_table('users', columns, pks, fks)
        
        assert '&lt;script&gt;' in result
        assert '<script>' not in result


class TestConvertSqliteMasterToHtml(unittest.TestCase):
    """Test suite for convert_sqlite_master_to_html function."""
    
    def test_convert_to_html_single_table(self):
        """Test converting single table to HTML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'datenbank.db')
            
            with sqlite3.connect(db_path) as conn:
                conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
                conn.commit()
            
            with patch('myapp.utils.sqlite_connector.get_user_directory', return_value=tmpdir):
                result = sqlite_connector.convert_sqlite_master_to_html('testuser')
            
            assert '<style>' in result
            assert 'u.dotted' in result
            assert 'users' in result
            assert '<br>' in result
    
    def test_convert_to_html_multiple_tables(self):
        """Test converting multiple tables to HTML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'datenbank.db')
            
            with sqlite3.connect(db_path) as conn:
                conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
                conn.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY, title TEXT)")
                conn.commit()
            
            with patch('myapp.utils.sqlite_connector.get_user_directory', return_value=tmpdir):
                result = sqlite_connector.convert_sqlite_master_to_html('testuser')
            
            assert 'users' in result
            assert 'posts' in result
            assert result.count('<br>') >= 2  # Style + at least 2 tables


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
