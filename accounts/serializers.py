from rest_framework import serializers
from django.contrib.auth.models import User
from .models import FarmerProfile, SubsidyApplication


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class FarmerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = FarmerProfile
        fields = '__all__'
        read_only_fields = ['user', 'verified', 'created_at']


class SubsidyApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubsidyApplication
        fields = '__all__'
        read_only_fields = ['farmer', 'status', 'admin_notes', 'submitted_at', 'decided_at']
