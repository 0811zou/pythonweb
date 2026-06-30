"""Aggregate DRF router URLs from all apps."""
from rest_framework import routers
from products.views import ProductViewSet, ProductBatchViewSet
from trade.views import OrderViewSet
from core.views import SubsidyViewSet, TrainingViewSet

router = routers.DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'batches', ProductBatchViewSet)
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'subsidies', SubsidyViewSet)
router.register(r'trainings', TrainingViewSet)

urlpatterns = router.urls
