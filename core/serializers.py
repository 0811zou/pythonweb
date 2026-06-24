from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from .models import FarmerProfile, Cooperative, Product, ProductBatch, Order, OrderItem, SubsidyApplication, Training, Review, TraceEvent

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','email','first_name','last_name']

class FarmerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = FarmerProfile
        fields = '__all__'
        read_only_fields = ['user', 'verified', 'created_at']

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
        fields = ['id','product','product_id','batch_code','harvest_date','quantity','images','trace_info','qc_report','qr_code','events','created_at']
        read_only_fields = ['batch_code', 'qr_code', 'created_at']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_batch', 'quantity', 'price']
        read_only_fields = ['price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    buyer = UserSerializer(read_only=True)
    class Meta:
        model = Order
        fields = ['id','buyer','total_amount','status','address','payment_proof','items','created_at']
        read_only_fields = ['buyer', 'total_amount', 'status', 'payment_proof', 'created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError('请先登录')
        if hasattr(request.user, 'farmerprofile'):
            raise serializers.ValidationError('农户账号不能下单')

        with transaction.atomic():
            order = Order.objects.create(buyer=request.user, **validated_data)
            total = 0
            for item in items_data:
                quantity = item.get('quantity') or 1
                if quantity <= 0:
                    raise serializers.ValidationError('数量必须大于0')
                batch = (
                    ProductBatch.objects
                    .select_for_update()
                    .select_related('product')
                    .get(pk=item['product_batch'].pk)
                )
                if batch.product.status != 'approved':
                    raise serializers.ValidationError(f'{batch.product.name} 未上架')
                if batch.quantity < quantity:
                    raise serializers.ValidationError(f'{batch.product.name} 库存不足')
                price = batch.product.price
                OrderItem.objects.create(order=order, product_batch=batch, quantity=quantity, price=price)
                batch.quantity -= quantity
                batch.save(update_fields=['quantity'])
                total += price * quantity
            order.total_amount = total
            order.save(update_fields=['total_amount'])
        return order

    def update(self, instance, validated_data):
        raise serializers.ValidationError('订单创建后不可通过通用接口修改')

class SubsidyApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubsidyApplication
        fields = '__all__'
        read_only_fields = ['farmer', 'status', 'admin_notes', 'submitted_at', 'decided_at']

class TrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Training
        fields = '__all__'
        read_only_fields = ['created_at']

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
