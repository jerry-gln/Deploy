# utils.py

from .models import Product, Order
from django.db.models import F  # Import F object from django.db.models
from twilio.rest import Client

def send_sms(to_number, message):
    # Your Twilio account SID and auth token
    account_sid = 'ACba8e8fd55df89b192c081e16e6565ab5'
    auth_token = '[AuthToken]'

    # Twilio phone number
    from_number = '+12512603871'

    # Initialize Twilio client
    client = Client(account_sid, auth_token)

    try:
        # Send the SMS message
        message = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        print("Message sent successfully!")
        return True
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False

# Example usage:
if __name__ == "__main__":
    # Specify recipient's phone number and message
    recipient_number = '+254111994228'  # Replace with recipient's phone number
    sms_message = 'Please enter your M-Pesa PIN to complete the transaction.'

    # Send the SMS
    send_sms(recipient_number, sms_message)


def check_and_create_orders():
    low_stock_products = Product.objects.filter(quantity__lte=F('low_stock_threshold'))
    
    for product in low_stock_products:
        # Create order for the product
        order = Order.objects.create(product=product, quantity=50)  # Example quantity, adjust as needed

        # Update product quantity
        product.quantity += order.quantity
        product.save()
