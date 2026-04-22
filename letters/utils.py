from django.conf import settings
from openai import OpenAI
import json
from .models import GeneratedLetter, LetterCreditWallet, LetterCreditTransaction
from account.models import Company



def check_and_deduct_letter_credit(func):
    def wrapper(request, letter_type, prompt, input_data, candidate_name=None, letter_category=None, letter=None):

        if not (hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'company_id')):
            return None, "Authentication required to generate letters."

        company = Company.objects.filter(id=request.user.company_id).first()
        if not company:
            return None, "Company not found."

        wallet, _ = LetterCreditWallet.objects.get_or_create(company=company)

        if wallet.remaining_credits <= 0:
            return None, "Insufficient Credits"

        # ✅ Get saved_letter also
        generated_content, saved_letter, error = func(
            request, letter_type, prompt, input_data, candidate_name, letter_category, letter
        )

        if error:
            return None, error

        wallet.used_credits += 1
        wallet.save(update_fields=['used_credits', 'updated'])

        LetterCreditTransaction.objects.create(
            company=company,
            wallet=wallet,
            transaction_type='deduction',
            credits=1,
            letter_type=letter_type,
            letter=saved_letter,  # ✅ Correct reference
        )

        return generated_content, None

    return wrapper


@check_and_deduct_letter_credit
def generate_and_save_letter(request, letter_type, prompt, input_data, candidate_name=None, letter_category=None, id=None):
    """
    Utility function to generate a letter using OpenAI and save it to the database.
    """
    try:
        api_key = settings.OPENAI_API_KEY
        client = OpenAI(api_key=api_key)

        # Standardizing on chat.completions.create as it's the most common and robust
        response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": f"Generate {letter_type}"
                    }
                ]
            )
        
        # Print letter name, price and token usage
        usage = getattr(response, 'usage', None)
        if usage:
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            
            # Calculate actual OpenAI cost for gpt-4o-mini
            # Input: $0.15 / 1M tokens, Output: $0.60 / 1M tokens
            input_cost = (prompt_tokens / 1000000) * 0.15
            output_cost = (completion_tokens / 1000000) * 0.60
            total_cost = input_cost + output_cost
            
            print(f"Letter Name: {letter_type}")
            print(f"Price (USD): {total_cost:.6f}")
            print(f"Tokens In (Prompt): {prompt_tokens}")
            print(f"Tokens Out (Completion): {completion_tokens}")

        generated_content = response.choices[0].message.content

        # Get company context
        company = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            company = Company.objects.filter(id=request.user.company_id).first()
        
        # If no company from request.user, try to get it from data if provided
        if not company and 'Company_Name' in input_data:
             # This is a fallback, ideally we want authenticated users
             pass
            
        saved_letter = None
        if company:
            saved_letter, created = GeneratedLetter.objects.update_or_create(
                id=id,
                defaults={
                    'company': company,
                    'created_by': request.user if request.user.is_authenticated else None,
                    'letter_type': letter_type,
                    'letter_category': letter_category,
                    'candidate_name': candidate_name,
                    'content': generated_content,
                    'input_data': input_data
                }
            )
            
        return generated_content, saved_letter, None

    except Exception as e:
        return None, None, str(e)

