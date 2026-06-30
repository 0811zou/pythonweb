from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('manage/', views.admin_dashboard, name='dashboard'),
    path('manage/products/', views.admin_products, name='products'),
    path('manage/products/<int:pk>/<str:action>/', views.admin_product_review, name='product_review'),
    path('manage/users/', views.admin_users, name='users'),
    path('manage/batches/', views.admin_batches, name='batches'),
    path('manage/batches/<int:pk>/<str:action>/', views.admin_batch_review, name='batch_review'),
    path('manage/export/orders/', views.export_orders_csv, name='export_orders'),
    path('manage/export/products/', views.export_products_csv, name='export_products'),
    path('manage/applications/', views.admin_applications, name='applications'),
]
