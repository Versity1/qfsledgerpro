from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UserProfile, ConnectWallet, AssetRecoveryForm, KYCVerification,
    Crytocurrency, AdminWallet, UserCryptoHolding, Deposit, Withdrawal, TotalBalance
)

# User Profile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'email_verified', 'subscribe_newsletter', 'created_at')
    list_filter = ('email_verified', 'subscribe_newsletter', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')

# Connect Wallet Admin
@admin.register(ConnectWallet)
class ConnectWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'wallet_type_display', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

    def wallet_type_display(self, obj):
        if obj.mnemonic_phrase:
            return "Mnemonic"
        elif obj.keystore_json:
            return "Keystore"
        elif obj.private_key:
            return "Private Key"
        return "Unknown"
    wallet_type_display.short_description = "Wallet Type"

# Asset Recovery Admin
@admin.register(AssetRecoveryForm)
class AssetRecoveryFormAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'wallet_address', 'submitted_at')
    list_filter = ('submitted_at',)
    search_fields = ('user__username', 'email', 'wallet_address')
    readonly_fields = ('submitted_at',)

# KYC Verification Admin
@admin.register(KYCVerification)
class KYCVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'status_badge', 'submitted_at')
    list_filter = ('status', 'document_type', 'submitted_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('submitted_at', 'reviewed_at', 'created_at', 'updated_at')
    actions = ['approve_kyc', 'reject_kyc']

    def status_badge(self, obj):
        colors = {
            'verified': 'green',
            'pending': 'orange',
            'rejected': 'red',
            'not_submitted': 'gray',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def approve_kyc(self, request, queryset):
        queryset.update(status='verified')
    approve_kyc.short_description = "Mark selected as Verified"

    def reject_kyc(self, request, queryset):
        queryset.update(status='rejected')
    reject_kyc.short_description = "Mark selected as Rejected"

# Cryptocurrency Admin
@admin.register(Crytocurrency)
class CrytocurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'coin_price', 'market_percentage', 'logo_preview')
    search_fields = ('name', 'symbol')
    list_editable = ('coin_price', 'market_percentage')

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="width: 30px; height: 30px;" />', obj.logo.url)
        return "-"
    logo_preview.short_description = "Logo"

# Admin Wallet Admin
@admin.register(AdminWallet)
class AdminWalletAdmin(admin.ModelAdmin):
    list_display = ('cryptocurrency', 'wallet_address', 'is_active', 'created_at')
    list_filter = ('is_active', 'cryptocurrency')
    search_fields = ('wallet_address', 'cryptocurrency__name')

# User Crypto Holding Admin
@admin.register(UserCryptoHolding)
class UserCryptoHoldingAdmin(admin.ModelAdmin):
    list_display = ('user', 'cryptocurrency', 'amount', 'amount_in_usd', 'acquired_at')
    list_filter = ('cryptocurrency', 'acquired_at')
    search_fields = ('user__username', 'cryptocurrency__symbol')

# Deposit Admin
@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'cryptocurrency', 'amount_in_usd', 'status_badge', 'created_at')
    list_filter = ('status', 'cryptocurrency', 'created_at')
    search_fields = ('user__username', 'tx_hash')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_completed', 'mark_failed']

    def status_badge(self, obj):
        colors = {
            'completed': 'green',
            'pending': 'orange',
            'failed': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def mark_completed(self, request, queryset):
        for deposit in queryset:
            deposit.status = 'completed'
            deposit.save() # Triggers signal/save method logic
    mark_completed.short_description = "Mark selected as Completed"

    def mark_failed(self, request, queryset):
        queryset.update(status='failed')
    mark_failed.short_description = "Mark selected as Failed"

# Withdrawal Admin
@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('user', 'cryptocurrency', 'amount_in_usd', 'status_badge', 'created_at')
    list_filter = ('status', 'cryptocurrency', 'created_at')
    search_fields = ('user__username', 'user_wallet_address', 'tx_hash')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_completed', 'mark_failed']

    def status_badge(self, obj):
        colors = {
            'completed': 'green',
            'pending': 'orange',
            'failed': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def mark_completed(self, request, queryset):
        for withdrawal in queryset:
            withdrawal.status = 'completed'
            withdrawal.save() # Triggers signal/save method logic
    mark_completed.short_description = "Mark selected as Completed"

    def mark_failed(self, request, queryset):
        queryset.update(status='failed')
    mark_failed.short_description = "Mark selected as Failed"

# Total Balance Admin
@admin.register(TotalBalance)
class TotalBalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_usd_balance', 'last_updated')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('last_updated',)
