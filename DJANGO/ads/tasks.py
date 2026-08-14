from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from datetime import timedelta
import logging

from .models import Sponsorship, SponsorshipPayment

logger = logging.getLogger(__name__)


@shared_task
def expire_sponsorships():
    """
    Tarefa para expirar patrocínios automaticamente
    """
    try:
        now = timezone.now()
        expired_count = 0
        
        # Buscar patrocínios ativos que expiraram
        expired_sponsorships = Sponsorship.objects.filter(
            status='active',
            end_date__lt=now
        )
        
        for sponsorship in expired_sponsorships:
            sponsorship.expire()
            expired_count += 1
            logger.info(f"Patrocínio {sponsorship.id} expirado automaticamente")
        
        logger.info(f"Total de {expired_count} patrocínios expirados")
        return f"Expirados {expired_count} patrocínios"
        
    except Exception as e:
        logger.error(f"Erro ao expirar patrocínios: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def activate_pending_sponsorships():
    """
    Tarefa para ativar patrocínios pagos que devem começar
    """
    try:
        now = timezone.now()
        activated_count = 0
        
        # Buscar patrocínios pagos que devem começar agora
        pending_sponsorships = Sponsorship.objects.filter(
            status='pending',
            is_paid=True,
            start_date__lte=now
        )
        
        for sponsorship in pending_sponsorships:
            sponsorship.activate()
            activated_count += 1
            logger.info(f"Patrocínio {sponsorship.id} ativado automaticamente")
        
        logger.info(f"Total de {activated_count} patrocínios ativados")
        return f"Ativados {activated_count} patrocínios"
        
    except Exception as e:
        logger.error(f"Erro ao ativar patrocínios: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def update_sponsorship_statistics():
    """
    Tarefa para atualizar estatísticas de patrocínios
    """
    try:
        stats = {}
        
        # Estatísticas gerais
        stats['total_sponsorships'] = Sponsorship.objects.count()
        stats['active_sponsorships'] = Sponsorship.objects.filter(status='active').count()
        stats['pending_sponsorships'] = Sponsorship.objects.filter(status='pending').count()
        stats['expired_sponsorships'] = Sponsorship.objects.filter(status='expired').count()
        stats['cancelled_sponsorships'] = Sponsorship.objects.filter(status='cancelled').count()
        
        # Estatísticas por tipo
        stats['sponsorships_by_type'] = dict(
            Sponsorship.objects.values('sponsorship_type')
            .annotate(count=Count('id'))
            .values_list('sponsorship_type', 'count')
        )
        
        # Estatísticas por status
        stats['sponsorships_by_status'] = dict(
            Sponsorship.objects.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )
        
        # Receita total
        stats['total_revenue'] = SponsorshipPayment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Receita do mês atual
        current_month = timezone.now().replace(day=1)
        stats['monthly_revenue'] = SponsorshipPayment.objects.filter(
            status='completed',
            created_at__gte=current_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Estatísticas de pagamentos
        stats['total_payments'] = SponsorshipPayment.objects.count()
        stats['completed_payments'] = SponsorshipPayment.objects.filter(status='completed').count()
        stats['pending_payments'] = SponsorshipPayment.objects.filter(status='pending').count()
        stats['failed_payments'] = SponsorshipPayment.objects.filter(status='failed').count()
        
        # Patrocínios por prioridade
        stats['sponsorships_by_priority'] = dict(
            Sponsorship.objects.values('priority_level')
            .annotate(count=Count('id'))
            .values_list('priority_level', 'count')
        )
        
        # Valor médio dos patrocínios
        stats['average_sponsorship_price'] = Sponsorship.objects.aggregate(
            avg_price=Avg('price')
        )['avg_price'] or 0
        
        # Top patrocinadores
        stats['top_sponsors'] = list(
            Sponsorship.objects.values('sponsor__full_name')
            .annotate(total=Sum('price'))
            .order_by('-total')[:10]
            .values('sponsor__full_name', 'total')
        )
        
        # Receita por mês (últimos 12 meses)
        revenue_by_month = []
        for i in range(12):
            month_start = (timezone.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
            month_end = month_start + timedelta(days=32)
            month_end = month_end.replace(day=1) - timedelta(days=1)
            
            revenue = SponsorshipPayment.objects.filter(
                status='completed',
                processed_at__gte=month_start,
                processed_at__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            revenue_by_month.append({
                'month': month_start.strftime('%Y-%m'),
                'revenue': revenue
            })
        
        stats['revenue_by_month'] = revenue_by_month
        
        logger.info("Estatísticas de patrocínios atualizadas com sucesso")
        return stats
        
    except Exception as e:
        logger.error(f"Erro ao atualizar estatísticas de patrocínios: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def notify_sponsorship_expirations():
    """
    Tarefa para notificar sobre patrocínios que expirarão em breve
    """
    try:
        # Patrocínios que expirarão nos próximos 7 dias
        notification_days = 7
        expiration_date = timezone.now() + timedelta(days=notification_days)
        
        expiring_sponsorships = Sponsorship.objects.filter(
            status='active',
            end_date__lte=expiration_date,
            end_date__gt=timezone.now()
        )
        
        notified_count = 0
        for sponsorship in expiring_sponsorships:
            days_until_expiry = (sponsorship.end_date - timezone.now()).days
            
            # Aqui você poderia implementar notificação por email, etc.
            logger.info(
                f"Notificação: Patrocínio do imóvel '{sponsorship.property.title}' "
                f"expirará em {days_until_expiry} dias"
            )
            notified_count += 1
        
        return f"Notificados {notified_count} patrocínios que expirarão em breve"
        
    except Exception as e:
        logger.error(f"Erro ao notificar sobre expiração: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def notify_pending_payments():
    """
    Tarefa para notificar sobre pagamentos pendentes
    """
    try:
        # Pagamentos pendentes há mais de 24 horas
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        pending_payments = SponsorshipPayment.objects.filter(
            status='pending',
            created_at__lt=cutoff_time
        )
        
        notified_count = 0
        for payment in pending_payments:
            hours_pending = (timezone.now() - payment.created_at).total_seconds() / 3600
            
            # Aqui você poderia implementar notificação por email, etc.
            logger.info(
                f"Notificação: Pagamento de {payment.amount} AOA pendente há "
                f"{int(hours_pending)} horas (Patrocínio: {payment.sponsorship.property.title})"
            )
            notified_count += 1
        
        return f"Notificados {notified_count} pagamentos pendentes"
        
    except Exception as e:
        logger.error(f"Erro ao notificar sobre pagamentos pendentes: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def cleanup_old_payments():
    """
    Tarefa para limpar pagamentos antigos cancelados/falhados
    """
    try:
        # Remover pagamentos cancelados/falhados com mais de 90 dias
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count = SponsorshipPayment.objects.filter(
            status__in=['cancelled', 'failed'],
            created_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Removidos {deleted_count} pagamentos antigos")
        return f"Removidos {deleted_count} pagamentos"
        
    except Exception as e:
        logger.error(f"Erro ao limpar pagamentos antigos: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def update_property_sponsorship_boost():
    """
    Tarefa para atualizar o boost de imóveis patrocinados
    """
    try:
        updated_count = 0
        
        # Para cada patrocínio ativo, atualizar as estatísticas
        active_sponsorships = Sponsorship.objects.filter(
            status='active',
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )
        
        for sponsorship in active_sponsorships:
            property_obj = sponsorship.property
            
            # Atualizar estatísticas do patrocínio com base nas visualizações e contatos do imóvel
            # (isso já é feito quando o imóvel é visualizado/contactado)
            
            # Verificar se o patrocínio ainda está válido
            if not sponsorship.is_active:
                sponsorship.expire()
                updated_count += 1
        
        logger.info(f"Atualizados {updated_count} patrocínios")
        return f"Atualizados {updated_count} patrocínios"
        
    except Exception as e:
        logger.error(f"Erro ao atualizar boost de patrocínios: {str(e)}")
        return f"Erro: {str(e)}"
