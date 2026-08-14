from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from listings.models import Property
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
        VACATION = 'vacation', _('Férias')
        EVENT = 'event', _('Evento')
    
    class ContractStatus(models.TextChoices):
        DRAFT = 'draft', _('Rascunho')
        PENDING = 'pending', _('Pendente')
        ACTIVE = 'active', _('Ativo')
        EXPIRED = 'expired', _('Expirado')
        TERMINATED = 'terminated', _('Terminado')
        CANCELLED = 'cancelled', _('Cancelado')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='rental_contracts',
        verbose_name=_('Imóvel')
    )
    landlord = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='landlord_contracts',
        verbose_name=_('Senhorio')
    )
    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tenant_contracts',
        verbose_name=_('Inquilino')
    )
    
    # Informações básicas do contrato
    contract_number = models.CharField(_('Número do Contrato'), max_length=50, unique=True)
    contract_type = models.CharField(
        _('Tipo de Contrato'),
        max_length=20,
        choices=ContractType.choices
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=ContractStatus.choices,
        default=ContractStatus.DRAFT
    )
    
    # Datas e duração
    start_date = models.DateField(_('Data de Início'))
    end_date = models.DateField(_('Data de Término'))
    duration_months = models.PositiveIntegerField(_('Duração (meses)'))
    
    # Valores financeiros
    monthly_rent = models.DecimalField(
        _('Renda Mensal'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    security_deposit = models.DecimalField(
        _('Caução'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    maintenance_fee = models.DecimalField(
        _('Taxa de Manutenção'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Condições de pagamento
    payment_day = models.PositiveIntegerField(_('Dia de Pagamento'), default=1)
    payment_method = models.CharField(
        _('Método de Pagamento'),
        max_length=50,
        choices=[
            ('bank_transfer', 'Transferência Bancária'),
            ('cash', 'Dinheiro'),
            ('multicaixa', 'Multicaixa'),
            ('check', 'Cheque'),
        ],
        default='bank_transfer'
    )
    
    # Termos e condições
    terms = models.TextField(_('Termos e Condições'))
    special_conditions = models.TextField(_('Condições Especiais'), blank=True, null=True)
    renewal_terms = models.TextField(_('Termos de Renovação'), blank=True, null=True)
    
    # Documentos
    contract_file = models.FileField(
        _('Arquivo do Contrato'),
        upload_to='contracts/',
        blank=True,
        null=True
    )
    tenant_id_document = models.FileField(
        _('Documento de Identificação do Inquilino'),
        upload_to='tenant_documents/',
        blank=True,
        null=True
    )
    landlord_id_document = models.FileField(
        _('Documento de Identificação do Senhorio'),
        upload_to='landlord_documents/',
        blank=True,
        null=True
    )
    
    # Assinaturas
    landlord_signature = models.TextField(_('Assinatura do Senhorio'), blank=True, null=True)
    tenant_signature = models.TextField(_('Assinatura do Inquilino'), blank=True, null=True)
    landlord_signed_at = models.DateTimeField(_('Assinado pelo Senhorio em'), blank=True, null=True)
    tenant_signed_at = models.DateTimeField(_('Assinado pelo Inquilino em'), blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    activated_at = models.DateTimeField(_('Ativado em'), blank=True, null=True)
    expired_at = models.DateTimeField(_('Expirado em'), blank=True, null=True)
    
    # Observações
    notes = models.TextField(_('Observações'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Contrato de Arrendamento')
        verbose_name_plural = _('Contratos de Arrendamento')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['property', 'status']),
            models.Index(fields=['landlord', 'status']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['contract_number']),
        ]
    
    def __str__(self):
        return f"Contrato {self.contract_number} - {self.property.title}"
    
    def save(self, *args, **kwargs):
        if not self.contract_number:
            self.contract_number = self.generate_contract_number()
        if self.start_date and self.end_date:
            self.duration_months = (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month)
        super().save(*args, **kwargs)
    
    def generate_contract_number(self):
        """Gera um número único de contrato"""
        import datetime
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        count = RentalContract.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).count() + 1
        return f"AR{year}{month:02d}{count:04d}"
    
    @property
    def is_active(self):
        """Verifica se o contrato está ativo"""
        from django.utils import timezone
        today = timezone.now().date()
        return (
            self.status == self.ContractStatus.ACTIVE and
            self.start_date <= today <= self.end_date
        )
    
    @property
    def days_until_expiry(self):
        """Retorna o número de dias até o término do contrato"""
        from django.utils import timezone
        today = timezone.now().date()
        if self.end_date >= today:
            return (self.end_date - today).days
        return 0
    
    @property
    def total_rent_amount(self):
        """Retorna o valor total da renda do contrato"""
        return self.monthly_rent * self.duration_months
    
    @property
    def is_signed_by_both(self):
        """Verifica se o contrato foi assinado por ambas as partes"""
        return self.landlord_signature and self.tenant_signature
    
    def can_be_activated(self):
        """Verifica se o contrato pode ser ativado"""
        return (
            self.is_signed_by_both and
            self.status == self.ContractStatus.PENDING and
            self.contract_file and
            self.tenant_id_document and
            self.landlord_id_document
        )
    
    def activate(self):
        """Ativa o contrato"""
        from django.utils import timezone
        if self.can_be_activated():
            self.status = self.ContractStatus.ACTIVE
            self.activated_at = timezone.now()
            self.save(update_fields=['status', 'activated_at'])
            
            # Atualizar status do imóvel
            self.property.status = Property.PropertyStatus.RENTED
            self.property.save(update_fields=['status'])
    
    def expire(self):
        """Expira o contrato"""
        from django.utils import timezone
        if self.status == self.ContractStatus.ACTIVE:
            self.status = self.ContractStatus.EXPIRED
            self.expired_at = timezone.now()
            self.save(update_fields=['status', 'expired_at'])
            
            # Retornar status do imóvel para ativo
            self.property.status = Property.PropertyStatus.ACTIVE
            self.property.save(update_fields=['status'])
    
    def terminate(self, reason=None):
        """Termina o contrato"""
        from django.utils import timezone
        self.status = self.ContractStatus.TERMINATED
        self.expired_at = timezone.now()
        if reason:
            self.notes = f"Contrato terminado: {reason}"
        self.save(update_fields=['status', 'expired_at', 'notes'])
        
        # Retornar status do imóvel para ativo
        self.property.status = Property.PropertyStatus.ACTIVE
        self.property.save(update_fields=['status'])
    
    def sign_by_landlord(self, signature):
        """Assina o contrato pelo senhorio"""
        from django.utils import timezone
        self.landlord_signature = signature
        self.landlord_signed_at = timezone.now()
        self.save(update_fields=['landlord_signature', 'landlord_signed_at'])
    
    def sign_by_tenant(self, signature):
        """Assina o contrato pelo inquilino"""
        from django.utils import timezone
        self.tenant_signature = signature
        self.tenant_signed_at = timezone.now()
        self.save(update_fields=['tenant_signature', 'tenant_signed_at'])


class RentalPayment(models.Model):
    """
    Modelo para pagamentos de rendas
    """
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        PAID = 'paid', _('Pago')
        OVERDUE = 'overdue', _('Em Atraso')
        PARTIAL = 'partial', _('Parcial')
        CANCELLED = 'cancelled', _('Cancelado')
    
    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'bank_transfer', _('Transferência Bancária')
        CASH = 'cash', _('Dinheiro')
        MULTICAIXA = 'multicaixa', _('Multicaixa')
        CHECK = 'check', _('Cheque')
    
    contract = models.ForeignKey(
        RentalContract,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Contrato')
    )
    payment_month = models.DateField(_('Mês de Pagamento'))
    amount = models.DecimalField(
        _('Valor'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    payment_method = models.CharField(
        _('Método de Pagamento'),
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True,
        null=True
    )
    
    # Datas
    due_date = models.DateField(_('Data de Vencimento'))
    paid_date = models.DateField(_('Data de Pagamento'), blank=True, null=True)
    
    # Prova de pagamento
    proof_file = models.FileField(
        _('Comprovante de Pagamento'),
        upload_to='payment_proofs/',
        blank=True,
        null=True
    )
    transaction_reference = models.CharField(_('Referência da Transação'), max_length=100, blank=True, null=True)
    
    # Observações
    notes = models.TextField(_('Observações'), blank=True, null=True)
    late_fee = models.DecimalField(
        _('Multa por Atraso'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Pagamento de Renda')
        verbose_name_plural = _('Pagamentos de Rendas')
        ordering = ['-payment_month']
        unique_together = [['contract', 'payment_month']]
        indexes = [
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['payment_month']),
        ]
    
    def __str__(self):
        return f"Pagamento de {self.amount} AOA - {self.payment_month.strftime('%m/%Y')}"
    
    @property
    def is_overdue(self):
        """Verifica se o pagamento está em atraso"""
        from django.utils import timezone
        return (
            self.status == self.PaymentStatus.PENDING and
            self.due_date < timezone.now().date()
        )
    
    @property
    def days_overdue(self):
        """Retorna o número de dias de atraso"""
        from django.utils import timezone
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0
    
    @property
    def total_amount(self):
        """Retorna o valor total incluindo multas"""
        return self.amount + self.late_fee
    
    def mark_as_paid(self, payment_method=None, proof_file=None, reference=None):
        """Marca o pagamento como pago"""
        from django.utils import timezone
        self.status = self.PaymentStatus.PAID
        self.paid_date = timezone.now().date()
        if payment_method:
            self.payment_method = payment_method
        if proof_file:
            self.proof_file = proof_file
        if reference:
            self.transaction_reference = reference
        self.save(update_fields=['status', 'paid_date', 'payment_method', 'proof_file', 'transaction_reference'])
    
    def mark_as_overdue(self):
        """Marca o pagamento como em atraso"""
        self.status = self.PaymentStatus.OVERDUE
        self.save(update_fields=['status'])
    
    def calculate_late_fee(self, daily_rate=0.02):
        """Calcula a multa por atraso (2% por dia padrão)"""
        if self.is_overdue:
            days_overdue = self.days_overdue
            self.late_fee = self.amount * daily_rate * days_overdue
            self.save(update_fields=['late_fee'])


class ContractRenewal(models.Model):
    """
    Modelo para renovações de contrato
    """
    
    class RenewalStatus(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        APPROVED = 'approved', _('Aprovado')
        REJECTED = 'rejected', _('Rejeitado')
        CANCELLED = 'cancelled', _('Cancelado')
    
    contract = models.ForeignKey(
        RentalContract,
        on_delete=models.CASCADE,
        related_name='renewals',
        verbose_name=_('Contrato')
    )
    new_end_date = models.DateField(_('Nova Data de Término'))
    new_monthly_rent = models.DecimalField(
        _('Nova Renda Mensal'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=RenewalStatus.choices,
        default=RenewalStatus.PENDING
    )
    
    # Justificativas
    landlord_reason = models.TextField(_('Motivo do Senhorio'), blank=True, null=True)
    tenant_reason = models.TextField(_('Motivo do Inquilino'), blank=True, null=True)
    
    # Aprovações
    landlord_approved = models.BooleanField(_('Aprovado pelo Senhorio'), default=False)
    tenant_approved = models.BooleanField(_('Aprovado pelo Inquilino'), default=False)
    landlord_approved_at = models.DateTimeField(_('Aprovado pelo Senhorio em'), blank=True, null=True)
    tenant_approved_at = models.DateTimeField(_('Aprovado pelo Inquilino em'), blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizada em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Renovação de Contrato')
        verbose_name_plural = _('Renovações de Contratos')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Renovação do Contrato {self.contract.contract_number}"
    
    @property
    def can_be_approved(self):
        """Verifica se a renovação pode ser aprovada"""
        return self.landlord_approved and self.tenant_approved
    
    def approve_by_landlord(self):
        """Aprova a renovação pelo senhorio"""
        from django.utils import timezone
        self.landlord_approved = True
        self.landlord_approved_at = timezone.now()
        self.save(update_fields=['landlord_approved', 'landlord_approved_at'])
        
        if self.can_be_approved:
            self.approve_renewal()
    
    def approve_by_tenant(self):
        """Aprova a renovação pelo inquilino"""
        from django.utils import timezone
        self.tenant_approved = True
        self.tenant_approved_at = timezone.now()
        self.save(update_fields=['tenant_approved', 'tenant_approved_at'])
        
        if self.can_be_approved:
            self.approve_renewal()
    
    def approve_renewal(self):
        """Aprova a renovação e atualiza o contrato"""
        from django.utils import timezone
        self.status = self.RenewalStatus.APPROVED
        
        # Atualizar contrato
        contract = self.contract
        contract.end_date = self.new_end_date
        contract.monthly_rent = self.new_monthly_rent
        contract.save(update_fields=['end_date', 'monthly_rent'])
        
        self.save(update_fields=['status'])
