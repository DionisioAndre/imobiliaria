from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Sponsorship, SponsorshipPackage, SponsorshipPayment

User = get_user_model()


class SponsorshipPackageSerializer(serializers.ModelSerializer):
    """Serializer para pacotes de patrocínio"""
    features = serializers.SerializerMethodField()
    
    class Meta:
        model = SponsorshipPackage
        fields = [
            'id', 'name', 'package_type', 'description', 'price',
            'duration_days', 'priority_level', 'show_in_featured',
            'show_in_recommendations', 'boost_factor', 'max_images_allowed',
            'max_videos_allowed', 'support_priority', 'analytics_access',
            'is_active', 'features'
        ]
        read_only_fields = ['id', 'is_active']
    
    def get_features(self, obj):
        """Retorna lista de benefícios do pacote"""
        return obj.get_features()


class SponsorshipPaymentSerializer(serializers.ModelSerializer):
    """Serializer para pagamentos de patrocínio"""
    
    class Meta:
        model = SponsorshipPayment
        fields = [
            'id', 'payment_method', 'status', 'amount', 'transaction_id',
            'reference_number', 'proof_file', 'notes', 'rejection_reason',
            'created_at', 'updated_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'status', 'created_at', 'updated_at', 'processed_at'
        ]
    
    def validate_proof_file(self, value):
        """Validar tamanho do comprovante"""
        if value:
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError("O comprovante não pode ter mais de 5MB")
        return value


class SponsorshipSerializer(serializers.ModelSerializer):
    """Serializer para patrocínios"""
    property_info = serializers.SerializerMethodField()
    sponsor_info = serializers.SerializerMethodField()
    package_info = serializers.SerializerMethodField()
    payments = SponsorshipPaymentSerializer(many=True, read_only=True)
    is_active = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    total_days = serializers.ReadOnlyField()
    
    class Meta:
        model = Sponsorship
        fields = [
            'id', 'property', 'property_info', 'sponsor', 'sponsor_info',
            'sponsorship_type', 'status', 'start_date', 'end_date',
            'duration_days', 'price', 'is_paid', 'paid_at',
            'priority_level', 'show_in_featured', 'show_in_recommendations',
            'boost_factor', 'views_boosted', 'contacts_boosted',
            'click_through_rate', 'created_at', 'updated_at',
            'activated_at', 'expired_at', 'notes', 'payments',
            'is_active', 'days_remaining', 'total_days', 'package_info'
        ]
        read_only_fields = [
            'id', 'sponsor', 'is_paid', 'paid_at', 'activated_at',
            'expired_at', 'views_boosted', 'contacts_boosted',
            'click_through_rate', 'created_at', 'updated_at'
        ]
    
    def get_property_info(self, obj):
        """Retorna informações do imóvel"""
        return {
            'id': obj.property.id,
            'title': obj.property.title,
            'property_type': obj.property.property_type,
            'transaction_type': obj.property.transaction_type,
            'price': obj.property.price,
            'main_image': obj.property.get_main_image().url if obj.property.get_main_image() else None,
        }
    
    def get_sponsor_info(self, obj):
        """Retorna informações do patrocinador"""
        return {
            'id': obj.sponsor.id,
            'full_name': obj.sponsor.full_name,
            'company_name': obj.sponsor.company_name,
            'is_verified': obj.sponsor.is_verified,
        }
    
    def get_package_info(self, obj):
        """Retorna informações do pacote (se baseado em pacote)"""
        # Se o patrocínio foi criado a partir de um pacote predefinido
        package = SponsorshipPackage.objects.filter(
            package_type=obj.sponsorship_type,
            is_active=True
        ).first()
        
        if package:
            return SponsorshipPackageSerializer(package).data
        return None
    
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
    
    def validate_property(self, value):
        """Validar se o usuário pode patrocinar este imóvel"""
        request = self.context.get('request')
        user = request.user
        
        # Verificar se o usuário é o proprietário do imóvel
        if value.owner != user:
            raise serializers.ValidationError("Você só pode patrocinar seus próprios imóveis")
        
        # Verificar se o imóvel está ativo
        if value.status != 'active':
            raise serializers.ValidationError("Apenas imóveis ativos podem ser patrocinados")
        
        # Verificar se já existe um patrocínio ativo para este imóvel
        active_sponsorship = value.sponsorships.filter(
            status='active',
            start_date__lte=value.end_date,
            end_date__gte=value.start_date
        ).first()
        
        if active_sponsorship:
            raise serializers.ValidationError(
                f"Este imóvel já possui um patrocínio ativo no período selecionado"
            )
        
        return value
    
    def create(self, validated_data):
        """Criar patrocínio"""
        request = self.context.get('request')
        validated_data['sponsor'] = request.user
        
        # Calcular duração em dias se não fornecida
        if not validated_data.get('duration_days'):
            start_date = validated_data['start_date']
            end_date = validated_data['end_date']
            duration = (end_date - start_date).days + 1
            validated_data['duration_days'] = duration
        
        # Se baseado em pacote, definir preço e outros campos
        sponsorship_type = validated_data.get('sponsorship_type')
        package = SponsorshipPackage.objects.filter(
            package_type=sponsorship_type,
            is_active=True
        ).first()
        
        if package:
            validated_data['price'] = package.price
            validated_data['priority_level'] = package.priority_level
            validated_data['show_in_featured'] = package.show_in_featured
            validated_data['show_in_recommendations'] = package.show_in_recommendations
            validated_data['boost_factor'] = package.boost_factor
        
        return super().create(validated_data)


class SponsorshipCreateSerializer(SponsorshipSerializer):
    """Serializer para criação de patrocínios"""
    package_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta(SponsorshipSerializer.Meta):
        fields = SponsorshipSerializer.Meta.fields + ['package_id']
    
    def validate_package_id(self, value):
        """Validar ID do pacote"""
        try:
            package = SponsorshipPackage.objects.get(id=value, is_active=True)
            return package
        except SponsorshipPackage.DoesNotExist:
            raise serializers.ValidationError("Pacote não encontrado ou inativo")
    
    def create(self, validated_data):
        """Criar patrocínio baseado em pacote"""
        package = validated_data.pop('package_id', None)
        request = self.context.get('request')
        
        if package:
            # Usar dados do pacote
            validated_data['sponsor'] = request.user
            validated_data['sponsorship_type'] = package.package_type
            validated_data['price'] = package.price
            validated_data['duration_days'] = package.duration_days
            validated_data['priority_level'] = package.priority_level
            validated_data['show_in_featured'] = package.show_in_featured
            validated_data['show_in_recommendations'] = package.show_in_recommendations
            validated_data['boost_factor'] = package.boost_factor
            
            # Calcular data de término baseada na duração
            start_date = validated_data['start_date']
            from datetime import timedelta
            end_date = start_date + timedelta(days=package.duration_days - 1)
            validated_data['end_date'] = end_date
        else:
            validated_data['sponsor'] = request.user
        
        return super().create(validated_data)


class SponsorshipListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagens"""
    property_info = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = Sponsorship
        fields = [
            'id', 'property', 'property_info', 'sponsorship_type', 'status',
            'start_date', 'end_date', 'price', 'is_paid', 'priority_level',
            'is_active', 'days_remaining', 'created_at'
        ]
    
    def get_property_info(self, obj):
        """Retorna informações básicas do imóvel"""
        return {
            'id': obj.property.id,
            'title': obj.property.title,
            'main_image': obj.property.get_main_image().url if obj.property.get_main_image() else None,
        }


class AdminSponsorshipSerializer(SponsorshipSerializer):
    """Serializer para administradores"""
    property_full_info = serializers.SerializerMethodField()
    sponsor_full_info = serializers.SerializerMethodField()
    
    class Meta(SponsorshipSerializer.Meta):
        fields = SponsorshipSerializer.Meta.fields + ['property_full_info', 'sponsor_full_info']
    
    def get_property_full_info(self, obj):
        """Retorna informações completas do imóvel"""
        return {
            'id': obj.property.id,
            'title': obj.property.title,
            'property_type': obj.property.get_property_type_display(),
            'transaction_type': obj.property.get_transaction_type_display(),
            'price': obj.property.price,
            'status': obj.property.status,
            'owner': obj.property.owner.full_name,
        }
    
    def get_sponsor_full_info(self, obj):
        """Retorna informações completas do patrocinador"""
        return {
            'id': obj.sponsor.id,
            'full_name': obj.sponsor.full_name,
            'email': obj.sponsor.email,
            'phone': obj.sponsor.phone,
            'user_type': obj.sponsor.get_user_type_display(),
            'is_verified': obj.sponsor.is_verified,
            'company_name': obj.sponsor.company_name,
        }


class AdminSponsorshipPackageSerializer(SponsorshipPackageSerializer):
    """Serializer para administradores gerenciarem pacotes"""
    
    class Meta(SponsorshipPackageSerializer.Meta):
        fields = SponsorshipPackageSerializer.Meta.fields
    
    def create(self, validated_data):
        """Criar pacote de patrocínio"""
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Atualizar pacote de patrocínio"""
        return super().update(instance, validated_data)
