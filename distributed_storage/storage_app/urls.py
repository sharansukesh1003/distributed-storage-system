from django.urls import path
from .views import upload_file_chunked, download_file, delete_file, file_details

urlpatterns = [
    path('download/<str:file_id>/', download_file, name='download'),
    path('upload_chunked/', upload_file_chunked, name='upload_chunked'),
     path('delete/<str:file_id>/', delete_file, name='delete_file'),
    path('file-details/<str:file_id>/', file_details, name='file_details'),
]
