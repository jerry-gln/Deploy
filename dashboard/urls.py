from django.urls import path 
from . import views


urlpatterns = [
    path('dashboard/', views.index, name='dashboard-index'),
    path('staff/', views.staff, name='dashboard-staff'),
    path('staff/index', views.staff_index, name='dashboard-staff-index'),  # Corrected URL pattern
    path('staff/detail/<int:pk>/', views.staff_detail, name='dashboard-staff-detail'),
    path('product/', views.product, name='dashboard-product'),
    path('product/delete/<int:pk>/', views.product_delete, name='dashboard-product-delete'),
    path('product/update/<int:pk>/', views.product_update, name='dashboard-product-update'),
    path('order/', views.order, name='dashboard-order'),
    path('suppliers/', views.supplier, name='dashboard-suppliers'),
    path('suppliers/add/', views.add_supplier, name='dashboard-add-supplier'),  # Add a new supplier
    path('suppliers/<int:pk>/edit/', views.edit_supplier, name='dashboard-edit-supplier'),  # Edit a supplier
    path('suppliers/<int:pk>/delete/', views.delete_supplier, name='dashboard-delete-supplier'),  # Delete a supplier
    path('search/', views.search, name='dashboard-search-results'), 
    path('sales/', views.sales, name='dashboard-sales'), 
    path('order/<int:pk>/cancel/', views.cancel_order, name='dashboard-cancel-order'),
    path('sales/analysis/', views.sales_analysis, name='dashboard-sales-analysis'),
    path('demand-forecast/', views.demand_forecast, name='demand-forecast'),  # Updated path for demand forecast
    path('pdf-report/', views.generate_pdf_report, name='pdf-report'),

]
