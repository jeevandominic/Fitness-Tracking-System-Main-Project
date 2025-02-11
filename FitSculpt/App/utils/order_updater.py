from django.db import connection
from datetime import datetime, timedelta
from .delivery_utils import get_nearest_center

def update_order_statuses():
    """Update order statuses based on time elapsed since payment"""
    with connection.cursor() as cursor:
        # Get orders that need status updates
        cursor.execute("""
            SELECT o.id, o.status, o.order_date, a.zip_code 
            FROM app_order o
            JOIN app_address a ON o.address_id = a.id
            WHERE o.status IN ('Paid', 'Shipped', 'On Transit', 'Out for Delivery')
        """)
        orders = cursor.fetchall()
        
        now = datetime.now()
        for order_id, status, order_date, pincode in orders:
            days_elapsed = (now - order_date).days
            new_status = None
            
            if status == 'Paid' and days_elapsed >= 1:
                new_status = 'Shipped'
            elif status == 'Shipped' and days_elapsed >= 2:
                new_status = 'On Transit'
            elif status == 'On Transit' and days_elapsed >= 3:
                new_status = 'Out for Delivery'
            
            if new_status:
                # Update order status
                cursor.execute("""
                    UPDATE app_order 
                    SET status = %s, 
                        delivery_center = %s
                    WHERE id = %s
                """, [new_status, get_nearest_center(pincode), order_id]) 