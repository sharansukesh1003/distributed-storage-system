from django.db import models

class StoredFile(models.Model):
    file_size = models.BigIntegerField()
    id = models.AutoField(primary_key=True)
    file_id = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name

class FileChunk(models.Model):
    file = models.ForeignKey(StoredFile, on_delete=models.CASCADE, related_name='chunks')
    chunk_number = models.IntegerField()
    chunk_size = models.BigIntegerField()
    chunk_path = models.CharField(max_length=500)
    checksum = models.CharField(max_length=64, null=True, blank=True)  # New field
    node_name = models.CharField(max_length=255, default="default_node") # Add this if missing

    def __str__(self):
        return f"{self.file.file_name} - Chunk {self.chunk_number}"
