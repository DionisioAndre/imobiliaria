from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
import logging

from .models import Chat, Message, ChatNotification, ChatBlock

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_notifications():
    """
    Tarefa para limpar notificações antigas (mais de 30 dias)
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = ChatNotification.objects.filter(
            created_at__lt=cutoff_date,
            is_read=True
        ).delete()[0]
        
        logger.info(f"Removidas {deleted_count} notificações antigas")
        return f"Removidas {deleted_count} notificações"
        
    except Exception as e:
        logger.error(f"Erro ao limpar notificações antigas: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def cleanup_inactive_chats():
    """
    Tarefa para arquivar chats inativos (sem mensagens há 90 dias)
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=90)
        
        # Buscar chats ativos sem mensagens recentes
        inactive_chats = Chat.objects.filter(
            status='active',
            last_message_at__lt=cutoff_date
        )
        
        archived_count = 0
        for chat in inactive_chats:
            chat.archive_chat()
            archived_count += 1
            logger.info(f"Chat {chat.id} arquivado por inatividade")
        
        logger.info(f"Arquivados {archived_count} chats inativos")
        return f"Arquivados {archived_count} chats"
        
    except Exception as e:
        logger.error(f"Erro ao arquivar chats inativos: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def update_chat_statistics():
    """
    Tarefa para atualizar estatísticas de chat
    """
    try:
        stats = {}
        
        # Estatísticas gerais
        stats['total_chats'] = Chat.objects.count()
        stats['active_chats'] = Chat.objects.filter(status='active').count()
        stats['closed_chats'] = Chat.objects.filter(status='closed').count()
        stats['archived_chats'] = Chat.objects.filter(status='archived').count()
        
        # Estatísticas de mensagens
        stats['total_messages'] = Message.objects.count()
        stats['unread_messages'] = Message.objects.filter(is_read=False).count()
        
        # Chats por tipo de imóvel
        stats['chats_by_property_type'] = dict(
            Chat.objects.values('property__property_type')
            .annotate(count=Count('id'))
            .values_list('property__property_type', 'count')
        )
        
        # Chats por tipo de transação
        stats['chats_by_transaction_type'] = dict(
            Chat.objects.values('property__transaction_type')
            .annotate(count=Count('id'))
            .values_list('property__transaction_type', 'count')
        )
        
        # Mensagens por tipo
        stats['messages_by_type'] = dict(
            Message.objects.values('message_type')
            .annotate(count=Count('id'))
            .values_list('message_type', 'count')
        )
        
        # Usuários mais ativos
        stats['most_active_users'] = list(
            Message.objects.values('sender__full_name')
            .annotate(message_count=Count('id'))
            .order_by('-message_count')[:10]
            .values('sender__full_name', 'message_count')
        )
        
        # Imóveis com mais chats
        stats['most_chatted_properties'] = list(
            Chat.objects.values('property__title', 'property__id')
            .annotate(chat_count=Count('id'))
            .order_by('-chat_count')[:10]
            .values('property__title', 'property__id', 'chat_count')
        )
        
        # Bloqueios ativos
        stats['active_blocks'] = ChatBlock.objects.count()
        
        # Taxa de resposta (mensagens lidas vs não lidas)
        total_messages = Message.objects.count()
        unread_messages = Message.objects.filter(is_read=False).count()
        if total_messages > 0:
            stats['read_rate'] = ((total_messages - unread_messages) / total_messages) * 100
        else:
            stats['read_rate'] = 0
        
        # Chats iniciados por mês (últimos 12 meses)
        chats_by_month = []
        for i in range(12):
            month_start = (timezone.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
            month_end = month_start + timedelta(days=32)
            month_end = month_end.replace(day=1) - timedelta(days=1)
            
            count = Chat.objects.filter(
                created_at__gte=month_start,
                created_at__lte=month_end
            ).count()
            
            chats_by_month.append({
                'month': month_start.strftime('%Y-%m'),
                'count': count
            })
        
        stats['chats_by_month'] = chats_by_month
        
        logger.info("Estatísticas de chat atualizadas com sucesso")
        return stats
        
    except Exception as e:
        logger.error(f"Erro ao atualizar estatísticas de chat: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def notify_unread_messages():
    """
    Tarefa para notificar usuários sobre mensagens não lidas
    """
    try:
        # Buscar usuários com mensagens não lidas
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        notified_users = 0
        
        for user in User.objects.all():
            unread_count = Message.objects.filter(
                chat__in=Chat.objects.filter(Q(seller=user) | Q(buyer=user)),
                sender__ne=user,
                is_read=False
            ).count()
            
            if unread_count > 0:
                # Aqui você poderia implementar notificação por email, push, etc.
                logger.info(
                    f"Notificação: Usuário {user.full_name} tem {unread_count} "
                    f"mensagens não lidas"
                )
                notified_users += 1
        
        return f"Notificados {notified_users} usuários sobre mensagens não lidas"
        
    except Exception as e:
        logger.error(f"Erro ao notificar sobre mensagens não lidas: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def cleanup_old_message_files():
    """
    Tarefa para limpar arquivos de mensagens antigos
    """
    try:
        # Remover arquivos de mensagens com mais de 1 ano
        cutoff_date = timezone.now() - timedelta(days=365)
        
        old_messages = Message.objects.filter(
            message_type__in=['image', 'file'],
            created_at__lt=cutoff_date,
            file__isnull=False
        )
        
        cleaned_count = 0
        for message in old_messages:
            try:
                # Remover arquivo físico
                if message.file and message.file.storage.exists(message.file.name):
                    message.file.delete()
                
                # Limpar referência no banco
                message.file = None
                message.save(update_fields=['file'])
                cleaned_count += 1
                
            except Exception as file_error:
                logger.error(f"Erro ao remover arquivo da mensagem {message.id}: {str(file_error)}")
        
        logger.info(f"Limpos {cleaned_count} arquivos de mensagens antigos")
        return f"Limpos {cleaned_count} arquivos"
        
    except Exception as e:
        logger.error(f"Erro ao limpar arquivos de mensagens: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def analyze_chat_activity():
    """
    Tarefa para analisar padrões de atividade nos chats
    """
    try:
        analysis = {}
        
        # Horas mais ativas do dia
        hourly_activity = []
        for hour in range(24):
            count = Message.objects.filter(
                created_at__hour=hour
            ).count()
            hourly_activity.append({
                'hour': hour,
                'count': count
            })
        
        analysis['hourly_activity'] = hourly_activity
        
        # Dias mais ativos da semana
        daily_activity = []
        for day in range(7):
            count = Message.objects.filter(
                created_at__week_day=day + 1  # Django week_day: 1=Sunday, 7=Saturday
            ).count()
            daily_activity.append({
                'day': day,
                'count': count
            })
        
        analysis['daily_activity'] = daily_activity
        
        # Tempo médio de resposta (vendedor → comprador)
        response_times = []
        chats = Chat.objects.filter(status='active')
        
        for chat in chats:
            messages = chat.messages.order_by('created_at')
            for i in range(len(messages) - 1):
                current = messages[i]
                next_msg = messages[i + 1]
                
                # Verificar se são remetentes diferentes
                if current.sender != next_msg.sender:
                    response_time = (next_msg.created_at - current.created_at).total_seconds() / 60  # em minutos
                    response_times.append(response_time)
        
        if response_times:
            analysis['average_response_time_minutes'] = sum(response_times) / len(response_times)
            analysis['median_response_time_minutes'] = sorted(response_times)[len(response_times) // 2]
        else:
            analysis['average_response_time_minutes'] = 0
            analysis['median_response_time_minutes'] = 0
        
        # Taxa de conversão (chats que levam a contratos/vendas)
        # Isso seria implementado com base na lógica de negócio específica
        
        logger.info("Análise de atividade de chat concluída")
        return analysis
        
    except Exception as e:
        logger.error(f"Erro ao analisar atividade de chat: {str(e)}")
        return f"Erro: {str(e)}"
