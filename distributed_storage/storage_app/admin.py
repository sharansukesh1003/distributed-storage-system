from . import models
from django.contrib import admin

# Register your models here.
admin.site.register(models.FileChunk)
admin.site.register(models.StoredFile)
