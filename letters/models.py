from django.contrib.postgres.fields import ArrayField
from django.db import models
from account.models import Company, Account
import uuid

class GeneratedLetter(models.Model):
    LETTER_TYPES = [
        ('offer', 'Offer Letter'),
        ('appointment', 'Appointment Letter'),
        ('confirmation', 'Confirmation Letter'),
        ('experience', 'Experience Letter'),
        ('increment', 'Increment Letter'),
        ('relieving', 'Relieving Letter'),
        ('leave_policy', 'Leave Policy'),
        ('wfh_policy', 'WFH/Hybrid Policy'),
        ('freelancer_contract', 'Freelancer Contract'),
        ('nda', 'NDA'),
        ('onboarding', 'Onboarding Plan'),
        ('evp', 'EVP Builder'),
        ('branding_post', 'Employer Branding Post'),
    ]
    CATEGORY_TYPES = [
        ('letters','Letters'),
        ('policies','Policies'),
        ('contracts','Contracts'),
        ('employerbranding','Employer Branding')
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='generated_letters')
    created_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    letter_type = models.CharField(max_length=50, choices=LETTER_TYPES)
    letter_category = models.CharField(max_length=50, choices=CATEGORY_TYPES,null=True,blank=True)
    candidate_name = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField()
    input_data = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_letter_type_display()} - {self.candidate_name or 'N/A'} ({self.company.name})"

    class Meta:
        ordering = ['-created']

class LetterSettings(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='letter_settings')
    
    # Default Signatory
    signatory_name = models.CharField(max_length=255, null=True, blank=True)
    signatory_title = models.CharField(max_length=255, null=True, blank=True)
    signatory_email = models.EmailField(null=True, blank=True)
    signatory_phone = models.CharField(max_length=20, null=True, blank=True)
    
    # Document Header Settings
    show_company_logo = models.BooleanField(default=True)
    show_company_name = models.BooleanField(default=True)
    show_release_date = models.BooleanField(default=True)
    header_tagline = models.CharField(max_length=255, null=True, blank=True)
    header_background_color = models.CharField(max_length=7, default="#FFFFFF") # Hex color
    
    # Document Footer Settings
    show_address = models.BooleanField(default=True)
    show_contact_details = models.BooleanField(default=True)
    custom_footer_text = models.TextField(null=True, blank=True)
    footer_background_color = models.CharField(max_length=7, default="#F5F5F5") # Hex color
    useCompanyContext = models.BooleanField(default=True)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Letter Settings - {self.company.name}"


# ─── Letters Billing System ──────────────────────────────────────────────────

class LetterCreditPackage(models.Model):
    """
    Admin-defined credit packages that companies can purchase.
    e.g. "Starter Pack – 10 credits for ₹199"
    """
    name = models.CharField(max_length=100)
    credits = models.PositiveIntegerField(help_text="Number of letter generation credits this package gives.")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base price in INR (excl. GST).")
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                      help_text="Discounted price in INR (excl. GST). Leave blank for no discount.")
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def effective_price(self):
        """Returns the price the customer actually pays (before GST)."""
        return self.offer_price if self.offer_price else self.price

    def __str__(self):
        return f"{self.name} ({self.credits} credits)"

    class Meta:
        ordering = ['price']


class LetterCreditWallet(models.Model):
    """
    One credit wallet per company, dedicated to letter generation.
    """
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='letter_credit_wallet')
    total_credits = models.PositiveIntegerField(default=0, help_text="Total credits ever added (purchases).")
    used_credits = models.PositiveIntegerField(default=0, help_text="Total credits consumed (letter generations).")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def remaining_credits(self):
        return max(0, self.total_credits - self.used_credits)

    def __str__(self):
        return f"{self.company.name} – Letter Wallet ({self.remaining_credits} remaining)"




class LetterCreditTransaction(models.Model):
    """
    Audit log of every credit movement (purchase or deduction).
    """
    TRANSACTION_TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('deduction', 'Deduction'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='letter_credit_transactions')
    letter = models.ForeignKey(GeneratedLetter, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    wallet = models.ForeignKey(LetterCreditWallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    credits = models.PositiveIntegerField(help_text="Credits added (purchase) or consumed (deduction).")
    letter_type = models.CharField(max_length=50, null=True, blank=True,
                                   help_text="Letter type for deduction transactions (e.g. 'offer').")
    # Razorpay fields – only populated for purchase transactions
    package = models.ForeignKey(LetterCreditPackage, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='transactions')
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                      help_text="Amount paid in INR (incl. GST), for purchase transactions.")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.company.name} | {self.transaction_type} | {self.credits} credits"

    class Meta:
        ordering = ['-created']

class Payment(models.Model):
    package = models.ForeignKey(LetterCreditPackage, on_delete=models.SET_NULL, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.razorpay_order_id


class ToolRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tool_name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)
    use_case = models.TextField(blank=True, null=True)
    requested_by = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='tool_requests')
    is_reviewed = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.tool_name} - {self.requested_by.username}"

class ApiIntegrationRequest(models.Model):
    """Model for API integration requests with platform, AI tools, and note fields"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    platform = models.CharField(max_length=255, blank=True, null=True, help_text="Platform name")
    ai_tools = ArrayField(
        models.CharField(max_length=255, blank=True, null=True),
        default=list,
        blank=True,
        null=True,
        help_text="List of AI tools"
    )
    note = models.TextField(blank=True, null=True, help_text="Additional notes")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'API Integration Request'
        verbose_name_plural = 'API Integration Requests'
        ordering = ['-created']
    
    def __str__(self):
        tools_str = ', '.join(self.ai_tools) if self.ai_tools else 'None'
        return f"{self.platform} - {tools_str} ({self.created.strftime('%Y-%m-%d %H:%M')})"