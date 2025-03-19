import io
import time
import boto3
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

from .forms import FileUploadForm
from .models import StoredFile, FileChunk
from .utils import compute_checksum

CHUNK_SIZE = 5 * 1024 * 1024  # 5MB

s3_client = boto3.client(
    's3',
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

@csrf_exempt
def upload_file_chunked(request):
    """
    Handle both GET (show the upload page) and POST (process file upload).
    We'll detect file type with python-magic and store an 'icon_class'
    that the template can use to show a nice icon (no endswith usage).
    """
    if request.method == 'GET':
        form = FileUploadForm()
        # Retrieve all stored files (latest first)
        files = StoredFile.objects.all().order_by('-uploaded_at')

        # Example: annotate each file with an icon_class
        for f in files:
            f.icon_class = map_mime_to_icon(f.file_name)

            # Optional: if you have logic to see which nodes hold each chunk
            chunk_nodes = list(FileChunk.objects.filter(file=f).values_list('node_name', flat=True).distinct())
            if chunk_nodes:
                f.nodes = chunk_nodes
            else:
                f.nodes = ['Unknown']

        return render(request, 'storage_app/upload_download.html', {
            'form': form,
            'files': files
        })

    elif request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            file_name = file.name
            file_size = file.size
            current_time_ms = int(time.time() * 1000)
            file_id = f"{file_name}_{file_size}_{current_time_ms}"

            # Create the StoredFile record
            stored_file = StoredFile.objects.create(
                file_id=file_id,
                file_name=file_name,
                file_size=file_size,
                file_path=f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{file_id}",
            )

            # Chunked upload to MinIO
            chunk_number = 0
            while True:
                chunk = file.read(CHUNK_SIZE)
                if not chunk:
                    break

                checksum = compute_checksum(chunk)
                chunk_filename = f"{file_id}_chunk{chunk_number}"
                s3_client.put_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=chunk_filename,
                    Body=chunk
                )

                # If you know which node stored this chunk, store it in 'node_name'
                # For example, if you have some distribution logic or from MinIO logs:
                node_name = determine_node_for_chunk(chunk_filename)  # you must define or mock
                FileChunk.objects.create(
                    file=stored_file,
                    chunk_number=chunk_number,
                    chunk_size=len(chunk),
                    chunk_path=f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{chunk_filename}",
                    checksum=checksum,
                    node_name=node_name,
                )
                chunk_number += 1

            return JsonResponse({
                'status': 'success',
                'file_id': file_id,
                'file_name': file_name,
                'file_size': file_size,
            })
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

import io
from django.http import FileResponse, HttpResponse
from django.core.cache import cache
from django.conf import settings

def download_file(request, file_id):
    """
    Download all chunks, verify checksums, combine them, return as a single file.
    """
    try:
        stored_file = StoredFile.objects.get(file_id=file_id)

        # Try cache
        cached_file = cache.get(file_id)
        if cached_file:
            print("Serving from cache")
            cached_file_buffer = io.BytesIO(cached_file)
            cached_file_buffer.seek(0)
            return FileResponse(cached_file_buffer, as_attachment=True, filename=stored_file.file_name)

        # Reconstruct file from chunks
        chunks = FileChunk.objects.filter(file=stored_file).order_by('chunk_number')
        file_buffer = io.BytesIO()

        for chunk in chunks:
            try:
                response = s3_client.get_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=chunk.chunk_path.split('/')[-1]
                )
                data = response['Body'].read()

                # Verify checksum
                downloaded_checksum = compute_checksum(data)
                if downloaded_checksum == chunk.checksum:
                    print(f"Verified Chunk {chunk.chunk_number}: {downloaded_checksum}")
                else:
                    print(f"Verify Failed for Chunk {chunk.chunk_number}")
                    return HttpResponse("File verification failed", status=500)

                file_buffer.write(data)

            except s3_client.exceptions.NoSuchKey:
                print(f"Chunk {chunk.chunk_number} is missing in S3.")
                return HttpResponse(
                    f"<div style='text-align: center; color: red; margin-top: 30px;'> <h2> Chunk {chunk.chunk_number} is missing.</h2></div>",
                    status=404,
                )

        # Cache for future (1 hour timeout restored)
        file_buffer.seek(0)  # Seek before caching
        content = file_buffer.read()
        cache.set(file_id, content, timeout=3600)

        file_buffer.seek(0)  # Seek again before serving
        return FileResponse(file_buffer, as_attachment=True, filename=stored_file.file_name)

    except StoredFile.DoesNotExist:
        return HttpResponse("File not found", status=404)


def delete_file(request, file_id):
    """
    Delete the file's DB entry and optionally remove from MinIO as well.
    """
    if request.method == 'POST':
        try:
            stored_file = StoredFile.objects.get(file_id=file_id)
            # Delete chunks from MinIO if desired
            chunks = FileChunk.objects.filter(file=stored_file)
            for c in chunks:
                object_key = c.chunk_path.split('/')[-1]
                try:
                    s3_client.delete_object(
                        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                        Key=object_key
                    )
                except Exception:
                    pass  # handle or log errors
            # Delete DB records
            stored_file.delete()
            return JsonResponse({'status': 'success'})
        except StoredFile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'File not found'}, status=404)
    else:
        return HttpResponse("Method not allowed", status=405)


# ----------------------
# HELPER FUNCTIONS
# ----------------------
def map_mime_to_icon(filename: str) -> str:
    """
    Use python-magic to detect file type from content, or fallback to extension.
    Return a Bootstrap Icons class name for the UI.
    """
    # If you want to read actual bytes, you'd open the file from S3 or your local storage
    # But for a large file, that's inefficient. So we might read just the first chunk
    # or fallback to extension-based approach. Here's a simple extension approach:

    ext = filename.lower().rsplit('.', 1)[-1]
    if ext in ['pdf']:
        return 'bi-file-earmark-pdf text-danger'
    elif ext in ['xls', 'xlsx', 'csv']:
        return 'bi-file-earmark-spreadsheet text-success'
    elif ext in ['doc', 'docx']:
        return 'bi-file-earmark-word text-primary'
    elif ext in ['png', 'jpg', 'jpeg', 'gif']:
        return 'bi-file-earmark-image'
    else:
        return 'bi-file-earmark'

def determine_node_for_chunk(chunk_filename: str) -> str:
    """
    If you're distributing chunks across multiple MinIO nodes or servers,
    you can implement logic to figure out which node stored the chunk.
    This might involve checking logs, or using the MinIO Admin API, etc.
    For now, let's just return a placeholder.
    """
    # Real approach might call a function or parse logs:
    # node = get_minio_node_for_object(chunk_filename)
    # return node
    return "minio1"  # or "minio2" etc.

from django.shortcuts import get_object_or_404

def file_details(request, file_id):
    """
    Render detailed information about a stored file,
    including its chunk information and any metadata.
    """
    stored_file = get_object_or_404(StoredFile, file_id=file_id)
    chunks = FileChunk.objects.filter(file=stored_file).order_by('chunk_number')
    context = {
        'file': stored_file,
        'chunks': chunks,
    }
    return render(request, 'storage_app/file_details.html', context)