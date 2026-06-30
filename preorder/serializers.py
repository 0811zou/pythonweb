from rest_framework import serializers
from .models import PreOrderCampaign, PreOrder


class PreOrderCampaignSerializer(serializers.ModelSerializer):
    farmer_name = serializers.CharField(source='farmer.user.username', read_only=True)
    progress = serializers.IntegerField(read_only=True)
    remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = PreOrderCampaign
        fields = '__all__'
        read_only_fields = ['farmer', 'current_quantity', 'status', 'created_at']


class PreOrderSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)
    campaign_name = serializers.CharField(source='campaign.product_name', read_only=True)

    class Meta:
        model = PreOrder
        fields = '__all__'
        read_only_fields = ['buyer', 'total_amount', 'status', 'created_at']
