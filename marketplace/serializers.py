from rest_framework import serializers
from .models import SupplyDemandPost


class SupplyDemandPostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = SupplyDemandPost
        fields = '__all__'
        read_only_fields = ['author', 'status', 'created_at']
