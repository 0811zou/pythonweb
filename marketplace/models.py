from django.conf import settings
from django.db import models


class SupplyDemandPost(models.Model):
    """供需对接帖子 — 农户发布供应，买家发布需求"""
    POST_TYPE_CHOICES = [
        ('supply', '供应'),
        ('demand', '需求'),
    ]
    STATUS_CHOICES = [
        ('active', '进行中'),
        ('closed', '已关闭'),
    ]
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='supply_demand_posts')
    post_type = models.CharField(max_length=20, choices=POST_TYPE_CHOICES, verbose_name='帖子类型')
    product_name = models.CharField(max_length=200, verbose_name='产品名称')
    category = models.CharField(max_length=100, verbose_name='产品分类', help_text='例如：水果、蔬菜、粮油、茶叶等')
    quantity = models.PositiveIntegerField(verbose_name='数量')
    unit = models.CharField(max_length=50, default='kg', verbose_name='单位')
    price_range = models.CharField(max_length=100, blank=True, verbose_name='价格区间', help_text='例如：10-15元/kg')
    region = models.CharField(max_length=200, verbose_name='所在地区')
    description = models.TextField(verbose_name='详细描述')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_supplydemandpost'
        ordering = ['-created_at']
        verbose_name = '供需对接帖子'
        verbose_name_plural = '供需对接帖子'

    def __str__(self):
        return f"[{'供' if self.post_type == 'supply' else '需'}] {self.product_name} ({self.author.username})"
