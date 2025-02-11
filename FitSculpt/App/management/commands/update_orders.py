from django.core.management.base import BaseCommand
from App.utils.order_updater import update_order_statuses

class Command(BaseCommand):
    help = 'Update order statuses based on time elapsed'

    def handle(self, *args, **kwargs):
        update_order_statuses()
        self.stdout.write(self.style.SUCCESS('Successfully updated order statuses')) 