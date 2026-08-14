from django.urls import path
from . import views

app_name = 'ads'

urlpatterns = [
    # Pacotes de patrocínio
    path('packages/', views.SponsorshipPackageListView.as_view(), name='package-list'),
    
    # Patrocínios
    path('', views.SponsorshipListView.as_view(), name='sponsorship-list'),
    path('<uuid:id>/', views.SponsorshipDetailView.as_view(), name='sponsorship-detail'),
    path('create/', views.SponsorshipCreateView.as_view(), name='sponsorship-create'),
    path('<uuid:id>/update/', views.SponsorshipUpdateView.as_view(), name='sponsorship-update'),
    path('<uuid:id>/delete/', views.SponsorshipDeleteView.as_view(), name='sponsorship-delete'),
    
    # Ações de patrocínio
    path('<uuid:id>/activate/', views.activate_sponsorship_view, name='sponsorship-activate'),
    path('<uuid:id>/cancel/', views.cancel_sponsorship_view, name='sponsorship-cancel'),
    path('my-sponsorships/', views.my_sponsorships_view, name='my-sponsorships'),
    path('stats/', views.sponsorship_stats_view, name='sponsorship-stats'),
    
    # Pagamentos
    path('<uuid:sponsorship_id>/payments/', views.SponsorshipPaymentListView.as_view(), name='payment-list'),
    path('<uuid:sponsorship_id>/payments/create/', views.SponsorshipPaymentCreateView.as_view(), name='payment-create'),
    
    # Ações de pagamento (admin)
    path('payments/<uuid:payment_id>/approve/', views.approve_payment_view, name='payment-approve'),
    path('payments/<uuid:payment_id>/reject/', views.reject_payment_view, name='payment-reject'),
    
    # Administração de pacotes
    path('admin/packages/', views.AdminSponsorshipPackageListView.as_view(), name='admin-package-list'),
    path('admin/packages/<uuid:id>/', views.AdminSponsorshipPackageDetailView.as_view(), name='admin-package-detail'),
    
    # Estatísticas admin
    path('admin/stats/', views.admin_sponsorship_stats_view, name='admin-sponsorship-stats'),
]
