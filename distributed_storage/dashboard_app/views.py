import json
import docker
from .models import ContainerStats
from django.shortcuts import render
from datetime import datetime, timezone
from storage_app.models import StoredFile, FileChunk

client = docker.from_env()

from .models import ContainerStats

def container_dashboard(request):
    # Get the status of the containers
    containers = client.containers.list(all=True)  # List all containers, running or stopped
    health_info = []
    metrics_info = []

    for container in containers:
        # Get container stats
        stats = container.stats(stream=False)
        stats_str = json.dumps(stats, indent=4)  # Optional, for debugging
        print(stats_str)  # Print JSON data for inspection

        # Collect container info
        container_info = {
            'name': container.name,
            'status': container.status,  # Running, Exited, etc.
        }

        try:
            # Get error message if any
            container_state = container.attrs.get('State', {})
            error_message = container_state.get('Error', '')
            container_info['error'] = error_message if error_message else 'No errors'
            
            # Check health status for running containers
            if container.status == "running":
                health = container_state.get('Health', {}).get('Status', 'N/A')
                container_info['health'] = health
        except Exception as e:
            container_info['error'] = f"Error retrieving info: {str(e)}"
        
        health_info.append(container_info)

        # Collect container resource usage metrics (CPU, Memory, etc.)
        metrics_info.append({
            'name': container.name,
            'cpu_usage': stats['cpu_stats']['cpu_usage']['total_usage'],
            'memory_usage': stats['memory_stats']['usage'],
            'pids_stats': stats.get('pids_stats', {}).get('current', 'N/A'),
            'rx_bytes': stats['networks']['eth0'].get('rx_bytes', 0),
            'tx_bytes': stats['networks']['eth0'].get('tx_bytes', 0),
            'rx_packets': stats['networks']['eth0'].get('rx_packets', 0),
            'tx_packets': stats['networks']['eth0'].get('tx_packets', 0),
        })

    # Pass the health and metrics info to the template
    return render(request, 'dashboard_app/container_dashboard.html', {
        'health_info': health_info,
        'metrics_info': metrics_info
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
