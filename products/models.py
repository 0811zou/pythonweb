import hashlib
import json
import secrets
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


def generate_batch_code():
    """生成可读批次编号：B-20260529-A3F2X7K9"""
    date_part = timezone.now().strftime('%Y%m%d')
    rand_part = secrets.token_hex(4).upper()
    return f'B-{date_part}-{rand_part}'


class Product(models.Model):
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending', '待审核'),
        ('approved', '已上架'),
        ('rejected', '未通过'),
    ]
    farmer = models.ForeignKey('accounts.FarmerProfile', on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True)
    variety = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, default='kg')
    image = models.ImageField(upload_to='products/', blank=True, null=True, help_text='产品图片')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    review_note = models.TextField(blank=True, help_text='审核意见')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_product'

    def __str__(self):
        return self.name


class ProductBatch(models.Model):
    BATCH_STATUS = [
        ('draft', '草稿'),
        ('pending', '待质检'),
        ('approved', '已通过'),
        ('rejected', '未通过'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    batch_code = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name='批次编码')
    harvest_date = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    images = models.JSONField(default=list, blank=True)
    trace_info = models.JSONField(default=dict, blank=True)
    qc_report = models.CharField(max_length=500, blank=True, verbose_name='质检报告')
    qc_images = models.JSONField(default=list, blank=True, verbose_name='质检图片')
    status = models.CharField(max_length=20, choices=BATCH_STATUS, default='draft', verbose_name='批次状态')
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True, help_text='溯源二维码')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_productbatch'

    def __str__(self):
        code = self.batch_code or f'待审核#{self.pk}'
        return f"{self.product.name} #{code}"

    @property
    def trace_url(self):
        if not self.batch_code:
            return ''
        base_url = getattr(settings, 'SITE_BASE_URL', '').rstrip('/')
        path = f"/trace/{self.batch_code}/"
        return f"{base_url}{path}" if base_url else path

    def save(self, *args, **kwargs):
        # 状态变为已通过且无批次编码时自动生成
        if self.status == 'approved' and not self.batch_code:
            self.batch_code = generate_batch_code()
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.status == 'approved':
            self.ensure_qr_code()
        elif self.status == 'approved' and not self.qr_code:
            self.ensure_qr_code()

    def ensure_qr_code(self):
        if self.qr_code or not self.batch_code:
            return
        import qrcode

        img = qrcode.make(self.trace_url)
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f"{self.batch_code}.png"
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
        super().save(update_fields=['qr_code'])


class Review(models.Model):
    order = models.ForeignKey('trade.Order', on_delete=models.CASCADE)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    farmer = models.ForeignKey('accounts.FarmerProfile', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.PositiveSmallIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_review'
