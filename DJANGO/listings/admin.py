from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Property, PropertyImage, PropertyVideo, PropertyDocument, PropertyView


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'property_type', 'transaction_type', 'price',
        'province', 'municipality', 'status', 'owner', 'created_at'
    ]
    list_filter = [
        'property_type', 'transaction_type', 'status', 'province',
        'is_furnished', 'featured', 'created_at'
    ]
    search_fields = [
        'title', 'description', 'owner__username', 'owner__email',
        'neighborhood', 'street'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'slug', 'views_count', 'contact_count', 'created_at',
        'updated_at', 'published_at', 'expires_at'
    ]
    
    fieldsets = (
        (None, {
            'fields': (
                'title', 'description', 'property_type', 'transaction_type',
                'price', 'price_negotiable'
            )
        }),
        (_('Localização'), {
            'fields': (
                'province', 'municipality', 'neighborhood', 'street',
                'reference_point', 'latitude', 'longitude'
            )
        }),
        (_('Características'), {
            'fields': (
                'bedrooms', 'bathrooms', 'parking_spaces', 'area_m2',
                'total_area_m2', 'is_furnished', 'furniture_description'
            )
        }),
        (_('Disponibilidade'), {
            'fields': (
                'available_from', 'available_until'
            )
        }),
        (_('Status e Controle'), {
            'fields': (
                'status', 'featured', 'additional_notes'
            )
        }),
        (_('Metadados'), {
            'fields': (
                'id', 'slug', 'owner', 'views_count', 'contact_count',
                'created_at', 'updated_at', 'published_at', 'expires_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_properties', 'deactivate_properties', 'mark_as_sold', 'mark_as_rented']
    
    def activate_properties(self, request, queryset):
        count = 0
        for property_obj in queryset.filter(status='pending'):
            if property_obj.check_completion():
                property_obj.status = Property.PropertyStatus.ACTIVE
                property_obj.save(update_fields=['status'])
                count += 1
        self.message_user(
            request,
            f'{count} imóveis ativados com sucesso.'
        )
    activate_properties.short_description = _('Ativar imóveis selecionados')
    
    def deactivate_properties(self, request, queryset):
        count = queryset.filter(status='active').update(
            status=Property.PropertyStatus.INACTIVE
        )
        self.message_user(
            request,
            f'{count} imóveis desativados com sucesso.'
        )
    deactivate_properties.short_description = _('Desativar imóveis selecionados')
    
    def mark_as_sold(self, request, queryset):
        count = queryset.update(status=Property.PropertyStatus.SOLD)
        self.message_user(
            request,
            f'{count} imóveis marcados como vendidos.'
        )
    mark_as_sold.short_description = _('Marcar como vendido')
    
    def mark_as_rented(self, request, queryset):
        count = queryset.update(status=Property.PropertyStatus.RENTED)
        self.message_user(
            request,
            f'{count} imóveis marcados como arrendados.'
        )
    mark_as_rented.short_description = _('Marcar como arrendado')


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = [
        'property_title', 'is_main', 'caption', 'order', 'created_at'
    ]
    list_filter = ['is_main', 'created_at']
    search_fields = [
        'property__title', 'caption'
    ]
    ordering = ['property', 'order', 'created_at']
    readonly_fields = ['created_at']
    
    def property_title(self, obj):
        return obj.property.title
    property_title.short_description = _('Imóvel')
    
    actions = ['set_as_main']
    
    def set_as_main(self, request, queryset):
        property_images = {}
        for image in queryset:
            if image.property_id not in property_images:
                property_images[image.property_id] = image
        
        count = 0
        for image in property_images.values():
            PropertyImage.objects.filter(property=image.property).update(is_main=False)
            image.is_main = True
            image.save(update_fields=['is_main'])
            count += 1
        
        self.message_user(
            request,
            f'{count} imagens definidas como principais.'
        )
    set_as_main.short_description = _('Definir como imagem principal')


@admin.register(PropertyVideo)
class PropertyVideoAdmin(admin.ModelAdmin):
    list_display = [
        'property_title', 'title', 'duration', 'created_at'
    ]
    search_fields = [
        'property__title', 'title', 'description'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def property_title(self, obj):
        return obj.property.title
    property_title.short_description = _('Imóvel')


@admin.register(PropertyDocument)
class PropertyDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'property_title', 'document_type', 'title', 'is_verified',
        'verified_by', 'created_at'
    ]
    list_filter = [
        'document_type', 'is_verified', 'created_at'
    ]
    search_fields = [
        'property__title', 'title', 'description'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def property_title(self, obj):
        return obj.property.title
    property_title.short_description = _('Imóvel')
    
    actions = ['verify_documents', 'unverify_documents']
    
    def verify_documents(self, request, queryset):
        count = queryset.filter(is_verified=False).update(
            is_verified=True,
            verified_by=request.user,
            verified_at=timezone.now()
        )
        self.message_user(
            request,
            f'{count} documentos verificados com sucesso.'
        )
    verify_documents.short_description = _('Verificar documentos selecionados')
    
    def unverify_documents(self, request, queryset):
        count = queryset.update(
            is_verified=False,
            verified_by=None,
            verified_at=None
        )
        self.message_user(
            request,
            f'{count} documentos desverificados com sucesso.'
        )
    unverify_documents.short_description = _('Desverificar documentos selecionados')


@admin.register(PropertyView)
class PropertyViewAdmin(admin.ModelAdmin):
    list_display = [
        'property_title', 'user', 'ip_address', 'viewed_at'
    ]
    list_filter = ['viewed_at']
    search_fields = [
        'property__title', 'user__username', 'user__email', 'ip_address'
    ]
    ordering = ['-viewed_at']
    readonly_fields = ['property', 'user', 'ip_address', 'user_agent', 'viewed_at']
    
    def property_title(self, obj):
        return obj.property.title
    property_title.short_description = _('Imóvel')
