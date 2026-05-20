from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "timezone", "preferred_ui_language", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "password", "name", "timezone", "preferred_ui_language"]
        read_only_fields = ["id"]

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
