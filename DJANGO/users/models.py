from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Modelo de usuário customizado para a plataforma imobiliária.
    Suporta três tipos de usuários: Cliente, Vendedor e Administrador.
    """
    
    class UserType(models.TextChoices):
        CLIENT = 'client', _('Cliente')
        VENDOR = 'vendor', _('Vendedor')
        ADMIN = 'admin', _('Administrador')
    
    # Campos básicos
    email = models.EmailField(_('Email'), unique=True)
    phone = models.CharField(_('Telefone'), max_length=20, blank=True, null=True)
    user_type = models.CharField(
        _('Tipo de Usuário'),
        max_length=10,
        choices=UserType.choices,
        default=UserType.CLIENT
    )
    
    # Campos de perfil
    bio = models.TextField(_('Biografia'), max_length=500, blank=True, null=True)
    profile_picture = models.ImageField(
        _('Foto de Perfil'),
        upload_to='profile_pictures/',
        blank=True,
        null=True
    )
    
    # Campos de endereço
    province = models.CharField(_('Província'), max_length=100, blank=True, null=True)
    municipality = models.CharField(_('Município'), max_length=100, blank=True, null=True)
    neighborhood = models.CharField(_('Bairro'), max_length=100, blank=True, null=True)
    
    # Campos de verificação
    is_verified = models.BooleanField(_('Verificado'), default=False)
    verification_document = models.FileField(
        _('Documento de Verificação'),
        upload_to='verification_documents/',
        blank=True,
        null=True
    )
    
    # Campos de timestamp
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    last_login_ip = models.GenericIPAddressField(_('Último IP'), blank=True, null=True)
    
    # Campos específicos para vendedores
    company_name = models.CharField(_('Nome da Empresa'), max_length=200, blank=True, null=True)
    company_document = models.FileField(
        _('Documento da Empresa'),
        upload_to='company_documents/',
        blank=True,
        null=True
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_vendor(self):
        return self.user_type == self.UserType.VENDOR
    
    @property
    def is_client(self):
        return self.user_type == self.UserType.CLIENT
    
    @property
    def is_admin_user(self):
        return self.user_type == self.UserType.ADMIN or self.is_superuser
    
    def get_properties_count(self):
        """Retorna o número de imóveis do usuário (se for vendedor)"""
        if self.is_vendor:
            return self.properties.count()
        return 0
    
    def can_create_property(self):
        """Verifica se o usuário pode criar imóveis"""
        return self.is_vendor and self.is_verified
    
    def can_view_documents(self):
        """Verifica se o usuário pode ver documentos de imóveis"""
        return self.is_admin_user


class UserVerification(models.Model):
    """
    Modelo para registrar tentativas de verificação de usuários
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_attempts',
        verbose_name=_('Usuário')
    )
    document_type = models.CharField(_('Tipo de Documento'), max_length=50)
    document_file = models.FileField(_('Arquivo do Documento'), upload_to='verification_attempts/')
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('approved', 'Aprovado'),
            ('rejected', 'Rejeitado'),
        ],
        default='pending'
    )
    rejection_reason = models.TextField(_('Motivo da Rejeição'), blank=True, null=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    reviewed_at = models.DateTimeField(_('Revisado em'), blank=True, null=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_verifications',
        verbose_name=_('Revisado por')
    )
    
    class Meta:
        verbose_name = _('Verificação de Usuário')
        verbose_name_plural = _('Verificações de Usuários')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Verificação de {self.user.full_name} - {self.status}"
