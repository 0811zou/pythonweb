from django.db import models

# ── Compatibility re-exports (models moved to dedicated apps) ──
# These allow existing imports to keep working during the transition.
# Remove after all views/serializers/admin are updated to import from new apps.
from accounts.models import FarmerProfile, SubsidyApplication, FarmerPaymentMethod
from products.models import Product, ProductBatch, Review, generate_batch_code
from traceability.models import TraceEvent
from trade.models import Order, OrderItem, Cart, CartItem, Favorite, LogisticsEvent
from marketplace.models import SupplyDemandPost
from knowledge.models import FarmingGuide
from preorder.models import PreOrderCampaign, PreOrder
from notifications.models import Notification

__all__ = [
    'FarmerProfile', 'SubsidyApplication', 'FarmerPaymentMethod',
    'Product', 'ProductBatch', 'Review', 'generate_batch_code',
    'TraceEvent',
    'Order', 'OrderItem', 'Cart', 'CartItem', 'Favorite', 'LogisticsEvent',
    'SupplyDemandPost',
    'FarmingGuide',
    'PreOrderCampaign', 'PreOrder',
    'Notification',
    'Training', 'Announcement',
]


class Training(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    resource_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_training'


class Announcement(models.Model):
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    is_active = models.BooleanField(default=True, verbose_name='是否显示')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_announcement'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class JoinApplication(models.Model):
    """平台入驻申请表"""
    APPLY_TYPE_CHOICES = [
        ('farmer', '农户入驻'),
    ]
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
    ]
    apply_type = models.CharField(max_length=20, choices=APPLY_TYPE_CHOICES, verbose_name='申请类型')
    name = models.CharField(max_length=200, verbose_name='姓名/合作社名称')
    phone = models.CharField(max_length=20, verbose_name='联系电话')
    region = models.CharField(max_length=200, verbose_name='所在地区')
    description = models.TextField(blank=True, verbose_name='简介（产品/规模/特色）')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='审核状态')
    reviewer_note = models.TextField(blank=True, verbose_name='审核备注')
    reviewed_by = models.ForeignKey(
        'auth.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_applications'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_joinapplication'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_apply_type_display()} - {self.name} ({self.get_status_display()})'
