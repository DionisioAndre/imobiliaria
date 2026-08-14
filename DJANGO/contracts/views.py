from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db.models import Sum, Count, Q

from .models import RentalContract, RentalPayment, ContractRenewal
from .serializers import (
    RentalContractSerializer, RentalContractCreateSerializer, RentalContractListSerializer,
    AdminRentalContractSerializer, RentalPaymentSerializer, ContractRenewalSerializer,
    ContractRenewalCreateSerializer
)
from users.permissions import IsOwnerOrAdmin, CanViewContract, CanManageContract, IsAdminUser, IsVendorOrAdmin


class RentalContractListView(generics.ListAPIView):
    """View para listar contratos do usuário"""
    serializer_class = RentalContractListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['contract_type', 'status']
    search_fields = ['contract_number', 'property__title', 'tenant__full_name']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'monthly_rent']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return RentalContract.objects.all()
        return RentalContract.objects.filter(Q(landlord=user) | Q(tenant=user)).distinct()


class RentalContractDetailView(generics.RetrieveAPIView):
    """View para detalhes de contrato"""
    serializer_class = RentalContractSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewContract]
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return RentalContract.objects.all()
        return RentalContract.objects.filter(Q(landlord=user) | Q(tenant=user)).distinct()
    
    def get_serializer_class(self):
        request = self.context.get('request')
        if request and request.user.is_admin_user:
            return AdminRentalContractSerializer
        return RentalContractSerializer


class RentalContractCreateView(generics.CreateAPIView):
    """View para criação de contratos"""
    serializer_class = RentalContractCreateSerializer
    permission_classes = [IsVendorOrAdmin]


class RentalContractUpdateView(generics.RetrieveUpdateAPIView):
    """View para atualização de contratos"""
    serializer_class = RentalContractSerializer
    permission_classes = [CanManageContract]
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return RentalContract.objects.all()
        return RentalContract.objects.filter(Q(landlord=user) | Q(tenant=user)).distinct()
    
    def update(self, request, *args, **kwargs):
        """Atualizar contrato"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        contract = serializer.save()
        
        # Se o contrato estiver completo e pendente, permitir ativação
        if contract.status == 'pending' and contract.can_be_activated():
            return Response({
                'message': 'Contrato pronto para ativação',
                'can_activate': True
            })
        
        return Response(RentalContractSerializer(contract, context={'request': request}).data)


class RentalContractDeleteView(generics.DestroyAPIView):
    """View para exclusão de contratos"""
    permission_classes = [CanManageContract]
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return RentalContract.objects.all()
        return RentalContract.objects.filter(landlord=user)


class RentalPaymentListView(generics.ListAPIView):
    """View para listar pagamentos de contrato"""
    serializer_class = RentalPaymentSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewContract]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'payment_method']
    ordering = ['-payment_month']
    
    def get_queryset(self):
        contract_id = self.kwargs['contract_id']
        try:
            contract = RentalContract.objects.get(id=contract_id)
            
            # Verificar permissão
            if not contract.can_user_view(self.request.user):
                return RentalPayment.objects.none()
            
            return RentalPayment.objects.filter(contract=contract)
        except RentalContract.DoesNotExist:
            return RentalPayment.objects.none()


class RentalPaymentDetailView(generics.RetrieveUpdateAPIView):
    """View para detalhes/atualização de pagamentos"""
    serializer_class = RentalPaymentSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewContract]
    lookup_field = 'id'
    
    def get_queryset(self):
        contract_id = self.kwargs['contract_id']
        try:
            contract = RentalContract.objects.get(id=contract_id)
            
            if not contract.can_user_view(self.request.user):
                return RentalPayment.objects.none()
            
            return RentalPayment.objects.filter(contract=contract)
        except RentalContract.DoesNotExist:
            return RentalPayment.objects.none()


class ContractRenewalListView(generics.ListAPIView):
    """View para listar renovações de contrato"""
    serializer_class = ContractRenewalSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewContract]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        contract_id = self.kwargs['contract_id']
        try:
            contract = RentalContract.objects.get(id=contract_id)
            
            if not contract.can_user_view(self.request.user):
                return ContractRenewal.objects.none()
            
            return ContractRenewal.objects.filter(contract=contract)
        except RentalContract.DoesNotExist:
            return ContractRenewal.objects.none()


class ContractRenewalCreateView(generics.CreateAPIView):
    """View para criação de renovações"""
    serializer_class = ContractRenewalCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_contract(self):
        contract_id = self.kwargs['contract_id']
        return RentalContract.objects.get(id=contract_id)
    
    def perform_create(self, serializer):
        contract = self.get_contract()
        
        # Verificar permissão
        if not contract.can_user_view(self.request.user):
            raise permissions.PermissionDenied("Sem permissão para criar renovação para este contrato")
        
        # Apenas senhorio pode criar renovação
        if contract.landlord != self.request.user and not self.request.user.is_admin_user:
            raise permissions.PermissionDenied("Apenas o senhorio pode criar renovações")
        
        serializer.save(contract=contract)


class ContractRenewalDetailView(generics.RetrieveAPIView):
    """View para detalhes de renovação"""
    serializer_class = ContractRenewalSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewContract]
    lookup_field = 'id'
    
    def get_queryset(self):
        contract_id = self.kwargs['contract_id']
        try:
            contract = RentalContract.objects.get(id=contract_id)
            
            if not contract.can_user_view(self.request.user):
                return ContractRenewal.objects.none()
            
            return ContractRenewal.objects.filter(contract=contract)
        except RentalContract.DoesNotExist:
            return ContractRenewal.objects.none()


@api_view(['POST'])
@permission_classes([CanManageContract])
def sign_contract_view(request, contract_id):
    """Assinar contrato"""
    try:
        contract = RentalContract.objects.get(id=contract_id)
        signature = request.data.get('signature', '')
        
        if not signature:
            return Response(
                {'error': 'Assinatura é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar qual parte está assinando
        if contract.landlord == request.user:
            contract.sign_by_landlord(signature)
            message = 'Contrato assinado pelo senhorio'
        elif contract.tenant == request.user:
            contract.sign_by_tenant(signature)
            message = 'Contrato assinado pelo inquilino'
        else:
            return Response(
                {'error': 'Sem permissão para assinar este contrato'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Se ambos assinaram e está pronto, ativar
        if contract.can_be_activated():
            contract.activate()
            message += ' e ativado com sucesso'
        else:
            message += ' com sucesso'
        
        return Response({
            'message': message,
            'is_signed_by_both': contract.is_signed_by_both,
            'can_activate': contract.can_be_activated()
        })
        
    except RentalContract.DoesNotExist:
        return Response(
            {'error': 'Contrato não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([CanManageContract])
def activate_contract_view(request, contract_id):
    """Ativar contrato"""
    try:
        contract = RentalContract.objects.get(id=contract_id)
        
        if not contract.can_be_activated():
            return Response(
                {
                    'error': 'Contrato não pode ser ativado',
                    'requirements': {
                        'signed_by_both': contract.is_signed_by_both,
                        'has_contract_file': bool(contract.contract_file),
                        'has_tenant_document': bool(contract.tenant_id_document),
                        'has_landlord_document': bool(contract.landlord_id_document)
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        contract.activate()
        
        return Response({'message': 'Contrato ativado com sucesso'})
        
    except RentalContract.DoesNotExist:
        return Response(
            {'error': 'Contrato não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([CanManageContract])
def terminate_contract_view(request, contract_id):
    """Terminar contrato"""
    try:
        contract = RentalContract.objects.get(id=contract_id)
        reason = request.data.get('reason', '')
        
        if contract.status != 'active':
            return Response(
                {'error': 'Apenas contratos ativos podem ser terminados'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Apenas senhorio ou administrador pode terminar
        if contract.landlord != request.user and not request.user.is_admin_user:
            return Response(
                {'error': 'Apenas o senhorio pode terminar o contrato'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        contract.terminate(reason)
        
        return Response({'message': 'Contrato terminado com sucesso'})
        
    except RentalContract.DoesNotExist:
        return Response(
            {'error': 'Contrato não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([CanManageContract])
def approve_renewal_view(request, contract_id, renewal_id):
    """Aprovar renovação"""
    try:
        contract = RentalContract.objects.get(id=contract_id)
        renewal = ContractRenewal.objects.get(id=renewal_id, contract=contract)
        
        if renewal.status != 'pending':
            return Response(
                {'error': 'Renovação não está pendente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar qual parte está aprovando
        if contract.landlord == request.user:
            renewal.approve_by_landlord()
            message = 'Renovação aprovada pelo senhorio'
        elif contract.tenant == request.user:
            renewal.approve_by_tenant()
            message = 'Renovação aprovada pelo inquilino'
        else:
            return Response(
                {'error': 'Sem permissão para aprovar esta renovação'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if renewal.status == 'approved':
            message += ' e contrato atualizado com sucesso'
        
        return Response({
            'message': message,
            'renewal_status': renewal.status,
            'can_be_approved': renewal.can_be_approved
        })
        
    except (RentalContract.DoesNotExist, ContractRenewal.DoesNotExist):
        return Response(
            {'error': 'Contrato ou renovação não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([CanManageContract])
def mark_payment_as_paid_view(request, contract_id, payment_id):
    """Marcar pagamento como pago"""
    try:
        contract = RentalContract.objects.get(id=contract_id)
        payment = RentalPayment.objects.get(id=payment_id, contract=contract)
        
        if payment.status == 'paid':
            return Response(
                {'error': 'Pagamento já está marcado como pago'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Apenas inquilino pode marcar como pago
        if contract.tenant != request.user and not request.user.is_admin_user:
            return Response(
                {'error': 'Apenas o inquilino pode marcar pagamentos como pagos'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        payment_method = request.data.get('payment_method')
        proof_file = request.FILES.get('proof_file')
        reference = request.data.get('reference')
        
        payment.mark_as_paid(payment_method, proof_file, reference)
        
        return Response({'message': 'Pagamento marcado como pago com sucesso'})
        
    except (RentalContract.DoesNotExist, RentalPayment.DoesNotExist):
        return Response(
            {'error': 'Contrato ou pagamento não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_contracts_view(request):
    """Listar contratos do usuário"""
    user = request.user
    
    contracts = RentalContract.objects.filter(Q(landlord=user) | Q(tenant=user)).distinct()
    serializer = RentalContractListSerializer(contracts, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def contract_stats_view(request):
    """Estatísticas de contratos do usuário"""
    user = request.user
    
    if user.is_vendor:
        stats = {
            'total_contracts': RentalContract.objects.filter(landlord=user).count(),
            'active_contracts': RentalContract.objects.filter(
                landlord=user,
                status='active'
            ).count(),
            'pending_contracts': RentalContract.objects.filter(
                landlord=user,
                status='pending'
            ).count(),
            'expired_contracts': RentalContract.objects.filter(
                landlord=user,
                status='expired'
            ).count(),
            'total_monthly_income': RentalContract.objects.filter(
                landlord=user,
                status='active'
            ).aggregate(total=Sum('monthly_rent'))['total'] or 0,
            'pending_payments': RentalPayment.objects.filter(
                contract__landlord=user,
                status='pending'
            ).count(),
            'overdue_payments': RentalPayment.objects.filter(
                contract__landlord=user,
                status='overdue'
            ).count(),
        }
    elif user.is_client:
        stats = {
            'total_contracts': RentalContract.objects.filter(tenant=user).count(),
            'active_contracts': RentalContract.objects.filter(
                tenant=user,
                status='active'
            ).count(),
            'total_monthly_rent': RentalContract.objects.filter(
                tenant=user,
                status='active'
            ).aggregate(total=Sum('monthly_rent'))['total'] or 0,
            'pending_payments': RentalPayment.objects.filter(
                contract__tenant=user,
                status='pending'
            ).count(),
            'overdue_payments': RentalPayment.objects.filter(
                contract__tenant=user,
                status='overdue'
            ).count(),
        }
    else:
        return Response({'error': 'Tipo de usuário inválido'}, status=status.HTTP_403_FORBIDDEN)
    
    return Response(stats)


# Views para Administradores
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_contract_stats_view(request):
    """Estatísticas de contratos para administradores"""
    stats = {
        'total_contracts': RentalContract.objects.count(),
        'active_contracts': RentalContract.objects.filter(status='active').count(),
        'pending_contracts': RentalContract.objects.filter(status='pending').count(),
        'expired_contracts': RentalContract.objects.filter(status='expired').count(),
        'terminated_contracts': RentalContract.objects.filter(status='terminated').count(),
        'total_monthly_value': RentalContract.objects.filter(
            status='active'
        ).aggregate(total=Sum('monthly_rent'))['total'] or 0,
        'total_payments': RentalPayment.objects.count(),
        'paid_payments': RentalPayment.objects.filter(status='paid').count(),
        'pending_payments': RentalPayment.objects.filter(status='pending').count(),
        'overdue_payments': RentalPayment.objects.filter(status='overdue').count(),
        'contracts_by_type': dict(
            RentalContract.objects.values('contract_type')
            .annotate(count=Count('id'))
            .values_list('contract_type', 'count')
        ),
        'contracts_by_status': dict(
            RentalContract.objects.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        ),
        'revenue_by_month': list(
            RentalPayment.objects.filter(status='paid')
            .extra({'month': "strftime('%%m-%%Y', paid_date)"})
            .values('month')
            .annotate(revenue=Sum('amount'))
            .order_by('-month')[:12]
        ),
    }
    
    return Response(stats)
