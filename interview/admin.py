from django.contrib import admin
from .models import Interview, RescheduleRequest, Feedback, AuditLog, InterviewCandidateStatus, InterviewerStatus, DeclineResponse
# Register your models here.
class InterviewAdmin(admin.ModelAdmin):
    list_display=('id','job')
    list_filter=('id',)
admin.site.register(Interview,InterviewAdmin)
admin.site.register(RescheduleRequest)
admin.site.register(Feedback)
admin.site.register(AuditLog)
admin.site.register(InterviewCandidateStatus)
admin.site.register(InterviewerStatus)
admin.site.register(DeclineResponse)