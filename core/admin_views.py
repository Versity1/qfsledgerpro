# ==========================================
# ADMIN MANAGEMENT VIEWS
# ==========================================

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import UserCryptoHolding, TotalBalance, Deposit, Withdrawal, UserInvestment, CreditCardRequest, MedbedRequest, KYCVerification

def is_admin(user):
    """Check if user is an admin"""
    return user.is_staff and user.is_superuser

@user_passes_test(is_admin)
def admin_users_view(request):
    """List all users"""
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'custom_admin/users.html', {'users': users})


@user_passes_test(is_admin)
def admin_user_detail_view(request, user_id):
    """View user details"""
    user = get_object_or_404(User, id=user_id)
    
    # Get user stats
    holdings = UserCryptoHolding.objects.filter(user=user)
    total_balance = TotalBalance.objects.filter(user=user).first()
    deposits = Deposit.objects.filter(user=user).order_by('-created_at')[:5]
    withdrawals = Withdrawal.objects.filter(user=user).order_by('-created_at')[:5]
    
    context = {
        'user_obj': user,
        'holdings': holdings,
        'total_balance': total_balance,
        'deposits': deposits,
        'withdrawals': withdrawals
    }
    return render(request, 'custom_admin/user_detail.html', context)


@user_passes_test(is_admin)
def admin_deposits_view(request):
    """List all deposits"""
    deposits = Deposit.objects.all().order_by('-created_at')
    return render(request, 'custom_admin/deposits.html', {'deposits': deposits})


@user_passes_test(is_admin)
def admin_update_deposit(request, deposit_id):
    """Update deposit status"""
    if request.method == 'POST':
        deposit = get_object_or_404(Deposit, id=deposit_id)
        action = request.POST.get('action')
        
        if action == 'approve':
            deposit.status = 'completed'
            deposit.save()
            messages.success(request, f'Deposit #{deposit_id} approved successfully!')
        elif action == 'reject':
            deposit.status = 'failed'
            deposit.save()
            messages.warning(request, f'Deposit #{deposit_id} rejected.')
    
    return redirect('admin_deposits')


@user_passes_test(is_admin)
def admin_withdrawals_view(request):
    """List all withdrawals"""
    withdrawals = Withdrawal.objects.all().order_by('-created_at')
    return render(request, 'custom_admin/withdrawals.html', {'withdrawals': withdrawals})


@user_passes_test(is_admin)
def admin_update_withdrawal(request, withdrawal_id):
    """Update withdrawal status"""
    if request.method == 'POST':
        withdrawal = get_object_or_404(Withdrawal, id=withdrawal_id)
        action = request.POST.get('action')
        
        if action == 'approve':
            withdrawal.status = 'completed'
            withdrawal.save()
            messages.success(request, f'Withdrawal #{withdrawal_id} approved successfully!')
        elif action == 'reject':
            withdrawal.status = 'failed'
            withdrawal.save()
            messages.warning(request, f'Withdrawal #{withdrawal_id} rejected.')
    
    return redirect('admin_withdrawals')


@user_passes_test(is_admin)
def admin_investments_view(request):
    """List all investments"""
    investments = UserInvestment.objects.all().order_by('-start_date')
    return render(request, 'custom_admin/investments.html', {'investments': investments})


@user_passes_test(is_admin)
def admin_credit_cards_view(request):
    """List all credit card requests"""
    requests = CreditCardRequest.objects.all().order_by('-created_at')
    return render(request, 'custom_admin/credit_cards.html', {'requests': requests})


@user_passes_test(is_admin)
def admin_update_credit_card(request, request_id):
    """Update credit card request status"""
    if request.method == 'POST':
        card_request = get_object_or_404(CreditCardRequest, id=request_id)
        action = request.POST.get('action')
        
        if action == 'approve':
            card_request.status = 'approved'
            card_request.save()  # This will auto-generate card details
            messages.success(request, f'Credit card request #{request_id} approved! Card details generated.')
        elif action == 'reject':
            card_request.status = 'rejected'
            card_request.save()
            messages.warning(request, f'Credit card request #{request_id} rejected.')
        elif action == 'ship':
            card_request.status = 'shipped'
            card_request.save()
            messages.success(request, f'Credit card #{request_id} marked as shipped.')
    
    return redirect('admin_credit_cards')


@user_passes_test(is_admin)
def admin_medbed_view(request):
    """List all medbed requests"""
    requests = MedbedRequest.objects.all().order_by('-created_at')
    return render(request, 'custom_admin/medbed.html', {'requests': requests})


@user_passes_test(is_admin)
def admin_update_medbed(request, request_id):
    """Update medbed request status"""
    if request.method == 'POST':
        medbed_request = get_object_or_404(MedbedRequest, id=request_id)
        action = request.POST.get('action')
        
        if action == 'confirm':
            medbed_request.status = 'confirmed'
            medbed_request.save()
            messages.success(request, f'Medbed request #{request_id} confirmed!')
        elif action == 'complete':
            medbed_request.status = 'completed'
            medbed_request.save()
            messages.success(request, f'Medbed request #{request_id} marked as completed.')
        elif action == 'cancel':
            medbed_request.status = 'cancelled'
            medbed_request.save()
            messages.warning(request, f'Medbed request #{request_id} cancelled.')
    
    return redirect('admin_medbed')


@user_passes_test(is_admin)
def admin_kyc_view(request):
    """List all KYC submissions"""
    kyc_submissions = KYCVerification.objects.all().order_by('-submitted_at')
    return render(request, 'custom_admin/kyc.html', {'kyc_submissions': kyc_submissions})


@user_passes_test(is_admin)
def admin_update_kyc(request, kyc_id):
    """Update KYC status"""
    if request.method == 'POST':
        kyc = get_object_or_404(KYCVerification, id=kyc_id)
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'verify':
            kyc.status = 'verified'
            kyc.review_notes = notes
            kyc.save()
            messages.success(request, f'KYC #{kyc_id} verified successfully!')
        elif action == 'reject':
            kyc.status = 'rejected'
            kyc.review_notes = notes
            kyc.save()
            messages.warning(request, f'KYC #{kyc_id} rejected.')
    
    return redirect('admin_kyc')
