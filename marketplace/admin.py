from django.contrib import admin
from .models import SupplyDemandPost


@admin.register(SupplyDemandPost)
class SupplyDemandPostAdmin(admin.ModelAdmin):
    list_display = ('post_type', 'product_name', 'author', 'category', 'status', 'created_at')
    list_filter = ('post_type', 'status', 'category')
    search_fields = ('product_name', 'author__username', 'region')
