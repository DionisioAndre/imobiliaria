from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from listings.models import Property
import uuid

User = get_user_model()


class Sponsorship(models.Model):
    """
    Modelo para patrocínios de imóveis
    """
    
    class SponsorshipType(models.TextChoices):
        BASIC = 'basic', _('Básico')
        PREMIUM = 'premium', _('Premium')
        ULTIMATE = 'ultimate', _('Ultimate')
        FEATURED = 'featured', _('Destaque')
    
    class SponsorshipStatus(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        ACTIVE = 'active', _('Ativo')
        EXPIRED = 'expired', _('Expirado')
        CANCELLED = 'cancelled', _('Cancelado')
        SUSPENDED = 'suspended', _('Suspenso')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='sponsorships',
        verbose_name=_('Imóvel')
    )
    sponsor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sponsorships',
        verbose_name=_('Patrocinador')
    )
    sponsorship_type = models.CharField(
        _('Tipo de Patrocínio'),
        max_length=20,
        choices=SponsorshipType.choices
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=SponsorshipStatus.choices,
        default=SponsorshipStatus.PENDING
    )
    
    # Duração e datas
    start_date = models.DateTimeField(_('Data de Início'))
    end_date = models.DateTimeField(_('Data de Fim'))
    duration_days = models.PositiveIntegerField(_('Duração (dias)'))
    
    # Preço e pagamento
    price = models.DecimalField(
        _('Preço'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    is_paid = models.BooleanField(_('Pago'), default=False)
    paid_at = models.DateTimeField(_('Pago em'), blank=True, null=True)
    
    # Benefícios
    priority_level = models.PositiveIntegerField(_('Nível de Prioridade'), default=1)
    show_in_featured = models.BooleanField(_('Mostrar em Destaques'), default=True)
    show_in_recommendations = models.BooleanField(_('Mostrar em Recomendações'), default=True)
    boost_factor = models.DecimalField(
        _('Fator de Impulsão'),
        max_digits=3,
        decimal_places=1,
        default=1.0,
        validators=[MinValueValidator(1.0)]
    )
    
    # Estatísticas
    views_boosted = models.PositiveIntegerField(_('Visualizações Impulsionadas'), default=0)
    contacts_boosted = models.PositiveIntegerField(_('Contatos Impulsionados'), default=0)
    click_through_rate = models.DecimalField(
        _('Taxa de Cliques'),
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    activated_at = models.DateTimeField(_('Ativado em'), blank=True, null=True)
    expired_at = models.DateTimeField(_('Expirado em'), blank=True, null=True)
    
    # Observações
    notes = models.TextField(_('Observações'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Patrocínio')
        verbose_name_plural = _('Patrocínios')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['property', 'status']),
            models.Index(fields=['sponsor', 'status']),
            models.Index(fields=['sponsorship_type', 'status']),
            models.Index(fields=['priority_level']),
        ]
    
    def __str__(self):
        return f"Patrocínio {self.get_sponsorship_type_display()} - {self.property.title}"
    
    @property
    def is_active(self):
        """Verifica se o patrocínio está ativo"""
        from django.utils import timezone
        return (
            self.status == self.SponsorshipStatus.ACTIVE and
            self.start_date <= timezone.now() <= self.end_date
        )
    
    @property
    def days_remaining(self):
        """Retorna o número de dias restantes"""
        from django.utils import timezone
        if self.is_active:
            return (self.end_date - timezone.now()).days
        return 0
    
    @property
    def total_days(self):
        """Retorna o número total de dias do patrocínio"""
        return (self.end_date - self.start_date).days + 1
    
    def activate(self):
        """Ativa o patrocínio"""
        from django.utils import timezone
        if self.status == self.SponsorshipStatus.PENDING and self.is_paid:
            self.status = self.SponsorshipStatus.ACTIVE
            self.activated_at = timezone.now()
            self.save(update_fields=['status', 'activated_at'])
    
    def expire(self):
        """Expira o patrocínio"""
        from django.utils import timezone
        if self.status == self.SponsorshipStatus.ACTIVE:
            self.status = self.SponsorshipStatus.EXPIRED
            self.expired_at = timezone.now()
            self.save(update_fields=['status', 'expired_at'])
    
    def cancel(self):
        """Cancela o patrocínio"""
        self.status = self.SponsorshipStatus.CANCELLED
        self.save(update_fields=['status'])
    
    def suspend(self):
        """Suspende o patrocínio"""
        self.status = self.SponsorshipStatus.SUSPENDED
        self.save(update_fields=['status'])
    
    def mark_as_paid(self):
        """Marca o patrocínio como pago"""
        from django.utils import timezone
        self.is_paid = True
        self.paid_at = timezone.now()
        self.save(update_fields=['is_paid', 'paid_at'])
    
    def update_statistics(self, views=0, contacts=0):
        """Atualiza as estatísticas do patrocínio"""
        self.views_boosted += views
        self.contacts_boosted += contacts
        
        # Calcular taxa de cliques
        if self.views_boosted > 0:
            self.click_through_rate = (self.contacts_boosted / self.views_boosted) * 100
        
        self.save(update_fields=['views_boosted', 'contacts_boosted', 'click_through_rate'])


class SponsorshipPackage(models.Model):
    """
    Modelo para pacotes de patrocínio predefinidos
    """
    
    class PackageType(models.TextChoices):
        BASIC = 'basic', _('Básico')
        PREMIUM = 'premium', _('Premium')
        ULTIMATE = 'ultimate', _('Ultimate')
        FEATURED = 'featured', _('Destaque')
    
    name = models.CharField(_('Nome'), max_length=100)
    package_type = models.CharField(
        _('Tipo de Pacote'),
        max_length=20,
        choices=PackageType.choices,
        unique=True
    )
    description = models.TextField(_('Descrição'))
    price = models.DecimalField(
        _('Preço'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    duration_days = models.PositiveIntegerField(_('Duração (dias)'))
    priority_level = models.PositiveIntegerField(_('Nível de Prioridade'), default=1)
    show_in_featured = models.BooleanField(_('Mostrar em Destaques'), default=True)
    show_in_recommendations = models.BooleanField(_('Mostrar em Recomendações'), default=True)
    boost_factor = models.DecimalField(
        _('Fator de Impulsão'),
        max_digits=3,
        decimal_places=1,
        default=1.0,
        validators=[MinValueValidator(1.0)]
    )
    
    # Benefícios adicionais
    max_images_allowed = models.PositiveIntegerField(_('Máximo de Imagens'), default=10)
    max_videos_allowed = models.PositiveIntegerField(_('Máximo de Vídeos'), default=2)
    support_priority = models.BooleanField(_('Suporte Prioritário'), default=False)
    analytics_access = models.BooleanField(_('Acesso a Analytics'), default=False)
    
    is_active = models.BooleanField(_('Ativo'), default=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Pacote de Patrocínio')
        verbose_name_plural = _('Pacotes de Patrocínio')
        ordering = ['priority_level', 'price']
    
    def __str__(self):
        return f"{self.name} - {self.price} AOA por {self.duration_days} dias"
    
    def get_features(self):
        """Retorna uma lista de benefícios do pacote"""
        features = []
        if self.show_in_featured:
            features.append('Destaque na listagem')
        if self.show_in_recommendations:
            features.append('Aparece em recomendações')
        if self.max_images_allowed > 4:
            features.append(f'Até {self.max_images_allowed} imagens')
        if self.max_videos_allowed > 1:
            features.append(f'Até {self.max_videos_allowed} vídeos')
        if self.support_priority:
            features.append('Suporte prioritário')
        if self.analytics_access:
            features.append('Acesso a analytics')
        return features


class SponsorshipPayment(models.Model):
    """
    Modelo para pagamentos de patrocínios
    """
    
    class PaymentMethod(models.TextChoices):
        REFERENCE = 'reference', _('Referência')
        MULTICAIXA = 'multicaixa', _('Multicaixa Express')
        BANK_TRANSFER = 'bank_transfer', _('Transferência Bancária')
        CASH = 'cash', _('Dinheiro')
        OTHER = 'other', _('Outro')
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        PROCESSING = 'processing', _('Processando')
        COMPLETED = 'completed', _('Concluído')
        FAILED = 'failed', _('Falhou')
        REFUNDED = 'refunded', _('Reembolsado')
        CANCELLED = 'cancelled', _('Cancelado')
    
    sponsorship = models.ForeignKey(
        Sponsorship,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Patrocínio')
    )
    payment_method = models.CharField(
        _('Método de Pagamento'),
        max_length=20,
        choices=PaymentMethod.choices
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    amount = models.DecimalField(
        _('Valor'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    transaction_id = models.CharField(_('ID da Transação'), max_length=100, blank=True, null=True)
    reference_number = models.CharField(_('Número de Referência'), max_length=100, blank=True, null=True)
    proof_file = models.FileField(
        _('Comprovante'),
        upload_to='payment_proofs/',
        blank=True,
        null=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    processed_at = models.DateTimeField(_('Processado em'), blank=True, null=True)
    
    # Observações
    notes = models.TextField(_('Observações'), blank=True, null=True)
    rejection_reason = models.TextField(_('Motivo da Rejeição'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Pagamento de Patrocínio')
        verbose_name_plural = _('Pagamentos de Patrocínios')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['sponsorship', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['reference_number']),
        ]
    
    def __str__(self):
        return f"Pagamento de {self.amount} AOA para {self.sponsorship.property.title}"
    
    def mark_as_completed(self):
        """Marca o pagamento como concluído"""
        from django.utils import timezone
        self.status = self.PaymentStatus.COMPLETED
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
        
        # Ativar o patrocínio
        self.sponsorship.mark_as_paid()
        self.sponsorship.activate()
    
    def mark_as_failed(self, reason=None):
        """Marca o pagamento como falhado"""
        from django.utils import timezone
        self.status = self.PaymentStatus.FAILED
        self.processed_at = timezone.now()
        if reason:
            self.rejection_reason = reason
        self.save(update_fields=['status', 'processed_at', 'rejection_reason'])
    
    def mark_as_refunded(self):
        """Marca o pagamento como reembolsado"""
        from django.utils import timezone
        self.status = self.PaymentStatus.REFUNDED
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
        
        # Cancelar o patrocínio se estiver ativo
        if self.sponsorship.is_active:
            self.sponsorship.cancel()
