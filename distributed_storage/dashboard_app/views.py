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
        # Get the container name and health status
        container_info = {
            'name': container.name,
            'status': container.status,  # Running, Exited, etc.
        }

        try:
            # Check for errors if the container is stopped or has finished
            container_state = container.attrs.get('State', {})
            error_message = container_state.get('Error', '')
            
            # If there's an error message, include it in the info
            if error_message:
                container_info['error'] = error_message
            else:
                container_info['error'] = 'No errors'
            
            # Check the health status for running containers
            if container.status == "running":
                health = container_state.get('Health', {}).get('Status', 'N/A')
                container_info['health'] = health
        except Exception as e:
            container_info['error'] = f"Error retrieving info: {str(e)}"
        
        health_info.append(container_info)

        # Collect container resource usage metrics (CPU, Memory, etc.)
        stats = container.stats(stream=False)  # Get one snapshot of the container's stats
        metrics_info.append({
            'name': container.name,
            'cpu_percent': stats['cpu_stats']['cpu_usage']['total_usage'],
            'memory_usage': stats['memory_stats']['usage'],
        })

    # Pass the health and metrics info to the template
    return render(request, 'dashboard_app/container_dashboard.html', {
        'health_info': health_info,
        'metrics_info': metrics_info
    })
