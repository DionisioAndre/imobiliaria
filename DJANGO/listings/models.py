from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Property(models.Model):
    """
    Modelo principal para imóveis na plataforma
    """
    
    class PropertyType(models.TextChoices):
        LUXURY_HOUSE = 'luxury_house', _('Casa de Luxo')
        LAND = 'land', _('Terreno')
        VILLA = 'villa', _('Vivenda')
        APARTMENT = 'apartment', _('Apartamento')
        SMALL_HOUSE = 'small_house', _('Casa Pequena')
        ROOM = 'room', _('Quarto em Bairro')
    
    class TransactionType(models.TextChoices):
        SALE = 'sale', _('Venda')
        RENT = 'rent', _('Arrendamento')
        SHORT_TERM_RENT = 'short_term_rent', _('Arrendamento Curto Duração')
    
    class PropertyStatus(models.TextChoices):
        ACTIVE = 'active', _('Ativo')
        INACTIVE = 'inactive', _('Inativo')
        SOLD = 'sold', _('Vendido')
        RENTED = 'rented', _('Arrendado')
        EXPIRED = 'expired', _('Expirado')
        PENDING = 'pending', _('Pendente')
    
    # Identificador único
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Informações básicas
    title = models.CharField(_('Título'), max_length=200)
    description = models.TextField(_('Descrição Detalhada'))
    property_type = models.CharField(
        _('Tipo de Imóvel'),
        max_length=20,
        choices=PropertyType.choices
    )
    transaction_type = models.CharField(
        _('Tipo de Transação'),
        max_length=20,
        choices=TransactionType.choices
    )
    
    # Preço
    price = models.DecimalField(
        _('Preço'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    price_negotiable = models.BooleanField(_('Preço Negociável'), default=False)
    
    # Localização
    province = models.CharField(_('Província'), max_length=100)
    municipality = models.CharField(_('Município'), max_length=100)
    neighborhood = models.CharField(_('Bairro'), max_length=100)
    street = models.CharField(_('Rua'), max_length=200, blank=True, null=True)
    reference_point = models.CharField(_('Ponto de Referência'), max_length=300, blank=True, null=True)
    latitude = models.DecimalField(
        _('Latitude'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.DecimalField(
        _('Longitude'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    
    # Características do imóvel
    bedrooms = models.PositiveIntegerField(_('Quartos'), default=1)
    bathrooms = models.PositiveIntegerField(_('Banheiros'), default=1)
    parking_spaces = models.PositiveIntegerField(_('Vagas de Estacionamento'), default=0)
    area_m2 = models.DecimalField(
        _('Área (m²)'),
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_area_m2 = models.DecimalField(
        _('Área Total (m²)'),
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    
    # Mobilidade e mobília
    is_furnished = models.BooleanField(_('Mobiliado'), default=False)
    furniture_description = models.TextField(
        _('Descrição dos Móveis'),
        blank=True,
        null=True
    )
    
    # Disponibilidade
    available_from = models.DateField(_('Disponível a partir de'), blank=True, null=True)
    available_until = models.DateField(_('Disponível até'), blank=True, null=True)
    
    # Status e controle
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=PropertyStatus.choices,
        default=PropertyStatus.PENDING
    )
    featured = models.BooleanField(_('Destaque'), default=False)
    views_count = models.PositiveIntegerField(_('Visualizações'), default=0)
    contact_count = models.PositiveIntegerField(_('Contatos'), default=0)
    
    # Relacionamentos
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='properties',
        verbose_name=_('Proprietário')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    published_at = models.DateTimeField(_('Publicado em'), blank=True, null=True)
    expires_at = models.DateTimeField(_('Expira em'), blank=True, null=True)
    
    # Observações adicionais
    additional_notes = models.TextField(_('Observações Adicionais'), blank=True, null=True)
    
    # Metadados para SEO
    slug = models.SlugField(_('Slug'), max_length=250, unique=True, blank=True)
    
    class Meta:
        verbose_name = _('Imóvel')
        verbose_name_plural = _('Imóveis')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['property_type', 'transaction_type']),
            models.Index(fields=['province', 'municipality']),
            models.Index(fields=['price']),
            models.Index(fields=['featured']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_property_type_display()} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_slug()
        
        # Validações críticas antes de salvar
        self.validate_critical_requirements()
        
        super().save(*args, **kwargs)
    
    def validate_critical_requirements(self):
        """
        Validações críticas para publicação de imóveis
        """
        errors = []
        
        # Verificar se está tentando publicar sem requisitos
        if self.status == self.PropertyStatus.ACTIVE:
            if not self.documents.exists():
                errors.append("Pelo menos 1 documento de titularidade é obrigatório")
            
            if self.images.count() < 4:
                errors.append("Mínimo de 4 imagens é obrigatório")
            
            if not self.videos.exists():
                errors.append("1 vídeo obrigatório")
            
            if not all([self.province, self.municipality, self.neighborhood]):
                errors.append("Descrição de localização obrigatória")
            
            if errors:
                self.status = self.PropertyStatus.PENDING
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Imóvel {self.id} não pode ser publicado: {', '.join(errors)}")
        
        return errors
    
    def generate_slug(self):
        """Gera um slug único para o imóvel"""
        import re
        from django.utils.text import slugify
        base_slug = slugify(f"{self.title}-{self.property_type}-{self.province}")
        slug = base_slug
        counter = 1
        while Property.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug
    
    @property
    def is_active(self):
        return self.status == self.PropertyStatus.ACTIVE
    
    @property
    def is_available(self):
        return self.status in [self.PropertyStatus.ACTIVE, self.PropertyStatus.PENDING]
    
    def is_sponsored(self):
        """Verifica se o imóvel tem patrocínio ativo"""
        return self.sponsorships.filter(status='active').exists()
    
    def can_be_contacted(self):
        """Verifica se o imóvel pode receber contatos"""
        return self.is_available and not self.is_sold_or_rented()
    
    def is_sold_or_rented(self):
        """Verifica se o imóvel foi vendido ou arrendado"""
        return self.status in [self.PropertyStatus.SOLD, self.PropertyStatus.RENTED]
    
    def increment_views(self):
        """Incrementa o contador de visualizações"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def increment_contacts(self):
        """Incrementa o contador de contatos"""
        self.contact_count += 1
        self.save(update_fields=['contact_count'])
    
    def get_main_image(self):
        """Retorna a imagem principal do imóvel"""
        main_image = self.images.filter(is_main=True).first()
        if main_image:
            return main_image.image
        return self.images.first().image if self.images.exists() else None
    
    def check_completion(self):
        """Verifica se o imóvel tem todos os campos obrigatórios preenchidos"""
        has_documents = self.documents.exists()
        has_images = self.images.count() >= 4
        has_video = self.videos.exists()
        has_location = all([
            self.province,
            self.municipality,
            self.neighborhood
        ])
        
        return has_documents and has_images and has_video and has_location
    
    def mark_as_expired(self):
        """Marca o imóvel como expirado"""
        if self.status == self.PropertyStatus.ACTIVE:
            self.status = self.PropertyStatus.EXPIRED
            self.save(update_fields=['status'])


class PropertyImage(models.Model):
    """
    Modelo para imagens de imóveis
    """
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Imóvel')
    )
    image = models.ImageField(_('Imagem'), upload_to='property_images/')
    is_main = models.BooleanField(_('Imagem Principal'), default=False)
    caption = models.CharField(_('Legenda'), max_length=200, blank=True, null=True)
    order = models.PositiveIntegerField(_('Ordem'), default=0)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Imagem do Imóvel')
        verbose_name_plural = _('Imagens dos Imóveis')
        ordering = ['order', 'created_at']
        unique_together = [['property', 'order']]
    
    def __str__(self):
        return f"Imagem de {self.property.title} - {'Principal' if self.is_main else f'Ordem {self.order}'}"
    
    def save(self, *args, **kwargs):
        # Se for a imagem principal, desmarcar as outras
        if self.is_main:
            PropertyImage.objects.filter(property=self.property, is_main=True).update(is_main=False)
        super().save(*args, **kwargs)


class PropertyVideo(models.Model):
    """
    Modelo para vídeos de imóveis
    """
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='videos',
        verbose_name=_('Imóvel')
    )
    video = models.FileField(_('Vídeo'), upload_to='property_videos/')
    thumbnail = models.ImageField(
        _('Thumbnail'),
        upload_to='video_thumbnails/',
        blank=True,
        null=True
    )
    title = models.CharField(_('Título'), max_length=200, blank=True, null=True)
    description = models.TextField(_('Descrição'), blank=True, null=True)
    duration = models.PositiveIntegerField(_('Duração (segundos)'), blank=True, null=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Vídeo do Imóvel')
        verbose_name_plural = _('Vídeos dos Imóveis')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Vídeo de {self.property.title}"


class PropertyDocument(models.Model):
    """
    Modelo para documentos de titularidade (privados - apenas administradores)
    """
    class DocumentType(models.TextChoices):
        DEED = 'deed', _('Escritura')
        REGISTRATION = 'registration', _('Registo')
        LICENSE = 'license', _('Licença')
        TAX = 'tax', _('Documento Fiscal')
        OTHER = 'other', _('Outro')
    
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('Imóvel')
    )
    document_type = models.CharField(
        _('Tipo de Documento'),
        max_length=20,
        choices=DocumentType.choices
    )
    document = models.FileField(_('Documento'), upload_to='property_documents/')
    title = models.CharField(_('Título'), max_length=200)
    description = models.TextField(_('Descrição'), blank=True, null=True)
    is_verified = models.BooleanField(_('Verificado'), default=False)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents',
        verbose_name=_('Verificado por')
    )
    verified_at = models.DateTimeField(_('Verificado em'), blank=True, null=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Documento do Imóvel')
        verbose_name_plural = _('Documentos dos Imóveis')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.property.title}"
    
    def mark_as_verified(self, verified_by_user):
        """Marca o documento como verificado"""
        from django.utils import timezone
        self.is_verified = True
        self.verified_by = verified_by_user
        self.verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'verified_by', 'verified_at'])


class PropertyView(models.Model):
    """
    Modelo para registrar visualizações de imóveis
    """
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='view_logs',
        verbose_name=_('Imóvel')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='property_views',
        verbose_name=_('Usuário')
    )
    ip_address = models.GenericIPAddressField(_('Endereço IP'), blank=True, null=True)
    user_agent = models.TextField(_('User Agent'), blank=True, null=True)
    viewed_at = models.DateTimeField(_('Visualizado em'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Visualização de Imóvel')
        verbose_name_plural = _('Visualizações de Imóveis')
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['property', 'viewed_at']),
            models.Index(fields=['user', 'viewed_at']),
        ]
    
    def __str__(self):
        user_info = f"por {self.user.full_name}" if self.user else f"do IP {self.ip_address}"
        return f"Visualização de {self.property.title} {user_info}"


class PropertyMessage(models.Model):
    """
    Modelo para mensagens de chat entre comprador e vendedor
    """
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='property_messages',
        verbose_name=_('Imóvel')
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='property_sent_messages',
        verbose_name=_('Remetente')
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='property_received_messages',
        verbose_name=_('Destinatário')
    )
    message = models.TextField(_('Mensagem'))
    is_read = models.BooleanField(_('Lido'), default=False)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Mensagem de Imóvel')
        verbose_name_plural = _('Mensagens de Imóveis')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property', 'created_at']),
            models.Index(fields=['sender', 'receiver', 'created_at']),
        ]
    
    def __str__(self):
        return f"Mensagem de {self.sender.full_name} para {self.receiver.full_name} sobre {self.property.title}"


class PropertyVisitRequest(models.Model):
    """
    Modelo para solicitações de visita a imóveis
    """
    class VisitStatus(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        CONFIRMED = 'confirmed', _('Confirmada')
        CANCELLED = 'cancelled', _('Cancelada')
        COMPLETED = 'completed', _('Realizada')
    
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='visit_requests',
        verbose_name=_('Imóvel')
    )
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='visit_requests',
        verbose_name=_('Comprador')
    )
    preferred_date = models.DateField(_('Data Preferida'))
    preferred_time = models.TimeField(_('Horário Preferido'))
    notes = models.TextField(_('Observações'), blank=True, null=True)
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=VisitStatus.choices,
        default=VisitStatus.PENDING
    )
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Solicitação de Visita')
        verbose_name_plural = _('Solicitações de Visita')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property', 'status', 'created_at']),
            models.Index(fields=['buyer', 'created_at']),
        ]
    
    def __str__(self):
        return f"Visita solicitada por {self.buyer.full_name} para {self.property.title}"