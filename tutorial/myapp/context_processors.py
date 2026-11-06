from myapp.utils.roles import can_manage_accounts, is_db_admin, is_global_admin


def account_roles(request):
    """Role flags for the navigation (and the review banner)."""
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {'is_db_admin': False, 'can_manage_accounts': False, 'is_global_admin': False, 'review': None}
    review = None
    if getattr(user, 'in_review', False):
        review = request.session.get('review')
    return {
        'is_db_admin': is_db_admin(user),
        'can_manage_accounts': can_manage_accounts(user),
        'is_global_admin': is_global_admin(user),
        'review': review,
    }
