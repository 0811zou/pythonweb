from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Consumer-facing
    path('products/', views.product_list_view, name='list'),
    path('products/<int:pk>/', views.product_detail_view, name='detail'),
    path('products/<int:pk>/batches/', views.product_batches_view, name='batches'),
    # Farmer
    path('farmer/', views.farmer_dashboard, name='farmer_dashboard'),
    path('farmer/products/', views.farmer_product_list, name='farmer_product_list'),
    path('farmer/products/create/', views.farmer_product_create, name='farmer_product_create'),
    path('farmer/products/<int:pk>/edit/', views.farmer_product_edit, name='farmer_product_edit'),
    path('farmer/products/<int:pk>/delete/', views.farmer_product_delete, name='farmer_product_delete'),
    path('farmer/products/<int:pk>/submit/', views.farmer_product_submit, name='farmer_product_submit'),
    path('farmer/batches/', views.farmer_batch_list, name='farmer_batch_list'),
    path('farmer/batches/create/', views.farmer_batch_create, name='farmer_batch_create'),
    path('farmer/batches/<int:pk>/', views.farmer_batch_detail, name='farmer_batch_detail'),
    path('farmer/batches/<int:pk>/delete/', views.farmer_batch_delete, name='farmer_batch_delete'),
    path('farmer/batches/<int:pk>/qr/', views.download_qr, name='download_qr'),
    # API (must be before router in config/urls.py)
    path('api/products/<int:pk>/reviews/', views.product_reviews, name='product_reviews'),
    path('api/products/filter-options/', views.product_filter_options, name='product_filter_options'),
    path('api/products/seasonal/', views.seasonal_products_api, name='seasonal_api'),
    path('api/stats/dashboard/', views.dashboard_stats, name='dashboard_stats'),
    path('api/stats/province-products/', views.province_products, name='province_products'),
    # Map
    path('map/', views.province_map_view, name='province_map'),
    # Farmers directory
    path('farmers/', views.farmer_directory, name='farmer_directory'),
]
