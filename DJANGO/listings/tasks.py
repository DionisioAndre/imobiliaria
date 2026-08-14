from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from datetime import timedelta
import logging

from .models import Property, PropertyView

logger = logging.getLogger(__name__)


@shared_task
def expire_properties():
    """
    Tarefa para expirar imóveis automaticamente
    """
    try:
        now = timezone.now()
        expired_count = 0
        
        # Buscar imóveis ativos que expiraram
        expired_properties = Property.objects.filter(
            status='active',
            expires_at__lte=now
        )
        
        for property_obj in expired_properties:
            property_obj.mark_as_expired()
            expired_count += 1
            logger.info(f"Imóvel {property_obj.id} expirado automaticamente")
        
        logger.info(f"Total de {expired_count} imóveis expirados")
        return f"Expirados {expired_count} imóveis"
        
    except Exception as e:
        logger.error(f"Erro ao expirar imóveis: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def update_property_statistics():
    """
    Tarefa para atualizar estatísticas dos imóveis
    """
    try:
        stats = {}
        
        # Estatísticas gerais
        stats['total_properties'] = Property.objects.count()
        stats['active_properties'] = Property.objects.filter(status='active').count()
        stats['pending_properties'] = Property.objects.filter(status='pending').count()
        stats['sold_properties'] = Property.objects.filter(status='sold').count()
        stats['rented_properties'] = Property.objects.filter(status='rented').count()
        stats['expired_properties'] = Property.objects.filter(status='expired').count()
        
        # Estatísticas por tipo
        stats['properties_by_type'] = dict(
            Property.objects.values('property_type')
            .annotate(count=Count('id'))
            .values_list('property_type', 'count')
        )
        
        # Estatísticas por transação
        stats['properties_by_transaction'] = dict(
            Property.objects.values('transaction_type')
            .annotate(count=Count('id'))
            .values_list('transaction_type', 'count')
        )
        
        # Estatísticas por província
        stats['properties_by_province'] = dict(
            Property.objects.values('province')
            .annotate(count=Count('id'))
            .values_list('province', 'count')
        )
        
        # Média de preços
        stats['average_price'] = Property.objects.aggregate(
            avg_price=Avg('price')
        )['avg_price'] or 0
        
        # Total de visualizações e contatos
        stats['total_views'] = Property.objects.aggregate(
            total=Sum('views_count')
        )['total'] or 0
        
        stats['total_contacts'] = Property.objects.aggregate(
            total=Sum('contact_count')
        )['total'] or 0
        
        # Imóveis mais visualizados (últimos 7 dias)
        week_ago = timezone.now() - timedelta(days=7)
        top_viewed = list(
            PropertyView.objects.filter(
                viewed_at__gte=week_ago
            ).values('property__title', 'property__id')
            .annotate(views=Count('id'))
            .order_by('-views')[:10]
        )
        stats['top_viewed_week'] = top_viewed
        
        # Imóveis com mais contatos (últimos 30 dias)
        month_ago = timezone.now() - timedelta(days=30)
        top_contacted = list(
            Property.objects.filter(
                updated_at__gte=month_ago
            ).values('title', 'id')
            .annotate(contacts=Sum('contact_count'))
            .order_by('-contacts')[:10]
        )
        stats['top_contacted_month'] = top_contacted
        
        logger.info("Estatísticas dos imóveis atualizadas com sucesso")
        return stats
        
    except Exception as e:
        logger.error(f"Erro ao atualizar estatísticas: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def cleanup_old_view_logs():
    """
    Tarefa para limpar logs de visualização antigos (mais de 90 dias)
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count = PropertyView.objects.filter(
            viewed_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Removidos {deleted_count} logs de visualização antigos")
        return f"Removidos {deleted_count} logs"
        
    except Exception as e:
        logger.error(f"Erro ao limpar logs de visualização: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def notify_expiring_properties():
    """
    Tarefa para notificar proprietários sobre imóveis que expirarão em breve
    """
    try:
        # Imóveis que expirarão nos próximos 7 dias
        soon_to_expire = timezone.now() + timedelta(days=7)
        properties = Property.objects.filter(
            status='active',
            expires_at__lte=soon_to_expire,
            expires_at__gt=timezone.now()
        )
        
        notified_count = 0
        for property_obj in properties:
            # Aqui você poderia implementar notificação por email, push, etc.
            # Por enquanto, apenas log
            logger.info(
                f"Notificação: Imóvel {property_obj.title} expirará em "
                f"{(property_obj.expires_at - timezone.now()).days} dias"
            )
            notified_count += 1
        
        return f"Notificados {notified_count} proprietários sobre expiração"
        
    except Exception as e:
        logger.error(f"Erro ao notificar sobre expiração: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def update_sponsored_properties_ranking():
    """
    Tarefa para atualizar ranking de imóveis patrocinados
    """
    try:
        from ads.models import Sponsorship
        
        # Atualizar estatísticas de patrocínios ativos
        active_sponsorships = Sponsorship.objects.filter(
            status='active',
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )
        
        updated_count = 0
        for sponsorship in active_sponsorships:
            # Calcular boost baseado em views e contatos
            property_obj = sponsorship.property
            
            # Atualizar estatísticas do patrocínio
            sponsorship.update_statistics(
                views=property_obj.views_count,
                contacts=property_obj.contact_count
            )
            updated_count += 1
        
        logger.info(f"Atualizadas estatísticas de {updated_count} patrocínios ativos")
        return f"Atualizados {updated_count} patrocínios"
        
    except Exception as e:
        logger.error(f"Erro ao atualizar ranking de patrocinados: {str(e)}")
        return f"Erro: {str(e)}"
