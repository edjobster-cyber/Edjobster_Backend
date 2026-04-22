from django.contrib import admin
from .models import ContactDetails, ScheduleCall

# Register your models here.
class ContactDetailsAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "mobile_number", "company_name","platform", "created")
    list_filter = ("id","full_name","platform")

admin.site.register(ContactDetails, ContactDetailsAdmin)

class ScheduleCallAdmin(admin.ModelAdmin):
    list_display = ("mobile_number", "date", "time", "created")
    list_filter = ("id","mobile_number")
admin.site.register(ScheduleCall, ScheduleCallAdmin)