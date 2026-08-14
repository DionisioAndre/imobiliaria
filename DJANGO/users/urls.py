from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'users'

urlpatterns = [
    # Autenticação
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.PasswordChangeView.as_view(), name='change-password'),
    path('stats/', views.user_stats_view, name='user-stats'),
    
    # Verificação
    path('verification/', views.UserVerificationView.as_view(), name='verification-list'),
    
    # URLs de administração
    path('admin/users/', views.AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/users/<uuid:pk>/', views.AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/verifications/', views.AdminVerificationListView.as_view(), name='admin-verification-list'),
    path('admin/verifications/<uuid:pk>/approve/', views.approve_verification_view, name='admin-approve-verification'),
    path('admin/verifications/<uuid:pk>/reject/', views.reject_verification_view, name='admin-reject-verification'),
]
