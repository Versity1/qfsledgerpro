from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
# Create your models here.

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

class ConnectWallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Changed to OneToOneField
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
class AssetRecoveryForm(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
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
    wallet_address = models.CharField(max_length=255, unique=True)
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