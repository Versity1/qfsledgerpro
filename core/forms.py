from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full focus:input-primary',
            'placeholder': 'John'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full focus:input-primary',
            'placeholder': 'Doe'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'input input-bordered w-full focus:input-primary',
            'placeholder': 'john.doe@example.com'
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full focus:input-primary rounded-l-none',
            'placeholder': '+399 555 0123'
        })
    )
    subscribe_newsletter = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary'
        })
    )
    
    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "password1", "password2", "phone_number", "subscribe_newsletter")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'input input-bordered w-full focus:input-primary pr-16',
            'placeholder': 'johndoe'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'input input-bordered w-full focus:input-primary pr-10',
            'placeholder': 'Create a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'input input-bordered w-full focus:input-primary',
            'placeholder': 'Confirm your password'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            from .models import UserProfile
            UserProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number', ''),
                subscribe_newsletter=self.cleaned_data.get('subscribe_newsletter', False)
            )
        return user


class LoginForm(forms.Form):
    """Form for user login"""
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full focus:input-primary',
            'placeholder': 'Enter your email or username'
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full focus:input-primary',
            'placeholder': 'Enter your password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary checkbox-sm'
        })
    )


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Email Address'
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Phone Number'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class DepositRequestForm(forms.Form):
    """Form for requesting a deposit"""
    cryptocurrency = forms.ModelChoiceField(
        queryset=None,
        required=True,
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full'
        }),
        empty_label="Select Cryptocurrency"
    )
    amount_in_usd = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        min_value=0.01,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '0.00',
            'step': '0.01'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Crytocurrency
        self.fields['cryptocurrency'].queryset = Crytocurrency.objects.all()


class WithdrawalRequestForm(forms.Form):
    """Form for requesting a withdrawal"""
    cryptocurrency = forms.ModelChoiceField(
        queryset=None,
        required=True,
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full'
        }),
        empty_label="Select Cryptocurrency"
    )
    amount_in_usd = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        min_value=0.01,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '0.00',
            'step': '0.01'
        })
    )
    user_wallet_address = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full font-mono',
            'placeholder': 'Enter your external wallet address'
        })
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Crytocurrency, UserCryptoHolding
        user_cryptos = UserCryptoHolding.objects.filter(
            user=user,
            amount_in_usd__gt=0
        ).values_list('cryptocurrency', flat=True)
        self.fields['cryptocurrency'].queryset = Crytocurrency.objects.filter(id__in=user_cryptos)
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        cryptocurrency = cleaned_data.get('cryptocurrency')
        amount_in_usd = cleaned_data.get('amount_in_usd')

        if cryptocurrency and amount_in_usd:
            from .models import UserCryptoHolding
            try:
                holding = UserCryptoHolding.objects.get(
                    user=self.user,
                    cryptocurrency=cryptocurrency
                )
                if holding.amount_in_usd < amount_in_usd:
                    raise ValidationError(
                        f'Insufficient balance. You have ${holding.amount_in_usd} in {cryptocurrency.symbol}'
                    )
            except UserCryptoHolding.DoesNotExist:
                raise ValidationError(f'You have no {cryptocurrency.symbol} balance')

        return cleaned_data


class WalletConnectForm(forms.Form):
    """Form for connecting wallet"""
    CONNECTION_METHODS = [
        ('mnemonic', 'Mnemonic Phrase (12-24 words)'),
        ('keystore', 'Keystore JSON'),
        ('private_key', 'Private Key'),
        
    ]

    connection_method = forms.ChoiceField(
        choices=CONNECTION_METHODS,
        required=True,
        widget=forms.RadioSelect(attrs={
            'class': 'radio radio-primary'
        })
    )
    mnemonic_phrase = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full font-mono',
            'placeholder': 'Enter your 12 or 24-word mnemonic phrase',
            'rows': 3
        })
    )
    keystore_json = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full font-mono',
            'placeholder': 'Paste your keystore JSON here',
            'rows': 5
        })
    )
    # platform
    # Platform Choices matching models.py
    PLATFORM_CHOICES = [
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
    platform = forms.ChoiceField(
        choices=PLATFORM_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full font-mono',
        })
    )
    private_key = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full font-mono',
            'placeholder': 'Enter your private key',
            'type': 'password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('connection_method')

        if method == 'mnemonic' and not cleaned_data.get('mnemonic_phrase'):
            raise ValidationError('Mnemonic phrase is required')
        elif method == 'keystore' and not cleaned_data.get('keystore_json'):
            raise ValidationError('Keystore JSON is required')
        elif method == 'private_key' and not cleaned_data.get('private_key'):
            raise ValidationError('Private key is required')

        return cleaned_data


class AssetRecoveryRequestForm(forms.ModelForm):
    """Form for asset recovery requests"""
    class Meta:
        from .models import AssetRecoveryForm as AssetRecoveryModel
        model = AssetRecoveryModel
        fields = ['full_name', 'email', 'phone_number', 'wallet_address', 'asset_details', 'additional_info']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Your Full Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'your.email@example.com'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+1234567890'
            }),
            'wallet_address': forms.TextInput(attrs={
                'class': 'input input-bordered w-full font-mono',
                'placeholder': 'Your wallet address'
            }),
            'asset_details': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'placeholder': 'Describe the assets you want to recover (type, amount, circumstances)',
                'rows': 4
            }),
            'additional_info': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'placeholder': 'Any additional information that might help (optional)',
                'rows': 3
            }),
        }


class KYCSubmissionForm(forms.ModelForm):
    """Form for KYC document submission"""
    class Meta:
        from .models import KYCVerification
        model = KYCVerification
        fields = ['document_type', 'document_image']
        widgets = {
            'document_type': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'document_image': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': 'image/*'
            })
        }


class CreateInvestmentForm(forms.Form):
    """Form for creating a new investment"""
    cryptocurrency = forms.ModelChoiceField(
        queryset=None,
        required=True,
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full'
        }),
        empty_label="Select Payment Wallet"
    )
    amount = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        required=True,
        label="Amount (USD)",
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Enter amount in USD',
            'step': '0.01'
        })
    )

    def __init__(self, user, plan, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.plan = plan
        
        # Only show cryptos where user has balance
        from .models import UserCryptoHolding, Crytocurrency
        user_holdings = UserCryptoHolding.objects.filter(
            user=user, 
            amount_in_usd__gt=0
        ).values_list('cryptocurrency', flat=True)
        
        self.fields['cryptocurrency'].queryset = Crytocurrency.objects.filter(id__in=user_holdings)
        
        # Set min/max help text
        self.fields['amount'].help_text = f"Min: ${plan.min_amount} - Max: ${plan.max_amount}"
        self.fields['amount'].widget.attrs['min'] = plan.min_amount
        self.fields['amount'].widget.attrs['max'] = plan.max_amount

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount:
            if amount < self.plan.min_amount:
                raise ValidationError(f"Minimum investment amount is ${self.plan.min_amount}")
            if amount > self.plan.max_amount:
                raise ValidationError(f"Maximum investment amount is ${self.plan.max_amount}")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        cryptocurrency = cleaned_data.get('cryptocurrency')
        amount = cleaned_data.get('amount')

        if cryptocurrency and amount:
            from .models import UserCryptoHolding
            try:
                holding = UserCryptoHolding.objects.get(
                    user=self.user,
                    cryptocurrency=cryptocurrency
                )
                if holding.amount_in_usd < amount:
                    raise ValidationError(
                        f"Insufficient balance in {cryptocurrency.symbol}. You have ${holding.amount_in_usd}."
                    )
            except UserCryptoHolding.DoesNotExist:
                raise ValidationError(f"You do not have any balance in {cryptocurrency.symbol}.")
        
        return cleaned_data


class MedbedRequestForm(forms.ModelForm):
    """Form for Medbed requests"""
    class Meta:
        from .models import MedbedRequest
        model = MedbedRequest
        fields = ['full_name', 'email', 'phone_number', 'request_type', 'preferred_date', 'medical_conditions']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Your Full Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'your.email@example.com'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+1234567890'
            }),
            'request_type': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'preferred_date': forms.DateInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'date'
            }),
            'medical_conditions': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'placeholder': 'Please describe your condition...',
                'rows': 4
            }),
        }


class AssetRecoveryRequestForm(forms.ModelForm):
    """Form for asset recovery requests"""
    class Meta:
        from .models import AssetRecoveryForm as AssetRecoveryModel
        model = AssetRecoveryModel
        fields = ['full_name', 'email', 'phone_number', 'wallet_address', 'asset_details', 'additional_info']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Your Full Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'your.email@example.com'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+1234567890'
            }),
            'wallet_address': forms.TextInput(attrs={
                'class': 'input input-bordered w-full font-mono',
                'placeholder': 'Your wallet address'
            }),
            'asset_details': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'placeholder': 'Describe the assets you want to recover (type, amount, circumstances)',
                'rows': 4
            }),
            'additional_info': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'placeholder': 'Any additional information that might help (optional)',
                'rows': 3
            }),
        }


class KYCSubmissionForm(forms.ModelForm):
    """Form for KYC document submission"""
    class Meta:
        from .models import KYCVerification
        model = KYCVerification
        fields = ['document_type', 'document_image']
        widgets = {
            'document_type': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'document_image': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': 'image/*'
            })
        }


class CreateInvestmentForm(forms.Form):
    """Form for creating a new investment"""
    cryptocurrency = forms.ModelChoiceField(
        queryset=None,
        required=True,
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full'
        }),
        empty_label="Select Payment Wallet"
    )
    amount = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        required=True,
        label="Amount (USD)",
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Enter amount in USD',
            'step': '0.01'
        })
    )

    def __init__(self, user, plan, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.plan = plan
        
        # Only show cryptos where user has balance
        from .models import UserCryptoHolding, Crytocurrency
        user_holdings = UserCryptoHolding.objects.filter(
            user=user, 
            amount_in_usd__gt=0
        ).values_list('cryptocurrency', flat=True)
        
        self.fields['cryptocurrency'].queryset = Crytocurrency.objects.filter(id__in=user_holdings)
        
        # Set min/max help text
        self.fields['amount'].help_text = f"Min: ${plan.min_amount} - Max: ${plan.max_amount}"
        self.fields['amount'].widget.attrs['min'] = plan.min_amount
        self.fields['amount'].widget.attrs['max'] = plan.max_amount

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount:
            if amount < self.plan.min_amount:
                raise ValidationError(f"Minimum investment amount is ${self.plan.min_amount}")
            if amount > self.plan.max_amount:
                raise ValidationError(f"Maximum investment amount is ${self.plan.max_amount}")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        cryptocurrency = cleaned_data.get('cryptocurrency')
        amount = cleaned_data.get('amount')

        if cryptocurrency and amount:
            from .models import UserCryptoHolding
            try:
                holding = UserCryptoHolding.objects.get(
                    user=self.user,
                    cryptocurrency=cryptocurrency
                )
                if holding.amount_in_usd < amount:
                    raise ValidationError(
                        f"Insufficient balance in {cryptocurrency.symbol}. You have ${holding.amount_in_usd}."
                    )
            except UserCryptoHolding.DoesNotExist:
                raise ValidationError(f"You do not have any balance in {cryptocurrency.symbol}.")
        
        return cleaned_data



class CreditCardRequestForm(forms.ModelForm):
    """Form for QFS Credit Card requests"""
    class Meta:
        from .models import CreditCardRequest
        model = CreditCardRequest
        fields = ['card_type', 'full_name', 'phone_number', 'address']
        widgets = {
            'card_type': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Full Name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Phone Number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Shipping Address'
            }),
        }