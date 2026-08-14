from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, F, Count, Avg, Sum, Case, When, Value
from django.utils import timezone
from django.db.models.functions import Random
import random

from .models import Property, PropertyImage, PropertyVideo, PropertyDocument, PropertyView, PropertyMessage, PropertyVisitRequest
from .serializers import (
    PropertySerializer, PropertyCreateSerializer, PropertyUpdateSerializer,
    PropertyListSerializer, PropertyDetailSerializer, AdminPropertySerializer,
    PropertyImageSerializer, PropertyVideoSerializer, PropertyDocumentSerializer,
    PropertyViewSerializer, PropertyMessageSerializer, PropertyVisitRequestSerializer
)

from users.permissions import (
    IsOwnerOrAdmin, IsVerifiedVendor, CanManageProperty, CanViewPropertyDocuments,
    IsVendorOrAdmin, IsAdminUser
)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

class PropertyImageUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, property_id):
        try:
            property = Property.objects.get(id=property_id, owner=request.user)
        except Property.DoesNotExist:
            return Response({"error": "Imóvel não encontrado ou não autorizado"}, status=status.HTTP_404_NOT_FOUND)

        files = request.FILES.getlist('images')

        if len(files) < 4:
            return Response({"error": "Mínimo de 4 imagens obrigatórias"}, status=status.HTTP_400_BAD_REQUEST)

        # Limpeza opcional: remover imagens antigas se for uma atualização
        PropertyImage.objects.filter(property=property).delete()

        for i, file in enumerate(files):
            PropertyImage.objects.create(
                property=property,
                image=file,
                order=i,
                is_main=(i == 0)
            )

        return Response({"success": True, "message": "Imagens enviadas com sucesso"}, status=status.HTTP_201_CREATED)

class PropertyVideoUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, property_id):
        try:
            property = Property.objects.get(id=property_id, owner=request.user)
        except Property.DoesNotExist:
            return Response({"error": "Imóvel não encontrado"}, status=status.HTTP_404_NOT_FOUND)

        video = request.FILES.get('video')

        if not video:
            return Response({"error": "Vídeo obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

        # Limpeza opcional: remover vídeos antigos
        PropertyVideo.objects.filter(property=property).delete()

        PropertyVideo.objects.create(
            property=property,
            video=video
        )

        return Response({"success": True, "message": "Vídeo enviado com sucesso"}, status=status.HTTP_201_CREATED)

class PropertyDocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, property_id):
        try:
            property = Property.objects.get(id=property_id, owner=request.user)
        except Property.DoesNotExist:
            return Response({"error": "Imóvel não encontrado ou não autorizado"}, status=status.HTTP_404_NOT_FOUND)

        files = request.FILES.getlist('documents')

        if not files or len(files) < 1:
            return Response({"error": "Pelo menos 1 documento é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

        # Limpeza opcional: remover documentos antigos
        PropertyDocument.objects.filter(property=property).delete()

        for i, file in enumerate(files):
            PropertyDocument.objects.create(
                property=property,
                document=file,
                document_type='ownership',  # Tipo padrão para documentos de titularidade
                title=f'Documento {i+1}'
            )

        return Response({"success": True, "message": f"{len(files)} documento(s) enviado(s) com sucesso"}, status=status.HTTP_201_CREATED)


class PropertyMessageView(generics.ListCreateAPIView):
    """View para mensagens de chat de um imóvel"""
    serializer_class = PropertyMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        property_id = self.kwargs['property_id']
        return PropertyMessage.objects.filter(property_id=property_id).select_related('sender', 'receiver')
    
    def perform_create(self, serializer):
        property_id = self.kwargs['property_id']
        print(f"========== CRIANDO MENSAGEM ==========")
        print(f"Property ID: {property_id}")
        print(f"Request user: {self.request.user}")
        print(f"Validated data: {serializer.validated_data}")
        
        property_obj = Property.objects.get(id=property_id)
        print(f"Property object: {property_obj}")
        print(f"Property owner: {property_obj.owner}")
        
        # O destinatário é o proprietário do imóvel
        serializer.save(property=property_obj, receiver=property_obj.owner)
        print(f"Mensagem criada com sucesso")


class PropertyVisitRequestView(generics.ListCreateAPIView):
    """View para solicitações de visita a um imóvel"""
    serializer_class = PropertyVisitRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        property_id = self.kwargs['property_id']
        return PropertyVisitRequest.objects.filter(property_id=property_id)
    
    def perform_create(self, serializer):
        property_id = self.kwargs['property_id']
        property_obj = Property.objects.get(id=property_id)
        serializer.save(property=property_obj)

class PropertyListView(generics.ListAPIView):
    """View para listagem de imóveis com ordenação personalizada"""
    serializer_class = PropertyListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'property_type', 'transaction_type', 'province', 'municipality',
        'neighborhood', 'bedrooms', 'bathrooms', 'is_furnished', 'status'
    ]
    search_fields = ['title', 'description', 'neighborhood', 'street']
    ordering_fields = ['created_at', 'price', 'area_m2', 'views_count']
    
    def get_queryset(self):
        """Queryset personalizado com ordenação de patrocinados primeiro"""
        queryset = Property.objects.filter(status='active')
        
        # Filtros personalizados
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        min_area = self.request.query_params.get('min_area')
        max_area = self.request.query_params.get('max_area')
        available_from = self.request.query_params.get('available_from')
        available_until = self.request.query_params.get('available_until')
        sponsored_only = self.request.query_params.get('sponsored_only')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if min_area:
            queryset = queryset.filter(area_m2__gte=min_area)
        if max_area:
            queryset = queryset.filter(area_m2__lte=max_area)
        if available_from:
            queryset = queryset.filter(available_from__lte=available_from)
        if available_until:
            queryset = queryset.filter(available_until__gte=available_until)
        
        if sponsored_only == 'true':
            # Apenas imóveis patrocinados
            sponsored_properties = []
            for prop in queryset:
                if prop.is_sponsored:
                    sponsored_properties.append(prop.id)
            queryset = queryset.filter(id__in=sponsored_properties)
        
        # Ordenação: patrocinados primeiro, depois aleatória
        sponsored_ids = []
        regular_ids = []
        
        for prop in queryset:
            if prop.is_sponsored:
                sponsored_ids.append(prop.id)
            else:
                regular_ids.append(prop.id)
        
        # Embaralhar os IDs regulares
        random.shuffle(regular_ids)
        
        # Combinar: patrocinados primeiro (em ordem de prioridade), depois aleatórios
        final_order = sponsored_ids + regular_ids
        
        # Preservar ordem no queryset
        if final_order:
            # Criar cláusula CASE para manter a ordem
            when_clauses = [When(Q(id=pk), then=Value(i)) for i, pk in enumerate(final_order)]
            queryset = queryset.filter(id__in=final_order).order_by(
                Case(*when_clauses)
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Sobrescrever list para registrar visualizações"""
        response = super().list(request, *args, **kwargs)
        
        # Registrar visualizações para cada imóvel retornado
        if request.user.is_authenticated:
            user = request.user
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            for property_data in response.data['results']:
                property_id = property_data['id']
                try:
                    property_obj = Property.objects.get(id=property_id)
                    
                    # Criar registro de visualização
                    PropertyView.objects.get_or_create(
                        property=property_obj,
                        user=user,
                        ip_address=ip,
                        user_agent=user_agent,
                        defaults={'viewed_at': timezone.now()}
                    )
                    
                    # Incrementar contador
                    property_obj.increment_views()
                    
                except Property.DoesNotExist:
                    pass
        
        return response


class PropertyDetailView(generics.RetrieveAPIView):
    """View para detalhes de imóvel"""
    serializer_class = PropertyDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Property.objects.all()
    
    def get_serializer_class(self):
        request = self.context.get('request')
        if request and request.user.is_admin_user:
            return AdminPropertySerializer
        return PropertyDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Sobrescrever retrieve para registrar visualização"""
        response = super().retrieve(request, *args, **kwargs)
        
        # Registrar visualização
        if request.user.is_authenticated:
            property_obj = self.get_object()
            
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            PropertyView.objects.get_or_create(
                property=property_obj,
                user=request.user,
                ip_address=ip,
                user_agent=user_agent,
                defaults={'viewed_at': timezone.now()}
            )
            
            # Incrementar contador
            property_obj.increment_views()
        
        return response


class PropertyCreateView(generics.CreateAPIView):
    """View para criação de imóveis (apenas vendedores verificados)"""
    serializer_class = PropertyCreateSerializer
    permission_classes = [IsVerifiedVendor]
    
    def perform_create(self, serializer):
        """Verificar completude antes de salvar"""
        property = serializer.save()
        
        # Verificar se o imóvel está completo
        if property.check_completion():
            property.status = Property.PropertyStatus.ACTIVE
            property.published_at = timezone.now()
            
            # Definir data de expiração (30 dias por padrão)
            from datetime import timedelta
            property.expires_at = timezone.now() + timedelta(days=30)
            
            property.save(update_fields=['status', 'published_at', 'expires_at'])
        else:
            property.status = Property.PropertyStatus.PENDING
            property.save(update_fields=['status'])


class PropertyUpdateView(generics.RetrieveUpdateAPIView):
    """View para atualização de imóveis"""
    serializer_class = PropertyUpdateSerializer
    permission_classes = [CanManageProperty]
    lookup_field = 'id'
    
    def get_queryset(self):
        if self.request.user.is_admin_user:
            return Property.objects.all()
        return Property.objects.filter(owner=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Atualizar imóvel e verificar completude"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        property = serializer.save()
        
        # Verificar completude após atualização
        if property.check_completion() and property.status == Property.PropertyStatus.PENDING:
            property.status = Property.PropertyStatus.ACTIVE
            property.published_at = timezone.now()
            
            # Definir data de expiração
            from datetime import timedelta
            if not property.expires_at:
                property.expires_at = timezone.now() + timedelta(days=30)
            
            property.save(update_fields=['status', 'published_at', 'expires_at'])
        
        return Response(PropertyDetailSerializer(property, context={'request': request}).data)


class PropertyDeleteView(generics.DestroyAPIView):
    """View para exclusão de imóveis"""
    permission_classes = [CanManageProperty]
    lookup_field = 'id'
    
    def get_queryset(self):
        if self.request.user.is_admin_user:
            return Property.objects.all()
        return Property.objects.filter(owner=self.request.user)


class PropertyImageView(generics.ListCreateAPIView):
    """View para imagens de imóveis"""
    serializer_class = PropertyImageSerializer
    permission_classes = [IsOwnerOrAdmin]
    
    def get_queryset(self):
        property_id = self.kwargs['property_id']
        try:
            property_obj = Property.objects.get(id=property_id)
            
            # Verificar permissão
            if self.request.user.is_admin_user or property_obj.owner == self.request.user:
                return PropertyImage.objects.filter(property=property_obj)
            else:
                return PropertyImage.objects.none()
        except Property.DoesNotExist:
            return PropertyImage.objects.none()
    
    def perform_create(self, serializer):
        property_id = self.kwargs['property_id']
        property_obj = Property.objects.get(id=property_id)
        serializer.save(property=property_obj)


class PropertyVideoView(generics.ListCreateAPIView):
    """View para vídeos de imóveis"""
    serializer_class = PropertyVideoSerializer
    permission_classes = [IsOwnerOrAdmin]
    
    def get_queryset(self):
        property_id = self.kwargs['property_id']
        try:
            property_obj = Property.objects.get(id=property_id)
            
            if self.request.user.is_admin_user or property_obj.owner == self.request.user:
                return PropertyVideo.objects.filter(property=property_obj)
            else:
                return PropertyVideo.objects.none()
        except Property.DoesNotExist:
            return PropertyVideo.objects.none()
    
    def perform_create(self, serializer):
        property_id = self.kwargs['property_id']
        property_obj = Property.objects.get(id=property_id)
        serializer.save(property=property_obj)


class PropertyDocumentView(generics.ListCreateAPIView):
    """View para documentos de imóveis (apenas administradores)"""
    serializer_class = PropertyDocumentSerializer
    permission_classes = [CanViewPropertyDocuments]
    
    def get_queryset(self):
        property_id = self.kwargs['property_id']
        try:
            property_obj = Property.objects.get(id=property_id)
            return PropertyDocument.objects.filter(property=property_obj)
        except Property.DoesNotExist:
            return PropertyDocument.objects.none()
    
    def perform_create(self, serializer):
        property_id = self.kwargs['property_id']
        property_obj = Property.objects.get(id=property_id)
        serializer.save(property=property_obj)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def contact_property_view(request, property_id):
    """View para registrar contato com imóvel"""
    try:
        property_obj = Property.objects.get(id=property_id)
        
        # Verificar se o imóvel pode ser contactado
        if not property_obj.can_be_contacted():
            return Response(
                {'error': 'Este imóvel não pode receber contatos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Incrementar contador de contatos
        property_obj.increment_contacts()
        
        return Response({
            'message': 'Contato registrado com sucesso',
            'contact_count': property_obj.contact_count
        })
        
    except Property.DoesNotExist:
        return Response(
            {'error': 'Imóvel não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsVendorOrAdmin])
def publish_property_view(request, property_id):
    """View para publicar imóvel"""
    try:
        property_obj = Property.objects.get(id=property_id)
        
        # Verificar permissão
        if not request.user.is_admin_user and property_obj.owner != request.user:
            return Response(
                {'error': 'Sem permissão para publicar este imóvel'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar completude
        if not property_obj.check_completion():
            return Response(
                {
                    'error': 'Imóvel incompleto',
                    'missing': [
                        'Documentos de titularidade' if not property_obj.documents.exists() else None,
                        'Mínimo de 4 imagens' if property_obj.images.count() < 4 else None,
                        'Vídeo obrigatório' if not property_obj.videos.exists() else None,
                        'Localização completa' if not all([
                            property_obj.province,
                            property_obj.municipality,
                            property_obj.neighborhood
                        ]) else None
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Publicar imóvel
        property_obj.status = Property.PropertyStatus.ACTIVE
        property_obj.published_at = timezone.now()
        
        # Definir data de expiração
        from datetime import timedelta
        if not property_obj.expires_at:
            property_obj.expires_at = timezone.now() + timedelta(days=30)
        
        property_obj.save(update_fields=['status', 'published_at', 'expires_at'])
        
        return Response({
            'message': 'Imóvel publicado com sucesso',
            'expires_at': property_obj.expires_at
        })
        
    except Property.DoesNotExist:
        return Response(
            {'error': 'Imóvel não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsVendorOrAdmin])
def deactivate_property_view(request, property_id):
    """View para desativar imóvel"""
    try:
        property_obj = Property.objects.get(id=property_id)
        
        # Verificar permissão
        if not request.user.is_admin_user and property_obj.owner != request.user:
            return Response(
                {'error': 'Sem permissão para desativar este imóvel'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Desativar imóvel
        property_obj.status = Property.PropertyStatus.INACTIVE
        property_obj.save(update_fields=['status'])
        
        return Response({'message': 'Imóvel desativado com sucesso'})
        
    except Property.DoesNotExist:
        return Response(
            {'error': 'Imóvel não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_properties_view(request):
    """View para listar imóveis do usuário"""
    user = request.user
    
    if user.is_vendor:
        properties = Property.objects.filter(owner=user)
        serializer = PropertyListSerializer(properties, many=True, context={'request': request})
        return Response(serializer.data)
    else:
        return Response({'error': 'Apenas vendedores possuem imóveis'}, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def property_stats_view(request):
    """View para estatísticas de imóveis (apenas admin)"""
    stats = {
        'total_properties': Property.objects.count(),
        'active_properties': Property.objects.filter(status='active').count(),
        'pending_properties': Property.objects.filter(status='pending').count(),
        'sold_properties': Property.objects.filter(status='sold').count(),
        'rented_properties': Property.objects.filter(status='rented').count(),
        'expired_properties': Property.objects.filter(status='expired').count(),
        'total_views': Property.objects.aggregate(total=Sum('views_count'))['total'] or 0,
        'total_contacts': Property.objects.aggregate(total=Sum('contact_count'))['total'] or 0,
        'properties_by_type': dict(
            Property.objects.values('property_type')
            .annotate(count=Count('id'))
            .values_list('property_type', 'count')
        ),
        'properties_by_transaction': dict(
            Property.objects.values('transaction_type')
            .annotate(count=Count('id'))
            .values_list('transaction_type', 'count')
        ),
        'properties_by_province': dict(
            Property.objects.values('province')
            .annotate(count=Count('id'))
            .values_list('province', 'count')
        ),
        'average_price': Property.objects.aggregate(
            avg_price=Avg('price')
        )['avg_price'] or 0,
    }
    
    return Response(stats)
