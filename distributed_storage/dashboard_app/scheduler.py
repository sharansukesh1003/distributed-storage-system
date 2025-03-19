from datetime import datetime
from .views import fetch_and_store_container_stats
from apscheduler.schedulers.background import BackgroundScheduler

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Schedule the fetch_and_store_container_stats function to run every 10 minutes
    scheduler.add_job(fetch_and_store_container_stats, 'interval', minutes=1)
    scheduler.start()

