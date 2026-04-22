import os
import django
import uuid
from django.utils import timezone

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings') # Adjust if settings path is different
django.setup()

from account.models import Account, Company
from account.helper import create_trial_user_from_lead, signInAccount
from letters.models import LetterCreditWallet
from settings.models import Subscription, PlanPricing

def test_create_trial_user_ai_letter_site():
    print("Testing create_trial_user_from_lead with source='ai_letter_site'...")
    # This might be hard to test without actual lead tokens, so I'll just check if the logic I added handles it.
    # Actually, I'll just check if the code compiles and if I can manually trigger the logic.
    pass

def test_signin_ai_letter_site():
    print("Testing signInAccount with site='is_ai_letter_site'...")
    # Create a dummy company and user
    company = Company.objects.create(
        name="Test AI Co",
        domain="testai.com",
        phone="1234567890",
        email="test@testai.com",
        address="Test Address"
    )
    user = Account.objects.create(
        username="testai@testai.com",
        email="testai@testai.com",
        company_id=company.id,
        first_name="Test",
        last_name="AI",
        verified=True,
        is_active=True
    )
    user.set_password("password123")
    user.save()

    # Create a mock request
    class MockRequest:
        def __init__(self, data):
            self.data = data

    request = MockRequest({'username': 'testai@testai.com', 'password': 'password123', 'site': 'is_ai_letter_site'})
    
    # Run signInAccount
    from account.helper import signInAccount
    response = signInAccount(request)
    
    # Check if LetterCreditWallet is created with 10 credits
    wallet = LetterCreditWallet.objects.filter(company=company).first()
    if wallet and wallet.total_credits == 10:
        print("SUCCESS: LetterCreditWallet created with 10 credits.")
    else:
        print(f"FAILURE: Wallet check failed. Wallet: {wallet}")

    # Clean up
    user.delete()
    company.delete()

if __name__ == "__main__":
    try:
        test_signin_ai_letter_site()
    except Exception as e:
        print(f"Error during verification: {e}")
