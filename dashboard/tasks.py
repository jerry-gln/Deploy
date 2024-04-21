# tasks.py

from celery import shared_task
from .models import Product, Order

@shared_task
def check_low_stock_and_generate_orders():
    # Define your threshold for low stock
    LOW_STOCK_THRESHOLD = 50
    
    # Get all products with quantity less than or equal to the threshold
    low_stock_products = Product.objects.filter(quantity__lte=LOW_STOCK_THRESHOLD)
    
    # Iterate through low stock products and generate orders
    for product in low_stock_products:
        # Calculate the quantity needed to reach the threshold

        # Create an order for the product
        Order.objects.create(product_name={{ product.name }}, order_quantity=200)
