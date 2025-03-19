from django.db import models

class ContainerStats(models.Model):
    container_name = models.CharField(max_length=255)
    cpu_usage = models.FloatField(default=0.0)
    memory_usage = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Stats for {self.container_name} at {self.timestamp}"
# Create your models here.