from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import Sponsorship, SponsorshipPackage, SponsorshipPayment
from .serializers import (
    SponsorshipSerializer, SponsorshipCreateSerializer, SponsorshipListSerializer,
    AdminSponsorshipSerializer, SponsorshipPackageSerializer, AdminSponsorshipPackageSerializer,
    SponsorshipPaymentSerializer
)
from users.permissions import IsOwnerOrAdmin, IsVendorOrAdmin, CanManageSponsorship, IsAdminUser


class SponsorshipPackageListView(generics.ListAPIView):
    """View para listar pacotes de patrocínio disponíveis"""
    serializer_class = SponsorshipPackageSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['package_type']
    ordering = ['priority_level', 'price']
    
    def get_queryset(self):
        return SponsorshipPackage.objects.filter(is_active=True)


class SponsorshipListView(generics.ListAPIView):
    """View para listar patrocínios do usuário"""
    serializer_class = SponsorshipListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['sponsorship_type', 'status']
    search_fields = ['property__title', 'property__neighborhood']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return Sponsorship.objects.all()
        return Sponsorship.objects.filter(sponsor=user)


class SponsorshipDetailView(generics.RetrieveAPIView):
    """View para detalhes de patrocínio"""
    serializer_class = SponsorshipSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return Sponsorship.objects.all()
        return Sponsorship.objects.filter(sponsor=user)
    
    def get_serializer_class(self):
        request = self.context.get('request')
        if request and request.user.is_admin_user:
            return AdminSponsorshipSerializer
        return SponsorshipSerializer


class SponsorshipCreateView(generics.CreateAPIView):
    """View para criação de patrocínios"""
    serializer_class = SponsorshipCreateSerializer
    permission_classes = [IsVendorOrAdmin]


class SponsorshipUpdateView(generics.RetrieveUpdateAPIView):
    """View para atualização de patrocínios"""
    serializer_class = SponsorshipSerializer
    permission_classes = [CanManageSponsorship]
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return Sponsorship.objects.all()
        return Sponsorship.objects.filter(sponsor=user)


class SponsorshipDeleteView(generics.DestroyAPIView):
    """View para exclusão de patrocínios"""
    permission_classes = [CanManageSponsorship]
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return Sponsorship.objects.all()
        return Sponsorship.objects.filter(sponsor=user)


class SponsorshipPaymentListView(generics.ListAPIView):
    """View para listar pagamentos de patrocínio"""
    serializer_class = SponsorshipPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['payment_method', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        sponsorship_id = self.kwargs['sponsorship_id']
        try:
            sponsorship = Sponsorship.objects.get(id=sponsorship_id)
            
            # Verificar permissão
            if self.request.user.is_admin_user or sponsorship.sponsor == self.request.user:
                return SponsorshipPayment.objects.filter(sponsorship=sponsorship)
            else:
                return SponsorshipPayment.objects.none()
        except Sponsorship.DoesNotExist:
            return SponsorshipPayment.objects.none()


class SponsorshipPaymentCreateView(generics.CreateAPIView):
    """View para criação de pagamentos de patrocínio"""
    serializer_class = SponsorshipPaymentSerializer
    permission_classes = [IsVendorOrAdmin]
    
    def get_sponsorship(self):
        sponsorship_id = self.kwargs['sponsorship_id']
        return Sponsorship.objects.get(id=sponsorship_id)
    
    def perform_create(self, serializer):
        sponsorship = self.get_sponsorship()
        
        # Verificar permissão
        if not self.request.user.is_admin_user and sponsorship.sponsor != self.request.user:
            raise permissions.PermissionDenied("Sem permissão para criar pagamento para este patrocínio")
        
        # Definir valor do pagamento
        serializer.save(sponsorship=sponsorship, amount=sponsorship.price)


@api_view(['POST'])
@permission_classes([CanManageSponsorship])
def activate_sponsorship_view(request, sponsorship_id):
    """Ativar patrocínio"""
    try:
        sponsorship = Sponsorship.objects.get(id=sponsorship_id)
        
        # Verificar se está pago
        if not sponsorship.is_paid:
            return Response(
                {'error': 'Patrocínio precisa ser pago para ser ativado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sponsorship.activate()
        
        return Response({'message': 'Patrocínio ativado com sucesso'})
        
    except Sponsorship.DoesNotExist:
        return Response(
            {'error': 'Patrocínio não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([CanManageSponsorship])
def cancel_sponsorship_view(request, sponsorship_id):
    """Cancelar patrocínio"""
    try:
        sponsorship = Sponsorship.objects.get(id=sponsorship_id)
        
        if sponsorship.status == 'active':
            # Se estiver ativo, verificar reembolso
            payment = sponsorship.payments.filter(status='completed').first()
            if payment:
                payment.mark_as_refunded()
        
        sponsorship.cancel()
        
        return Response({'message': 'Patrocínio cancelado com sucesso'})
        
    except Sponsorship.DoesNotExist:
        return Response(
            {'error': 'Patrocínio não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_payment_view(request, payment_id):
    """Aprovar pagamento de patrocínio"""
    try:
        payment = SponsorshipPayment.objects.get(id=payment_id)
        
        if payment.status != 'pending':
            return Response(
                {'error': 'Pagamento não está pendente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.mark_as_completed()
        
        return Response({'message': 'Pagamento aprovado com sucesso'})
        
    except SponsorshipPayment.DoesNotExist:
        return Response(
            {'error': 'Pagamento não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reject_payment_view(request, payment_id):
    """Rejeitar pagamento de patrocínio"""
    try:
        payment = SponsorshipPayment.objects.get(id=payment_id)
        reason = request.data.get('reason', 'Pagamento rejeitado')
        
        payment.mark_as_failed(reason)
        
        return Response({'message': 'Pagamento rejeitado com sucesso'})
        
    except SponsorshipPayment.DoesNotExist:
        return Response(
            {'error': 'Pagamento não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_sponsorships_view(request):
    """Listar patrocínios do usuário"""
    user = request.user
    
    if user.is_vendor:
        sponsorships = Sponsorship.objects.filter(sponsor=user)
        serializer = SponsorshipListSerializer(sponsorships, many=True, context={'request': request})
        return Response(serializer.data)
    else:
        return Response({'error': 'Apenas vendedores possuem patrocínios'}, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def sponsorship_stats_view(request):
    """Estatísticas de patrocínio do usuário"""
    user = request.user
    
    if not user.is_vendor:
        return Response({'error': 'Apenas vendedores possuem estatísticas'}, status=status.HTTP_403_FORBIDDEN)
    
    stats = {
        'total_sponsorships': Sponsorship.objects.filter(sponsor=user).count(),
        'active_sponsorships': Sponsorship.objects.filter(
            sponsor=user,
            status='active'
        ).count(),
        'pending_sponsorships': Sponsorship.objects.filter(
            sponsor=user,
            status='pending'
        ).count(),
        'expired_sponsorships': Sponsorship.objects.filter(
            sponsor=user,
            status='expired'
        ).count(),
        'total_invested': Sponsorship.objects.filter(
            sponsor=user,
            payments__status='completed'
        ).aggregate(total=Sum('price'))['total'] or 0,
        'total_views_boosted': Sponsorship.objects.filter(
            sponsor=user
        ).aggregate(total=Sum('views_boosted'))['total'] or 0,
        'total_contacts_boosted': Sponsorship.objects.filter(
            sponsor=user
        ).aggregate(total=Sum('contacts_boosted'))['total'] or 0,
    }
    
    return Response(stats)


# Views para Administradores gerenciarem pacotes
class AdminSponsorshipPackageListView(generics.ListCreateAPIView):
    """View para administradores gerenciarem pacotes de patrocínio"""
    serializer_class = AdminSponsorshipPackageSerializer
    permission_classes = [IsAdminUser]
    queryset = SponsorshipPackage.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['package_type', 'is_active']
    ordering = ['priority_level', 'price']


class AdminSponsorshipPackageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View para detalhes/atualização/exclusão de pacotes"""
    serializer_class = AdminSponsorshipPackageSerializer
    permission_classes = [IsAdminUser]
    queryset = SponsorshipPackage.objects.all()
    lookup_field = 'id'


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_sponsorship_stats_view(request):
    """Estatísticas de patrocínio para administradores"""
    stats = {
        'total_sponsorships': Sponsorship.objects.count(),
        'active_sponsorships': Sponsorship.objects.filter(status='active').count(),
        'pending_sponsorships': Sponsorship.objects.filter(status='pending').count(),
        'expired_sponsorships': Sponsorship.objects.filter(status='expired').count(),
        'total_revenue': SponsorshipPayment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'pending_payments': SponsorshipPayment.objects.filter(status='pending').count(),
        'completed_payments': SponsorshipPayment.objects.filter(status='completed').count(),
        'failed_payments': SponsorshipPayment.objects.filter(status='failed').count(),
        'sponsorships_by_type': dict(
            Sponsorship.objects.values('sponsorship_type')
            .annotate(count=Count('id'))
            .values_list('sponsorship_type', 'count')
        ),
        'revenue_by_month': list(
            SponsorshipPayment.objects.filter(status='completed')
            .extra({'month': "strftime('%%m-%%Y', created_at)"})
            .values('month')
            .annotate(revenue=Sum('amount'))
            .order_by('-month')[:12]
        ),
        'top_sponsors': list(
            Sponsorship.objects.values('sponsor__full_name')
            .annotate(total=Sum('price'))
            .order_by('-total')[:10]
            .values('sponsor__full_name', 'total')
        ),
    }
    
    return Response(stats)
