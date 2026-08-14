from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
import uuid

# Importações corrigidas para estabelecer o relacionamento
from listings.models import Property

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
    
    # Relacionamentos usando ForeignKey para tirar proveito do ORM
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="sponsorships",
        verbose_name=_('Imóvel')
    )
    sponsor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sponsorships",
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
    
    # Datas
    start_date = models.DateTimeField(_('Data de Início'))
    end_date = models.DateTimeField(_('Data de Término'))
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    activated_at = models.DateTimeField(_('Ativado em'), blank=True, null=True)
    expired_at = models.DateTimeField(_('Expirado em'), blank=True, null=True)
    
    # Valores
    price = models.DecimalField(_('Preço'), max_digits=12, decimal_places=2)
    
    class Meta:
        verbose_name = _('Patrocínio')
        verbose_name_plural = _('Patrocínios')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Patrocínio {self.get_sponsorship_type_display()} - Imóvel: {self.property.id}"


class SponsorshipPackage(models.Model):
    """
    Modelo para pacotes de patrocínio
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
    price = models.DecimalField(_('Preço'), max_digits=12, decimal_places=2)
    duration_days = models.PositiveIntegerField(_('Duração (dias)'))
    priority_level = models.PositiveIntegerField(_('Nível de Prioridade'), default=1)
    description = models.TextField(_('Descrição'))
    features = models.TextField(_('Características'))
    is_active = models.BooleanField(_('Ativo'), default=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Pacote de Patrocínio')
        verbose_name_plural = _('Pacotes de Patrocínio')
        ordering = ['priority_level', 'price']
    
    def __str__(self):
        return self.name


class SponsorshipPayment(models.Model):
    """
    Modelo para pagamentos de patrocínios
    """
    
    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'bank_transfer', _('Transferência Bancária')
        MOBILE_MONEY = 'mobile_money', _('Dinheiro Móvel')
        CREDIT_CARD = 'credit_card', _('Cartão de Crédito')
        CASH = 'cash', _('Dinheiro')
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        PROCESSING = 'processing', _('Processando')
        COMPLETED = 'completed', _('Concluído')
        FAILED = 'failed', _('Falhou')
        CANCELLED = 'cancelled', _('Cancelado')
        REFUNDED = 'refunded', _('Reembolsado')
    
    sponsorship = models.ForeignKey(
        Sponsorship,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Patrocínio')
    )
    
    amount = models.DecimalField(_('Valor'), max_digits=12, decimal_places=2)
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
    
    # Datas
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    processed_at = models.DateTimeField(_('Processado em'), blank=True, null=True)
    
    # Informações de pagamento
    transaction_id = models.CharField(_('ID da Transação'), max_length=100, blank=True, null=True)
    reference_number = models.CharField(_('Número de Referência'), max_length=100, blank=True, null=True)
    proof_file = models.FileField(_('Comprovante'), upload_to='payment_proofs/', blank=True, null=True)
    
    class Meta:
        verbose_name = _('Pagamento de Patrocínio')
        verbose_name_plural = _('Pagamentos de Patrocínio')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Pagamento de {self.amount} AOA - {self.get_status_display()}"