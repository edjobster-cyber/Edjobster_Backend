from django.contrib import admin

# Register your models here.
from .models import (Candidate, Note, CandidateExperience, CandidateQualification, 
                    ApplicantWebForm, Mail, Tasks, EmailSettings, Events, Call, 
                    SubjectSpecialization, Skill, Candidatewithoutlogin, CandidateTimeline,
                    SavedJob, CandidateResume, CandidateProfile, RJMSAnalysis, CoresignalPreview, CoresignalCandidateStatus, CoresignalCandidateVisiteCompany)
my_modules = [Candidate, CandidateExperience, CandidateQualification, ApplicantWebForm, Note, Mail]
#Registering Candidate on admin panel

class MailAdmin(admin.ModelAdmin):
    list_display=('id',)
    list_filter=('id',)
admin.site.register(Mail,MailAdmin)

class NoteAdmin(admin.ModelAdmin):
    list_display=('id',)
    list_filter=('id',)
admin.site.register(Note,NoteAdmin)

class CandidateAdmin(admin.ModelAdmin):
    # list_display=('first_name','last_name','id','job','created',)
    list_display=('first_name','last_name','id','updated','pipeline_stage','pipeline_stage_status','account','company','source')
    list_filter=('id',)
admin.site.register(Candidate,CandidateAdmin)

class ApplicantWebFormAdmin(admin.ModelAdmin):
    list_display=('id',)
    list_filter=('id',)
admin.site.register(ApplicantWebForm,ApplicantWebFormAdmin)

#register candidate according to experience
class CandidateExperienceAdmin(admin.ModelAdmin):
    list_display=('id','candidate','employer','jobProfile')
    list_filter=('id',)
admin.site.register(CandidateExperience,CandidateExperienceAdmin)

class CandidateTimelineAdmin(admin.ModelAdmin):
    list_display=("id","performed_by","description")
    list_filter=("id",)

class SavedJobAdmin(admin.ModelAdmin):
    list_display=("id","candidate","job")
    list_filter=("id",)

class CandidateResumeAdmin(admin.ModelAdmin):
    list_display=("id","candidate","resume")
    list_filter=("id",)
    
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display=("id","candidate","profile_photo")
    list_filter=("id",)

admin.site.register(Tasks)
admin.site.register(Events)
admin.site.register(Call)
admin.site.register(EmailSettings)
admin.site.register(SubjectSpecialization)
admin.site.register(Skill)
admin.site.register(Candidatewithoutlogin)
admin.site.register(CandidateTimeline,CandidateTimelineAdmin)
admin.site.register(SavedJob,SavedJobAdmin)
admin.site.register(CandidateResume,CandidateResumeAdmin)
admin.site.register(CandidateProfile,CandidateProfileAdmin)
admin.site.register(RJMSAnalysis)

class CoresignalPreviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'coresignal_id','is_list', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('coresignal_id',)
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(CoresignalPreview, CoresignalPreviewAdmin)

class CoresignalCandidateStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'coresignal_candidate', 'company', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('coresignal_candidate__coresignal_id', 'company__name')
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(CoresignalCandidateStatus, CoresignalCandidateStatusAdmin)

class CoresignalCandidateVisiteCompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'get_visits_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('company__name',)
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('visitescandidatelist',)
    
    def get_visits_count(self, obj):
        return obj.visitescandidatelist.count()
    get_visits_count.short_description = 'Visits Count'

admin.site.register(CoresignalCandidateVisiteCompany, CoresignalCandidateVisiteCompanyAdmin)