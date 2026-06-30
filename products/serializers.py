from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import Product, ProductBatch, Review
from traceability.models import TraceEvent


class ProductBatchListSerializer(serializers.ModelSerializer):
    """用于在产品详情中嵌套显示批次"""
    class Meta:
        model = ProductBatch
        fields = ['id', 'batch_code', 'harvest_date', 'quantity', 'images', 'trace_info', 'qc_report', 'qr_code', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    batches = ProductBatchListSerializer(many=True, read_only=True)
    farmer_address = serializers.SerializerMethodField()

    def get_farmer_address(self, obj):
        if obj.farmer and obj.farmer.address:
            return obj.farmer.address
        return ''

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['farmer', 'status', 'review_note', 'created_at']


class TraceEventSerializer(serializers.ModelSerializer):
    operator = UserSerializer(read_only=True)

    class Meta:
        model = TraceEvent
        fields = [
            'id', 'batch', 'event_type', 'title', 'description', 'operator',
            'occurred_at', 'location', 'previous_hash', 'data_hash', 'created_at',
        ]
        read_only_fields = ['operator', 'previous_hash', 'data_hash', 'created_at']


class ProductBatchSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)
    events = TraceEventSerializer(many=True, read_only=True)

    class Meta:
        model = ProductBatch
        fields = ['id', 'product', 'product_id', 'batch_code', 'harvest_date', 'quantity', 'images', 'trace_info', 'qc_report', 'qr_code', 'events', 'created_at']
        read_only_fields = ['batch_code', 'qr_code', 'created_at']


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['buyer', 'farmer', 'created_at']


class ReviewDetailSerializer(serializers.ModelSerializer):
    """只读评价序列化器 — 含用户名"""
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)
    product_name = serializers.SerializerMethodField()

    def get_product_name(self, obj):
        first_item = obj.order.items.first()
        if first_item and first_item.product_batch:
            return first_item.product_batch.product.name
        return ''

    class Meta:
        model = Review
        fields = ['id', 'order', 'buyer_name', 'product_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at', 'buyer_name', 'product_name']
