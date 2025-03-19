import json
import docker
from django.shortcuts import render

# Initialize Docker client
client = docker.from_env()

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
