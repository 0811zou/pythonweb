from django.urls import path, include
from rest_framework import routers
from .views import ProductViewSet, ProductBatchViewSet, OrderViewSet, SubsidyViewSet, TrainingViewSet, trace_view

router = routers.DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'batches', ProductBatchViewSet)
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'subsidies', SubsidyViewSet)
router.register(r'trainings', TrainingViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('trace/<str:batch_code>/', trace_view, name='trace'),
]
