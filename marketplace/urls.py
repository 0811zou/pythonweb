from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('marketplace/', views.supply_demand_list, name='list'),
    path('marketplace/create/', views.supply_demand_create, name='create'),
    path('marketplace/<int:pk>/', views.supply_demand_detail, name='detail'),
]
