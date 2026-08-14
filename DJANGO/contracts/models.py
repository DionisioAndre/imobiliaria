from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class RentalContract(models.Model):
    """
    Modelo para contratos de arrendamento
    """
    
    class ContractType(models.TextChoices):
        RESIDENTIAL = 'residential', _('Residencial')
        COMMERCIAL = 'commercial', _('Comercial')
        SHORT_TERM = 'short_term', _('Curto Prazo')
    
    class ContractStatus(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        ACTIVE = 'active', _('Ativo')
        EXPIRED = 'expired', _('Expirado')
        TERMINATED = 'terminated', _('Terminado')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract_number = models.CharField(_('Número do Contrato'), max_length=50, unique=True)
    
    # Campos básicos - removendo ForeignKey temporariamente
    property_id = models.UUIDField(_('ID do Imóvel'))
    landlord_id = models.UUIDField(_('ID do Senhorio'))
    tenant_id = models.UUIDField(_('ID do Inquilino'))
    
    contract_type = models.CharField(
        _('Tipo de Contrato'),
        max_length=20,
        choices=ContractType.choices
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=ContractStatus.choices,
        default=ContractStatus.PENDING
    )
    
    # Datas
    start_date = models.DateField(_('Data de Início'))
    end_date = models.DateField(_('Data de Término'))
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    activated_at = models.DateTimeField(_('Ativado em'), blank=True, null=True)
    expired_at = models.DateTimeField(_('Expirado em'), blank=True, null=True)
    
    # Valores
    monthly_rent = models.DecimalField(_('Renda Mensal'), max_digits=12, decimal_places=2)
    deposit_amount = models.DecimalField(_('Caução'), max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Duração
    duration_months = models.PositiveIntegerField(_('Duração (meses)'))
    
    # Método de pagamento
    payment_method = models.CharField(_('Método de Pagamento'), max_length=50)
    payment_day = models.PositiveIntegerField(_('Dia de Pagamento'), default=1)
    
    class Meta:
        verbose_name = _('Contrato de Arrendamento')
        verbose_name_plural = _('Contratos de Arrendamento')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.contract_number


class RentalPayment(models.Model):
    """
    Modelo para pagamentos de contratos
    """
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        PAID = 'paid', _('Pago')
        OVERDUE = 'overdue', _('Em Atraso')
        PARTIAL = 'partial', _('Parcial')
    
    contract = models.ForeignKey(
        RentalContract,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Contrato')
    )
    
    payment_month = models.DateField(_('Mês de Pagamento'))
    amount = models.DecimalField(_('Valor'), max_digits=12, decimal_places=2)
    due_date = models.DateField(_('Data de Vencimento'))
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    
    # Datas
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    paid_date = models.DateField(_('Data de Pagamento'), blank=True, null=True)
    
    # Valores adicionais
    late_fee = models.DecimalField(_('Multa'), max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(_('Valor Pago'), max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Informações de pagamento
    transaction_reference = models.CharField(_('Referência da Transação'), max_length=100, blank=True, null=True)
    proof_file = models.FileField(_('Comprovante'), upload_to='payment_proofs/', blank=True, null=True)
    
    class Meta:
        verbose_name = _('Pagamento de Contrato')
        verbose_name_plural = _('Pagamentos de Contrato')
        ordering = ['-payment_month']
        unique_together = [['contract', 'payment_month']]
    
    def __str__(self):
        return f"Pagamento de {self.amount} AOA - {self.payment_month.strftime('%m/%Y')}"


class ContractRenewal(models.Model):
    """
    Modelo para renovações de contratos
    """
    
    class RenewalStatus(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        APPROVED = 'approved', _('Aprovado')
        REJECTED = 'rejected', _('Rejeitado')
    
    contract = models.ForeignKey(
        RentalContract,
        on_delete=models.CASCADE,
        related_name='renewals',
        verbose_name=_('Contrato')
    )
    
    new_end_date = models.DateField(_('Nova Data de Término'))
    new_monthly_rent = models.DecimalField(_('Nova Renda Mensal'), max_digits=12, decimal_places=2)
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=RenewalStatus.choices,
        default=RenewalStatus.PENDING
    )
    
    # Aprovações
    landlord_approved = models.BooleanField(_('Aprovado pelo Senhorio'), default=False)
    tenant_approved = models.BooleanField(_('Aprovado pelo Inquilino'), default=False)
    
    # Datas
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    landlord_approved_at = models.DateTimeField(_('Aprovado pelo Senhorio em'), blank=True, null=True)
    tenant_approved_at = models.DateTimeField(_('Aprovado pelo Inquilino em'), blank=True, null=True)
    
    # Motivos
    landlord_reason = models.TextField(_('Motivo do Senhorio'), blank=True, null=True)
    tenant_reason = models.TextField(_('Motivo do Inquilino'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Renovação de Contrato')
        verbose_name_plural = _('Renovações de Contrato')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Renovação do Contrato {self.contract.contract_number}"
