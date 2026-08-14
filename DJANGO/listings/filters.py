import django_filters
from django.db.models import Q, Count
from .models import Property


class PropertyFilter(django_filters.FilterSet):
    """
    Filtros avançados para imóveis
    """
    
    # Filtros de preço
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    price_range = django_filters.RangeFilter(field_name='price')
    
    # Filtros de área
    min_area = django_filters.NumberFilter(field_name='area_m2', lookup_expr='gte')
    max_area = django_filters.NumberFilter(field_name='area_m2', lookup_expr='lte')
    area_range = django_filters.RangeFilter(field_name='area_m2')
    
    # Filtros de quartos e banheiros
    bedrooms_min = django_filters.NumberFilter(field_name='bedrooms', lookup_expr='gte')
    bedrooms_max = django_filters.NumberFilter(field_name='bedrooms', lookup_expr='lte')
    bathrooms_min = django_filters.NumberFilter(field_name='bathrooms', lookup_expr='gte')
    bathrooms_max = django_filters.NumberFilter(field_name='bathrooms', lookup_expr='lte')
    
    # Filtros de estacionamento
    parking_min = django_filters.NumberFilter(field_name='parking_spaces', lookup_expr='gte')
    
    # Filtros de disponibilidade
    available_from = django_filters.DateFilter(field_name='available_from', lookup_expr='lte')
    available_until = django_filters.DateFilter(field_name='available_until', lookup_expr='gte')
    
    # Filtro de localização combinado
    location = django_filters.CharFilter(method='filter_location')
    
    # Filtro de características
    features = django_filters.CharFilter(method='filter_features')
    
    # Filtro de patrocínio
    sponsored_only = django_filters.BooleanFilter(method='filter_sponsored')
    
    # Filtro de busca textual avançada
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Property
        fields = [
            'property_type', 'transaction_type', 'province', 'municipality',
            'neighborhood', 'bedrooms', 'bathrooms', 'parking_spaces',
            'is_furnished', 'status', 'featured'
        ]
    
    def filter_location(self, queryset, name, value):
        """
        Filtro por localização (busca em múltiplos campos)
        """
        if not value:
            return queryset
        
        # Buscar em província, município, bairro e rua
        return queryset.filter(
            Q(province__icontains=value) |
            Q(municipality__icontains=value) |
            Q(neighborhood__icontains=value) |
            Q(street__icontains=value) |
            Q(reference_point__icontains=value)
        )
    
    def filter_features(self, queryset, name, value):
        """
        Filtro por características (texto livre)
        """
        if not value:
            return queryset
        
        # Buscar em descrição e observações
        return queryset.filter(
            Q(description__icontains=value) |
            Q(additional_notes__icontains=value) |
            Q(furniture_description__icontains=value)
        )
    
    def filter_sponsored(self, queryset, name, value):
        """
        Filtro para apenas imóveis patrocinados
        """
        if value is True:
            sponsored_properties = []
            for prop in queryset:
                if prop.is_sponsored:
                    sponsored_properties.append(prop.id)
            return queryset.filter(id__in=sponsored_properties)
        return queryset
    
    def filter_search(self, queryset, name, value):
        """
        Busca textual avançada em múltiplos campos
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(province__icontains=value) |
            Q(municipality__icontains=value) |
            Q(neighborhood__icontains=value) |
            Q(street__icontains=value) |
            Q(reference_point__icontains=value) |
            Q(additional_notes__icontains=value)
        )


class PropertyAdminFilter(PropertyFilter):
    """
    Filtros adicionais para administradores
    """
    
    # Filtros de data
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    published_after = django_filters.DateFilter(field_name='published_at', lookup_expr='gte')
    published_before = django_filters.DateFilter(field_name='published_at', lookup_expr='lte')
    expires_after = django_filters.DateFilter(field_name='expires_at', lookup_expr='gte')
    expires_before = django_filters.DateFilter(field_name='expires_at', lookup_expr='lte')
    
    # Filtros de estatísticas
    min_views = django_filters.NumberFilter(field_name='views_count', lookup_expr='gte')
    max_views = django_filters.NumberFilter(field_name='views_count', lookup_expr='lte')
    min_contacts = django_filters.NumberFilter(field_name='contact_count', lookup_expr='gte')
    max_contacts = django_filters.NumberFilter(field_name='contact_count', lookup_expr='lte')
    
    # Filtro por proprietário
    owner = django_filters.CharFilter(field_name='owner__username', lookup_expr='icontains')
    owner_email = django_filters.CharFilter(field_name='owner__email', lookup_expr='icontains')
    
    # Filtro de completude
    is_complete = django_filters.BooleanFilter(method='filter_complete')
    has_documents = django_filters.BooleanFilter(method='filter_has_documents')
    has_min_images = django_filters.BooleanFilter(method='filter_has_min_images')
    has_video = django_filters.BooleanFilter(method='filter_has_video')
    
    class Meta(PropertyFilter.Meta):
        fields = PropertyFilter.Meta.fields + [
            'created_after', 'created_before', 'published_after', 'published_before',
            'expires_after', 'expires_before', 'min_views', 'max_views',
            'min_contacts', 'max_contacts', 'owner', 'owner_email',
            'is_complete', 'has_documents', 'has_min_images', 'has_video'
        ]
    
    def filter_complete(self, queryset, name, value):
        """Filtrar imóveis completos/incompletos"""
        filtered_properties = []
        for prop in queryset:
            if prop.check_completion() == value:
                filtered_properties.append(prop.id)
        return queryset.filter(id__in=filtered_properties)
    
    def filter_has_documents(self, queryset, name, value):
        """Filtrar imóveis com/sem documentos"""
        if value is True:
            return queryset.filter(documents__isnull=False).distinct()
        elif value is False:
            return queryset.filter(documents__isnull=True)
        return queryset
    
    def filter_has_min_images(self, queryset, name, value):
        """Filtrar imóveis com/selo mínimo de imagens"""
        if value is True:
            return queryset.annotate(
                img_count=Count('images')
            ).filter(img_count__gte=4)
        elif value is False:
            return queryset.annotate(
                img_count=Count('images')
            ).filter(img_count__lt=4)
        return queryset
    
    def filter_has_video(self, queryset, name, value):
        """Filtrar imóveis com/selo vídeo"""
        if value is True:
            return queryset.filter(videos__isnull=False).distinct()
        elif value is False:
            return queryset.filter(videos__isnull=True)
        return queryset
