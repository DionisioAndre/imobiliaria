from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username', 'email', 'full_name', 'user_type', 
        'is_verified', 'is_active', 'created_at'
    ]
    list_filter = [
        'user_type', 'is_verified', 'is_active', 
        'is_staff', 'is_superuser', 'created_at'
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Informações Pessoais'), {
            'fields': (
                'first_name', 'last_name', 'email', 'phone', 
                'bio', 'profile_picture'
            )
        }),
        (_('Tipo de Usuário'), {
            'fields': ('user_type', 'is_verified')
        }),
        (_('Localização'), {
            'fields': ('province', 'municipality', 'neighborhood')
        }),
        (_('Informações da Empresa'), {
            'fields': ('company_name', 'company_document'),
            'classes': ('collapse',)
        }),
        (_('Permissões'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
        }),
        (_('Datas Importantes'), {
            'fields': ('last_login', 'date_joined', 'last_login_ip')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'first_name', 'last_name',
                'password1', 'password2', 'user_type'
            ),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'last_login_ip']
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    full_name.short_description = _('Nome Completo')


@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'document_type', 'status', 
        'created_at', 'reviewed_at', 'reviewed_by'
    ]
    list_filter = [
        'document_type', 'status', 'created_at', 'reviewed_at'
    ]
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 
        'user__last_name', 'title'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'reviewed_at', 'reviewed_by']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'document_type', 'title', 'document_file')
        }),
        (_('Status'), {
            'fields': ('status', 'rejection_reason')
        }),
        (_('Revisão'), {
            'fields': ('reviewed_by', 'reviewed_at'),
            'classes': ('collapse',)
        }),
        (_('Datas'), {
            'fields': ('created_at',),
        }),
    )
    
    actions = ['approve_verifications', 'reject_verifications']
    
    def approve_verifications(self, request, queryset):
        from django.utils import timezone
        count = 0
        for verification in queryset.filter(status='pending'):
            verification.status = 'approved'
            verification.reviewed_by = request.user
            verification.reviewed_at = timezone.now()
            verification.save()
            
            # Marcar usuário como verificado
            verification.user.is_verified = True
            verification.user.save(update_fields=['is_verified'])
            count += 1
        
        self.message_user(
            request, 
            f'{count} verificações aprovadas com sucesso.'
        )
    approve_verifications.short_description = _('Aprovar verificações selecionadas')
    
    def reject_verifications(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(
            request, 
            f'{count} verificações rejeitadas com sucesso.'
        )
    reject_verifications.short_description = _('Rejeitar verificações selecionadas')
