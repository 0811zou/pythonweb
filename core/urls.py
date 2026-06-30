from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('seasonal/', views.seasonal_products_page, name='seasonal'),
    path('apply/', views.apply_join, name='apply_join'),
    path('training/', views.training_list, name='training_list'),
    path('training/<int:pk>/', views.training_detail, name='training_detail'),
]
