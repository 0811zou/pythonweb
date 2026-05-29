from django.db import models
from django.contrib.auth.models import User
import secrets
from datetime import datetime


def generate_batch_code():
    """生成可读批次编号：B-20260529-A3F2X7K9"""
    date_part = datetime.now().strftime('%Y%m%d')
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
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    batch_code = models.CharField(max_length=100, unique=True, default=generate_batch_code)
    harvest_date = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    images = models.JSONField(default=list, blank=True)
    trace_info = models.JSONField(default=dict, blank=True)
    qc_report = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} #{self.batch_code}"

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

class Review(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class LogisticsEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=200, blank=True)
    note = models.TextField(blank=True)
