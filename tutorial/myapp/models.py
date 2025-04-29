from django.db import models

class ZippedFolder(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    zip_file = models.FileField(upload_to='myapp/staticfiles/')