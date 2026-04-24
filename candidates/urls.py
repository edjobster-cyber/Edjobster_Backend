from django.urls import path
from .import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from django.urls import include, path




urlpatterns = [
    path('apply/', views.ApplyApi.as_view(), name='apply'),
    path('apply-job/', views.ApplyJobApi.as_view(), name='apply-job'),
    path('applications/', views.ApplicationsApi.as_view(), name='applications'),
    path('candidate/', views.CandidatesApi.as_view(), name='candidate'),
    path('resume/', views.ApplicationsResumeApi.as_view(), name='resume'),
    path('resume-parse/', views.ApplicationsResumeParseApi.as_view(), name='resume-parse'),
    path('candidate/upload-document/', views.CandidateUpload_documentApi.as_view(), name='candidate_upload_document'),
    path('details/', views.CandidateDetailsApi.as_view(), name='details'),
    path('notes/', views.NoteApi.as_view(), name='notes'),
    path('notes/<int:pk>', views.DetailNoteApi.as_view(), name='notes-details'),    
    path('notes-update/<int:pk>', views.NotesUpdateApi.as_view(), name='notes-update'),
    path('create-candidate/', views.CreateCandidateUsingResume.as_view(), name='create-candidate'),
    path('create-candidate-web/', views.CreateCandidateUsingWebForm.as_view(), name='create-candidate-web'),
    path('candidate-stats/', views.CandidateStats.as_view(), name='candidate-stats'),
    path('hiring-funnel/', views.HiringFunnelApi.as_view(), name='hiring-funnel'),
    path('hires-by-source/', views.HiresBySourceApi.as_view(), name='hires-by-source'),
    path('dashboard-cards/', views.DashboardCardsApi.as_view(), name='dashboard-cards'),
    path('daily-candidate-count/', views.DailyCandidateCountApi.as_view(), name='daily-candidate-count'),
    path('update-candidate-pipeline-status/',views.UpdateCandidatePipelineStatus.as_view(), name='update-candidate-pipeline-status'),

    path('applicant-get/<str:lookup_field>/<str:lookup_value>/', views.ApplicationWebFormByJobApi.as_view(), name='applicant-get'),
    path('applicant-update/<int:pk>', views.ApplicationWebFormUpdateApi.as_view(), name='applicant-update'),
    path('applicant-delete/<int:pk>', views.ApplicationWebFormDeleteApi.as_view(), name='applicant-delete'),
    path('applicant/', views.ApplicationWebFormCreateApi.as_view(), name='applicant-create'),

    path('update-candidate-status/', views.UpdateCandidateStatusApi.as_view(), name='update-candidate-status'),
    path('assign-job/', views.AssignJob.as_view(), name='assign-job'),
    path('assign-job-to-candidates/', views.AssignJobToCandidates.as_view(), name='assign-job-to-candidates'),
    path('ParseResume/', views.ParseResumeAPIView.as_view(), name='ParseResume'),
    # path('generate-extract/', views.ExtractResumeView.as_view(), name='extract_resume'),
    path('generate-extract/', views.ExtractResumeProgressSSE.as_view(), name='extract_resume'),
    path("create-candidates/", views.CandidateApiView.as_view(), name="candidate-list"),
    path("create-candidates/<int:pk>/", views.CandidateApiView.as_view(), name="candidate-detail"),
    path("careersite-create-candidates/", views.CareerSiteCandidateApiView.as_view(), name="careersite-create-candidates"),
    # path("task/", views.TasksApiView.as_view(), name="task"),
    # path("task/<int:pk>/", views.TasksApiView.as_view(), name="task-detail"),
    # path("task-by-candidate/<int:pk>/", views.TaskByCandidate.as_view(), name="taskbycandidate"),
    path('tasks-options/', views.TaskOptionsView.as_view(), name='task-options'),
    path('tasks/', views.TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:id>/', views.TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:id>/complete/', views.MarkTaskCompletedView.as_view(), name='mark_task_completed'),
    path('events-options/', views.EventOptionsView.as_view(), name='events-options'),
    path('events/', views.EventListCreateView.as_view(), name='events-list-create'),
    path('events/<int:id>/', views.EventListCreateView.as_view(), name='events-list-create'),
    path('calls-options/', views.CallOptionsView.as_view(), name='calls-options'),
    path('calls/', views.CallListCreateView.as_view(), name='calls-list-create'),
    path('calls/<int:id>/', views.CallListCreateView.as_view(), name='call-list-create'),
    path('multiple-jobs/<int:candidate_id>/', views.CreateMultipleCandidates.as_view(), name='create-multiple-candidates'),
    path('custom_query/', views.ExecuteSQLQueryView.as_view(), name='custom_query'),
    path('skill/',views.SkillApiView.as_view(),name="skill"),
    path('subject-specialization/',views.SubjectSpecializationApiView.as_view(),name="subject-specialization"),
    path('candidate-json-data/',views.CandidateJsonDataView.as_view(),name="candidate-json-data"),
    path('candidate-timeline/<int:candidate_id>/',views.TimeLineView.as_view(),name='candidate-timeline'),
    path('candidate-bulk-mail-send/',views.CandidateBulkMailApi.as_view(),name="candidate-bulk-mail-send"),
    
    path('email_setting_smtp/', views.EmailSettingsApiView.as_view(), name='email_setting_smtp'),
    path('email_setting_smtp/<int:pk>/', views.EmailSettingsApiView.as_view(), name='email_setting_smtp_update'),
    path('daily-email-quota/',views.DailyEmailQuotaApi.as_view(),name="daily-email-quota"),

    path('hiring-status-timeline/<int:id>/',views.HiringStatusTimeLineApi.as_view(),name="hiring-status-timeline"),

    path('AddData/',views.AddData,name="AddData"),
    
    path('candidates-without-login/',views.CandidateWithoutLoginAPI.as_view(),name='candidate-without-login-list'),
    path('candidates-without-login-applied/<str:login_email>/',views.CandidateApplyJobCareerApi.as_view(),name='candidate-without-login-applied'),

    path('candidate-list/',views.CandidateApplyJobCareerApi.as_view(),name='candidate-list'),
    path('saved-jobs/',views.SaveJobView.as_view(),name='saved-jobs'),
    path('saved-jobs/<int:pk>/',views.SaveJobView.as_view(),name='saved-jobs-update'),
    path('candidate-resume/',views.CandidateResumeView.as_view(),name='candidate-resume'),
    path('candidate-resume/<uuid:pk>/',views.CandidateResumeView.as_view(),name='candidate-resume-update'),
    path('candidate-profile/',views.CandidateProfileView.as_view(),name='candidate-profile'),
    path('candidate-profile/<uuid:pk>/',views.CandidateProfileView.as_view(),name='candidate-profile-update'),
    path('candidate-interview-status/', views.CandidateStatusBySiteAPI.as_view(), name='candidate-status-by-site'),
    
    path('coresignal-collect/', views.CoresignalCollectApi.as_view(), name='coresignal-collect'),
    path('coresignal-collect/<str:id>/', views.CoresignalPreviewApi.as_view(), name='coresignal-preview'),
    path('coresignal/status/', views.CoresignalCandidateStatusView.as_view(), name='coresignal-status'),
    path('send-candidate-email/', views.CoresignalCandidateSEmailView.as_view(), name='send-candidate-email'),
    path('send-candidate-email/<int:id>', views.CoresignalCandidateSEmailView.as_view(), name='send-candidate-email'),

    path('generate-email-reply/', views.EmailReplyGeneratorAPIView.as_view(), name='generate-email-reply'),
    path('visited-candidates/', views.CandidateVisiteCompanyListView.as_view(), name='visited-candidates-list'),
    path('generate-candidate-search/<int:id>/',views.Corsignalcandidatesearch.as_view()),
    path('corsignal-candidate-scrongin/<int:job_id>/<str:corsignal_id>/',views.CorsignalCandidateScrongin.as_view()),
    # path('ai-resume-match-upload/', views.AiResumeMatchUpload.as_view(), name='ai-resume-match-upload'),

    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', views.MarkNotificationReadView.as_view(), name='mark-notification-read'),
]

urlpatterns += static(settings.RESUME_URL, document_root=settings.RESUME_URL_ROOT)