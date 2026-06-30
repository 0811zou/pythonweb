from django.conf import settings
from django.db import models
from django.utils import timezone


class PreOrderCampaign(models.Model):
    """预售/认养活动 — 农户提前发布，消费者预订"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('active', '进行中'),
        ('ended', '已结束'),
        ('cancelled', '已取消'),
    ]
    farmer = models.ForeignKey('accounts.FarmerProfile', on_delete=models.CASCADE, related_name='preorder_campaigns')
    product_name = models.CharField(max_length=200, verbose_name='产品名称')
    description = models.TextField(verbose_name='活动描述')
    cover_image = models.CharField(max_length=500, blank=True, verbose_name='封面图片URL')
    target_quantity = models.PositiveIntegerField(verbose_name='目标数量')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='原价')
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='预售价')
    unit = models.CharField(max_length=50, default='kg', verbose_name='单位')
    start_date = models.DateTimeField(default=timezone.now, verbose_name='开始时间')
    end_date = models.DateTimeField(verbose_name='结束时间')
    harvest_date = models.DateField(null=True, blank=True, verbose_name='预计采收日期')
    current_quantity = models.PositiveIntegerField(default=0, verbose_name='已预订数量')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_preordercampaign'
        ordering = ['-created_at']
        verbose_name = '预售活动'
        verbose_name_plural = '预售活动'

    def __str__(self):
        return f"{self.product_name} 预售 ({self.farmer.user.username})"

    @property
    def progress(self):
        if self.target_quantity == 0:
            return 0
        return min(100, int(self.current_quantity / self.target_quantity * 100))

    @property
    def remaining(self):
        return max(0, self.target_quantity - self.current_quantity)


class PreOrder(models.Model):
    """预售订单 — 消费者的预订记录"""
    STATUS_CHOICES = [
        ('pending', '待确认'),
        ('confirmed', '已确认'),
        ('cancelled', '已取消'),
    ]
    campaign = models.ForeignKey(PreOrderCampaign, on_delete=models.CASCADE, related_name='preorders')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preorders')
    quantity = models.PositiveIntegerField(default=1, verbose_name='预订数量')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='总金额')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    address = models.CharField(max_length=300, verbose_name='收货地址')
    note = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_preorder'
        ordering = ['-created_at']
        unique_together = ('campaign', 'buyer')
        verbose_name = '预售订单'
        verbose_name_plural = '预售订单'

    def __str__(self):
        return f"{self.buyer.username} 预订 {self.campaign.product_name} x{self.quantity}"
