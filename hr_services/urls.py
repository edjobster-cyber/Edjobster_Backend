from django.urls import path
from .import views


urlpatterns = [
    path('contact-details/', views.ContactDetailsView.as_view(), name='contact-details'),
    path('schedule-call/', views.ScheduleCallView.as_view(), name='schedule-call'),
]