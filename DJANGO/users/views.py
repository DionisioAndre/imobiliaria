from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    UserUpdateSerializer, PasswordChangeSerializer, UserVerificationSerializer,
    AdminUserSerializer, AdminUserUpdateSerializer
)
from .models import UserVerification
from .permissions import IsOwnerOrAdmin, IsAdminUser

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """View para registro de novos usuários"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Gerar tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class UserLoginView(generics.GenericAPIView):
    """View para login de usuários"""
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Gerar tokens JWT
        refresh = RefreshToken.for_user(user)
        
        # Atualizar último login IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        user.last_login_ip = ip
        user.save(update_fields=['last_login_ip'])
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


class UserProfileView(generics.RetrieveUpdateAPIView):
    """View para visualizar e atualizar perfil do usuário"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return UserUpdateSerializer
        return UserProfileSerializer


class PasswordChangeView(generics.GenericAPIView):
    """View para alteração de senha"""
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Senha alterada com sucesso'})


class UserVerificationView(generics.ListCreateAPIView):
    """View para solicitações de verificação de usuário"""
    serializer_class = UserVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserVerification.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """View para logout do usuário"""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Logout realizado com sucesso'})
    except Exception as e:
        return Response({'error': 'Erro ao fazer logout'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats_view(request):
    """View para estatísticas do usuário"""
    user = request.user
    
    stats = {
        'properties_count': user.get_properties_count(),
        'can_create_property': user.can_create_property(),
        'is_verified': user.is_verified,
        'user_type': user.user_type,
        'is_vendor': user.is_vendor,
        'is_client': user.is_client,
        'is_admin_user': user.is_admin_user,
    }
    
    if user.is_vendor:
        stats.update({
            'active_properties': user.properties.filter(status='active').count(),
            'sold_properties': user.properties.filter(status='sold').count(),
            'rented_properties': user.properties.filter(status='rented').count(),
            'total_views': sum(prop.views_count for prop in user.properties.all()),
            'total_contacts': sum(prop.contact_count for prop in user.properties.all()),
        })
    
    return Response(stats)


# Views para Administradores
class AdminUserListView(generics.ListAPIView):
    """View para listar usuários (apenas admin)"""
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user_type', 'is_active', 'is_verified']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'last_login', 'user_type']
    ordering = ['-created_at']


class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    """View para detalhes e atualização de usuário (apenas admin)"""
    queryset = User.objects.all()
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AdminUserUpdateSerializer
        return AdminUserSerializer


class AdminVerificationListView(generics.ListAPIView):
    """View para listar verificações pendentes (apenas admin)"""
    queryset = UserVerification.objects.filter(status='pending')
    serializer_class = UserVerificationSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['document_type', 'status']
    ordering = ['-created_at']


@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_verification_view(request, verification_id):
    """View para aprovar verificação de usuário (apenas admin)"""
    try:
        verification = UserVerification.objects.get(id=verification_id)
        verification.status = 'approved'
        verification.reviewed_by = request.user
        verification.reviewed_at = timezone.now()
        verification.save()
        
        # Marcar usuário como verificado
        verification.user.is_verified = True
        verification.user.save(update_fields=['is_verified'])
        
        return Response({'message': 'Verificação aprovada com sucesso'})
    except UserVerification.DoesNotExist:
        return Response({'error': 'Verificação não encontrada'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reject_verification_view(request, verification_id):
    """View para rejeitar verificação de usuário (apenas admin)"""
    try:
        verification = UserVerification.objects.get(id=verification_id)
        rejection_reason = request.data.get('rejection_reason', '')
        
        verification.status = 'rejected'
        verification.rejection_reason = rejection_reason
        verification.reviewed_by = request.user
        verification.reviewed_at = timezone.now()
        verification.save()
        
        return Response({'message': 'Verificação rejeitada com sucesso'})
    except UserVerification.DoesNotExist:
        return Response({'error': 'Verificação não encontrada'}, status=status.HTTP_404_NOT_FOUND)
