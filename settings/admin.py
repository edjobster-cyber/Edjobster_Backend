from django.contrib import admin

# Register your models here.
from .models import (BillingCycle, Contacts, Location, Degree, Department, Designation, EmailCategory, EmailTemplate, 
                     Pipeline, PipelineStage, EmailFields, Webform, Testimonials, TemplateVariables, 
                     Plan, Payment, Subscription, RazorpaySettings, EmailCredential, Module, 
                     UnsubscribeEmailToken, OrganizationalEmail, ShortLink, QRModel, LinkdingCompanyid, 
                     ZwayamAmplifyKey, CandidateEvaluationCriteria, JobBoardList, JobBoard, PlanPricing,
                     Feature, PlanFeatureCredit, FeatureUsage, CreditWallet, CreditHistory, BilingHistory, AddonPlan)

my_modules = [Location, Degree, Designation, EmailTemplate, EmailFields , Webform, Testimonials, TemplateVariables, RazorpaySettings, Module, UnsubscribeEmailToken, OrganizationalEmail,Plan,BillingCycle,PlanPricing]

# class SubscriptionAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user_email', 'plan_name', 'start_date', 'end_date', 'is_active')
#     list_filter = ('active', 'start_date', 'end_date')
#     search_fields = ('user__email', 'plan__name')
#     readonly_fields = ('start_date',)
    
#     def user_email(self, obj):
#         return obj.user.email
#     user_email.short_description = 'User Email'
#     user_email.admin_order_field = 'user__email'
    
#     def plan_name(self, obj):
#         return obj.plan.name
#     plan_name.short_description = 'Plan'
#     plan_name.admin_order_field = 'plan__name'
    
#     def is_active(self, obj):
#         return obj.active
#     is_active.boolean = True
#     is_active.short_description = 'Active'

class PipelineAdmin(admin.ModelAdmin):
    list_display=('id',)
    list_filter=('id',)

class ContactsAdmin(admin.ModelAdmin):
    list_display=('id','name', 'mobile', 'email', 'company_name')
    list_filter=('id',)
    def company_name(self, contacts):
        return contacts.company.name



admin.site.register(EmailCategory, PipelineAdmin)
admin.site.register(Department, PipelineAdmin)
admin.site.register(Pipeline)
admin.site.register(PipelineStage)
admin.site.register(Contacts, ContactsAdmin)
admin.site.register(EmailCredential)

class ShortLinkAdmin(admin.ModelAdmin):
    list_display = ('code', 'job_display', 'long_url', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('code', 'long_url', 'job__title')
    readonly_fields = ('created_at',)
    
    def job_display(self, obj):
        return f"{obj.job.title} (ID: {obj.job.id})" if obj.job else "-"
    job_display.short_description = 'Job'
    job_display.admin_order_field = 'job__id'

class QRModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_display', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('job__title', 'url')
    readonly_fields = ('created_at', 'updated_at', 'qr_image_preview')
    
    def job_display(self, obj):
        return f"{obj.job.title} (ID: {obj.job.id})" if obj.job else "-"
    job_display.short_description = 'Job'
    job_display.admin_order_field = 'job__id'
    
    def qr_image_preview(self, obj):
        if obj.qr_image:
            return f'<img src="{obj.qr_image.url}" width="200" height="200" />'
        return "No QR Image"
    qr_image_preview.short_description = 'QR Code Preview'
    qr_image_preview.allow_tags = True

@admin.register(LinkdingCompanyid)
class LinkdingCompanyidAdmin(admin.ModelAdmin):
    list_display = ('company', 'linkding_id', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('company__name', 'linkding_id')
    list_select_related = ('company',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    list_per_page = 20

admin.site.register(ShortLink, ShortLinkAdmin)
admin.site.register(QRModel, QRModelAdmin)

@admin.register(ZwayamAmplifyKey)
class ZwayamAmplifyKeyAdmin(admin.ModelAdmin):
    list_display = ('company', 'api_key', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('company__name', 'api_key')
    list_select_related = ('company',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    list_per_page = 20


admin.site.register(my_modules)
admin.site.register(Subscription)


class JobBoardListAdmin(admin.ModelAdmin):
    list_display = ('title', 'subtitle', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'subtitle', 'value')
    readonly_fields = ('created_at', 'updated_at')


class JobBoardAdmin(admin.ModelAdmin):
    list_display = ('id', 'company_name', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('company__name',)
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('job_board_list',)
    
    def company_name(self, obj):
        return obj.company.name
    company_name.short_description = 'Company'
    company_name.admin_order_field = 'company__name'


admin.site.register(JobBoardList, JobBoardListAdmin)
admin.site.register(JobBoard, JobBoardAdmin)


class FeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'isdayli','iswithoutcredit', 'iscredit', 'created_at')
    list_filter = ('isdayli', 'iscredit', 'created_at')
    search_fields = ('name', 'code', 'description')
    # list_editable = ('isdayli', 'iscredit')


class PlanFeatureCreditAdmin(admin.ModelAdmin):
    list_display = ('plan', 'feature', 'credit_limit', 'created_at')
    list_filter = ('plan', 'feature', 'created_at')
    search_fields = ('plan__name', 'feature__name')
    list_select_related = ('plan', 'feature')


class FeatureUsageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'feature', 'used_credit', 'created_at')
    list_filter = ('feature', 'created_at')
    search_fields = ('name', 'code', 'feature__name')
    list_select_related = ('feature',)


class CreditWalletAdmin(admin.ModelAdmin):
    list_display = ('company', 'feature', 'total_credit', 'used_credit', 'available_credit', 'created_at')
    list_filter = ('isdayli', 'iscredit', 'created_at')
    search_fields = ('company__name', 'feature__name')
    list_select_related = ('company', 'feature')
    
    def available_credit(self, obj):
        return obj.total_credit - obj.used_credit
    available_credit.short_description = 'Available Credit'


class CreditHistoryAdmin(admin.ModelAdmin):
    list_display = ('credit_wallet', 'feature', 'credit', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('credit_wallet__company__name', 'feature__name', 'feature_usage__name')
    list_select_related = ('credit_wallet', 'feature', 'feature_usage')
    date_hierarchy = 'created_at'


class BilingHistoryAdmin(admin.ModelAdmin):
    list_display = ('company', 'transaction_type', 'plan_pricing', 'feature', 'price', 'credit', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('company__name', 'plan_pricing__plan__name', 'feature__name')
    list_select_related = ('company', 'plan_pricing', 'feature')
    date_hierarchy = 'created_at'


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('razorpay_order_id', 'razorpay_payment_id', 'amount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('razorpay_order_id', 'razorpay_payment_id')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)


# Register the new admin classes
admin.site.register(Feature, FeatureAdmin)
admin.site.register(PlanFeatureCredit, PlanFeatureCreditAdmin)
admin.site.register(FeatureUsage, FeatureUsageAdmin)
admin.site.register(CreditWallet, CreditWalletAdmin)
admin.site.register(CreditHistory, CreditHistoryAdmin)
admin.site.register(BilingHistory, BilingHistoryAdmin)
admin.site.register(Payment, PaymentAdmin)


@admin.register(CandidateEvaluationCriteria)
class CandidateEvaluationCriteriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'company')
    search_fields = ('company__name',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(AddonPlan)
class AddonPlanAdmin(admin.ModelAdmin):
    list_display = ('feature', 'name', 'credits', 'price', 'offer_price', 'is_active', 'created_at')
    list_filter = ('feature', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'feature__name')
    list_select_related = ('feature',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    list_editable = ('is_active',)