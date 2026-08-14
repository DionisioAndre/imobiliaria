from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import timedelta
import logging

from .models import RentalContract, RentalPayment

logger = logging.getLogger(__name__)


@shared_task
def update_contract_statuses():
    """
    Tarefa para atualizar status de contratos automaticamente
    """
    try:
        now = timezone.now()
        today = now.date()
        updated_count = 0
        
        # Expirar contratos ativos que chegaram ao término
        expired_contracts = RentalContract.objects.filter(
            status='active',
            end_date__lt=today
        )
        
        for contract in expired_contracts:
            contract.expire()
            updated_count += 1
            logger.info(f"Contrato {contract.contract_number} expirado automaticamente")
        
        # Ativar contratos pendentes que devem começar hoje
        starting_contracts = RentalContract.objects.filter(
            status='pending',
            start_date__lte=today,
            end_date__gte=today
        ).filter(
            # Verificar se está pronto para ativação
            Q(contract_file__isnull=False) &
            Q(tenant_id_document__isnull=False) &
            Q(landlord_id_document__isnull=False) &
            Q(landlord_signature__isnull=False) &
            Q(tenant_signature__isnull=False)
        )
        
        for contract in starting_contracts:
            contract.activate()
            updated_count += 1
            logger.info(f"Contrato {contract.contract_number} ativado automaticamente")
        
        logger.info(f"Total de {updated_count} contratos atualizados")
        return f"Atualizados {updated_count} contratos"
        
    except Exception as e:
        logger.error(f"Erro ao atualizar status de contratos: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def calculate_overdue_payments():
    """
    Tarefa para calcular multas de pagamentos em atraso
    """
    try:
        today = timezone.now().date()
        updated_count = 0
        
        # Buscar pagamentos pendentes que estão em atraso
        overdue_payments = RentalPayment.objects.filter(
            status='pending',
            due_date__lt=today
        )
        
        for payment in overdue_payments:
            payment.mark_as_overdue()
            payment.calculate_late_fee()
            updated_count += 1
            logger.info(f"Pagamento {payment.id} marcado como em atraso")
        
        logger.info(f"Total de {updated_count} pagamentos marcados como em atraso")
        return f"Processados {updated_count} pagamentos em atraso"
        
    except Exception as e:
        logger.error(f"Erro ao calcular multas: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def generate_monthly_payments():
    """
    Tarefa para gerar pagamentos mensais de contratos ativos
    """
    try:
        today = timezone.now().date()
        current_month = today.replace(day=1)
        generated_count = 0
        
        # Buscar contratos ativos
        active_contracts = RentalContract.objects.filter(status='active')
        
        for contract in active_contracts:
            # Verificar se já existe pagamento para este mês
            existing_payment = RentalPayment.objects.filter(
                contract=contract,
                payment_month=current_month
            ).first()
            
            if not existing_payment:
                # Criar pagamento para o mês atual
                due_day = contract.payment_day or 1
                if due_day > today.day:
                    # Vence este mês
                    due_date = today.replace(day=due_day)
                else:
                    # Vence no próximo mês
                    next_month = today.replace(day=28) + timedelta(days=4)  # Garantir próximo mês
                    due_date = next_month.replace(day=min(due_day, 28))
                
                RentalPayment.objects.create(
                    contract=contract,
                    payment_month=current_month,
                    amount=contract.monthly_rent,
                    due_date=due_date,
                    status='pending'
                )
                
                generated_count += 1
                logger.info(f"Gerado pagamento para contrato {contract.contract_number}")
        
        logger.info(f"Gerados {generated_count} pagamentos mensais")
        return f"Gerados {generated_count} pagamentos"
        
    except Exception as e:
        logger.error(f"Erro ao gerar pagamentos mensais: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def notify_upcoming_payments():
    """
    Tarefa para notificar sobre pagamentos que vencerão em breve
    """
    try:
        # Pagamentos que vencerão nos próximos 5 dias
        notification_days = 5
        upcoming_date = timezone.now().date() + timedelta(days=notification_days)
        
        upcoming_payments = RentalPayment.objects.filter(
            status='pending',
            due_date__lte=upcoming_date,
            due_date__gt=timezone.now().date()
        )
        
        notified_count = 0
        for payment in upcoming_payments:
            # Aqui você poderia implementar notificação por email, SMS, etc.
            days_until_due = (payment.due_date - timezone.now().date()).days
            
            logger.info(
                f"Notificação: Pagamento de {payment.amount} AOA vencerá em "
                f"{days_until_due} dias (Contrato: {payment.contract.contract_number})"
            )
            notified_count += 1
        
        return f"Notificados {notified_count} pagamentos que vencerão em breve"
        
    except Exception as e:
        logger.error(f"Erro ao notificar sobre pagamentos: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def notify_contract_expirations():
    """
    Tarefa para notificar sobre contratos que expirarão em breve
    """
    try:
        # Contratos que expirarão nos próximos 30 dias
        notification_days = 30
        expiration_date = timezone.now().date() + timedelta(days=notification_days)
        
        expiring_contracts = RentalContract.objects.filter(
            status='active',
            end_date__lte=expiration_date,
            end_date__gt=timezone.now().date()
        )
        
        notified_count = 0
        for contract in expiring_contracts:
            days_until_expiry = (contract.end_date - timezone.now().date()).days
            
            # Notificar senhorio e inquilino
            logger.info(
                f"Notificação: Contrato {contract.contract_number} expirará em "
                f"{days_until_expiry} dias"
            )
            notified_count += 1
        
        return f"Notificados {notified_count} contratos que expirarão em breve"
        
    except Exception as e:
        logger.error(f"Erro ao notificar sobre expiração: {str(e)}")
        return f"Erro: {str(e)}"


@shared_task
def update_contract_statistics():
    """
    Tarefa para atualizar estatísticas de contratos
    """
    try:
        stats = {}
        
        # Estatísticas gerais
        stats['total_contracts'] = RentalContract.objects.count()
        stats['active_contracts'] = RentalContract.objects.filter(status='active').count()
        stats['pending_contracts'] = RentalContract.objects.filter(status='pending').count()
        stats['expired_contracts'] = RentalContract.objects.filter(status='expired').count()
        stats['terminated_contracts'] = RentalContract.objects.filter(status='terminated').count()
        
        # Estatísticas por tipo
        stats['contracts_by_type'] = dict(
            RentalContract.objects.values('contract_type')
            .annotate(count=Count('id'))
            .values_list('contract_type', 'count')
        )
        
        # Estatísticas por status
        stats['contracts_by_status'] = dict(
            RentalContract.objects.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )
        
        # Valor total mensal de contratos ativos
        stats['total_monthly_revenue'] = RentalContract.objects.filter(
            status='active'
        ).aggregate(total=Sum('monthly_rent'))['total'] or 0
        
        # Estatísticas de pagamentos
        stats['total_payments'] = RentalPayment.objects.count()
        stats['paid_payments'] = RentalPayment.objects.filter(status='paid').count()
        stats['pending_payments'] = RentalPayment.objects.filter(status='pending').count()
        stats['overdue_payments'] = RentalPayment.objects.filter(status='overdue').count()
        
        # Valor total recebido
        stats['total_revenue'] = RentalPayment.objects.filter(
            status='paid'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Contratos por província
        stats['contracts_by_province'] = dict(
            RentalContract.objects.values('property__province')
            .annotate(count=Count('id'))
            .values_list('property__province', 'count')
        )
        
        logger.info("Estatísticas de contratos atualizadas com sucesso")
        return stats
        
    except Exception as e:
        logger.error(f"Erro ao atualizar estatísticas de contratos: {str(e)}")
        return f"Erro: {str(e)}"
