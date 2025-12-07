from django.urls import path
from . import views
from django.conf import settings

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-complete/', views.password_reset_complete, name='password_reset_complete'),
    
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('buy-crypto/', views.buy_crypto_view, name='buy_crypto'),
    
    path('deposit/', views.deposit_request_view, name='deposit'),
    path('withdraw/', views.withdrawal_request_view, name='withdraw'),
    path('transactions/', views.transactions_view, name='transactions'),
    
    path('wallet/connect/', views.wallet_connect_view, name='wallet_connect'),
    path('wallet/disconnect/', views.wallet_disconnect_view, name='wallet_disconnect'),
    
    path('asset-recovery/', views.asset_recovery_request_view, name='asset_recovery'),
    path('asset-recovery/status/', views.asset_recovery_status_view, name='asset_recovery_status'),
    
    path('kyc/submit/', views.kyc_submit_view, name='kyc_submit'),
    path('kyc/status/', views.kyc_status_view, name='kyc_status'),
    
    path('investments/plans/', views.investment_plans_view, name='investment_plans'),
    path('investments/create/<int:plan_id>/', views.create_investment_view, name='create_investment'),
    path('investments/my-investments/', views.my_investments_view, name='my_investments'),
    path('investments/detail/<int:investment_id>/', views.investment_detail_view, name='investment_detail'),
    
    path('medbed/request/', views.medbed_request_view, name='medbed_request'),
    path('medbed/success/', views.medbed_success_view, name='medbed_success'),
    
    path('credit-card/request/', views.credit_card_request_view, name='credit_card_request'),
    
    path('admin/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/users/', views.admin_users_view, name='admin_users'),
    path('admin/users/<int:user_id>/', views.admin_user_detail_view, name='admin_user_detail'),
    path('admin/users/<int:user_id>/edit-balance/', views.admin_edit_user_balance, name='admin_edit_user_balance'),
    path('admin/users/<int:user_id>/toggle-status/', views.admin_toggle_user_status, name='admin_toggle_user_status'),
    path('admin/users/<int:user_id>/reset-password/', views.admin_reset_user_password, name='admin_reset_user_password'),
    path('admin/users/<int:user_id>/impersonate/', views.admin_impersonate_user, name='admin_impersonate_user'),
    path('admin/users/<int:user_id>/send-email/', views.admin_send_email_to_user, name='admin_send_email_to_user'),
    path('admin/stop-impersonation/', views.admin_stop_impersonation, name='admin_stop_impersonation'),
    
    path('admin/deposits/', views.admin_deposits_view, name='admin_deposits'),
    path('admin/deposits/<int:deposit_id>/update/', views.admin_update_deposit, name='admin_update_deposit'),
    path('admin/deposits/<int:deposit_id>/edit/', views.admin_edit_deposit, name='admin_edit_deposit'),
    
    path('admin/withdrawals/', views.admin_withdrawals_view, name='admin_withdrawals'),
    path('admin/withdrawals/<int:withdrawal_id>/update/', views.admin_update_withdrawal, name='admin_update_withdrawal'),
    path('admin/withdrawals/<int:withdrawal_id>/edit/', views.admin_edit_withdrawal, name='admin_edit_withdrawal'),
    
    path('admin/investments/', views.admin_investments_view, name='admin_investments'),
    path('admin/investments/<int:investment_id>/edit/', views.admin_edit_investment, name='admin_edit_investment'),
    
    path('admin/credit-cards/', views.admin_credit_cards_view, name='admin_credit_cards'),
    path('admin/credit-cards/<int:request_id>/update/', views.admin_update_credit_card, name='admin_update_credit_card'),
    path('admin/credit-cards/<int:request_id>/detail/', views.admin_card_detail_view, name='admin_card_detail'),
    path('admin/credit-cards/<int:request_id>/ban/', views.admin_ban_card, name='admin_ban_card'),
    path('admin/credit-cards/<int:request_id>/unban/', views.admin_unban_card, name='admin_unban_card'),
    path('admin/credit-cards/<int:request_id>/update-details/', views.admin_update_card_details, name='admin_update_card_details'),
    path('admin/credit-cards/<int:request_id>/regulate/', views.admin_regulate_card_limits, name='admin_regulate_card_limits'),
    
    path('admin/medbed/', views.admin_medbed_view, name='admin_medbed'),
    path('admin/medbed/<int:request_id>/update/', views.admin_update_medbed, name='admin_update_medbed'),
    path('admin/kyc/', views.admin_kyc_view, name='admin_kyc'),
    path('admin/kyc/<int:kyc_id>/update/', views.admin_update_kyc, name='admin_update_kyc'),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)