from django.contrib import admin
from .models import FarmerProfile, SubsidyApplication


@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'verified')


@admin.register(SubsidyApplication)
class SubsidyAdmin(admin.ModelAdmin):
    list_display = ('farmer', 'type', 'amount_requested', 'status', 'submitted_at')
