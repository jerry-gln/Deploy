from django.contrib import admin
from .models import Product, Order, AutoOrder
from .models import Sales, Supplier

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity')
    list_filter = ('category',)

class AutoOrderAdmin(admin.ModelAdmin):
    list_display = ('product', 'order_quantity', 'date', 'is_auto_generated')
    

# Register your models here.
admin.site.register(Product, ProductAdmin)
admin.site.register(Order)
admin.site.register(AutoOrder, AutoOrderAdmin)
admin.site.register(Sales)
admin.site.register(Supplier)
