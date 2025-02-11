from apscheduler.schedulers.background import BackgroundScheduler
from .utils.order_updater import update_order_statuses
from django.conf import settings

def start():
    if settings.DEBUG:
        scheduler = BackgroundScheduler()
        scheduler.add_job(update_order_statuses, 'interval', hours=24)
        scheduler.start() 