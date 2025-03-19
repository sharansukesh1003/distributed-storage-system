import json
import docker
from .models import ContainerStats
from django.shortcuts import render
from datetime import datetime, timezone
from storage_app.models import StoredFile, FileChunk

client = docker.from_env()

from .models import ContainerStats

def container_dashboard(request):
    containers = client.containers.list(all=True)
    health_info = []
    metrics_info = []

    # Fetch the latest 15 rows based on timestamp
    latest_15_stats = ContainerStats.objects.all().order_by('-timestamp')[:15]

    # Map container stats to container names for easier access
    container_stats_map = {stat.container_name: stat for stat in latest_15_stats}

    for container in containers:
        try:
            container_state = container.attrs.get('State', {})
            network_settings = container.attrs.get('NetworkSettings', {})
            networks = network_settings.get('Networks', {})
            network_info = list(networks.values())[0] if networks else {}

            started_at_raw = container_state.get('StartedAt', '')
            started_at_readable = "N/A"
            if started_at_raw:
                started_dt = datetime.strptime(started_at_raw.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                started_dt = started_dt.replace(tzinfo=timezone.utc)
                time_diff = datetime.now(timezone.utc) - started_dt
                started_at_readable = str(time_diff).split('.')[0]

            container_info = {
                'name': container.name,
                'status': container.status,
                'error': container_state.get('Error', '') or 'No errors',
                'started_at': started_at_readable,
                'ip_address': network_info.get('IPAddress', 'N/A'),
            }
        except Exception as e:
            container_info = {
                'name': container.name,
                'status': container.status,
                'error': f"Error retrieving info",
                'started_at': 'N/A',
                'ip_address': 'N/A',
            }

        health_info.append(container_info)

        # Fetch metrics from the previously fetched ContainerStats
        stats = container_stats_map.get(container.name)
        if stats:
            metrics_info.append({
                'name': container.name,
                'cpu_usage': [stats.cpu_usage],  # Changed to a list
                'memory_usage': [stats.memory_usage],  # Changed to a list
                'status': container.status,
                'error': container_state.get('Error', '') or 'No errors',
                'started_at': started_at_readable,
                'ip_address': network_info.get('IPAddress', 'N/A'),
            })
        else:
            metrics_info.append({
                'name': container.name,
                'cpu_usage': ['N/A'],  # Changed to a list
                'memory_usage': ['N/A'],  # Changed to a list
                'status': container.status,
                'error': f"Error retrieving info",
                'started_at': 'N/A',
                'ip_address': 'N/A',
            })

    # Add file and chunk counts here
    total_files = StoredFile.objects.count()
    total_chunks = FileChunk.objects.count()

    return render(request, 'dashboard_app/container_dashboard.html', {
        'health_info': health_info,
        'metrics_info': metrics_info,
        'total_files': total_files,
        'total_chunks': total_chunks,
    })


def fetch_and_store_container_stats():
    containers = client.containers.list(all=True)

    for container in containers:
        try:
            stats = container.stats(stream=False)

            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100

            memory_usage = stats['memory_stats']['usage']
            memory_mb = round(memory_usage / (1024 * 1024), 2)

            # Save the stats to the database
            container_stats = ContainerStats.objects.create(
                container_name=container.name,
                cpu_usage=round(cpu_percent, 2),
                memory_usage=memory_mb,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            print(f"Error retrieving stats for container {container.name}: {e}")
