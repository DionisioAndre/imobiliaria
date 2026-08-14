from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Chat, Message, ChatNotification, ChatBlock


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = [
        'property_title', 'seller', 'buyer', 'status',
        'last_message_at', 'created_at'
    ]
    list_filter = [
        'status', 'created_at', 'last_message_at'
    ]
    search_fields = [
        'property__title', 'seller__username', 'seller__email',
        'buyer__username', 'buyer__email'
    ]
    ordering = ['-last_message_at', '-created_at']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'last_message_at'
    ]
    
    def property_title(self, obj):
        return obj.property.title
    property_title.short_description = _('Imóvel')
    
    actions = ['close_chats', 'archive_chats']
    
    def close_chats(self, request, queryset):
        count = queryset.filter(status='active').update(status='closed')
        self.message_user(
            request,
            f'{count} chats fechados com sucesso.'
        )
    close_chats.short_description = _('Fechar chats selecionados')
    
    def archive_chats(self, request, queryset):
        count = queryset.update(status='archived')
        self.message_user(
            request,
            f'{count} chats arquivados com sucesso.'
        )
    archive_chats.short_description = _('Arquivar chats selecionados')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'chat_property', 'sender', 'message_type', 'content_preview',
        'is_read', 'created_at'
    ]
    list_filter = [
        'message_type', 'is_read', 'created_at'
    ]
    search_fields = [
        'chat__property__title', 'sender__username', 'sender__email',
        'content'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'chat', 'sender', 'created_at', 'updated_at'
    ]
    
    def chat_property(self, obj):
        return obj.chat.property.title
    chat_property.short_description = _('Imóvel')
    
    def content_preview(self, obj):
        max_length = 50
        if len(obj.content) > max_length:
            return obj.content[:max_length] + '...'
        return obj.content
    content_preview.short_description = _('Conteúdo')
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        count = queryset.filter(is_read=False).update(is_read=True)
        self.message_user(
            request,
            f'{count} mensagens marcadas como lidas.'
        )
    mark_as_read.short_description = _('Marcar como lidas')
    
    def mark_as_unread(self, request, queryset):
        count = queryset.filter(is_read=True).update(is_read=False)
        self.message_user(
            request,
            f'{count} mensagens marcadas como não lidas.'
        )
    mark_as_unread.short_description = _('Marcar como não lidas')


@admin.register(ChatNotification)
class ChatNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'chat_property', 'message_preview', 'is_read',
        'created_at'
    ]
    list_filter = [
        'is_read', 'created_at'
    ]
    search_fields = [
        'user__username', 'user__email', 'chat__property__title',
        'message__content'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'user', 'chat', 'message', 'created_at'
    ]
    
    def chat_property(self, obj):
        return obj.chat.property.title
    chat_property.short_description = _('Imóvel')
    
    def message_preview(self, obj):
        max_length = 50
        if len(obj.message.content) > max_length:
            return obj.message.content[:max_length] + '...'
        return obj.message.content
    message_preview.short_description = _('Mensagem')
    
    actions = ['mark_as_read', 'delete_read_notifications']
    
    def mark_as_read(self, request, queryset):
        count = queryset.filter(is_read=False).update(is_read=True)
        self.message_user(
            request,
            f'{count} notificações marcadas como lidas.'
        )
    mark_as_read.short_description = _('Marcar como lidas')
    
    def delete_read_notifications(self, request, queryset):
        count = queryset.filter(is_read=True).delete()[0]
        self.message_user(
            request,
            f'{count} notificações lidas removidas.'
        )
    delete_read_notifications.short_description = _('Remover notificações lidas')


@admin.register(ChatBlock)
class ChatBlockAdmin(admin.ModelAdmin):
    list_display = [
        'blocker', 'blocked', 'property_title', 'reason', 'created_at'
    ]
    list_filter = [
        'created_at'
    ]
    search_fields = [
        'blocker__username', 'blocker__email', 'blocked__username',
        'blocked__email', 'property__title', 'reason'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'blocker', 'created_at'
    ]
    
    def property_title(self, obj):
        if obj.property:
            return obj.property.title
        return _('Todos os imóveis')
    property_title.short_description = _('Imóvel')
    
    actions = ['remove_blocks']
    
    def remove_blocks(self, request, queryset):
        count = queryset.delete()[0]
        self.message_user(
            request,
            f'{count} bloqueios removidos com sucesso.'
        )
    remove_blocks.short_description = _('Remover bloqueios selecionados')
