from django.urls import path
from . import views

app_name = 'contracts'

urlpatterns = [
    # Contratos
    path('', views.RentalContractListView.as_view(), name='contract-list'),
    path('<uuid:id>/', views.RentalContractDetailView.as_view(), name='contract-detail'),
    path('create/', views.RentalContractCreateView.as_view(), name='contract-create'),
    path('<uuid:id>/update/', views.RentalContractUpdateView.as_view(), name='contract-update'),
    path('<uuid:id>/delete/', views.RentalContractDeleteView.as_view(), name='contract-delete'),
    
    # Ações de contrato
    path('<uuid:id>/sign/', views.sign_contract_view, name='contract-sign'),
    path('<uuid:id>/activate/', views.activate_contract_view, name='contract-activate'),
    path('<uuid:id>/terminate/', views.terminate_contract_view, name='contract-terminate'),
    path('my-contracts/', views.my_contracts_view, name='my-contracts'),
    path('stats/', views.contract_stats_view, name='contract-stats'),
    
    # Pagamentos
    path('<uuid:contract_id>/payments/', views.RentalPaymentListView.as_view(), name='payment-list'),
    path('payments/<uuid:id>/', views.RentalPaymentDetailView.as_view(), name='payment-detail'),
    path('<uuid:contract_id>/payments/<uuid:payment_id>/paid/', views.mark_payment_as_paid_view, name='payment-mark-paid'),
    
    # Renovações
    path('<uuid:contract_id>/renewals/', views.ContractRenewalListView.as_view(), name='renewal-list'),
    path('<uuid:contract_id>/renewals/create/', views.ContractRenewalCreateView.as_view(), name='renewal-create'),
    path('<uuid:contract_id>/renewals/<uuid:id>/', views.ContractRenewalDetailView.as_view(), name='renewal-detail'),
    path('<uuid:contract_id>/renewals/<uuid:renewal_id>/approve/', views.approve_renewal_view, name='renewal-approve'),
    
    # Estatísticas admin
    path('admin/stats/', views.admin_contract_stats_view, name='admin-contract-stats'),
]
