from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ZippedFolder(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    zip_file = models.FileField(upload_to='zip/')

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('FORCED_LOGOUT', 'Forced Logout'),
        ('SESSION_TIMEOUT', 'Session Timeout'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=150)  # Store username even if user is deleted
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    operating_system = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    session_id = models.CharField(max_length=40, null=True, blank=True)  # Django session key length
    timestamp = models.DateTimeField(default=timezone.now)
    forced_reason = models.CharField(max_length=200, null=True, blank=True)  # For forced logouts
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.username} - {self.action} at {self.timestamp}"

class AccountPrefix(models.Model):
    """A course/batch prefix (e.g. 'q11inf'). Claimed by the group admin who uses it first."""
    name = models.CharField(max_length=16, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_prefixes')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AccountProfile(models.Model):
    """User-management data for an account."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # The group admin supervising this account. None = independent account.
    managed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_accounts')
    prefix = models.ForeignKey(AccountPrefix, on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts')
    delete_at = models.DateTimeField(null=True, blank=True)  # automatic deletion
    lock_at = models.DateTimeField(null=True, blank=True)    # scheduled lock (e.g. project submission)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Profile of {self.user.username}"


def get_profile(user) -> AccountProfile:
    profile, _ = AccountProfile.objects.get_or_create(user=user)
    return profile
