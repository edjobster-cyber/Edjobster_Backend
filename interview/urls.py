from django.urls import path
from . import views

urlpatterns = [
	#interview
	path("interviews-schedule/", views.InterviewListCreateAPIView.as_view(), name="interview-list-create"),
	path("interviews/<int:pk>/", views.InterviewDetailAPIView.as_view(), name="interview-detail"),

	# Reschedule
	path("interviews/<str:token>/reschedule/", views.RescheduleRequestAPIView.as_view(), name="reschedule-list-create"),
	path("reschedule/<int:pk>/", views.RescheduleRequestAPIView.as_view(), name="reschedule-update"),
	path("reschedule-action/<int:pk>", views.RescheduleAPIView.as_view(), name="reschedule-action"),

	# Feedback
	path("interviews/<int:interview_id>/feedback/", views.FeedbackAPIView.as_view(), name="feedback"),
	path("feedbackfeelchack/<int:interview_id>/<int:interviewer_id>/<int:candidate_id>/",views.FeedbackFeelChackAPIView.as_view(),name="feedback-feel-chack"),

	# Headless
	path("headless/validate/<str:token>/<str:user_type>/<int:interview_id>/", views.HeadlessValidateAPIView.as_view(), name="headless-validate"),
	path("headless/action/<str:token>/", views.HeadlessActionAPIView.as_view(), name="headless-action"),

	# ICS download
	path("interviews/<int:interview_id>/ics/", views.InterviewICSAPIView.as_view(), name="interview-ics"),

	# Job, Candidate And DashBoard Interview Table
	path('JobInterviewDetails/', views.JobInterviewDetailsApi.as_view(), name='JobInterviewDetails'),
    path('candidateInterviewDetails/', views.CandidateInterviewDetailsApi.as_view(), name='candidateInterviewDetails'),
	path('interview-latest/', views.LatestInterviewDetailsApi.as_view(), name='interview-latest'),
	# Status Change

	path("interview/<int:pk>/status/", views.InterviewStatusChangeAPIView.as_view(), name="interview-status"),
	path("candidate/<int:pk>/status/", views.CandidateStatusChangeAPIView.as_view(), name="candidate-status"),
	path("interviewer/<int:pk>/status/", views.InterviewerStatusChangeAPIView.as_view(), name="interviewer-status"),

]
