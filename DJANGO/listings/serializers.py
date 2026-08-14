from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Property, PropertyImage, PropertyVideo, PropertyDocument, PropertyView, PropertyMessage, PropertyVisitRequest

User = get_user_model()


class PropertyImageSerializer(serializers.ModelSerializer):
    """Serializer para imagens de imóveis"""
    
    class Meta:
        model = PropertyImage
        fields = [
            'id', 'image', 'is_main', 'caption', 'order', 'created_at'
        ]
    
    def validate_image(self, value):
        """Validar tamanho da imagem"""
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError("A imagem não pode ter mais de 5MB")
        return value


class PropertyVideoSerializer(serializers.ModelSerializer):
    """Serializer para vídeos de imóveis"""
    
    class Meta:
        model = PropertyVideo
        fields = [
            'id', 'video', 'thumbnail', 'title', 'description', 
            'duration', 'created_at'
        ]
    
    def validate_video(self, value):
        """Validar tamanho do vídeo"""
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError("O vídeo não pode ter mais de 50MB")
        return value


class PropertyDocumentSerializer(serializers.ModelSerializer):
    """Serializer para documentos de imóveis (apenas para administradores)"""
    
    class Meta:
        model = PropertyDocument
        fields = [
            'id', 'document_type', 'document', 'title', 'description',
            'is_verified', 'verified_by', 'verified_at', 'created_at'
        ]
        read_only_fields = ['is_verified', 'verified_by', 'verified_at']
    
    def validate_document(self, value):
        """Validar tamanho do documento"""
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError("O documento não pode ter mais de 10MB")
        return value


class PropertySerializer(serializers.ModelSerializer):
    """Serializer principal para imóveis"""
    owner_info = serializers.SerializerMethodField()
    images = PropertyImageSerializer(many=True, read_only=True)
    videos = PropertyVideoSerializer(many=True, read_only=True)
    has_documents = serializers.SerializerMethodField()
    images_count = serializers.SerializerMethodField()
    videos_count = serializers.SerializerMethodField()
    is_sponsored = serializers.ReadOnlyField()
    main_image = serializers.SerializerMethodField()
    location_full = serializers.SerializerMethodField()
    can_be_contacted = serializers.ReadOnlyField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'description', 'property_type', 'transaction_type',
            'price', 'price_negotiable', 'province', 'municipality', 'neighborhood',
            'street', 'reference_point', 'latitude', 'longitude', 'bedrooms',
            'bathrooms', 'parking_spaces', 'area_m2', 'total_area_m2',
            'is_furnished', 'furniture_description', 'available_from', 'available_until',
            'status', 'featured', 'views_count', 'contact_count', 'owner',
            'owner_info', 'created_at', 'updated_at', 'published_at', 'expires_at',
            'additional_notes', 'slug', 'images', 'videos', 'has_documents',
            'images_count', 'videos_count', 'is_sponsored', 'main_image',
            'location_full', 'can_be_contacted'
        ]
        read_only_fields = [
            'id', 'owner', 'views_count', 'contact_count', 'created_at',
            'updated_at', 'published_at', 'expires_at', 'slug', 'is_sponsored'
        ]
    
    def get_owner_info(self, obj):
        """Retorna informações básicas do proprietário"""
        return {
            'id': obj.owner.id,
            'full_name': obj.owner.full_name,
            'is_verified': obj.owner.is_verified,
            'company_name': obj.owner.company_name,
        }
    
    def get_has_documents(self, obj):
        """Retorna se há documentos (apenas para proprietário e administradores)"""
        request = self.context.get('request')
        if request and (request.user.is_admin_user or request.user == obj.owner):
            return obj.documents.exists()
        return False
    
    def get_images_count(self, obj):
        """Retorna o número de imagens"""
        return obj.images.count()
    
    def get_videos_count(self, obj):
        """Retorna o número de vídeos"""
        return obj.videos.count()
    
    def get_main_image(self, obj):
        """Retorna a imagem principal"""
        main_image = obj.get_main_image()
        if main_image:
            return main_image.url
        return None
    
    def get_location_full(self, obj):
        """Retorna a localização completa"""
        parts = [obj.province, obj.municipality, obj.neighborhood]
        if obj.street:
            parts.append(obj.street)
        if obj.reference_point:
            parts.append(f"Ref: {obj.reference_point}")
        return ", ".join(parts)
    
    def validate_price(self, value):
        """Validar preço"""
        if value <= 0:
            raise serializers.ValidationError("O preço deve ser maior que zero")
        return value
    
    def validate_area_m2(self, value):
        """Validar área"""
        if value <= 0:
            raise serializers.ValidationError("A área deve ser maior que zero")
        return value
    
    def validate(self, attrs):
        """Validações adicionais"""
        available_from = attrs.get('available_from')
        available_until = attrs.get('available_until')
        
        if available_from and available_until and available_from >= available_until:
            raise serializers.ValidationError(
                "A data de início deve ser anterior à data de término"
            )
        
        return attrs


class PropertyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'description', 'property_type', 'transaction_type',
            'price', 'price_negotiable', 'province', 'municipality',
            'neighborhood', 'bedrooms', 'bathrooms', 'area_m2',
            'is_furnished', 'additional_notes'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        request = self.context.get('request')
        # Criação apenas dos dados textuais/numéricos
        property = Property.objects.create(owner=request.user, **validated_data)
        return property
class PropertyUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de imóveis"""
    images = PropertyImageSerializer(many=True, required=False)
    videos = PropertyVideoSerializer(many=True, required=False)
    documents = PropertyDocumentSerializer(many=True, required=False)
    
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'price', 'price_negotiable',
            'bedrooms', 'bathrooms', 'parking_spaces', 'area_m2',
            'total_area_m2', 'is_furnished', 'furniture_description',
            'available_from', 'available_until', 'additional_notes',
            'images', 'videos', 'documents'
        ]
    
    def update(self, instance, validated_data):
        """Atualizar imóvel com imagens, vídeos e documentos"""
        images_data = validated_data.pop('images', None)
        videos_data = validated_data.pop('videos', None)
        documents_data = validated_data.pop('documents', None)
        
        # Atualizar campos do imóvel
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Atualizar imagens
        if images_data is not None:
            instance.images.all().delete()
            for image_data in images_data:
                PropertyImage.objects.create(property=instance, **image_data)
        
        # Atualizar vídeos
        if videos_data is not None:
            instance.videos.all().delete()
            for video_data in videos_data:
                PropertyVideo.objects.create(property=instance, **video_data)
        
        # Atualizar documentos
        if documents_data is not None:
            instance.documents.all().delete()
            for doc_data in documents_data:
                PropertyDocument.objects.create(property=instance, **doc_data)
        
        return instance


class PropertyListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagens - documentos ocultos para compradores"""
    owner_info = serializers.SerializerMethodField()
    main_image = serializers.SerializerMethodField()
    location_short = serializers.SerializerMethodField()
    images = PropertyImageSerializer(many=True, read_only=True)
    videos = PropertyVideoSerializer(many=True, read_only=True)
    is_sponsored = serializers.ReadOnlyField()
    has_documents = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'property_type', 'transaction_type', 'price',
            'price_negotiable', 'province', 'municipality', 'neighborhood',
            'bedrooms', 'bathrooms', 'area_m2', 'is_furnished',
            'status', 'featured', 'views_count', 'contact_count',
            'created_at', 'owner_info', 'main_image', 'location_short',
            'is_sponsored','images', 'videos', 'has_documents'
        ]
    
    def get_owner_info(self, obj):
        """Retorna informações básicas do proprietário"""
        return {
            'id': obj.owner.id,
            'full_name': obj.owner.full_name,
            'is_verified': obj.owner.is_verified,
            'company_name': obj.owner.company_name,
        }
    
    def get_has_documents(self, obj):
        """Retorna se há documentos (apenas para proprietário e administradores)"""
        request = self.context.get('request')
        if request and (request.user.is_admin_user or request.user == obj.owner):
            return obj.documents.exists()
        return False
    
    def get_main_image(self, obj):
        """Retorna a imagem principal"""
        main_image = obj.get_main_image()
        if main_image:
            return main_image.url
        return None
    
    def get_location_short(self, obj):
        """Retorna localização resumida"""
        return f"{obj.neighborhood}, {obj.municipality}"


class PropertyDetailSerializer(PropertySerializer):
    """Serializer detalhado para visualização de imóveis"""
    documents = serializers.SerializerMethodField()
    
    class Meta(PropertySerializer.Meta):
        fields = PropertySerializer.Meta.fields + ['documents']
    
    def get_documents(self, obj):
        """Retorna documentos (apenas para administradores)"""
        request = self.context.get('request')
        if request and request.user.is_admin_user:
            return PropertyDocumentSerializer(obj.documents.all(), many=True).data
        return []


class PropertyMessageSerializer(serializers.ModelSerializer):
    """Serializer para mensagens de chat"""
    sender_info = serializers.SerializerMethodField()
    receiver_info = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyMessage
        fields = [
            'id', 'property', 'sender', 'receiver', 'message', 'is_read',
            'created_at', 'sender_info', 'receiver_info'
        ]
        read_only_fields = ['id', 'sender', 'receiver', 'created_at', 'property']
        extra_kwargs = {
            'message': {'required': True, 'allow_blank': False}
        }
    
    def get_sender_info(self, obj):
        return {
            'id': obj.sender.id,
            'full_name': obj.sender.full_name,
        }
    
    def get_receiver_info(self, obj):
        return {
            'id': obj.receiver.id,
            'full_name': obj.receiver.full_name,
        }
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['sender'] = request.user
        return super().create(validated_data)


class PropertyVisitRequestSerializer(serializers.ModelSerializer):
    """Serializer para solicitações de visita"""
    buyer_info = serializers.SerializerMethodField()
    property_info = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyVisitRequest
        fields = [
            'id', 'property', 'buyer', 'preferred_date', 'preferred_time',
            'notes', 'status', 'created_at', 'updated_at', 'buyer_info', 'property_info'
        ]
        read_only_fields = ['id', 'buyer', 'property', 'created_at', 'updated_at']
    
    def get_buyer_info(self, obj):
        return {
            'id': obj.buyer.id,
            'full_name': obj.buyer.full_name,
        }
    
    def get_property_info(self, obj):
        return {
            'id': obj.property.id,
            'title': obj.property.title,
        }
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['buyer'] = request.user
        return super().create(validated_data)


class PropertyViewSerializer(serializers.ModelSerializer):
    """Serializer para registro de visualizações"""
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyView
        fields = [
            'id', 'property', 'user', 'user_info', 'ip_address',
            'user_agent', 'viewed_at'
        ]
        read_only_fields = ['id', 'user', 'ip_address', 'user_agent', 'viewed_at']
    
    def get_user_info(self, obj):
        """Retorna informações do usuário (apenas para administradores)"""
        if obj.user:
            return {
                'id': obj.user.id,
                'full_name': obj.user.full_name,
                'email': obj.user.email,
            }
        return None


class AdminPropertySerializer(PropertySerializer):
    """Serializer para administradores"""
    documents = PropertyDocumentSerializer(many=True, read_only=True)
    completion_status = serializers.SerializerMethodField()
    
    class Meta(PropertySerializer.Meta):
        fields = PropertySerializer.Meta.fields + ['documents', 'completion_status']
    
    def get_completion_status(self, obj):
        """Retorna status de completude do imóvel"""
        return {
            'has_documents': obj.documents.exists(),
            'has_min_images': obj.images.count() >= 4,
            'has_video': obj.videos.exists(),
            'has_location': all([obj.province, obj.municipality, obj.neighborhood]),
            'is_complete': obj.check_completion(),
        }
