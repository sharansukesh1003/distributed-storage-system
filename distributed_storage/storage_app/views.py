import os
import io
import boto3
from django.conf import settings
from .forms import FileUploadForm
from django.shortcuts import render
from .models import StoredFile, FileChunk
from django.http import FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

CHUNK_SIZE = 5 * 1024 * 1024  # 5MB per chunk

s3_client = boto3.client(
    's3',
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

@csrf_exempt
def upload_file_chunked(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            file_name = file.name
            file_size = file.size
            file_id = f"{file_name}_{file_size}"  # Unique ID for chunks

            # Save metadata for the full file
            stored_file = StoredFile.objects.create(
                file_id=file_id,
                file_name=file_name,
                file_size=file_size,
                file_path=f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{file_id}"
            )

            chunk_number = 0
            while True:
                chunk = file.read(CHUNK_SIZE)
                if not chunk:
                    break
                
                chunk_filename = f"{file_id}_chunk{chunk_number}"
                s3_client.put_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=chunk_filename,
                    Body=chunk
                )

                # Save chunk metadata
                FileChunk.objects.create(
                    file=stored_file,
                    chunk_number=chunk_number,
                    chunk_size=len(chunk),
                    chunk_path=f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{chunk_filename}"
                )

                chunk_number += 1

            return render(request, 'storage_app/upload_success.html', {'file_name': file_name})

    else:
        form = FileUploadForm()

    return render(request, 'storage_app/upload.html', {'form': form})

def download_file(request, file_id):
    try:
        stored_file = StoredFile.objects.get(file_id=file_id)
        print(stored_file)
        chunks = FileChunk.objects.filter(file=stored_file).order_by('chunk_number')

        file_buffer = io.BytesIO()
        
        for chunk in chunks:
            response = s3_client.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=chunk.chunk_path.split('/')[-1])
            file_buffer.write(response['Body'].read())

        file_buffer.seek(0)
        response = FileResponse(file_buffer, as_attachment=True, filename=stored_file.file_name)
        return response

    except StoredFile.DoesNotExist:
        return HttpResponse("File not found", status=404)