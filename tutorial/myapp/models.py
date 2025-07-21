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
    user_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    forced_reason = models.CharField(max_length=200, null=True, blank=True)  # For forced logouts
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.username} - {self.action} at {self.timestamp}"