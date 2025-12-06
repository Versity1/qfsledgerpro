
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
