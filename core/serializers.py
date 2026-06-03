from rest_framework import serializers
from django.contrib.auth.models import User
from .models import FarmerProfile, Cooperative, Product, ProductBatch, Order, OrderItem, SubsidyApplication, Training, Review

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','email','first_name','last_name']

class FarmerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = FarmerProfile
        fields = '__all__'

class ProductBatchListSerializer(serializers.ModelSerializer):
    """用于在产品详情中嵌套显示批次"""
    class Meta:
        model = ProductBatch
        fields = ['id', 'batch_code', 'harvest_date', 'quantity', 'images', 'trace_info', 'qc_report', 'created_at']

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

class ProductBatchSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)
    class Meta:
        model = ProductBatch
        fields = ['id','product','product_id','batch_code','harvest_date','quantity','images','trace_info','qc_report','created_at']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ['order']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    class Meta:
        model = Order
        fields = ['id','buyer','total_amount','status','address','payment_proof','items','created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        total = 0
        for it in items_data:
            OrderItem.objects.create(order=order, **it)
            total += it['price'] * it['quantity']
        order.total_amount = total
        order.save()
        return order

class SubsidyApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubsidyApplication
        fields = '__all__'

class TrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Training
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'


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
