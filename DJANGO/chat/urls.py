from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Chats
    path('', views.ChatListView.as_view(), name='chat-list'),
    path('<uuid:id>/', views.ChatDetailView.as_view(), name='chat-detail'),
    path('create/', views.ChatCreateView.as_view(), name='chat-create'),
    
    # Ações de chat
    path('<uuid:id>/close/', views.close_chat_view, name='chat-close'),
    path('<uuid:id>/archive/', views.archive_chat_view, name='chat-archive'),
    
    # Mensagens
    path('<uuid:chat_id>/messages/', views.MessageListView.as_view(), name='message-list'),
    path('<uuid:chat_id>/messages/create/', views.MessageCreateView.as_view(), name='message-create'),
    path('messages/<uuid:id>/', views.MessageDetailView.as_view(), name='message-detail'),
    
    # Notificações
    path('notifications/', views.ChatNotificationListView.as_view(), name='notification-list'),
    path('notifications/mark-all-read/', views.mark_notifications_as_read_view, name='notifications-mark-all-read'),
    path('notifications/<uuid:notification_id>/read/', views.mark_notification_as_read_view, name='notification-mark-read'),
    
    # Bloqueios
    path('blocks/', views.ChatBlockListView.as_view(), name='block-list'),
    path('blocks/<uuid:id>/', views.ChatBlockDetailView.as_view(), name='block-detail'),
    
    # Estatísticas
    path('stats/', views.chat_stats_view, name='chat-stats'),
    path('admin/stats/', views.admin_chat_stats_view, name='admin-chat-stats'),
]
