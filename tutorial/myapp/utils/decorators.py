def is_global_admin(user):
    return user.is_authenticated and user.username == 'admin'

def is_db_admin(user):
    return user.is_authenticated and user.username.endswith('_admin')
