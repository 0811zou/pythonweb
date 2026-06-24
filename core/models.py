import hashlib
import json
import secrets
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def generate_batch_code():
    """生成可读批次编号：B-20260529-A3F2X7K9"""
    date_part = timezone.now().strftime('%Y%m%d')
    rand_part = secrets.token_hex(4).upper()
    return f'B-{date_part}-{rand_part}'

class Cooperative(models.Model):
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=200, blank=True, null=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class FarmerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cooperative = models.ForeignKey(Cooperative, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    address = models.CharField(max_length=300, blank=True)
    location_lat = models.FloatField(null=True, blank=True)
    location_lng = models.FloatField(null=True, blank=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FarmerProfile({self.user.username})"

class Product(models.Model):
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending', '待审核'),
        ('approved', '已上架'),
        ('rejected', '未通过'),
    ]
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='products')
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
    batch_code = models.CharField(max_length=100, unique=True, default=generate_batch_code)
    harvest_date = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    images = models.JSONField(default=list, blank=True)
    trace_info = models.JSONField(default=dict, blank=True)
    qc_report = models.CharField(max_length=500, blank=True, verbose_name='质检报告')
    qc_images = models.JSONField(default=list, blank=True, verbose_name='质检图片')
    status = models.CharField(max_length=20, choices=BATCH_STATUS, default='draft', verbose_name='批次状态')
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True, help_text='溯源二维码')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} #{self.batch_code}"

    @property
    def trace_url(self):
        base_url = getattr(settings, 'SITE_BASE_URL', '').rstrip('/')
        path = f"/trace/{self.batch_code}/"
        return f"{base_url}{path}" if base_url else path

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.ensure_qr_code()

    def ensure_qr_code(self):
        if self.qr_code:
            return
        import qrcode

        img = qrcode.make(self.trace_url)
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f"{self.batch_code}.png"
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
        super().save(update_fields=['qr_code'])


class TraceEvent(models.Model):
    EVENT_TYPES = [
        ('planting', '种植'),
        ('fertilizing', '施肥'),
        ('pesticide', '农药'),
        ('harvest', '采收'),
        ('qc', '质检'),
        ('storage', '入库'),
        ('shipping', '发货'),
        ('other', '其他'),
    ]
    batch = models.ForeignKey(ProductBatch, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES, default='other')
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=200, blank=True)
    previous_hash = models.CharField(max_length=64, blank=True)
    data_hash = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['occurred_at', 'created_at']

    def __str__(self):
        return f"{self.batch.batch_code} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.previous_hash:
            previous = (
                TraceEvent.objects
                .filter(batch=self.batch)
                .exclude(pk=self.pk)
                .order_by('-created_at', '-id')
                .first()
            )
            self.previous_hash = previous.data_hash if previous else ''
        self.data_hash = self.calculate_hash()
        super().save(*args, **kwargs)

    def calculate_hash(self):
        payload = {
            'batch_code': self.batch.batch_code,
            'event_type': self.event_type,
            'title': self.title,
            'description': self.description,
            'operator_id': self.operator_id,
            'occurred_at': self.occurred_at.isoformat() if self.occurred_at else '',
            'location': self.location,
            'previous_hash': self.previous_hash,
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending','pending'),
        ('paid_offline','paid_offline'),
        ('confirmed','confirmed'),
        ('shipped','shipped'),
        ('delivered','delivered'),
        ('cancelled','cancelled'),
    ]
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    address = models.CharField(max_length=300)
    payment_proof = models.CharField(max_length=500, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True, verbose_name='快递单号')
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_batch = models.ForeignKey(ProductBatch, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

class SubsidyApplication(models.Model):
    STATUS = [('submitted','submitted'),('approved','approved'),('rejected','rejected')]
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='subsidies')
    type = models.CharField(max_length=100)
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2)
    documents = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='submitted')
    admin_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

class Training(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    resource_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Announcement(models.Model):
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    is_active = models.BooleanField(default=True, verbose_name='是否显示')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Review(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.PositiveSmallIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class LogisticsEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=200, blank=True)
    note = models.TextField(blank=True)
