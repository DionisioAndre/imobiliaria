from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import RentalContract, RentalPayment, ContractRenewal


@admin.register(RentalContract)
class RentalContractAdmin(admin.ModelAdmin):
    list_display = [
        'contract_number', 'property_id', 'landlord_id', 'tenant_id',
        'contract_type', 'status', 'start_date', 'end_date',
        'monthly_rent', 'created_at'
    ]
    list_filter = [
        'contract_type', 'status', 'start_date', 'end_date',
        'created_at'
    ]
    search_fields = [
        'contract_number', 'property_id', 'landlord_id', 'tenant_id'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'contract_number', 'duration_months',
        'created_at', 'updated_at', 'activated_at', 'expired_at'
    ]
    
    def property_title(self, obj):
        return obj.property.title
    property_title.short_description = _('Imóvel')
    
    actions = [
        'activate_contracts', 'expire_contracts', 'terminate_contracts'
    ]
    
    def activate_contracts(self, request, queryset):
        count = 0
        for contract in queryset.filter(status='pending'):
            if contract.can_be_activated():
                contract.activate()
                count += 1
        self.message_user(
            request,
            f'{count} contratos ativados com sucesso.'
        )
    activate_contracts.short_description = _('Ativar contratos selecionados')
    
    def expire_contracts(self, request, queryset):
        count = 0
        for contract in queryset.filter(status='active'):
            contract.expire()
            count += 1
        self.message_user(
            request,
            f'{count} contratos expirados com sucesso.'
        )
    expire_contracts.short_description = _('Expirar contratos selecionados')
    
    def terminate_contracts(self, request, queryset):
        count = 0
        for contract in queryset.filter(status='active'):
            contract.terminate('Terminado pelo administrador')
            count += 1
        self.message_user(
            request,
            f'{count} contratos terminados com sucesso.'
        )
    terminate_contracts.short_description = _('Terminar contratos selecionados')


@admin.register(RentalPayment)
class RentalPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'contract', 'payment_month', 'amount', 'status',
        'due_date', 'paid_date', 'created_at'
    ]
    list_filter = [
        'status', 'due_date', 'paid_date', 'created_at'
    ]
    search_fields = [
        'contract__contract_number', 'contract__property__title',
        'contract__landlord__username', 'contract__tenant__username',
        'transaction_reference', 'reference_number'
    ]
    ordering = ['-payment_month']
    readonly_fields = [
        'id', 'contract', 'amount', 'created_at', 'updated_at'
    ]
    
    def contract_info(self, obj):
        return f"{obj.contract.contract_number} - {obj.contract.property.title}"
    contract_info.short_description = _('Contrato')
    
    actions = [
        'mark_as_paid', 'mark_as_overdue', 'calculate_late_fees'
    ]
    
    def mark_as_paid(self, request, queryset):
        count = queryset.filter(status='pending').update(
            status='paid',
            paid_date=timezone.now().date()
        )
        self.message_user(
            request,
            f'{count} pagamentos marcados como pagos.'
        )
    mark_as_paid.short_description = _('Marcar como pagos')
    
    def mark_as_overdue(self, request, queryset):
        count = 0
        for payment in queryset.filter(status='pending'):
            if payment.is_overdue:
                payment.mark_as_overdue()
                count += 1
        self.message_user(
            request,
            f'{count} pagamentos marcados como em atraso.'
        )
    mark_as_overdue.short_description = _('Marcar como em atraso')
    
    def calculate_late_fees(self, request, queryset):
        count = 0
        for payment in queryset.filter(status='overdue'):
            payment.calculate_late_fee()
            count += 1
        self.message_user(
            request,
            f'{count} multas calculadas com sucesso.'
        )
    calculate_late_fees.short_description = _('Calcular multas')


@admin.register(ContractRenewal)
class ContractRenewalAdmin(admin.ModelAdmin):
    list_display = [
        'contract_info', 'new_end_date', 'new_monthly_rent', 'status',
        'landlord_approved', 'tenant_approved', 'created_at'
    ]
    list_filter = [
        'status', 'landlord_approved', 'tenant_approved', 'created_at'
    ]
    search_fields = [
        'contract__contract_number', 'contract__property__title',
        'landlord_reason', 'tenant_reason'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'contract', 'landlord_approved', 'tenant_approved',
        'landlord_approved_at', 'tenant_approved_at', 'created_at', 'updated_at'
    ]
    
    def contract_info(self, obj):
        return f"{obj.contract.contract_number} - {obj.contract.property.title}"
    contract_info.short_description = _('Contrato')
    
    actions = [
        'approve_by_landlord', 'approve_by_tenant', 'reject_renewals'
    ]
    
    def approve_by_landlord(self, request, queryset):
        count = 0
        for renewal in queryset.filter(status='pending'):
            renewal.approve_by_landlord()
            count += 1
        self.message_user(
            request,
            f'{count} renovações aprovadas pelo senhorio.'
        )
    approve_by_landlord.short_description = _('Aprovar pelo senhorio')
    
    def approve_by_tenant(self, request, queryset):
        count = 0
        for renewal in queryset.filter(status='pending'):
            renewal.approve_by_tenant()
            count += 1
        self.message_user(
            request,
            f'{count} renovações aprovadas pelo inquilino.'
        )
    approve_by_tenant.short_description = _('Aprovar pelo inquilino')
    
    def reject_renewals(self, request, queryset):
        count = queryset.filter(status='pending').update(status='rejected')
        self.message_user(
            request,
            f'{count} renovações rejeitadas com sucesso.'
        )
    reject_renewals.short_description = _('Rejeitar renovações')
