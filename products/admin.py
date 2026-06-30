from django.contrib import admin
from .models import Product, ProductBatch, Review


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'farmer', 'price', 'unit')


@admin.register(ProductBatch)
class ProductBatchAdmin(admin.ModelAdmin):
    list_display = ('product', 'batch_code', 'harvest_date', 'quantity', 'qr_code')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('order', 'buyer', 'farmer', 'rating')
