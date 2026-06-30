from rest_framework import serializers
from .models import FarmingGuide


class FarmingGuideSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = FarmingGuide
        fields = '__all__'
        read_only_fields = ['author', 'created_at']
