from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import RentalContract, RentalPayment, ContractRenewal

User = get_user_model()


class RentalPaymentSerializer(serializers.ModelSerializer):
    """Serializer para pagamentos de renda"""
    is_overdue = serializers.ReadOnlyField()
    days_overdue = serializers.ReadOnlyField()
    total_amount = serializers.ReadOnlyField()
    
    class Meta:
        model = RentalPayment
        fields = [
            'id', 'contract', 'payment_month', 'amount', 'status',
            'payment_method', 'due_date', 'paid_date', 'proof_file',
            'transaction_reference', 'notes', 'late_fee', 'created_at',
            'updated_at', 'is_overdue', 'days_overdue', 'total_amount'
        ]
        read_only_fields = [
            'id', 'contract', 'created_at', 'updated_at', 'late_fee'
        ]
    
    def validate_proof_file(self, value):
        """Validar tamanho do comprovante"""
        if value:
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError("O comprovante não pode ter mais de 5MB")
        return value


class ContractRenewalSerializer(serializers.ModelSerializer):
    """Serializer para renovações de contrato"""
    can_be_approved = serializers.ReadOnlyField()
    
    class Meta:
        model = ContractRenewal
        fields = [
            'id', 'contract', 'new_end_date', 'new_monthly_rent', 'status',
            'landlord_reason', 'tenant_reason', 'landlord_approved',
            'tenant_approved', 'landlord_approved_at', 'tenant_approved_at',
            'created_at', 'updated_at', 'can_be_approved'
        ]
        read_only_fields = [
            'id', 'contract', 'landlord_approved', 'tenant_approved',
            'landlord_approved_at', 'tenant_approved_at', 'created_at', 'updated_at'
        ]
    
    def validate_new_end_date(self, value):
        """Validar nova data de término"""
        request = self.context.get('request')
        contract = self.instance.contract if self.instance else None
        
        if contract:
            if value <= contract.end_date:
                raise serializers.ValidationError(
                    "A nova data de término deve ser posterior à data atual de término"
                )
        
        return value
    
    def validate_new_monthly_rent(self, value):
        """Validar nova renda mensal"""
        if value <= 0:
            raise serializers.ValidationError("A renda mensal deve ser maior que zero")
        return value


class RentalContractSerializer(serializers.ModelSerializer):
    """Serializer para contratos de arrendamento"""
    landlord_info = serializers.SerializerMethodField()
    tenant_info = serializers.SerializerMethodField()
    property_info = serializers.SerializerMethodField()
    payments = RentalPaymentSerializer(many=True, read_only=True)
    renewals = ContractRenewalSerializer(many=True, read_only=True)
    is_active = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    total_rent_amount = serializers.ReadOnlyField()
    is_signed_by_both = serializers.ReadOnlyField()
    
    class Meta:
        model = RentalContract
        fields = [
            'id', 'property', 'property_info', 'landlord', 'landlord_info',
            'tenant', 'tenant_info', 'contract_number', 'contract_type',
            'status', 'start_date', 'end_date', 'duration_months',
            'monthly_rent', 'security_deposit', 'maintenance_fee',
            'payment_day', 'payment_method', 'terms', 'special_conditions',
            'renewal_terms', 'contract_file', 'tenant_id_document',
            'landlord_id_document', 'landlord_signature', 'tenant_signature',
            'landlord_signed_at', 'tenant_signed_at', 'created_at',
            'updated_at', 'activated_at', 'expired_at', 'notes', 'payments',
            'renewals', 'is_active', 'days_until_expiry', 'total_rent_amount',
            'is_signed_by_both'
        ]
        read_only_fields = [
            'id', 'landlord', 'contract_number', 'duration_months',
            'landlord_signature', 'landlord_signed_at', 'tenant_signature',
            'tenant_signed_at', 'created_at', 'updated_at', 'activated_at',
            'expired_at'
        ]
    
    def get_landlord_info(self, obj):
        """Retorna informações do senhorio"""
        return {
            'id': obj.landlord.id,
            'full_name': obj.landlord.full_name,
            'email': obj.landlord.email,
            'phone': obj.landlord.phone,
            'is_verified': obj.landlord.is_verified,
        }
    
    def get_tenant_info(self, obj):
        """Retorna informações do inquilino"""
        return {
            'id': obj.tenant.id,
            'full_name': obj.tenant.full_name,
            'email': obj.tenant.email,
            'phone': obj.tenant.phone,
            'is_verified': obj.tenant.is_verified,
        }
    
    def get_property_info(self, obj):
        """Retorna informações do imóvel"""
        return {
            'id': obj.property.id,
            'title': obj.property.title,
            'property_type': obj.property.property_type,
            'address': f"{obj.property.neighborhood}, {obj.property.municipality}",
            'area_m2': obj.property.area_m2,
            'bedrooms': obj.property.bedrooms,
            'bathrooms': obj.property.bathrooms,
        }
    
    def validate_start_date(self, value):
        """Validar data de início"""
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("A data de início não pode ser no passado")
        return value
    
    def validate_end_date(self, value):
        """Validar data de término"""
        start_date = self.initial_data.get('start_date')
        if start_date and value <= start_date:
            raise serializers.ValidationError("A data de término deve ser posterior à data de início")
        return value
    
    def validate_monthly_rent(self, value):
        """Validar renda mensal"""
        if value <= 0:
            raise serializers.ValidationError("A renda mensal deve ser maior que zero")
        return value
    
    def validate_security_deposit(self, value):
        """Validar caução"""
        if value < 0:
            raise serializers.ValidationError("A caução não pode ser negativa")
        return value
    
    def validate_contract_file(self, value):
        """Validar arquivo do contrato"""
        if value:
            max_size = 10 * 1024 * 1024  # 10MB
            if value.size > max_size:
                raise serializers.ValidationError("O contrato não pode ter mais de 10MB")
        return value
    
    def validate_tenant_id_document(self, value):
        """Validar documento do inquilino"""
        if value:
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError("O documento não pode ter mais de 5MB")
        return value
    
    def validate_landlord_id_document(self, value):
        """Validar documento do senhorio"""
        if value:
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError("O documento não pode ter mais de 5MB")
        return value
    
    def validate(self, attrs):
        """Validações adicionais"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date:
            duration_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            if duration_months < 1:
                raise serializers.ValidationError("O contrato deve ter duração mínima de 1 mês")
        
        return attrs


class RentalContractCreateSerializer(RentalContractSerializer):
    """Serializer para criação de contratos"""
    
    class Meta(RentalContractSerializer.Meta):
        fields = RentalContractSerializer.Meta.fields
    
    def validate_property(self, value):
        """Validar se o usuário pode criar contrato para este imóvel"""
        request = self.context.get('request')
        user = request.user
        
        # Verificar se o usuário é o proprietário do imóvel
        if value.owner != user:
            raise serializers.ValidationError("Apenas o proprietário pode criar contratos")
        
        # Verificar se o imóvel é para arrendamento
        if value.transaction_type not in ['rent', 'short_term_rent']:
            raise serializers.ValidationError("Apenas imóveis para arrendamento podem ter contratos")
        
        # Verificar se não há contrato ativo
        active_contract = value.rental_contracts.filter(status='active').first()
        if active_contract:
            raise serializers.ValidationError("Este imóvel já possui um contrato ativo")
        
        return value
    
    def create(self, validated_data):
        """Criar contrato"""
        request = self.context.get('request')
        validated_data['landlord'] = request.user
        
        return super().create(validated_data)


class RentalContractListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagens"""
    property_info = serializers.SerializerMethodField()
    tenant_info = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    
    class Meta:
        model = RentalContract
        fields = [
            'id', 'contract_number', 'property', 'property_info', 'tenant',
            'tenant_info', 'status', 'start_date', 'end_date', 'monthly_rent',
            'is_active', 'days_until_expiry', 'created_at'
        ]
    
    def get_property_info(self, obj):
        """Retorna informações básicas do imóvel"""
        return {
            'id': obj.property.id,
            'title': obj.property.title,
            'address': f"{obj.property.neighborhood}, {obj.property.municipality}",
        }
    
    def get_tenant_info(self, obj):
        """Retorna informações básicas do inquilino"""
        return {
            'id': obj.tenant.id,
            'full_name': obj.tenant.full_name,
        }


class ContractRenewalCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de renovações"""
    
    class Meta:
        model = ContractRenewal
        fields = [
            'new_end_date', 'new_monthly_rent', 'tenant_reason'
        ]
    
    def validate_new_end_date(self, value):
        """Validar nova data de término"""
        if self.instance:
            contract = self.instance.contract
            if value <= contract.end_date:
                raise serializers.ValidationError(
                    "A nova data de término deve ser posterior à data atual de término"
                )
        return value
    
    def validate_new_monthly_rent(self, value):
        """Validar nova renda mensal"""
        if value <= 0:
            raise serializers.ValidationError("A renda mensal deve ser maior que zero")
        return value


class AdminRentalContractSerializer(RentalContractSerializer):
    """Serializer para administradores"""
    property_full_info = serializers.SerializerMethodField()
    landlord_full_info = serializers.SerializerMethodField()
    tenant_full_info = serializers.SerializerMethodField()
    
    class Meta(RentalContractSerializer.Meta):
        fields = RentalContractSerializer.Meta.fields + [
            'property_full_info', 'landlord_full_info', 'tenant_full_info'
        ]
    
    def get_property_full_info(self, obj):
        """Retorna informações completas do imóvel"""
        return {
            'id': obj.property.id,
            'title': obj.property.title,
            'property_type': obj.property.get_property_type_display(),
            'transaction_type': obj.property.get_transaction_type_display(),
            'price': obj.property.price,
            'address': f"{obj.property.neighborhood}, {obj.property.municipality}, {obj.property.province}",
            'area_m2': obj.property.area_m2,
            'bedrooms': obj.property.bedrooms,
            'bathrooms': obj.property.bathrooms,
            'owner': obj.property.owner.full_name,
        }
    
    def get_landlord_full_info(self, obj):
        """Retorna informações completas do senhorio"""
        return {
            'id': obj.landlord.id,
            'full_name': obj.landlord.full_name,
            'email': obj.landlord.email,
            'phone': obj.landlord.phone,
            'user_type': obj.landlord.get_user_type_display(),
            'is_verified': obj.landlord.is_verified,
            'company_name': obj.landlord.company_name,
        }
    
    def get_tenant_full_info(self, obj):
        """Retorna informações completas do inquilino"""
        return {
            'id': obj.tenant.id,
            'full_name': obj.tenant.full_name,
            'email': obj.tenant.email,
            'phone': obj.tenant.phone,
            'user_type': obj.tenant.get_user_type_display(),
            'is_verified': obj.tenant.is_verified,
        }
