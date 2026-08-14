from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from listings.models import Property
import uuid

User = get_user_model()


class Chat(models.Model):
    """
    Modelo para chats entre vendedor e comprador sobre um imóvel específico
    """
    
    class ChatStatus(models.TextChoices):
        ACTIVE = 'active', _('Ativo')
        CLOSED = 'closed', _('Fechado')
        ARCHIVED = 'archived', _('Arquivado')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='chats',
        verbose_name=_('Imóvel')
    )
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='seller_chats',
        verbose_name=_('Vendedor')
    )
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='buyer_chats',
        verbose_name=_('Comprador')
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=ChatStatus.choices,
        default=ChatStatus.ACTIVE
    )
    last_message_at = models.DateTimeField(_('Última Mensagem'), blank=True, null=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Chat')
        verbose_name_plural = _('Chats')
        ordering = ['-last_message_at', '-created_at']
        unique_together = [['property', 'buyer']]  # Um chat por imóvel por comprador
        indexes = [
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['property', 'status']),
            models.Index(fields=['last_message_at']),
        ]
    
    def __str__(self):
        return f"Chat sobre {self.property.title} - {self.buyer.full_name}"
    
    def other_user(self, current_user):
        """Retorna o outro usuário no chat (não o usuário atual)"""
        if current_user == self.seller:
            return self.buyer
        elif current_user == self.buyer:
            return self.seller
        return None
    
    def unread_count(self, user):
        """Retorna o número de mensagens não lidas para um usuário"""
        return self.messages.filter(
            sender__ne=user,
            is_read=False
        ).count()
    
    def get_last_message(self):
        """Retorna a última mensagem do chat"""
        return self.messages.order_by('-created_at').first()
    
    def mark_messages_as_read(self, user):
        """Marca todas as mensagens como lidas para um usuário"""
        self.messages.filter(
            sender__ne=user,
            is_read=False
        ).update(is_read=True)
    
    def can_user_participate(self, user):
        """Verifica se um usuário pode participar deste chat"""
        return user in [self.seller, self.buyer]
    
    def close_chat(self):
        """Fecha o chat"""
        self.status = self.ChatStatus.CLOSED
        self.save(update_fields=['status'])
    
    def archive_chat(self):
        """Arquiva o chat"""
        self.status = self.ChatStatus.ARCHIVED
        self.save(update_fields=['status'])


class Message(models.Model):
    """
    Modelo para mensagens dentro de um chat
    """
    
    class MessageType(models.TextChoices):
        TEXT = 'text', _('Texto')
        IMAGE = 'image', _('Imagem')
        FILE = 'file', _('Arquivo')
        LOCATION = 'location', _('Localização')
        CONTACT = 'contact', _('Contato')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Chat')
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_('Remetente')
    )
    message_type = models.CharField(
        _('Tipo de Mensagem'),
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT
    )
    content = models.TextField(_('Conteúdo'))
    file = models.FileField(
        _('Arquivo'),
        upload_to='chat_files/',
        blank=True,
        null=True
    )
    is_read = models.BooleanField(_('Lida'), default=False)
    read_at = models.DateTimeField(_('Lida em'), blank=True, null=True)
    created_at = models.DateTimeField(_('Criada em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizada em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Mensagem')
        verbose_name_plural = _('Mensagens')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"Mensagem de {self.sender.full_name} em {self.chat.property.title}"
    
    def mark_as_read(self):
        """Marca a mensagem como lida"""
        if not self.is_read:
            self.is_read = True
            self.read_at = models.timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
            
            # Atualizar o último message_at do chat
            self.chat.last_message_at = self.created_at
            self.chat.save(update_fields=['last_message_at'])
    
    def can_user_view(self, user):
        """Verifica se um usuário pode ver esta mensagem"""
        return self.chat.can_user_participate(user)
    
    def can_user_edit(self, user):
        """Verifica se um usuário pode editar esta mensagem"""
        return self.sender == user and self.created_at > models.timezone.now() - models.timedelta(minutes=15)
    
    def can_user_delete(self, user):
        """Verifica se um usuário pode deletar esta mensagem"""
        return self.sender == user and self.created_at > models.timezone.now() - models.timedelta(hours=1)


class ChatNotification(models.Model):
    """
    Modelo para notificações de chat
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_notifications',
        verbose_name=_('Usuário')
    )
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Chat')
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Mensagem')
    )
    is_read = models.BooleanField(_('Lida'), default=False)
    created_at = models.DateTimeField(_('Criada em'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Notificação de Chat')
        verbose_name_plural = _('Notificações de Chat')
        ordering = ['-created_at']
        unique_together = [['user', 'message']]
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['chat', 'created_at']),
        ]
    
    def __str__(self):
        return f"Notificação para {self.user.full_name} sobre {self.chat.property.title}"
    
    def mark_as_read(self):
        """Marca a notificação como lida"""
        self.is_read = True
        self.save(update_fields=['is_read'])


class ChatBlock(models.Model):
    """
    Modelo para bloqueios de usuários em chats
    """
    blocker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blocked_users',
        verbose_name=_('Bloqueador')
    )
    blocked = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blocked_by_users',
        verbose_name=_('Bloqueado')
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='chat_blocks',
        verbose_name=_('Imóvel'),
        blank=True,
        null=True
    )
    reason = models.TextField(_('Motivo'), blank=True, null=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Bloqueio de Chat')
        verbose_name_plural = _('Bloqueios de Chat')
        ordering = ['-created_at']
        unique_together = [['blocker', 'blocked', 'property']]
        indexes = [
            models.Index(fields=['blocker', 'created_at']),
            models.Index(fields=['blocked', 'created_at']),
        ]
    
    def __str__(self):
        property_info = f" - {self.property.title}" if self.property else ""
        return f"{self.blocker.full_name} bloqueou {self.blocked.full_name}{property_info}"
    
    @classmethod
    def is_blocked(cls, user1, user2, property=None):
        """Verifica se um usuário bloqueou o outro"""
        if property:
            return cls.objects.filter(
                blocker=user1,
                blocked=user2,
                property=property
            ).exists()
        return cls.objects.filter(
            blocker=user1,
            blocked=user2
        ).exists()
    
    @classmethod
    def can_message(cls, sender, receiver, property=None):
        """Verifica se o remetente pode enviar mensagem para o receptor"""
        return not cls.is_blocked(sender, receiver, property) and not cls.is_blocked(receiver, sender, property)
