from django.urls import path
from . import views

app_name = 'preorder'

urlpatterns = [
    path('preorder/', views.preorder_list, name='list'),
    path('preorder/<int:pk>/', views.preorder_detail, name='detail'),
    path('preorder/create/', views.preorder_create, name='create'),
]
