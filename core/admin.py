from django.contrib import admin
from .models import Announcement, Training


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active',)


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
