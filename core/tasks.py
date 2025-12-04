from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .models import UserInvestment, InvestmentTransaction, TotalBalance, UserCryptoHolding
from .utils import send_mail  # We'll need a specific email function later

@shared_task
def distribute_daily_profits():
    """
    Calculate and distribute daily profits for all active investments.
    """
    active_investments = UserInvestment.objects.filter(status='active')
    
    for investment in active_investments:
        # Check if profit should be distributed today (e.g., not already distributed)
        today = timezone.now().date()
        if investment.last_profit_date == today:
            continue
            
        # Calculate daily profit
        daily_profit = investment.daily_profit
        
        with transaction.atomic():
            # Update investment stats
            investment.total_profit_earned += daily_profit
            investment.last_profit_date = today
            investment.save()
            
            # Record transaction
            InvestmentTransaction.objects.create(
                investment=investment,
                transaction_type='daily_profit',
                amount=daily_profit,
                description=f"Daily profit for {investment.plan.name} plan"
            )
            
            # Note: We are NOT adding to user balance yet, only accumulating in the investment record.
            # If you want to release profit daily to balance, uncomment below:
            # holding = UserCryptoHolding.objects.get(user=investment.user, cryptocurrency=investment.cryptocurrency)
            # holding.amount_in_usd += daily_profit
            # holding.save()
            # TotalBalance.update_user_balance(investment.user)
            
    return f"Processed daily profits for {active_investments.count()} investments."

@shared_task
def process_matured_investments():
    """
    Check for matured investments and release capital + profit.
    """
    today = timezone.now().date()
    matured_investments = UserInvestment.objects.filter(status='active', end_date__lte=today)
    
    for investment in matured_investments:
        with transaction.atomic():
            # Calculate total return (Principal + Total Profit)
            # Note: If we were releasing profit daily, we would only return principal here.
            # But based on the model, we accumulate profit and release at end (or user can withdraw).
            # Let's assume we release everything to the user's crypto balance now.
            
            total_return_usd = investment.amount_in_usd + investment.total_profit_earned
            
            # Update user balance
            # We need to find the user's holding for this crypto
            holding, created = UserCryptoHolding.objects.get_or_create(
                user=investment.user, 
                cryptocurrency=investment.cryptocurrency,
                defaults={'amount': 0, 'amount_in_usd': 0}
            )
            
            holding.amount_in_usd += total_return_usd
            # We should also update the 'amount' (crypto quantity) based on current price
            # But price might have changed. For simplicity, we just add USD value 
            # and maybe recalculate crypto amount based on current price?
            # Or better, just add the USD value as that's what we track for profit.
            # Let's update crypto amount based on current price to keep it consistent.
            if investment.cryptocurrency.coin_price > 0:
                holding.amount += total_return_usd / investment.cryptocurrency.coin_price
            
            holding.save()
            
            # Update Total Balance
            TotalBalance.update_user_balance(investment.user)
            
            # Mark investment as completed
            investment.status = 'completed'
            investment.save()
            
            # Record transaction
            InvestmentTransaction.objects.create(
                investment=investment,
                transaction_type='capital_return',
                amount=total_return_usd,
                description=f"Capital return + profit for {investment.plan.name} plan"
            )
            
            # Send email
            # send_investment_completed_email(investment.user, investment) # To be implemented
            
    return f"Processed {matured_investments.count()} matured investments."
