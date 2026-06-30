from django.urls import path
from . import views

app_name = 'traceability'

urlpatterns = [
    path('trace/', views.trace_query_view, name='trace_query'),
    path('trace/<str:batch_code>/', views.trace_view, name='trace'),
]
