from django.contrib import admin
from .models import Order, Cart, Favorite, LogisticsEvent


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'total_amount', 'status', 'created_at')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')


@admin.register(LogisticsEvent)
class LogisticsAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'timestamp')
