from django.contrib import admin

from .models import Account, Company, TokenEmailVerification, CareerSiteCompanyDetail,CaptureLead,LeadToken
from .models import Account, Company, TokenEmailVerification, CareerSiteCompanyDetail, ZohoCRMHistory

class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_id', 'first_name','last_name','role','company','username')
    list_filter = ("account_id",)
    search_fields = ['role', 'mobile', 'company']

admin.site.register(Account, AccountAdmin)

class CompanyAdmin(admin.ModelAdmin):
    list_display=('admin','name','id','website')
    list_filter=('id',)
admin.site.register(Company,CompanyAdmin)

class TokenEmailVerificationAdmin(admin.ModelAdmin):
    list_display=('id','user','is_verified')
    list_filter=('created','is_verified')
admin.site.register(TokenEmailVerification,TokenEmailVerificationAdmin)

admin.site.register(CareerSiteCompanyDetail)

class CaptureLeadAdmin(admin.ModelAdmin):   
    list_display=('id','fullname','email','phone','company','created','updated')
    list_filter=('id','created')
admin.site.register(CaptureLead,CaptureLeadAdmin)

class ZohoCRMHistoryAdmin(admin.ModelAdmin):
    list_display=('id','lead','zohocrmid','created')
    list_filter=('id','created')
admin.site.register(ZohoCRMHistory,ZohoCRMHistoryAdmin)
admin.site.register(LeadToken)