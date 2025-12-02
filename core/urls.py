from django.urls import path
from . import views


urlpatterns = [
    # Authentication
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-complete/', views.password_reset_complete, name='password_reset_complete'),

    # Dashboard & Profile
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),

    # Crypto Operations
    path('deposit/', views.deposit_request_view, name='deposit'),
    path('withdraw/', views.withdrawal_request_view, name='withdraw'),
    path('transactions/', views.transactions_view, name='transactions'),

    # Wallet
    path('wallet/connect/', views.wallet_connect_view, name='wallet_connect'),
    path('wallet/disconnect/', views.wallet_disconnect_view, name='wallet_disconnect'),

    # Asset Recovery
    path('asset-recovery/', views.asset_recovery_request_view, name='asset_recovery'),
    path('asset-recovery/status/', views.asset_recovery_status_view, name='asset_recovery_status'),

    # KYC
    path('kyc/submit/', views.kyc_submit_view, name='kyc_submit'),
    path('kyc/status/', views.kyc_status_view, name='kyc_status'),
]