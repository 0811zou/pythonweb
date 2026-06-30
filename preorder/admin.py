from django.contrib import admin
from .models import PreOrderCampaign, PreOrder


@admin.register(PreOrderCampaign)
class PreOrderCampaignAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'farmer', 'discount_price', 'current_quantity', 'target_quantity', 'status', 'end_date')
    list_filter = ('status',)
    search_fields = ('product_name', 'farmer__user__username')


@admin.register(PreOrder)
class PreOrderAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'buyer', 'quantity', 'total_amount', 'status', 'created_at')
    list_filter = ('status',)
