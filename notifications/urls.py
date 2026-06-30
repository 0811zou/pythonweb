from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('notifications/', views.notifications_view, name='list'),
    path('notifications/unread-count/', views.notifications_unread_count, name='unread_count'),
    path('notifications/mark-read/<int:pk>/', views.notifications_mark_read, name='mark_read'),
    path('notifications/delete/<int:pk>/', views.notifications_delete, name='delete'),
]
