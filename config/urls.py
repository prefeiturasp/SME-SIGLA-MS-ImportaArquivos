from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView
from importa_arquivos.views import SwaggerFromFileView


def healthcheck(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('importa_arquivos.urls')),
    path('api/v1/', include('exporta_arquivo.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SwaggerFromFileView.as_view(url_name='schema'), name='swagger-ui'),
    path('', healthcheck, name='healthcheck'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
