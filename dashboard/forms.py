from django import forms
from .models import Product, Order # Import the Supplier model
from .models import Supplier, Sales
from django.utils import timezone


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'quantity']
     


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'email', 'phone_number', 'product'] # Include the fields you want to appear in the form
        
class OrderForm(forms.ModelForm):
    # Define choices for suppliers
   
    # Add a field for selecting suppliers
    # Define choices for suppliers
    class Meta:
        model = Order
        fields = ['product', 'order_quantity', 'supplier', 'is_auto_generated']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})  # Use DateInput widget
        }

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        # Populate the supplier field with available options
        self.fields['supplier'].queryset = Supplier.objects.all()
        # Set the initial value for the date field to the current date
        self.initial['date'] = timezone.now().date()

class SalesForm(forms.ModelForm):
    class Meta:
        model = Sales
        fields = ['product', 'quantity', 'price']
