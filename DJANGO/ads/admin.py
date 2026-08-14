from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Sponsorship, SponsorshipPackage, SponsorshipPayment


@admin.register(SponsorshipPackage)
class SponsorshipPackageAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'package_type', 'price', 'duration_days',
        'priority_level', 'is_active', 'created_at'
    ]
    list_filter = [
        'package_type', 'priority_level', 'is_active', 'created_at'
    ]
    search_fields = [
        'name', 'description', 'package_type'
    ]
    ordering = ['priority_level', 'price']
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['activate_packages', 'deactivate_packages']
    
    def activate_packages(self, request, queryset):
        count = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(
            request,
            f'{count} pacotes ativados com sucesso.'
        )
    activate_packages.short_description = _('Ativar pacotes selecionados')
    
    def deactivate_packages(self, request, queryset):
        count = queryset.filter(is_active=True).update(is_active=False)
        self.message_user(
            request,
            f'{count} pacotes desativados com sucesso.'
        )
    deactivate_packages.short_description = _('Desativar pacotes selecionados')


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = [
        'property_id', 'sponsor_id', 'sponsorship_type', 'status',
        'start_date', 'end_date', 'price', 'created_at'
    ]
    list_filter = [
        'sponsorship_type', 'status',
        'start_date', 'end_date', 'created_at'
    ]
    search_fields = [
        'property_id', 'sponsor_id'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'activated_at', 'expired_at'
    ]
    
    def property_title(self, obj):
        return obj.property.title
    property_title.short_description = _('Imóvel')
    
    actions = [
        'activate_sponsorships', 'expire_sponsorships', 'cancel_sponsorships',
        'mark_as_paid'
    ]
    
    def activate_sponsorships(self, request, queryset):
        count = 0
        for sponsorship in queryset.filter(status='pending', is_paid=True):
            sponsorship.activate()
            count += 1
        self.message_user(
            request,
            f'{count} patrocínios ativados com sucesso.'
        )
    activate_sponsorships.short_description = _('Ativar patrocínios selecionados')
    
    def expire_sponsorships(self, request, queryset):
        count = 0
        for sponsorship in queryset.filter(status='active'):
            sponsorship.expire()
            count += 1
        self.message_user(
            request,
            f'{count} patrocínios expirados com sucesso.'
        )
    expire_sponsorships.short_description = _('Expirar patrocínios selecionados')
    
    def cancel_sponsorships(self, request, queryset):
        count = 0
        for sponsorship in queryset.filter(status__in=['pending', 'active']):
            sponsorship.cancel()
            count += 1
        self.message_user(
            request,
            f'{count} patrocínios cancelados com sucesso.'
        )
    cancel_sponsorships.short_description = _('Cancelar patrocínios selecionados')
    
    def mark_as_paid(self, request, queryset):
        count = queryset.filter(is_paid=False).update(is_paid=True)
        self.message_user(
            request,
            f'{count} patrocínios marcados como pagos.'
        )
    mark_as_paid.short_description = _('Marcar como pagos')


@admin.register(SponsorshipPayment)
class SponsorshipPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'sponsorship_property', 'payment_method', 'status', 'amount',
        'transaction_id', 'created_at', 'processed_at'
    ]
    list_filter = [
        'payment_method', 'status', 'created_at', 'processed_at'
    ]
    search_fields = [
        'sponsorship__property__title', 'sponsorship__sponsor__username',
        'sponsorship__sponsor__email', 'transaction_id', 'reference_number'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'sponsorship', 'amount', 'created_at', 'updated_at'
    ]
    
    def sponsorship_property(self, obj):
        return obj.sponsorship.property.title
    sponsorship_property.short_description = _('Imóvel')
    
    actions = [
        'approve_payments', 'reject_payments', 'mark_as_completed',
        'mark_as_failed'
    ]
    
    def approve_payments(self, request, queryset):
        count = 0
        for payment in queryset.filter(status='pending'):
            payment.mark_as_completed()
            count += 1
        self.message_user(
            request,
            f'{count} pagamentos aprovados com sucesso.'
        )
    approve_payments.short_description = _('Aprovar pagamentos selecionados')
    
    def reject_payments(self, request, queryset):
        count = 0
        for payment in queryset.filter(status='pending'):
            payment.mark_as_failed()
            count += 1
        self.message_user(
            request,
            f'{count} pagamentos rejeitados com sucesso.'
        )
    reject_payments.short_description = _('Rejeitar pagamentos selecionados')
    
    def mark_as_completed(self, request, queryset):
        count = queryset.filter(status__in=['pending', 'processing']).update(
            status='completed',
            processed_at=timezone.now()
        )
        self.message_user(
            request,
            f'{count} pagamentos marcados como concluídos.'
        )
    mark_as_completed.short_description = _('Marcar como concluídos')
    
    def mark_as_failed(self, request, queryset):
        count = queryset.filter(status__in=['pending', 'processing']).update(
            status='failed',
            processed_at=timezone.now()
        )
        self.message_user(
            request,
            f'{count} pagamentos marcados como falhados.'
        )
    mark_as_failed.short_description = _('Marcar como falhados')
