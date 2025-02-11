from django.contrib import admin
from django.urls import include, path
from App import views
from django.conf import settings
from django.contrib import admin
from django.urls import path
from App import views
from django.apps import apps
from apscheduler.schedulers.background import BackgroundScheduler
from App.utils.order_updater import update_order_statuses

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('App.urls')),
]

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_order_statuses, 'interval', hours=24)
    scheduler.start()

# Only start scheduler if it's the main process
if not apps.is_installed('django.contrib.admin'):
    start_scheduler()
