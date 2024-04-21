from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Order, Supplier, AutoOrder, SoldProduct
from .forms import ProductForm, OrderForm, SalesForm  # Import OrderForm
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import SupplierForm
from django.db.models import Q  # Import Q object
from .models import Sales 
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseServerError
import logging
import locale
from django.http import JsonResponse
import datetime
from django.db import models 
from collections import Counter
from datetime import timedelta
from collections import defaultdict
from django.template.loader import render_to_string
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from django.utils import timezone
from django.db.models import Sum, F
from django.db.models import F, ExpressionWrapper, FloatField
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image
import io
from .models import AutoOrder
from .models import SoldProduct
from django.db.models.functions import TruncDay

# Get an instance of a logger
logger = logging.getLogger(__name__)


@login_required
def index(request):
    # Call the function to generate auto orders
    AutoOrder.generate_auto_orders()

    # Get all products
    products = Product.objects.all()

    # Retrieve all orders (both manual and auto)
    orders = Order.objects.filter(is_auto_generated=False)  # Manual orders
    auto_orders = AutoOrder.objects.all()  # Auto orders

    # Combine manual and auto orders
    all_orders = list(orders) + list(auto_orders)

    # Retrieve low stock products
    low_stock_products = Product.objects.filter(quantity__lt=50)  # Adjust the threshold as needed

    # Get unique categories of low stock products
    low_stock_categories = low_stock_products.values_list('category', flat=True).distinct()

    # Retrieve all suppliers
    suppliers = Supplier.objects.all()

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Extract form data
            product_name = form.cleaned_data['product_name']
            category = form.cleaned_data['category']
            quantity = form.cleaned_data['quantity']
            supplier_id = form.cleaned_data['supplier']

            # Get or create product
            product, created = Product.objects.get_or_create(name=product_name, category=category)

            # Get the supplier
            supplier = Supplier.objects.get(pk=supplier_id)

            # Send email to supplier
            subject = 'New Order Received'
            message = f'You have received a new order for {quantity} units of {product_name}. Please process it.'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = supplier.email


            try:
                send_mail(subject, message, from_email, [to_email])
            except Exception as e:
                # Log any exception that occurs during email sending
                logger.error(f"Error sending email to {to_email}: {e}")
                # Return an error response if the email fails to send
                return HttpResponseServerError("An error occurred while sending the email. Please try again later.")


             # Check if an order already exists for the product
            existing_order = Order.objects.filter(product=product, is_auto_generated=False).first()

            if existing_order:
                # Update the existing order quantity
                existing_order.order_quantity += quantity
                existing_order.save()

            else:
                # Create order
                Order.objects.create(product=product, staff=request.user, order_quantity=quantity, supplier=supplier)

            return redirect('dashboard-index')
        
    else:
        form = OrderForm()

    context = {
        'orders': all_orders,
        'form': form,  # Pass the form to the template context
        'products': products,
        'low_stock_products': low_stock_products,
        'low_stock_categories': low_stock_categories,
        'suppliers': suppliers,  # Pass suppliers to the template context
        'auto_orders': auto_orders,
    }
    return render(request, 'dashboard/index.html', context)

@login_required
def staff(request):
    workers = User.objects.all()
    workers_count = workers.count()

    context = {
        'workers': workers,
        'workers_count': workers_count,
    }
    return render(request, 'dashboard/staff.html', context)

def staff_detail(request, pk):
    worker = User.objects.get(id=pk)
    context = {
        'worker': worker,
    }
    return render(request, 'dashboard/staff_detail.html', context)

@login_required
def staff_index(request):
    orders = Order.objects.all()  # Retrieve all orders
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()  # Save the form data to the database
            return redirect('dashboard-staff-index')
    else:
        form = OrderForm()  # Instantiate the OrderForm

    context = {
        'orders': orders,  # Pass orders data to the template
        'form': form,  # Pass the form to the template
    }
    return render(request, 'dashboard/staff_index.html', context)

@login_required
def product(request):
    items = Product.objects.all()
    product_count = items.count()
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product_name = form.cleaned_data.get('name')
            quantity = form.cleaned_data.get('quantity')
            price = form.cleaned_data.get('price')
            # Check if a product with the same name already exists
            existing_product = Product.objects.filter(name=product_name).first()
            if existing_product:
                # Update the existing product quantity by adding the new quantity
                existing_product.quantity += quantity
                existing_product.price = price  # Update price if needed
                existing_product.save()
                messages.success(request, f'{quantity} units of {product_name} has been added')
            else:
                # Create a new product
                form.save()
                messages.success(request, f'{quantity} units of {product_name} has been added')
                
            return redirect('dashboard-product')
    else:
        form = ProductForm()
    
    context = {
        'items': items,
        'form': form,
        'product_count': product_count,
    }
    return render(request, 'dashboard/product.html', context)

@login_required
def product_delete(request, pk):
    item = Product.objects.get(id=pk)
    if request.method == 'POST':
        item.delete()
        return redirect('dashboard-product')
    return render(request, 'dashboard/product_delete.html')

def product_update(request, pk):
    item = Product.objects.get(id=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('dashboard-product')
    else:
        form = ProductForm(instance=item)
    context = {
        'form': form,
    }
    return render(request, 'dashboard/product_update.html', context)

@login_required
def order(request):
    # Retrieve manually created orders by the logged-in user
    manual_orders = Order.objects.filter(staff=request.user)

    # Retrieve automatically generated orders for all users
    auto_orders = AutoOrder.objects.all()

    # Combine manual and automatic orders
    orders = list(manual_orders) + list(auto_orders)
    orders_count = len(orders)

    

    context = {
        'orders': orders,
        'orders_count': orders_count,
        'auto_orders' : auto_orders,
    }
    return render(request, 'dashboard/order.html', context)


def search(request):
    query = request.GET.get('q', '')  # Retrieve search query from request parameters

    if query:  # Check if query is not empty
        # Perform search using the query
        results = Product.objects.filter(name__icontains=query)
    else:
        results = []  # Return an empty list if query is empty

    context = {
        'query': query,
        'results': results,
    }
    # Render the search results in a template or return them as JSON data
    return render(request, 'dashboard/search_results.html', context)

@login_required
def supplier(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            # Fetch the product instance based on the provided product_id
            product = form.cleaned_data['product']
            
            # Create a new Supplier instance and associate it with the product
            supplier = form.save(commit=False)
            supplier.product = product
            supplier.save()
            
            return redirect('dashboard-suppliers')  # Redirect to the suppliers page after adding a new supplier
    else:
        form = SupplierForm()
    
    suppliers = Supplier.objects.all()
    context = {
        'form': form,
        'suppliers': suppliers,
    }
    return render(request, 'dashboard/suppliers.html', context)


@login_required
def add_supplier(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard-suppliers')  # Redirect to the list of suppliers after successful creation
    else:
        form = SupplierForm()
    return render(request, 'dashboard/add_supplier.html', {'form': form})

@login_required
def edit_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('dashboard-suppliers')  # Redirect to the list of suppliers after successful update
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'dashboard/edit_supplier.html', {'form': form})

@login_required
def delete_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        return redirect('dashboard-suppliers')  # Redirect to the list of suppliers after successful deletion
    return render(request, 'dashboard/delete_supplier.html', {'supplier': supplier})

@login_required
def sales(request):
    # Set the locale to use the user's preferred locale or the default locale if not available
    try:
        locale.setlocale(locale.LC_ALL, settings.LANGUAGE_CODE)
    except locale.Error:
        locale.setlocale(locale.LC_ALL, '')

    if request.method == 'POST':
        form = SalesForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity_sold = form.cleaned_data['quantity']
            unit_price = form.cleaned_data['price']
            
            # Check if requested quantity exceeds available stock
            if quantity_sold > product.quantity:
                error_message = f"Not enough stock available.<br> Available stock is: {product.quantity}"
                return render(request, 'dashboard/sales.html', {'error_message': error_message,'quantity_sold': quantity_sold})

            # Calculate the total sale price
            total_price = quantity_sold * unit_price

            # Update available quantity of the product
            product.quantity -= quantity_sold
            product.save()

            # Format the total price with comma as thousands separator
            formatted_total_price = "{:,.2f}".format(total_price)

           # Create SoldProduct instance
            sold_product = SoldProduct.objects.create(
                product=product,
                quantity_sold=quantity_sold,
                price_per_unit=unit_price,
                total_price=formatted_total_price,
                staff=request.user  # Associate the currently logged-in user (staff) with the sale
            )
            sold_product.save()

            # Retrieve all sold products
            sold_products = SoldProduct.objects.all()

            return redirect('dashboard-sales')  # Redirect to the sales page after making the sale
    else:
        form = SalesForm()
        # Retrieve all sold products
    sold_products = SoldProduct.objects.all()

    context = {
        'form': form,
        'sold_products': sold_products, 
    }
    return render(request, 'dashboard/sales.html', context)

@receiver(post_save, sender=Product)
def update_auto_order(sender, instance, **kwargs):
    # Check if the quantity has been updated
    if instance.quantity >= 50:  # Assuming the low stock threshold is 50
        # Check if there is an AutoOrder associated with the Product
        auto_order = AutoOrder.objects.filter(product=instance).first()
        if auto_order:
            # Delete the AutoOrder
            auto_order.delete()

def cancel_order(request, pk):
    # Get the order instance by its primary key
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.delete()
        return redirect('dashboard-cancel-order')
    return render(request, 'dashboard/cancel_order.html')
    
    # Redirect to a success page or another appropriate page
    return redirect('dashboard-staff-index')


def sales_analysis(request):
    # Retrieve sales data
    sales = SoldProduct.objects.all()  # Assuming SoldProduct is the model containing sales data
    
    # Prepare data for the graph (assuming SoldProduct model has 'date_sold' and 'total_price' fields)
    sales_data = [{'date': sale.date_sold, 'total_price': sale.total_price} for sale in sales]
    
    # Logic to identify products not sold frequently (e.g., products sold less than 5 times in the past month)
    month_ago = datetime.date.today() - datetime.timedelta(days=30)
    infrequent_products = Product.objects.filter(soldproduct__date_sold__gte=month_ago).annotate(num_sales=models.Count('soldproduct__id')).filter(num_sales__lt=5)

    context = {
        'sales_data': sales_data,
        'infrequent_products': infrequent_products
    }
    
    return render(request, 'dashboard/sales_analysis.html', context)

@login_required
def demand_forecast_view(request):
    # Retrieve past sales data
    sales = SoldProduct.objects.all()

    # Prepare sales data in the format required by the demand_forecast function
    sales_data = [(sale.product.name, sale.quantity_sold) for sale in sales]

    # Perform demand forecasting
    top_products_forecast = demand_forecast(sales_data)

    context = {
        'top_products_forecast': top_products_forecast
    }

    return render(request, 'dashboard/demand_forecast.html', context)


def demand_forecast(request):
    # Retrieve past sales data from SoldProduct objects
    sales = SoldProduct.objects.all()

    # Prepare sales data in the format required by the demand_forecast function
    sales_data = [(sale.product.name, sale.quantity_sold) for sale in sales]

    # Step 1: Analyze past sales data
    product_sales = defaultdict(int)
    for product, quantity_sold in sales_data:
        product_sales[product] += quantity_sold
    
    # Step 2: Determine the most purchased products
    top_products = Counter(product_sales).most_common(5)  # Adjust the number of products as needed
    
    # Step 3: Forecast demand for future periods (you can implement more sophisticated forecasting techniques here)
    forecasted_demand = {product: quantity_sold * 2 for product, quantity_sold in top_products}
    
    # Convert forecasted demand to a list of tuples for easier iteration in the template
    top_products_forecast = [(product, demand) for product, demand in forecasted_demand.items()]

    context = {
        'top_products_forecast': top_products_forecast
    }
    return render(request, 'dashboard/demand_forecast.html', context)

@login_required
def generate_pdf_report(request):
    

    auto_orders = AutoOrder.objects.all()

    # Get the current date and time
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Set the locale to use the Kenyan locale
    locale.setlocale(locale.LC_ALL, 'en_KE.UTF-8')

    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Sales_report.pdf"'

    # Create a canvas
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Draw text - Sales Report
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Sales Report", styles['Heading1']))
    elements.append(Spacer(1, 12))

    # Draw text - Report generated on current_datetime
    elements.append(Paragraph(f"Report generated on: {current_datetime}", styles['Normal']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Auto Orders Report", getSampleStyleSheet()['Title']))
    elements.append(Spacer(1, 12))

    # Get sales data for the past month
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=30)
    sales_data = SoldProduct.objects.filter(date_sold__range=[start_date, end_date]).values('date_sold', 'quantity_sold')

    # Extract dates and quantities for the sales graph
    dates = [sale['date_sold'] for sale in sales_data]
    quantities = [sale['quantity_sold'] for sale in sales_data]

    # Create a Matplotlib figure for the sales graph
    plt.figure(figsize=(8, 4))
    plt.plot(dates, quantities)
    plt.title('Sales in the Past Month')
    plt.xlabel('Date')
    plt.ylabel('Quantity Sold')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the Matplotlib figure to a BytesIO buffer
    plt.savefig(buffer, format='png')
    plt.close()

    # Move to the beginning of the buffer
    buffer.seek(0)

    image_data = buffer.getvalue()

    elements.append(Paragraph("Sales Graph for the Past Month:", styles['Heading2']))
    elements.append(Spacer(1, 12))
    image = Image(io.BytesIO(image_data), width=400, height=200)
    elements.append(image)
    elements.append(Spacer(1, 12))

    # Get most sold items (for example, items sold more than 10 times)
    most_sold_items = SoldProduct.objects.values('product__name').annotate(total_sold=Sum('quantity_sold')).filter(total_sold__gt=10)

    # Create a list to hold table data for most sold items
    data = [["Product Name", "Units Sold", "Total Price (KSH)", "Available Stock", "Anticipated Depletion Date"]]

    # Populate the table data for most sold items
    for item in most_sold_items:
        product_name = item['product__name']
        total_sold = item['total_sold']
        
        # Calculate total price for the sold item
        total_price = SoldProduct.objects.filter(product__name=product_name).aggregate(total_price=Sum(F('quantity_sold') * F('price_per_unit')))['total_price']

        # Get available stock of the product
        available_stock = Product.objects.filter(name=product_name).values_list('quantity', flat=True).first()
        
        # Calculate the average sales per day
        average_sales_per_day = SoldProduct.objects.filter(product__name=product_name).annotate(
            days_since_sale=ExpressionWrapper(timezone.now() - F('date_sold'), output_field=FloatField())
        ).aggregate(average_sales=Sum('quantity_sold') / Sum('days_since_sale'))['average_sales']

        # Calculate the anticipated depletion date
        if average_sales_per_day:
            days_until_depletion = available_stock / average_sales_per_day
            anticipated_depletion_date = datetime.now() + timedelta(days=days_until_depletion)
        else:
            anticipated_depletion_date = "N/A"

        # Format total price in KSH with thousand separator
        formatted_total_price = locale.format_string("%d", total_price, grouping=True)

        # Add row to the table data for most sold items
        data.append([product_name, total_sold, formatted_total_price, available_stock, anticipated_depletion_date])

    # Create table for most sold items
    table_style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                              ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                              ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                              ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                              ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                              ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                              ('GRID', (0, 0), (-1, -1), 1, colors.black)])

    t = Table(data)
    t.setStyle(table_style)
    elements.append(Paragraph("Most Sold Items:", styles['Heading2']))
    elements.append(t)
    elements.append(Spacer(1, 12))

    # Draw delivery information
    elements.append(Paragraph("Delivery Information:", styles['Heading2']))
    elements.append(Spacer(1, 12))

    # Get products that were previously out of stock and now have a higher threshold
    newly_delivered_products = Product.objects.filter(quantity__gt=0, low_stock_threshold=50)

    # Create a list to hold table data for delivery information
    delivery_data = [["Product Name", "Quantity Delivered", "Threshold Reached"]]

    # Populate the table data for delivery information
    for product in newly_delivered_products:
        # Calculate the quantity delivered
        quantity_delivered = product.quantity - product.low_stock_threshold
        # Add row to the table data for delivery information
        delivery_data.append([product.name, quantity_delivered, product.quantity])

    # Create table for delivery information
    delivery_table_style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                                       ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                       ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                       ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                       ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                       ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                       ('GRID', (0, 0), (-1, -1), 1, colors.black)])

    delivery_table = Table(delivery_data)
    delivery_table.setStyle(delivery_table_style)
    elements.append(delivery_table)
    elements.append(Spacer(1, 12))

     # Add table header for auto orders
    data = [["Product", "Order Quantity", "Date"]]
    for order in auto_orders:
        data.append([order.product.name, order.order_quantity, order.date])

        # Create table for auto orders
    table_style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                              ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                              ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                              ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                              ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                              ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                              ('GRID', (0, 0), (-1, -1), 1, colors.black)])

    t = Table(data)
    t.setStyle(table_style)
    elements.append(Paragraph("Auto Orders:", getSampleStyleSheet()['Heading2']))
    elements.append(t)
    elements.append(Spacer(1, 12))

    # Build PDF document
    doc.build(elements)

    # Get PDF content from buffer and return as response
    pdf_content = buffer.getvalue()
    buffer.close()
    response.write(pdf_content)

    return response