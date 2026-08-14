from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão personalizada que permite acesso apenas ao dono do recurso ou administradores
    """
    
    def has_object_permission(self, request, view, obj):
        # Administradores têm acesso total
        if request.user.is_admin_user:
            return True
        
        # Verificar se o objeto tem um campo user/owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'seller'):
            return obj.seller == request.user
        elif hasattr(obj, 'buyer'):
            return obj.buyer == request.user
        elif hasattr(obj, 'landlord'):
            return obj.landlord == request.user
        elif hasattr(obj, 'tenant'):
            return obj.tenant == request.user
        elif hasattr(obj, 'sponsor'):
            return obj.sponsor == request.user
        
        # Se o objeto for o próprio usuário
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id
        
        return False


class IsAdminUser(permissions.BasePermission):
    """
    Permissão personalizada para administradores
    """
    
    def has_permission(self, request, view):
        return request.user.is_admin_user


class IsVendorOrAdmin(permissions.BasePermission):
    """
    Permissão para vendedores ou administradores
    """
    
    def has_permission(self, request, view):
        return request.user.is_vendor or request.user.is_admin_user


class IsClientOrAdmin(permissions.BasePermission):
    """
    Permissão para clientes ou administradores
    """
    
    def has_permission(self, request, view):
        return request.user.is_client or request.user.is_admin_user


class IsVerifiedVendor(permissions.BasePermission):
    """
    Permissão para vendedores verificados
    """
    
    def has_permission(self, request, view):
        return request.user.is_vendor and request.user.is_verified


class CanViewPropertyDocuments(permissions.BasePermission):
    """
    Permissão para visualizar documentos de imóveis (apenas administradores)
    """
    
    def has_permission(self, request, view):
        return request.user.is_admin_user


class CanManageProperty(permissions.BasePermission):
    """
    Permissão para gerenciar imóveis
    """
    
    def has_object_permission(self, request, view, obj):
        # Administradores podem gerenciar todos os imóveis
        if request.user.is_admin_user:
            return True
        
        # Vendedores podem gerenciar apenas seus próprios imóveis
        if request.user.is_vendor:
            return obj.owner == request.user
        
        return False


class CanParticipateInChat(permissions.BasePermission):
    """
    Permissão para participar de um chat
    """
    
    def has_object_permission(self, request, view, obj):
        # Verificar se o usuário pode participar deste chat
        return obj.can_user_participate(request.user)


class CanSendMessage(permissions.BasePermission):
    """
    Permissão para enviar mensagens em um chat
    """
    
    def has_object_permission(self, request, view, obj):
        # Verificar se o usuário pode participar do chat
        if not obj.chat.can_user_participate(request.user):
            return False
        
        # Verificar se não há bloqueios
        from chat.models import ChatBlock
        return ChatBlock.can_message(
            request.user, 
            obj.chat.other_user(request.user),
            obj.chat.property
        )


class CanViewContract(permissions.BasePermission):
    """
    Permissão para visualizar contratos
    """
    
    def has_object_permission(self, request, view, obj):
        # Administradores podem ver todos os contratos
        if request.user.is_admin_user:
            return True
        
        # Senhorio e inquilino podem ver seus próprios contratos
        return obj.landlord == request.user or obj.tenant == request.user


class CanManageContract(permissions.BasePermission):
    """
    Permissão para gerenciar contratos
    """
    
    def has_object_permission(self, request, view, obj):
        # Administradores podem gerenciar todos os contratos
        if request.user.is_admin_user:
            return True
        
        # Senhorio pode gerenciar seus contratos
        if obj.landlord == request.user:
            return True
        
        # Inquilino pode visualizar e assinar seus contratos
        if obj.tenant == request.user and request.method in ['GET', 'PUT', 'PATCH']:
            return True
        
        return False


class CanManageSponsorship(permissions.BasePermission):
    """
    Permissão para gerenciar patrocínios
    """
    
    def has_object_permission(self, request, view, obj):
        # Administradores podem gerenciar todos os patrocínios
        if request.user.is_admin_user:
            return True
        
        # Vendedores podem gerenciar apenas seus patrocínios
        if request.user.is_vendor:
            return obj.sponsor == request.user
        
        return False
