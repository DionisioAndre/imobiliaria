from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Chat, Message, ChatNotification, ChatBlock

User = get_user_model()


class ChatSerializer(serializers.ModelSerializer):
    """Serializer para chats"""
    property_info = serializers.SerializerMethodField()
    seller_info = serializers.SerializerMethodField()
    buyer_info = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    can_participate = serializers.SerializerMethodField()
    
    class Meta:
        model = Chat
        fields = [
            'id', 'property', 'property_info', 'seller', 'seller_info',
            'buyer', 'buyer_info', 'status', 'last_message_at',
            'created_at', 'updated_at', 'last_message', 'unread_count',
            'can_participate'
        ]
        read_only_fields = [
            'id', 'seller', 'last_message_at', 'created_at', 'updated_at'
        ]
    
    def get_property_info(self, obj):
        """Retorna informações básicas do imóvel"""
        return {
            'id': obj.property.id,
            'title': obj.property.title,
            'property_type': obj.property.property_type,
            'transaction_type': obj.property.transaction_type,
            'price': obj.property.price,
            'main_image': obj.property.get_main_image().url if obj.property.get_main_image() else None,
        }
    
    def get_seller_info(self, obj):
        """Retorna informações do vendedor"""
        return {
            'id': obj.seller.id,
            'full_name': obj.seller.full_name,
            'is_verified': obj.seller.is_verified,
        }
    
    def get_buyer_info(self, obj):
        """Retorna informações do comprador"""
        return {
            'id': obj.buyer.id,
            'full_name': obj.buyer.full_name,
        }
    
    def get_last_message(self, obj):
        """Retorna a última mensagem"""
        last_msg = obj.get_last_message()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None
    
    def get_unread_count(self, obj):
        """Retorna o número de mensagens não lidas"""
        request = self.context.get('request')
        if request:
            return obj.unread_count(request.user)
        return 0
    
    def get_can_participate(self, obj):
        """Verifica se o usuário pode participar do chat"""
        request = self.context.get('request')
        if request:
            return obj.can_user_participate(request.user)
        return False


class MessageSerializer(serializers.ModelSerializer):
    """Serializer para mensagens"""
    sender_info = serializers.SerializerMethodField()
    is_own = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'chat', 'sender', 'sender_info', 'message_type',
            'content', 'file', 'is_read', 'read_at', 'created_at',
            'updated_at', 'is_own', 'can_edit', 'can_delete'
        ]
        read_only_fields = [
            'id', 'sender', 'is_read', 'read_at', 'created_at', 'updated_at'
        ]
    
    def get_sender_info(self, obj):
        """Retorna informações do remetente"""
        return {
            'id': obj.sender.id,
            'full_name': obj.sender.full_name,
            'is_verified': obj.sender.is_verified,
        }
    
    def get_is_own(self, obj):
        """Verifica se a mensagem é do usuário atual"""
        request = self.context.get('request')
        if request:
            return obj.sender == request.user
        return False
    
    def get_can_edit(self, obj):
        """Verifica se o usuário pode editar a mensagem"""
        request = self.context.get('request')
        if request:
            return obj.can_user_edit(request.user)
        return False
    
    def get_can_delete(self, obj):
        """Verifica se o usuário pode deletar a mensagem"""
        request = self.context.get('request')
        if request:
            return obj.can_user_delete(request.user)
        return False
    
    def validate_content(self, value):
        """Validar conteúdo da mensagem"""
        if not value.strip():
            raise serializers.ValidationError("O conteúdo da mensagem não pode estar vazio")
        return value.strip()
    
    def validate_file(self, value):
        """Validar tamanho do arquivo"""
        if value:
            max_size = 10 * 1024 * 1024  # 10MB
            if value.size > max_size:
                raise serializers.ValidationError("O arquivo não pode ter mais de 10MB")
        return value


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de mensagens"""
    
    class Meta:
        model = Message
        fields = ['message_type', 'content', 'file']
    
    def validate(self, attrs):
        """Validar mensagem"""
        message_type = attrs.get('message_type')
        content = attrs.get('content')
        file = attrs.get('file')
        
        if message_type == 'text' and not content:
            raise serializers.ValidationError("Mensagens de texto devem ter conteúdo")
        
        if message_type in ['image', 'file'] and not file:
            raise serializers.ValidationError("Mensagens com arquivo devem incluir um arquivo")
        
        return attrs


class ChatNotificationSerializer(serializers.ModelSerializer):
    """Serializer para notificações de chat"""
    message_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatNotification
        fields = [
            'id', 'user', 'chat', 'message', 'message_info',
            'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'chat', 'message', 'created_at']
    
    def get_message_info(self, obj):
        """Retorna informações da mensagem"""
        return {
            'id': obj.message.id,
            'content': obj.message.content[:100] + '...' if len(obj.message.content) > 100 else obj.message.content,
            'sender': obj.message.sender.full_name,
            'chat_id': obj.chat.id,
        }


class ChatBlockSerializer(serializers.ModelSerializer):
    """Serializer para bloqueios de chat"""
    blocker_info = serializers.SerializerMethodField()
    blocked_info = serializers.SerializerMethodField()
    property_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatBlock
        fields = [
            'id', 'blocker', 'blocker_info', 'blocked', 'blocked_info',
            'property', 'property_info', 'reason', 'created_at'
        ]
        read_only_fields = ['id', 'blocker', 'created_at']
    
    def get_blocker_info(self, obj):
        """Retorna informações do bloqueador"""
        return {
            'id': obj.blocker.id,
            'full_name': obj.blocker.full_name,
        }
    
    def get_blocked_info(self, obj):
        """Retorna informações do bloqueado"""
        return {
            'id': obj.blocked.id,
            'full_name': obj.blocked.full_name,
        }
    
    def get_property_info(self, obj):
        """Retorna informações do imóvel (se houver)"""
        if obj.property:
            return {
                'id': obj.property.id,
                'title': obj.property.title,
            }
        return None


class ChatCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de chats"""
    
    class Meta:
        model = Chat
        fields = ['property']
    
    def validate_property(self, value):
        """Validar se o usuário pode criar chat para este imóvel"""
        request = self.context.get('request')
        user = request.user
        
        # Verificar se o imóvel está disponível
        if not value.is_available:
            raise serializers.ValidationError("Este imóvel não está disponível para contato")
        
        # Verificar se o usuário não é o proprietário
        if value.owner == user:
            raise serializers.ValidationError("Você não pode criar um chat para seu próprio imóvel")
        
        # Verificar se já existe um chat para este usuário e imóvel
        if Chat.objects.filter(property=value, buyer=user).exists():
            raise serializers.ValidationError("Você já possui um chat para este imóvel")
        
        # Verificar se não há bloqueios
        if ChatBlock.is_blocked(value.owner, user, value) or ChatBlock.is_blocked(user, value.owner, value):
            raise serializers.ValidationError("Não é possível criar chat devido a bloqueios")
        
        return value
    
    def create(self, validated_data):
        """Criar chat"""
        request = self.context.get('request')
        property = validated_data['property']
        
        chat = Chat.objects.create(
            property=property,
            seller=property.owner,
            buyer=request.user
        )
        
        return chat


class AdminChatSerializer(ChatSerializer):
    """Serializer para administradores"""
    all_messages_count = serializers.SerializerMethodField()
    
    class Meta(ChatSerializer.Meta):
        fields = ChatSerializer.Meta.fields + ['all_messages_count']
    
    def get_all_messages_count(self, obj):
        """Retorna o número total de mensagens"""
        return obj.messages.count()


class AdminMessageSerializer(MessageSerializer):
    """Serializer para administradores"""
    chat_info = serializers.SerializerMethodField()
    
    class Meta(MessageSerializer.Meta):
        fields = MessageSerializer.Meta.fields + ['chat_info']
    
    def get_chat_info(self, obj):
        """Retorna informações do chat"""
        return {
            'id': obj.chat.id,
            'property_title': obj.chat.property.title,
            'participants': f"{obj.chat.seller.full_name} x {obj.chat.buyer.full_name}",
        }
