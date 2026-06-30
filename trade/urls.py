from django.urls import path
from . import views

app_name = 'trade'

urlpatterns = [
    path('order/create/', views.order_create_view, name='order_create'),
    path('orders/', views.consumer_orders_view, name='consumer_orders'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:pk>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:pk>/', views.cart_remove, name='cart_remove'),
    path('cart/checkout/', views.cart_checkout, name='cart_checkout'),
    path('payment/<int:order_id>/', views.payment_view, name='payment'),
    path('cart/batch-checkout/', views.cart_batch_checkout, name='cart_batch_checkout'),
    path('favorites/', views.favorites_view, name='favorites'),
    path('favorite/toggle/<int:pk>/', views.favorite_toggle, name='favorite_toggle'),
    path('api/orders/<int:order_id>/review/', views.order_review_api, name='order_review_api'),
    path('farmer/orders/', views.farmer_orders_view, name='farmer_orders'),
    path('farmer/orders/<int:order_id>/tracking/', views.farmer_set_tracking, name='farmer_set_tracking'),
]
