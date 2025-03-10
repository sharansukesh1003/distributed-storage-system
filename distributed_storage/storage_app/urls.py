from django.urls import path
from .views import upload_file_chunked, download_file

urlpatterns = [
    path('download/<str:file_id>/', download_file, name='download'),
    path('upload_chunked/', upload_file_chunked, name='upload_chunked'),
]
