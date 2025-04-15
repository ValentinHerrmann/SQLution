from django.db import models

# Create your models here.
class TodoItem(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title + " - " + str(self.completed)
    
class DatabaseModel(models.Model):
    json = models.JSONField()
    sql = models.CharField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return super().__str__()