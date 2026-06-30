from django.contrib import admin
from .models import FarmingGuide


@admin.register(FarmingGuide)
class FarmingGuideAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'crop_type', 'is_published', 'created_at')
    list_filter = ('category', 'crop_type', 'is_published')
    search_fields = ('title', 'content')
