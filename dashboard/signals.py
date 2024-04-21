from django.db.models.signals import post_save
from django.dispatch import receiver, User
from .models import Product, Order

@receiver(post_save, sender=Product)
def generate_order_on_low_stock(sender, instance, created, **kwargs):
    if not created:  # Check if the product is being updated
        low_stock_threshold = 50  # Retrieve threshold from settings or a separate model
        if instance.quantity < low_stock_threshold:
            # Customize order details based on your requirements
            order_quantity = max(low_stock_threshold - instance.quantity, 1)  # Ensure order quantity is at least 1
            # You can associate the order with the current user or a default staff member
            # For demonstration purposes, let's use a default staff member with ID=1
            default_staff = User.objects.get(pk=1)
            Order.objects.create(product=instance, staff=default_staff, order_quantity=order_quantity)
