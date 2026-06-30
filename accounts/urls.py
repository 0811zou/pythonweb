from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/register/', views.register_view, name='register'),
    path('farmer/<int:farmer_id>/shop/', views.farmer_shop_view, name='farmer_shop'),
    path('farmer/shop/settings/', views.farmer_shop_settings, name='farmer_shop_settings'),
    path('farmer/subsidies/', views.subsidy_list, name='subsidy_list'),
    path('farmer/subsidies/create/', views.subsidy_create, name='subsidy_create'),
    path('farmer/payment-methods/', views.farmer_payment_methods, name='farmer_payment_methods'),
]
