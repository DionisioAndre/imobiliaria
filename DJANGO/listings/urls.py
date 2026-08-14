from django.urls import path
from . import views
from .views import PropertyImageUploadView, PropertyVideoUploadView, PropertyDocumentUploadView, PropertyMessageView, PropertyVisitRequestView
app_name = 'listings'

urlpatterns = [
    # Imóveis
    path('', views.PropertyListView.as_view(), name='property-list'),
    path('<uuid:id>/', views.PropertyDetailView.as_view(), name='property-detail'),
    path('create/', views.PropertyCreateView.as_view(), name='property-create'),
    path('<uuid:id>/update/', views.PropertyUpdateView.as_view(), name='property-update'),
    path('<uuid:id>/delete/', views.PropertyDeleteView.as_view(), name='property-delete'),
    path('properties/<uuid:property_id>/images/', PropertyImageUploadView.as_view(), name='property-images-upload'),
    path('properties/<uuid:property_id>/video/', PropertyVideoUploadView.as_view(), name='property-video-upload'),
    path('properties/<uuid:property_id>/documents/', PropertyDocumentUploadView.as_view(), name='property-documents-upload'),
    # Ações de imóveis
    path('<uuid:id>/contact/', views.contact_property_view, name='property-contact'),
    path('<uuid:id>/publish/', views.publish_property_view, name='property-publish'),
    path('<uuid:id>/deactivate/', views.deactivate_property_view, name='property-deactivate'),
    path('my-properties/', views.my_properties_view, name='my-properties'),
    
    # Mídia dos imóveis
    path('<uuid:property_id>/images/', views.PropertyImageView.as_view(), name='property-images'),
    path('<uuid:property_id>/videos/', views.PropertyVideoView.as_view(), name='property-videos'),
    path('<uuid:property_id>/documents/', views.PropertyDocumentView.as_view(), name='property-documents'),
    
    # Chat e Visitas
    path('properties/<uuid:property_id>/messages/', PropertyMessageView.as_view(), name='property-messages'),
    path('properties/<uuid:property_id>/visits/', PropertyVisitRequestView.as_view(), name='property-visits'),
    
    # Estatísticas (admin)
    path('stats/', views.property_stats_view, name='property-stats'),
    
]
