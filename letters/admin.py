from django.contrib import admin
from .models import GeneratedLetter, LetterSettings, LetterCreditPackage, LetterCreditWallet, LetterCreditTransaction, ApiIntegrationRequest

@admin.register(ApiIntegrationRequest)
class ApiIntegrationRequestAdmin(admin.ModelAdmin):
    list_display = ('platform', 'ai_tools_display', 'note', 'created', 'updated')
    list_filter = ('platform', 'created')
    search_fields = ('platform', 'ai_tools', 'note')
    readonly_fields = ('id', 'created', 'updated')
    ordering = ('-created',)
    
    def ai_tools_display(self, obj):
        if obj.ai_tools:
            return ", ".join(obj.ai_tools)
        return "-"
    ai_tools_display.short_description = 'AI Tools'

@admin.register(GeneratedLetter)
class GeneratedLetterAdmin(admin.ModelAdmin):
    list_display = ('candidate_name', 'letter_type', 'company', 'created','updated')
    list_filter = ('letter_type', 'letter_category', 'company')
    search_fields = ('candidate_name', 'company__name')
    readonly_fields = ('created','updated')

@admin.register(LetterSettings)
class LetterSettingsAdmin(admin.ModelAdmin):
    list_display = ('company', 'signatory_name', 'updated')
    search_fields = ('company__name', 'signatory_name')

@admin.register(LetterCreditPackage)
class LetterCreditPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'credits', 'price', 'offer_price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('-created',)

@admin.register(LetterCreditWallet)
class LetterCreditWalletAdmin(admin.ModelAdmin):
    list_display = ('company', 'total_credits', 'used_credits')
    search_fields = ('company__name',)

@admin.register(LetterCreditTransaction)
class LetterCreditTransactionAdmin(admin.ModelAdmin):
    list_display = ('company', 'transaction_type', 'credits', 'amount_paid', 'created')
    list_filter = ('transaction_type', 'company')
    search_fields = ('company__name', 'razorpay_order_id', 'razorpay_payment_id')
    readonly_fields = ('created',)