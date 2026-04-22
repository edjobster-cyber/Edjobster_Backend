from django.urls import path
from .import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from .sitemaps import JobSitemap

sitemaps_dict = {
    'jobs': JobSitemap,
}

urlpatterns = [
    path('job/', views.JobApi.as_view(), name='job'),
    path('job/<int:pk>', views.JobApi.as_view(), name='job'),
    path('job/clone/<int:job_id>', views.CloneJobApi.as_view(), name='clone-job'),
    path('job/upload-document/', views.JobUpload_documentApi.as_view(), name='jobs_upload_document'),
    path('job/upload-document/<int:pk>', views.JobUpload_documentApi.as_view(), name='jobs_upload_document'),
    path('job/upload_assessment/', views.JobUpload_AssesmentApi.as_view(), name='job-upload-assessment'),
    path('job/upload_assessment/<int:pk>/', views.JobUpload_AssesmentApi.as_view(), name='job-upload-assessment-delete'),
    # path('job-details/', views.JobDetailsApi.as_view(), name='job-details'),
    path('all-jobs/', views.JobsList.as_view(), name='jobs'),
    path('job-details/<int:pk>/', views.JobsDetail.as_view(), name='jobs_details'),
    path('template-job-details/<int:pk>/', views.TemplateJobsDetail.as_view(), name='template_jobs_details'),
    path('job-details-career/<int:pk>/', views.JobsDetailCareer.as_view(), name='job-details-career'),
    path('all-template-jobs/', views.TemplateJobApi.as_view(), name='all-template-jobs'),
    path('all-template-jobs/<int:pk>/', views.TemplateJobApi.as_view(), name='all-template-jobs'),
    path('all-draftsave-jobs/', views.DraftSaveJobApi.as_view(), name='all-draftsave-jobs'),
    path('all-draftsave-jobs/<int:pk>/', views.DraftSaveJobApi.as_view(), name='all-draftsave-jobs'),
    path('job-candidates/<int:pk>/', views.JobsCandidates.as_view(), name='jobs_details'),
    path('job-candidates/<int:job_id>/<str:status>/', views.JobsCandidatesByStatus.as_view(), name='jobs_candidates'),
    path('assesment/', views.AssesmentApi.as_view(), name='assesment'),
    path('assesment-career/<int:pk>/', views.AssesmentCareerApi.as_view(), name='assesment-career'),
    path('assesment/<int:pk>', views.AssismentDetail.as_view(), name='assesment'),
    path('assesment-question/', views.AssesmentQuestionApi.as_view(), name='assesment-question'),
    path('assesment-category/', views.AssesmentCategoryApi.as_view(), name='assesment-category'),
    path('board/', views.BoardApi.as_view(), name='board'),
    path('job-notes/', views.JobNotesApi.as_view(), name='job-notes'),
    path('all-job-candidate/',views.JobCandidateList.as_view(), name='all-job-candidate' ), 
    path('job-stats/',views.JobStats.as_view(), name='job-stats'),
    path('job-status-stats/',views.JobStatusStats.as_view(), name='job-status-stats'),
    path('dashboard-stats/',views.DashboardJobStats.as_view(), name='dashboard-stats'),
    path('a',views.CreateJobApi.as_view(), name = "a"),
    path('job_query/', views.JobSQLQueryView.as_view(), name='job_query'),
    path('job-by-company/<str:pk>/', views.JobByCompanyApi.as_view(), name='job-by-company-api'),
    path('assessment_query/', views.AssesmentSQLQueryView.as_view(), name='assessment_query'),
    path('latest-jobs/', views.LatestJobsView.as_view(), name='latest-jobs'),
    path('count-list/', views.CountList.as_view(), name='count-list'),
    path('daily-jobs-count/', views.DailyCreatedJobsCount.as_view(), name='daily-jobs-count'),
    path('tasks-options/', views.JobTaskOptionsView.as_view(), name='task-options'),
    path('tasks/', views.JobTaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:id>/', views.JobTaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:id>/complete/', views.JobMarkTaskCompletedView.as_view(), name='mark_task_completed'),
    path('events-options/', views.JobEventOptionsView.as_view(), name='events-options'),
    path('events/', views.JobEventListCreateView.as_view(), name='events-list-create'),
    path('events/<int:id>/', views.JobEventListCreateView.as_view(), name='events-list-create'),
    path('calls-options/', views.JobCallOptionsView.as_view(), name='calls-options'),
    path('calls/', views.JobCallListCreateView.as_view(), name='calls-list-create'),
    path('calls/<int:id>/', views.JobCallListCreateView.as_view(), name='call-list-create'),
    path('age-job-count/', views.AgeJobView.as_view(), name='age-job-count'),
    path("assessment-json-data/",views.AssessmentJsonDataView.as_view(),name="assessment-json-data"),
    path('associate-job-apply/<int:candidate_id>/', views.AssociateJobApplyGet.as_view(), name='associate-job-apply'),
    path('job-timeline/<int:job_id>/', views.JobTimelineView.as_view(), name='job-timeline'),
    

    #Job Portels
    path('what-job-list/', views.WhatjobsListView.as_view(), name='what-job-list'),
    path('adzuna-job-list/', views.AdzunaJobListView.as_view(), name='adzuna-job-list'),
    path('xml-job/', views.JobListView.as_view(), name='xml-job'),
    path('linkedin-jobs-list/', views.LinkedInJobFeedView.as_view(), name='linkedin_job_feed'),
    path('indeed-jobs-list/', views.IndeedJobFeedView.as_view(), name='indeed_job_feed'),
    path('post-jobs-list/', views.PostJobFreeView.as_view(), name='post_job_feed'),
    
    path('google/sitemap.xml', sitemap, {'sitemaps': sitemaps_dict}, name='django.contrib.sitemaps.views.sitemap'),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path('<int:job_id>/', views.job_detail, name='job_detail'),
    
    path('xml-job-upload/', views.JobUploadView.as_view(), name='xml-job-upload'),
    path('adzuna-jobs-api/', views.AdzunaJobApi.as_view(), name='adzuna-jobs-api'),
    path('linkedin/callback/', views.LinkedInCallbackView.as_view(), name='linkedin_callback'),
    path('naukri-post-job/', views.NaukriJobPostingAPI.as_view(), name='naukri-post-job'),
    path('job-board/', views.JobBoardView.as_view(), name='job_board'),
    path('google/job-list/', views.GoogleJobList.as_view(), name='google_job_list'),
    
    # AI Job Description Class-based APIs And Assessment
    path('ai/generate-job-description/', views.AIJobDescriptionGenerateApi.as_view(), name='ai-generate-job-description'),
    path('ai/generate-assessment-questions/', views.AIJobAssessmentsGenerateApi.as_view(), name='ai-generate-assessment-questions'),
    path('ai/status/', views.AIServiceStatusApi.as_view(), name='ai-status'),
    path('ai/generate-job-descriptionapp/', views.AIJobDescriptionGenerateMainApi.as_view(), name='ai-generate-job-description'),
    
    path('related-jobs/', views.RelatedJobsAPIView.as_view(), name='related-jobs'),
    path('search/', views.SmartJobSearchAPIView .as_view(), name='job-search'),
]
urlpatterns += static(settings.JOB_DOC_URL, document_root=settings.JOB_DOC_URL_ROOT)
