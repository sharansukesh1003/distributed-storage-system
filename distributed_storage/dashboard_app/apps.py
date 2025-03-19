from django.apps import AppConfig

class DashboardAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard_app'

    def ready(self):
        from .scheduler import start_scheduler  # Import the scheduler start function
        start_scheduler()  # Start the scheduler when the app is ready
