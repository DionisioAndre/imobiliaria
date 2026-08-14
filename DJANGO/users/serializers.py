from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserVerification


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer para registro de novos usuários"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'phone', 'user_type',
            'province', 'municipality', 'neighborhood'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("As senhas não conferem")
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email já está em uso")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer para login de usuários"""
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError('Credenciais inválidas')
            
            if not user.is_active:
                raise serializers.ValidationError('Usuário inativo')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Email e senha são obrigatórios')


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para perfil de usuário"""
    full_name = serializers.ReadOnlyField()
    is_vendor = serializers.ReadOnlyField()
    is_client = serializers.ReadOnlyField()
    is_admin_user = serializers.ReadOnlyField()
    properties_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'user_type', 'bio', 'profile_picture', 'province',
            'municipality', 'neighborhood', 'is_verified', 'created_at',
            'is_vendor', 'is_client', 'is_admin_user', 'properties_count',
            'company_name', 'last_login'
        ]
        read_only_fields = ['id', 'username', 'email', 'created_at', 'last_login', 'is_verified']
    
    def get_properties_count(self, obj):
        return obj.get_properties_count()


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de dados do usuário"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'bio', 'profile_picture',
            'province', 'municipality', 'neighborhood', 'company_name'
        ]
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer para alteração de senha"""
    current_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Senha atual incorreta')
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError('As novas senhas não conferem')
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserVerificationSerializer(serializers.ModelSerializer):
    """Serializer para verificação de usuários"""
    
    class Meta:
        model = UserVerification
        fields = [
            'id', 'document_type', 'document_file', 'status',
            'rejection_reason', 'created_at', 'reviewed_at'
        ]
        read_only_fields = ['id', 'status', 'rejection_reason', 'created_at', 'reviewed_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer para administração de usuários"""
    full_name = serializers.ReadOnlyField()
    properties_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'user_type', 'is_active', 'is_verified', 'created_at',
            'last_login', 'properties_count', 'last_login_ip'
        ]
        read_only_fields = ['id', 'username', 'email', 'created_at', 'last_login']
    
    def get_properties_count(self, obj):
        return obj.get_properties_count()


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer para administração de usuários"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'user_type', 'is_active',
            'is_verified', 'province', 'municipality', 'neighborhood'
        ]
