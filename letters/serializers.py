from rest_framework import serializers
from .models import ApiIntegrationRequest, LetterSettings, GeneratedLetter, LetterCreditPackage, LetterCreditWallet, LetterCreditTransaction, ToolRequest


class LetterSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetterSettings
        fields = [
            'id', 'company', 'signatory_name', 'signatory_title',
            'signatory_email', 'signatory_phone', 'show_company_logo',
            'show_company_name', 'show_release_date', 'header_tagline',
            'header_background_color', 'show_address', 'show_contact_details',
            'custom_footer_text', 'footer_background_color', 'updated','useCompanyContext'
        ]
        read_only_fields = ['id', 'company', 'updated']


class GeneratedLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedLetter
        fields = [
            'id', 'company', 'created_by', 'letter_type', 'letter_category',
            'candidate_name', 'content', 'input_data', 'created', 'updated'
        ]
        read_only_fields = ['id', 'company', 'created_by', 'created', 'updated']


# ─── Letters Billing Serializers ─────────────────────────────────────────────

class LetterCreditPackageSerializer(serializers.ModelSerializer):
    effective_price = serializers.SerializerMethodField()

    class Meta:
        model = LetterCreditPackage
        fields = ['id', 'name', 'credits', 'price', 'offer_price', 'effective_price', 'is_active']

    def get_effective_price(self, obj):
        return str(obj.effective_price())


class LetterCreditWalletSerializer(serializers.ModelSerializer):
    remaining_credits = serializers.IntegerField(read_only=True)

    class Meta:
        model = LetterCreditWallet
        fields = ['id', 'company', 'total_credits', 'used_credits', 'remaining_credits', 'created', 'updated']
        read_only_fields = ['id', 'company', 'total_credits', 'used_credits', 'remaining_credits', 'created', 'updated']


class LetterCreditTransactionSerializer(serializers.ModelSerializer):
    letter_name = serializers.SerializerMethodField()

    class Meta:
        model = LetterCreditTransaction
        fields = [
            'id', 'company', 'wallet', 'transaction_type', 'credits',
            'letter', 'letter_name', 'letter_type', 'package',
            'razorpay_order_id', 'razorpay_payment_id',
            'amount_paid', 'created', 'updated'
        ]

    def get_letter_name(self, obj):
        # Handle missing letter safely
        if not obj.letter:
            return "N/A"

        letter_type = obj.letter.get_letter_type_display()
        candidate = obj.letter.candidate_name or "N/A"
        company = obj.company.name if obj.company else "N/A"

        return f"{letter_type} - {candidate}"


class ToolRequestSerializer(serializers.ModelSerializer):
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)
    requested_by_email = serializers.CharField(source='requested_by.email', read_only=True)
    
    class Meta:
        model = ToolRequest
        fields = [
            'id', 'tool_name', 'description', 'category', 'use_case',
            'requested_by', 'requested_by_username', 'requested_by_email',
            'created', 'is_reviewed'
        ]
        read_only_fields = ['id', 'requested_by', 'created', 'is_reviewed']



class ApiIntegrationRequestSerializer(serializers.ModelSerializer):
    """Serializer for API Integration Request model"""
    
    class Meta:
        model = ApiIntegrationRequest
        fields = ['id', 'platform', 'ai_tools', 'note', 'created', 'updated']
        read_only_fields = ['id', 'created', 'updated']