from django.db import transaction
from rest_framework import serializers
from accounts.serializers import UserSerializer
from products.models import ProductBatch
from .models import Order, OrderItem


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
        fields = ['id', 'buyer', 'total_amount', 'status', 'address', 'payment_proof', 'items', 'created_at']
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
                if batch.product.wholesale_price and quantity >= batch.product.wholesale_min_quantity:
                    price = batch.product.wholesale_price
                OrderItem.objects.create(order=order, product_batch=batch, quantity=quantity, price=price)
                batch.quantity -= quantity
                batch.save(update_fields=['quantity'])
                total += price * quantity
            order.total_amount = total
            order.save(update_fields=['total_amount'])
        return order

    def update(self, instance, validated_data):
        raise serializers.ValidationError('订单创建后不可通过通用接口修改')
