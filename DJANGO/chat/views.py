from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import Chat, Message, ChatNotification, ChatBlock
from .serializers import (
    ChatSerializer, ChatCreateSerializer, MessageSerializer, MessageCreateSerializer,
    ChatNotificationSerializer, ChatBlockSerializer, AdminChatSerializer, AdminMessageSerializer
)
from users.permissions import IsOwnerOrAdmin, CanParticipateInChat, CanSendMessage, IsAdminUser


class ChatListView(generics.ListAPIView):
    """View para listar chats do usuário"""
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'property__property_type', 'property__transaction_type']
    search_fields = ['property__title', 'property__neighborhood']
    ordering_fields = ['last_message_at', 'created_at']
    ordering = ['-last_message_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return Chat.objects.all()
        return Chat.objects.filter(Q(seller=user) | Q(buyer=user)).distinct()


class ChatDetailView(generics.RetrieveAPIView):
    """View para detalhes de um chat"""
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated, CanParticipateInChat]
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return Chat.objects.all()
        return Chat.objects.filter(Q(seller=user) | Q(buyer=user)).distinct()
    
    def get_serializer_class(self):
        request = self.context.get('request')
        if request and request.user.is_admin_user:
            return AdminChatSerializer
        return ChatSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Marcar mensagens como lidas ao visualizar o chat"""
        response = super().retrieve(request, *args, **kwargs)
        
        # Marcar mensagens como lidas
        chat = self.get_object()
        chat.mark_messages_as_read(request.user)
        
        return response


class ChatCreateView(generics.CreateAPIView):
    """View para criação de chats"""
    serializer_class = ChatCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class MessageListView(generics.ListAPIView):
    """View para listar mensagens de um chat"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, CanParticipateInChat]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['message_type', 'is_read']
    ordering = ['created_at']
    
    def get_queryset(self):
        chat_id = self.kwargs['chat_id']
        try:
            chat = Chat.objects.get(id=chat_id)
            
            # Verificar permissão
            if not chat.can_user_participate(self.request.user):
                return Message.objects.none()
            
            return Message.objects.filter(chat=chat)
        except Chat.DoesNotExist:
            return Message.objects.none()


class MessageCreateView(generics.CreateAPIView):
    """View para criação de mensagens"""
    serializer_class = MessageCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_chat(self):
        chat_id = self.kwargs['chat_id']
        return Chat.objects.get(id=chat_id)
    
    def perform_create(self, serializer):
        chat = self.get_chat()
        
        # Verificar se o usuário pode participar do chat
        if not chat.can_user_participate(self.request.user):
            raise permissions.PermissionDenied("Você não pode participar deste chat")
        
        # Verificar se não há bloqueios
        from .models import ChatBlock
        if not ChatBlock.can_message(
            self.request.user, 
            chat.other_user(self.request.user),
            chat.property
        ):
            raise permissions.PermissionDenied("Mensagem bloqueada")
        
        # Criar mensagem
        message = serializer.save(
            chat=chat,
            sender=self.request.user
        )
        
        # Marcar como lida pelo remetente
        message.mark_as_read()
        
        # Criar notificação para o outro usuário
        other_user = chat.other_user(self.request.user)
        ChatNotification.objects.create(
            user=other_user,
            chat=chat,
            message=message
        )
        
        # Atualizar último message_at do chat
        chat.last_message_at = message.created_at
        chat.save(update_fields=['last_message_at'])


class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View para detalhes/atualização/exclusão de mensagens"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return Message.objects.all()
        
        # Apenas mensagens de chats onde o usuário participa
        return Message.objects.filter(
            chat__in=Chat.objects.filter(Q(seller=user) | Q(buyer=user))
        ).distinct()
    
    def update(self, request, *args, **kwargs):
        """Atualizar mensagem (apenas se for do usuário e dentro do tempo limite)"""
        message = self.get_object()
        
        if not message.can_user_edit(request.user):
            return Response(
                {'error': 'Você não pode editar esta mensagem'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Excluir mensagem (apenas se for do usuário e dentro do tempo limite)"""
        message = self.get_object()
        
        if not message.can_user_delete(request.user):
            return Response(
                {'error': 'Você não pode excluir esta mensagem'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)


class ChatNotificationListView(generics.ListAPIView):
    """View para listar notificações de chat do usuário"""
    serializer_class = ChatNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_read']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return ChatNotification.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notifications_as_read_view(request):
    """Marcar todas as notificações como lidas"""
    ChatNotification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)
    
    return Response({'message': 'Notificações marcadas como lidas'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_as_read_view(request, notification_id):
    """Marcar notificação específica como lida"""
    try:
        notification = ChatNotification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.mark_as_read()
        
        return Response({'message': 'Notificação marcada como lida'})
    except ChatNotification.DoesNotExist:
        return Response(
            {'error': 'Notificação não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )


class ChatBlockListView(generics.ListCreateAPIView):
    """View para listar e criar bloqueios"""
    serializer_class = ChatBlockSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return ChatBlock.objects.filter(blocker=user)
    
    def perform_create(self, serializer):
        serializer.save(blocker=self.request.user)


class ChatBlockDetailView(generics.DestroyAPIView):
    """View para remover bloqueios"""
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        return ChatBlock.objects.filter(blocker=user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def close_chat_view(request, chat_id):
    """Fechar um chat"""
    try:
        chat = Chat.objects.get(id=chat_id)
        
        # Verificar permissão
        if not chat.can_user_participate(request.user):
            return Response(
                {'error': 'Sem permissão para fechar este chat'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        chat.close_chat()
        
        return Response({'message': 'Chat fechado com sucesso'})
        
    except Chat.DoesNotExist:
        return Response(
            {'error': 'Chat não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def archive_chat_view(request, chat_id):
    """Arquivar um chat"""
    try:
        chat = Chat.objects.get(id=chat_id)
        
        # Verificar permissão
        if not chat.can_user_participate(request.user):
            return Response(
                {'error': 'Sem permissão para arquivar este chat'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        chat.archive_chat()
        
        return Response({'message': 'Chat arquivado com sucesso'})
        
    except Chat.DoesNotExist:
        return Response(
            {'error': 'Chat não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def chat_stats_view(request):
    """Estatísticas de chat do usuário"""
    user = request.user
    
    stats = {
        'total_chats': Chat.objects.filter(Q(seller=user) | Q(buyer=user)).distinct().count(),
        'active_chats': Chat.objects.filter(
            Q(seller=user) | Q(buyer=user),
            status='active'
        ).distinct().count(),
        'unread_messages': Message.objects.filter(
            chat__in=Chat.objects.filter(Q(seller=user) | Q(buyer=user)),
            sender__ne=user,
            is_read=False
        ).count(),
        'unread_notifications': ChatNotification.objects.filter(
            user=user,
            is_read=False
        ).count(),
        'blocked_users': ChatBlock.objects.filter(blocker=user).count(),
    }
    
    if user.is_vendor:
        stats.update({
            'buyer_chats': Chat.objects.filter(seller=user).count(),
            'total_messages_sent': Message.objects.filter(sender=user).count(),
        })
    elif user.is_client:
        stats.update({
            'seller_chats': Chat.objects.filter(buyer=user).count(),
            'total_messages_sent': Message.objects.filter(sender=user).count(),
        })
    
    return Response(stats)


# Views para Administradores
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_chat_stats_view(request):
    """Estatísticas de chat para administradores"""
    stats = {
        'total_chats': Chat.objects.count(),
        'active_chats': Chat.objects.filter(status='active').count(),
        'closed_chats': Chat.objects.filter(status='closed').count(),
        'archived_chats': Chat.objects.filter(status='archived').count(),
        'total_messages': Message.objects.count(),
        'total_blocks': ChatBlock.objects.count(),
        'chats_by_property_type': dict(
            Chat.objects.values('property__property_type')
            .annotate(count=Count('id'))
            .values_list('property__property_type', 'count')
        ),
        'most_active_properties': list(
            Chat.objects.values('property__title')
            .annotate(message_count=Count('messages'))
            .order_by('-message_count')[:10]
            .values('property__title', 'message_count')
        ),
    }
    
    return Response(stats)
