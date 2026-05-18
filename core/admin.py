from django.contrib import admin
from .models import Cooperative, FarmerProfile, Product, ProductBatch, Order, OrderItem, SubsidyApplication, Training, Review, LogisticsEvent

@admin.register(Cooperative)
class CooperativeAdmin(admin.ModelAdmin):
    list_display = ('name','region','verified')

@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = ('user','cooperative','phone','verified')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name','farmer','price','unit')

@admin.register(ProductBatch)
class ProductBatchAdmin(admin.ModelAdmin):
    list_display = ('product','batch_code','harvest_date','quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','buyer','total_amount','status','created_at')

@admin.register(SubsidyApplication)
class SubsidyAdmin(admin.ModelAdmin):
    list_display = ('farmer','type','amount_requested','status','submitted_at')

@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ('title','created_at')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('order','buyer','farmer','rating')

@admin.register(LogisticsEvent)
class LogisticsAdmin(admin.ModelAdmin):
    list_display = ('order','status','timestamp')
