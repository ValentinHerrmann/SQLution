"""
Django shell script to create a superuser with username and password.

Usage in Django shell:
    python manage.py shell < create_user.py

Or interactively:
    python manage.py shell
    >>> exec(open('create_user.py').read())
    >>> create_superuser('admin', 'mypassword123')
"""

from django.contrib.auth import get_user_model


def create_superuser(username, password, email=''):
    """
    Create a superuser with the given username and password.
    
    Args:
        username (str): The username for the new superuser
        password (str): The password for the new superuser
        email (str): Optional email address (defaults to empty string)
    
    Returns:
        User: The created user object, or None if user already exists
    """
    User = get_user_model()
    
    if User.objects.filter(username=username).exists():
        print(f'Error: User "{username}" already exists')
        return None
    
    user = User.objects.create_superuser(
        username=username,
        password=password,
        email=email
    )
    print(f'Superuser "{username}" created successfully')
    return user


def delete_user(username):
    """
    Delete a user by username.
    
    Args:
        username (str): The username of the user to delete
    
    Returns:
        bool: True if user was deleted, False if user was not found
    """
    User = get_user_model()
    
    user = User.objects.filter(username=username).first()
    if user:
        user.delete()
        print(f'User "{username}" deleted successfully')
        return True
    else:
        print(f'Error: User "{username}" not found')
        return False


def list_users():
    """
    List all users in the database.
    
    Returns:
        QuerySet: All user objects
    """
    User = get_user_model()
    users = User.objects.all()
    
    print(f'\nTotal users: {users.count()}')
    print('-' * 60)
    for user in users:
        status = 'superuser' if user.is_superuser else 'staff' if user.is_staff else 'user'
        print(f'{user.username:20} | {user.email:30} | {status}')
    print('-' * 60)
    
    return users


# Example usage (uncomment to run automatically):
# create_superuser('admin', 'admin123')
