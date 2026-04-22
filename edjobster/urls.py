from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from settings.views import redirect_short_url 

def health_check(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('account.urls')),
    path('common/', include('common.urls')),
    path('settings/', include('settings.urls')),
    path('jobs/', include('job.urls')),
    path('candidate/', include('candidates.urls')),
    path('interview/', include('interview.urls')),
    path('hr_services/', include('hr_services.urls')),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("letters/", include('letters.urls')),
    path(
        "openapi/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="ui",
    ),
    path('health/', health_check),
    path("<str:code>/", redirect_short_url),
]

urlpatterns += static(settings.LOGO_URL, document_root=settings.LOGO_URL_ROOT)
urlpatterns += static(settings.PHOTO_URL, document_root=settings.PHOTO_URL_ROOT)
