from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .models import Subscription, CreditWallet
import logging

logger = logging.getLogger(__name__)

@shared_task
def deactivate_expired_subscriptions():
    """
    Task to deactivate subscriptions that have passed their end date.
    Runs daily at midnight.
    """
    try:
        now = timezone.now()
        # Find all active subscriptions that have an end date in the past
        expired_subscriptions = Subscription.objects.filter(
            is_active=True,
            end_date__isnull=False,
            end_date__lt=now
        )
        
        count = expired_subscriptions.count()
        if count > 0:
            expired_subscriptions.update(is_active=False)
            logger.info(f"Deactivated {count} expired subscriptions")
            return f"Deactivated {count} expired subscriptions"
        return "No expired subscriptions to deactivate"
    except Exception as e:
        logger.error(f"Error in deactivate_expired_subscriptions: {str(e)}", exc_info=True)
        raise


@shared_task
def reset_daily_credits():
    """
    Task to reset daily credit usage and handle credit rollover.
    Should run daily at midnight after deactivate_expired_subscriptions.
    """
    try:
        updated_wallets = 0
        rollover_wallets = 0
        
        # Get all active daily credit wallets
        daily_wallets = CreditWallet.objects.filter(
            isdayli=True,
            iscredit=True
        )
        
        with transaction.atomic():
            for wallet in daily_wallets:
                if wallet.used_credit > 0:
                    # Calculate excess credits (if any)
                    excess_credits = max(0, wallet.used_credit - wallet.total_credit)
                    
                    if excess_credits > 0:
                        # If there's excess, set used_credit to excess value
                        wallet.used_credit = excess_credits
                        rollover_wallets += 1
                    else:
                        # Otherwise, reset to 0
                        wallet.used_credit = 0
                    
                    wallet.save(update_fields=['used_credit'])
                    updated_wallets += 1
        
        logger.info(
            f"Reset daily credits for {updated_wallets} wallets. "
            f"{rollover_wallets} wallets had credits rolled over to next day."
        )
        
        return {
            'status': 'success',
            'updated_wallets': updated_wallets,
            'rollover_wallets': rollover_wallets,
            'message': f'Successfully updated {updated_wallets} wallets with {rollover_wallets} rollovers'
        }
        
    except Exception as e:
        logger.error(f"Error in reset_daily_credits: {str(e)}", exc_info=True)
        raise
