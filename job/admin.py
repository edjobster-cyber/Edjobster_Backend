from django.contrib import admin

# Register your models here.

from .models import Job, Assesment, AssesmentQuestion, AssesmentCategory, JobNotes, CompanyCredentials, TemplateJob, JobBoard, JobTimeline, DraftSaveJob, WhatJobsJob
my_modules = [Job, Assesment, AssesmentQuestion, AssesmentCategory, JobNotes, CompanyCredentials, TemplateJob, JobBoard]

class JobAdmin(admin.ModelAdmin):
    list_display=('id','title','company','vacancies', 'job_status','published')
    list_filter=('id',)
admin.site.register(Job,JobAdmin)


class TemplateJobAdmin(admin.ModelAdmin):
    list_display=('id','title','company','published')
    list_filter=('id',)
admin.site.register(TemplateJob,TemplateJobAdmin)

class AssessmentAdmin(admin.ModelAdmin):
    list_display=('id','company','category','name','updated')
    list_filter=('id','updated')
admin.site.register(Assesment,AssessmentAdmin)

class AssesmentQuestionAdmin(admin.ModelAdmin):
    list_display=('id','created','type')
    list_filter=('id',)
admin.site.register(AssesmentQuestion,AssesmentQuestionAdmin)

class AssesmentCategoryAdmin(admin.ModelAdmin):
    list_display=('id','company','name')
    list_filter=('id',)
admin.site.register(AssesmentCategory,AssesmentCategoryAdmin)

class JobNotesAdmin(admin.ModelAdmin):
    list_display=('id','added_by')
    list_filter=('id',)
admin.site.register(JobNotes,JobNotesAdmin)

class CompanyCredentialsAdmin(admin.ModelAdmin):
    list_display=('linkedIn_company_id','company','board')
    list_filter=('linkedIn_company_id',)
admin.site.register(CompanyCredentials,CompanyCredentialsAdmin)

admin.site.register(JobBoard)
admin.site.register(JobTimeline)
admin.site.register(DraftSaveJob)
class WhatJobsJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'whatjobs_id', 'created_at', 'updated_at', 'get_job_status')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('whatjobs_id', 'job__title', 'message')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('job',)
    
    def get_job_status(self, obj):
        return obj.job.job_status if obj.job else 'N/A'
    get_job_status.short_description = 'Job Status'
    get_job_status.admin_order_field = 'job__job_status'

admin.site.register(WhatJobsJob, WhatJobsJobAdmin)