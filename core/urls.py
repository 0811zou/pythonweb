from django.urls import path, include
from rest_framework import routers
from .views import (
    ProductViewSet, ProductBatchViewSet, OrderViewSet,
    SubsidyViewSet, TrainingViewSet,
    trace_view, home_view, product_list_view, product_detail_view,
    trace_query_view, login_view, logout_view, register_view,
)

router = routers.DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'batches', ProductBatchViewSet)
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'subsidies', SubsidyViewSet)
router.register(r'trainings', TrainingViewSet)

urlpatterns = [
    path('', home_view, name='home'),
    path('products/', product_list_view, name='product_list'),
    path('products/<int:pk>/', product_detail_view, name='product_detail'),
    path('trace/', trace_query_view, name='trace_query'),
    path('trace/<str:batch_code>/', trace_view, name='trace'),
    path('accounts/login/', login_view, name='login'),
    path('accounts/logout/', logout_view, name='logout'),
    path('accounts/register/', register_view, name='register'),
    path('api/', include(router.urls)),
]
