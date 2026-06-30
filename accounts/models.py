from django.conf import settings
from django.db import models


class FarmerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=32, blank=True)
    address = models.CharField(max_length=300, blank=True)
    location_lat = models.FloatField(null=True, blank=True)
    location_lng = models.FloatField(null=True, blank=True)
    verified = models.BooleanField(default=False)
    shop_description = models.TextField(blank=True, verbose_name='店铺简介')
    shop_avatar = models.ImageField(upload_to='shop_avatars/', blank=True, null=True)
    farm_story = models.TextField(blank=True, verbose_name='农场故事', help_text='介绍你的农场历史、种植理念等')
    farm_photos = models.JSONField(default=list, blank=True, verbose_name='农场照片', help_text='农场照片URL列表')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_farmerprofile'

    def __str__(self):
        return f"FarmerProfile({self.user.username})"


class FarmerPaymentMethod(models.Model):
    """农户收款方式"""
    METHOD_CHOICES = [
        ('wechat', '微信支付'),
        ('alipay', '支付宝'),
        ('bank', '银行卡转账'),
    ]
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=20, choices=METHOD_CHOICES, verbose_name='收款方式')
    account_name = models.CharField(max_length=100, verbose_name='收款人/户名')
    account_number = models.CharField(max_length=100, verbose_name='账号')
    qr_code = models.ImageField(upload_to='payment_qr/', blank=True, null=True, verbose_name='收款码图片')
    is_active = models.BooleanField(default=True, verbose_name='启用')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_farmerpaymentmethod'
        ordering = ['-is_active', '-created_at']

    def __str__(self):
        return f'{self.get_method_type_display()} - {self.account_name}'


class SubsidyApplication(models.Model):
    STATUS = [('submitted', 'submitted'), ('approved', 'approved'), ('rejected', 'rejected')]
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='subsidies')
    type = models.CharField(max_length=100)
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2)
    documents = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='submitted')
    admin_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'core_subsidyapplication'
