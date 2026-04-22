from django.urls import path
from .import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('location/', views.LocationsApi.as_view(), name='location'),
    path('location-career/', views.LocationsCareerApi.as_view(), name='location-career'),
    path('location-career/<int:pk>/', views.LocationsCareerApi.as_view(), name='location-career'),
    path('location/<int:pk>', views.LocationsDetailApi.as_view(), name='location-detail'),
    path('department/', views.DepartmentApi.as_view(), name='department'),
    path('designation/', views.DesignationApi.as_view(), name='designation'),
    path('degree/', views.DegreeApi.as_view(), name='degree'),
    path('job-associate-pipeline-stages/', views.JobAssociatePipelineStagesApi.as_view(), name='job-associate-pipeline-stages'),
    path('pipeline-stage/', views.PipelineStageApi.as_view(), name='pipeline-stage'),
    path('pipeline-details/', views.PipelineDetails.as_view(), name='pipeline-details'),
    path('pipeline-detalis/<int:id>/', views.PipelinesDetailApi.as_view(), name='pipeline_details'),
    path('pipeline-stage-delete/<int:id>/', views.PipelineStageDelete.as_view(), name='pipeline-stage-delete'),
    path('pipeline-update-stage/<int:id>/', views.PipelineStageUpdate.as_view(), name='pipeline_details'),
    path('pipeline-detalis-by-company/<int:id>/', views.PipelinesDetailCompanyApi.as_view(), name='pipeline-update-stage'),
    path('pipeline/', views.PipelinesApi.as_view(), name='pipeline'),
    path('email-field/', views.EmailFieldApi.as_view(), name='email-field'),
    path('email-category/', views.EmailCategoryApi.as_view(), name='email-category'),
    path('email-template/', views.EmailTemplateApi.as_view(), name='email-template'),
    path('email-template/<int:pk>', views.EmailTemplateDetailApi.as_view(), name='email-template'),
    path('module/', views.ModuleApi.as_view(), name='module'),
    path('moduletypes/', views.ModuleTypesApi.as_view(), name='moduletypes'),
    path('modulecompany', views.ModuleCompanyApi.as_view(), name='module'),
    path('module/<int:id>/<str:companyId>/', views.ModuleApi.as_view(), name='module'),
    
    path('moduletypesJob/', views.ModuleTypesJobApi.as_view(), name='moduletypesjob'),
    
    path('webform/', views.WebformApi.as_view(), name='webform'),
    path('webform-fields/', views.WebformFieldsApi.as_view(), name='webform-fields'),
    path('contacts/', views.ContactsApi.as_view(), name='contacts'),
    path('email_credentials/', views.EmailCredentialsApi.as_view(), name='email_credentials'),  

    path('template-variables/', views.TemplateVariablesApi.as_view(), name='template-variables'),

    path('testimonials/', views.TestimonialsCView.as_view(), name='testimonials-c'),
    path('testimonials/<int:pk>', views.TestimonialsRUDView.as_view(), name='testimonials-crud'),
    
    path('billing-plan/', views.BillingPlanView.as_view(), name='billing-plan'),
    path('create_order/', views.create_order, name='create_order'),
    path('payment_success/', views.payment_success, name='payment_success'),

    path('custom_addon_payment/', views.custom_credit_order_create, name='custom_addon_payment'),
    path('custom_addon_payment_success/', views.custom_addon_payment_success, name='custom_addon_payment_success'),

    path('current_subscription_plan/', views.CurrentSubscriptionView.as_view(), name='current_subscription_plan'),
    
    path('all_mails/<int:id>/', views.GmailAllEmailsView.as_view(), name='all_mails'), 
    
    path('DesignationCareer/', views.DesignationCareerApi.as_view(), name='DesignationCareer'), 
    path('DegreeCareer/', views.DegreeCareerApi.as_view(), name='DegreeCareer'),   
    
    path('organizational-email/', views.OrganizationalEmailApi.as_view(), name='organizational-email'),
    path('organizational-email/<int:id>/', views.OrganizationalEmailApi.as_view(), name='organizational-email'),
    path('unsubscribe-email-token/<str:token>/', views.UnsubscribeEmailTokenApi.as_view(), name='unsubscribe-email-token'), 
    path('unsubscribe-link/', views.UnsubscribeLinkApi.as_view(), name='unsubscribe-link'),
    path('attachment-categories/', views.AttachmentCategoryApi.as_view(), name='attachment-categories'),
    
    # Short URL and QR Code APIs
    path('short-url/<int:id>/', views.ShortUrlApi.as_view(), name='short-url'),
    path('qr-code/<int:id>/', views.QRModelApi.as_view(), name='qr-code-detail'),
    
    # Linkding Company ID URLs
    path('linkedin-company/', views.LinkedinCompanyidAPI.as_view(), name='linkding-company-list'),
    path('linkedin-company/<int:id>/', views.LinkedinCompanyidAPI.as_view(), name='linkding-company-detail'),
    
    # Candidate Evaluation Criteria URLs
    path('evaluation-criteria/', views.CandidateEvaluationCriteriaView.as_view(), name='evaluation-criteria-list'),
    path('evaluation-criteria/<int:id>/', views.CandidateEvaluationCriteriaView.as_view(), name='evaluation-criteria-detail'),

    path('job-board-list/', views.JobBoardListApi.as_view(), name='job-board-list'),
    path('job-board-list/<int:id>/', views.JobBoardListApi.as_view(), name='job-board-list'),
    path('job-board/', views.JobBoardApi.as_view(), name='job-board'),
    path('job-board/<int:id>/', views.JobBoardApi.as_view(), name='job-board'),
    
    # Credit Wallet API
    path('credits/', views.CreditWalletAPI.as_view(), name='credits-list'),
    path('credits/<str:feature_code>/', views.CreditWalletAPI.as_view(), name='credits-detail'),
    path('credits/<str:feature_code>/<str:feature_usage>/', views.CreditWalletAPI.as_view(), name='credits-detail'),

    path('check-feature-availability/<str:feature_code>/', views.CheckFeatureAvailability.as_view(), name='check-feature-availability'),
    path('temp/', views.temp.as_view(), name='temp'),
    
    # Addon Plan APIs
    path('addon-plans/', views.AddonPlanListAPIView.as_view(), name='addon-plans'),
    
    # Plan Feature Credit API
    path('plan-feature-credits/<int:plan_id>/', views.PlanFeatureCreditAPIView.as_view(), name='plan-feature-credits'),
    path('credit-history/', views.CreditHistoryAPIView.as_view(), name='credit-history'),
    path('billing-history/', views.BillingHistoryAPIView.as_view(), name='billing-history'),
] 

urlpatterns += static(settings.PHOTO_URL, document_root=settings.PHOTO_URL_ROOT)