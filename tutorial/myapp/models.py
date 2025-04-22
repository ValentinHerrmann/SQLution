from django.db import models

    
class DatabaseModel(models.Model):
    user = models.TextField(default='anonymous', primary_key=True)
    json = models.JSONField(default=dict, blank=True, null=True)
    sql = models.TextField(default='')
    db = models.BinaryField(default=b'', null=True, blank=True)
    updated_at = models.CharField()