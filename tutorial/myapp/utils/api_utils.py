"""
Business logic utilities for API endpoints.
This module contains non-HTTP-related logic extracted from API views.
"""

import json
import os
import shutil
from typing import List, Dict, Tuple, Optional, Any
from sqlite3 import OperationalError
import psutil

from myapp.utils.directories import fullpath, get_directory_tree_with_sizes, get_user_directory, sqllock_get, sqllock_release
from myapp.utils.sqlite_connector import runSql
from myapp.utils.diagram import load_json
from myapp.utils.users import get_logged_in_users_count, get_session_details
from myapp.utils.utils import timestamp
from myapp import views_user
from myapp.utils.json_to_sql import ModelAnalyzer

# Constants
SQL_DOUBLE_EXT = '.sql.sql'
SQL_EXT = '.sql'


def build_endpoint_dict(pattern, path: str) -> Dict[str, Optional[str]]:
    """Build an endpoint dictionary from a URL pattern."""
    name = pattern.name if hasattr(pattern, 'name') else None
    return {
        'path': '/' + path.lstrip('^').rstrip('$').replace('\\', ''),
        'name': name
    }


def extract_api_endpoints(url_patterns, prefix: str = '') -> List[Dict[str, Optional[str]]]:
    """Extract API endpoints from URL patterns."""
    endpoints = []
    if prefix != '' and not prefix.startswith('api/'):
        return endpoints
    
    for pattern in url_patterns:
        if hasattr(pattern, 'url_patterns'):
            # This is an included URLconf, recurse into it
            endpoints.extend(extract_api_endpoints(pattern.url_patterns, prefix + str(pattern.pattern)))
        else:
            # This is a regular URL pattern
            path = prefix + str(pattern.pattern)
            if path.startswith('api/'):
                endpoints.append(build_endpoint_dict(pattern, path))
    
    return endpoints


def save_sql_file(user_dir: str, filename: str, sql_content: str) -> None:
    """
    Save SQL content to a file in the user's directory.
    
    Args:
        user_dir: User's directory path
        filename: Name of the SQL file
        sql_content: SQL content to save
    
    Raises:
        Exception: If file cannot be saved
    """
    filename = filename.replace(SQL_DOUBLE_EXT, SQL_EXT)
    if not filename.endswith(SQL_EXT):
        filename += SQL_EXT
    
    with open(fullpath(user_dir, filename), 'w') as f:
        f.write(sql_content)


def read_sql_file(user_dir: str, filename: str) -> str:
    """
    Read SQL content from a file in the user's directory.
    
    Args:
        user_dir: User's directory path
        filename: Name of the SQL file
    
    Returns:
        SQL file content as string
    
    Raises:
        Exception: If file cannot be read
    """
    filename = filename.replace(SQL_DOUBLE_EXT, SQL_EXT)
    if not filename.endswith(SQL_EXT):
        filename += SQL_EXT
    
    with open(fullpath(user_dir, filename), 'r') as f:
        return f.read()


def delete_sql_file(user_dir: str, filename: str) -> bool:
    """
    Delete a SQL file from the user's directory.
    
    Args:
        user_dir: User's directory path
        filename: Name of the SQL file
    
    Returns:
        True if file was deleted, False if file didn't exist
    
    Raises:
        Exception: If file cannot be deleted
    """
    filename = filename.replace(SQL_DOUBLE_EXT, SQL_EXT)
    if not filename.endswith(SQL_EXT):
        filename += SQL_EXT
    
    filepath = fullpath(user_dir, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False


def replace_all_sql_files(user_dir: str, files: List[Dict[str, str]]) -> None:
    """
    Delete all existing SQL files and create new ones from the provided list.
    
    Args:
        user_dir: User's directory path
        files: List of dictionaries with 'filename' and 'sql' keys
    
    Raises:
        Exception: If files cannot be processed
    """
    # Delete all existing .sql files
    for file in os.listdir(user_dir):
        if file.endswith(SQL_EXT):
            os.remove(os.path.join(user_dir, file))
    
    # Create new files
    for file in files:
        filename = file['filename']
        sql = file['sql']
        save_sql_file(user_dir, filename, sql)


def list_sql_files(user_dir: str) -> List[str]:
    """
    List all SQL files in the user's directory.
    
    Args:
        user_dir: User's directory path
    
    Returns:
        Sorted list of SQL filenames
    
    Raises:
        Exception: If directory cannot be read
    """
    files = [f for f in os.listdir(user_dir) if f.endswith(SQL_EXT)]
    files.sort()
    return files


def execute_sql_query(sql: str, username: str) -> Dict[str, Any]:
    """
    Execute a SQL query and return the results.
    
    Args:
        sql: SQL query string
        username: Username for database context
    
    Returns:
        Dictionary with 'columns', 'result', and 'error' keys
    """
    try:
        if not sql:
            return {'columns': [], 'result': [], 'error': 'No SQL provided'}
        
        cursor = runSql(sql, username)
        if cursor and cursor.description:
            columns = [col[0] for col in cursor.description]
            result = cursor.fetchall()
            # Convert rows to lists for JSON
            result_list = [list(r) for r in result]
            return {'columns': columns, 'result': result_list, 'error': None}
        else:
            return {'columns': [], 'result': [], 'error': None}
    except OperationalError as oe:
        print(f"OperationalError in execute_sql_query: {oe}")
        return {'columns': [], 'result': [], 'error': str(oe)}
    except Exception as e:
        print(f"Error in execute_sql_query: {e}")
        return {'columns': [], 'result': [], 'error': str(e)}


def save_database_file(user_dir: str, data: bytes) -> None:
    """
    Save database file from binary data.
    
    Args:
        user_dir: User's directory path
        data: Binary database content
    
    Raises:
        Exception: If file cannot be saved
    """
    file_path = os.path.join(user_dir, "datenbank.db")
    with open(file_path, 'wb+') as destination:
        destination.write(data)


def read_diagram_json(user_dir: str, filename: str) -> bytes:
    """
    Read diagram JSON file.
    
    Args:
        user_dir: User's directory path
        filename: Name of the JSON file (model.json or editor_model.json)
    
    Returns:
        File content as bytes
    
    Raises:
        Exception: If file cannot be read
    """
    with open(f'{user_dir}/{filename}', 'rb') as f:
        return f.read()


def save_diagram_json(user_dir: str, filename: str, data: bytes, process_diagram: bool = False, username: Optional[str] = None) -> None:
    """
    Save diagram JSON file and optionally process it.
    
    Args:
        user_dir: User's directory path
        filename: Name of the JSON file (model.json or editor_model.json)
        data: JSON data as bytes
        process_diagram: Whether to process the diagram (for model.json)
        username: Username (required if process_diagram is True)
    
    Raises:
        Exception: If file cannot be saved
    """
    
    json_string = data.decode('utf-8')
    jsondict = json.loads(json_string)
    jsondict = ModelAnalyzer._renamed_element_ids_to_readble_names(jsondict)
    
    with open(f'{user_dir}/{filename}', 'wb+') as f:
        f.write(json.dumps(jsondict).encode('utf-8'))
    
    if process_diagram and username:
        load_json(data, username)


def collect_system_data() -> Dict[str, Any]:
    """
    Collect comprehensive system information including disk, RAM, CPU, users, and audit logs.
    
    Returns:
        Dictionary containing all system data
    
    Raises:
        Exception: If system data cannot be collected
    """
    print(f"{timestamp()}Collecting system data...")
    
    # Get user databases directory information
    try:
        user_databases_path = os.path.join(os.getcwd(), 'user_databases')
        user_data = get_directory_tree_with_sizes(user_databases_path)
    except Exception as e:
        print(f"Error getting user directory data: {e}")
        user_data = []

    # Get system drive usage
    try:
        if os.name == 'nt':  # Windows
            current_drive = os.path.splitdrive(os.getcwd())[0] + os.sep
            total, used, free = shutil.disk_usage(current_drive)
        else:  # Unix/Linux
            total, used, free = shutil.disk_usage("/")
        
        fullness_percentage = (used / total) * 100
    except Exception as e:
        print(f"Error getting disk usage: {e}")
        total, used, free = 0, 0, 0
        fullness_percentage = 0

    # Convert to GB
    total_gb = round(total / (1024 ** 3), 2)
    used_gb = round(used / (1024 ** 3), 2)
    free_gb = round(free / (1024 ** 3), 2)

    # Get RAM usage
    try:
        ram = psutil.virtual_memory()
        ram_total = round(ram.total / (1024 ** 3), 2)
        ram_used = round(ram.used / (1024 ** 3), 2)
        ram_free = round(ram.available / (1024 ** 3), 2)
        ram_percentage = ram.percent
    except Exception as e:
        print(f"Error getting RAM usage: {e}")
        ram_total = ram_used = ram_free = ram_percentage = 0

    # Get CPU usage
    try:
        cpu_percentage = psutil.cpu_percent(0.5)
    except Exception as e:
        print(f"Error getting CPU usage: {e}")
        cpu_percentage = 0

    # Get logged-in users count
    logged_in_users = get_logged_in_users_count()
    print(f"{timestamp()}Logged in users count: {logged_in_users}")

    # Get detailed session information
    session_details = get_session_details()
    print(session_details)
    
    # Get recent audit logs
    recent_audit_logs = views_user.get_recent_audit_logs()
    
    # Prepare response data
    response_data = {
        'directories': user_data,
        "fullness_percentage": int(round(fullness_percentage, 0)),
        "total_gb": "{:.2f}".format(total_gb),
        "used_gb": "{:.2f}".format(used_gb),
        "free_gb": "{:.2f}".format(free_gb),
        "ram_total": "{:.2f}".format(ram_total),
        "ram_used": "{:.2f}".format(ram_used),
        "ram_free": "{:.2f}".format(ram_free),
        "ram_percentage": int(round(ram_percentage, 0)),
        "cpu_percentage": int(round(cpu_percentage, 0)),
        "logged_in_users": logged_in_users,
        "session_info": session_details,
        "recent_audit_logs": [
            {
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'username': log.username,
                'action': log.action,
                'action_display': dict(log.ACTION_CHOICES).get(log.action, log.action),
                'ip_address': log.ip_address or 'Unknown',
                'operating_system': log.operating_system or 'Unknown',
                'location': log.location or 'Unknown',
                'session_id': log.session_id or 'Unknown'
            } for log in recent_audit_logs
        ]
    }
    
    return response_data


def log_and_rotate_system_data(response_data: Dict[str, Any]) -> None:
    """
    Log system data to CSV and perform audit log rotation check.
    
    Args:
        response_data: System data dictionary to log
    """
    # Log data to CSV
    print(f"{timestamp()}Logging resource data to CSV...")
    views_user.log_resource_data_to_csv(response_data)
    print(f"{timestamp()}CSV logging completed.")
    
    # Check for audit log rotation (every 10th call to avoid overhead)
    import random
    if random.randint(1, 10) == 1:
        try:
            print(f"{timestamp()}Checking audit log rotation...")
            views_user.rotate_audit_logs()
        except Exception as e:
            print(f"{timestamp()}Error during audit log rotation check: {e}")
