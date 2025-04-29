import os
from django.db import models

from tutorial.tutorial.settings import BASE_DIR

class ZippedFolder(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    zip_file = models.FileField(upload_to=os.path.join(BASE_DIR, 'static'))