from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import ApiToken, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "timezone", "preferred_ui_language", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class UpdateMeSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        read_only_fields = ["id", "email", "date_joined"]


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


class ApiTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiToken
        fields = ["id", "name", "last_used_at", "created_at"]
        read_only_fields = fields


class ApiTokenCreateSerializer(serializers.ModelSerializer):
    token = serializers.CharField(read_only=True)

    class Meta:
        model = ApiToken
        fields = ["id", "name", "token", "created_at"]
        read_only_fields = ["id", "token", "created_at"]
