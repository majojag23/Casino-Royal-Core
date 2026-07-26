from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, PasswordReset
import secrets
from django.utils import timezone
from datetime import timedelta


class UserSerializer(serializers.ModelSerializer):
    """Serializador para usuarios"""

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'document_type', 'document_number', 'phone', 'date_of_birth',
            'address', 'city', 'state', 'postal_code', 'country',
            'balance', 'bonus_balance', 'bonus_wagering_required', 'bonus_wagering_progress',
            'welcome_bonus_claimed', 'status', 'email_verified', 'document_verified', 'kyc_verified',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'balance', 'bonus_balance', 'bonus_wagering_required',
                             'bonus_wagering_progress', 'welcome_bonus_claimed', 'created_at', 'updated_at']


class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializador para registro de usuarios"""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'date_of_birth'
        ]

    def validate_email(self, value):
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta registrada con este correo")
        return value

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Serializador para login"""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Usuario o contraseña inválidos")
        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializador para perfil de usuario"""

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'document_type', 'document_number',
            'address', 'city', 'state', 'postal_code', 'country',
            'balance', 'bonus_balance', 'bonus_wagering_required', 'bonus_wagering_progress',
            'welcome_bonus_claimed', 'status', 'email_verified', 'document_verified', 'kyc_verified'
        ]
        read_only_fields = ['id', 'balance', 'bonus_balance', 'bonus_wagering_required',
                             'bonus_wagering_progress', 'welcome_bonus_claimed', 'status']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializador para cambiar contraseña"""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Las contraseñas no coinciden"})
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializador para recuperación de contraseña"""

    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    """Serializador para reestablecer contraseña"""

    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})
        return data
