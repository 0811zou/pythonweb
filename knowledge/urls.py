from django.urls import path
from . import views

app_name = 'knowledge'

urlpatterns = [
    path('guides/', views.guide_list, name='list'),
    path('guides/<int:pk>/', views.guide_detail, name='detail'),
]
