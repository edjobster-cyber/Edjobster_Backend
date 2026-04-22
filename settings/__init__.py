# These will be imported on first use to avoid circular imports
check_subscription_and_credits_for_ai = None
deduct_credits_after = None

def lazy_import_decorators():
    global check_subscription_and_credits_for_ai, deduct_credits_after
    if check_subscription_and_credits_for_ai is None or deduct_credits_after is None:
        from .decorators import check_subscription_and_credits_for_ai as _check_credits
        from .decorators import deduct_credits_after as _deduct_credits
        check_subscription_and_credits_for_ai = _check_credits
        deduct_credits_after = _deduct_credits
    return check_subscription_and_credits_for_ai, deduct_credits_after

__all__ = ['check_subscription_and_credits_for_ai', 'deduct_credits_after', 'lazy_import_decorators']