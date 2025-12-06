
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
