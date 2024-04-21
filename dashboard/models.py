from django.db.models import F  # Add this import statement at the beginning of your models.py file
from django.db import models
from django.contrib.auth.models import User

CATEGORY = (
    ('Industrial Supply', 'Industrial Supply'),
    ('Kitchen & Cooking', 'Kitchen & Cooking'),
    ('Construction Material', 'Construction Material'),
    ('Cleaning and Janitorial Supplies', 'Cleaning and Janitorial Supplies'),
    ('Maintenance and Repair', 'Maintenance and Repair'),
    ('Electronics', 'Electronics'),
    ('Telecommunications', 'Telecommunications'),
    ('Electrical and Lighting', 'Electrical and Lighting'),
    ('Safety and Security', 'Safety and Security'),
)

SUPPLIER = (
    ('Total Gas', 'Total Gas'),
    ('Iron Sheets', 'Iron Sheets'),
)

class Product(models.Model):
    name = models.CharField(max_length=100, null=True)
    category = models.CharField(max_length=200, choices=CATEGORY, null=True)
    quantity = models.PositiveIntegerField(null=True)
    low_stock_threshold = models.PositiveIntegerField(default=50)
    price = models.OneToOneField('Price', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f'{self.name} - {self.quantity}'
    
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold
    
class Supplier(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, default=1)
    

    def __str__(self):
        return self.name


class AutoOrder(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order_quantity = models.PositiveIntegerField()
   
    date = models.DateTimeField(auto_now_add=True)
    is_auto_generated = models.BooleanField(default=True)

    def __str__(self):
        return f'Auto Order for {self.product}'

    @staticmethod
    def generate_auto_orders():
        low_stock_products = Product.objects.filter(quantity__lte=F('low_stock_threshold'))
         
        for product in low_stock_products:
            existing_auto_order = AutoOrder.objects.filter(product=product).exists()
            if not existing_auto_order:
                order_quantity = product.low_stock_threshold - product.quantity
                AutoOrder.objects.create(product=product, order_quantity=150)

class Price(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'${self.amount}'

class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    staff = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    order_quantity = models.PositiveIntegerField(null=True)
    category = models.CharField(max_length=200, choices=CATEGORY, null=True)
    date = models.DateTimeField(auto_now_add=True)
    is_auto_generated = models.BooleanField(default=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f'Sale: {self.product} - {self.order_quantity}'

    @staticmethod
    def sell_product(product, staff, quantity):
        if product.quantity >= quantity:
            product.quantity -= quantity
            product.save()

            Order.objects.create(product=product, staff=staff, order_quantity=quantity)
            return True
        else:
            return False
        

class Sales(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True) 

    def total_cost(self):
        return self.quantity * self.price

    def __str__(self):
        return f'Sale of {self.quantity} {self.product.name} on {self.date}'
    
class SoldProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_sold = models.PositiveIntegerField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    date_sold = models.DateTimeField(auto_now_add=True)
    staff = models.ForeignKey(User, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # Calculate total price before saving
        self.total_price = self.quantity_sold * self.price_per_unit
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Sold {self.quantity_sold} of {self.product.name} on {self.date_sold}'