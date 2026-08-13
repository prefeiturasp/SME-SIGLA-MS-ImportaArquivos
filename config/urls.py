"""URLs do projeto convocacao_processes."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpRequest, JsonResponse
from django.urls import URLPattern, URLResolver, include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def healthcheck(_request: HttpRequest) -> JsonResponse:
    """Retorna o status de saúde do serviço."""
    return JsonResponse({"status": "ok"})


_static_urlpatterns: list[URLPattern | URLResolver] = [
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
]

_core_urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("importa_arquivos.api.urls")),
    path("api/v1/", include("exporta_arquivo.api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("", healthcheck, name="healthcheck"),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]

# Só as rotas da app entram sob MS_PATH. Static/media ficam na raiz (/django_static/, /media/)  # noqa: E501
# para bater com STATIC_URL e MEDIA_URL usados pelo admin e pelo collectstatic.
if getattr(settings, "DJANGO_ENVIRONMENT", "local") != "local":
    _ms_prefix = getattr(settings, "MS_PATH", "/ms-importa-arquivos").strip(
        "/"
    )
    urlpatterns = [
        path(f"{_ms_prefix}/", include(_core_urlpatterns)),
    ] + _static_urlpatterns
else:
    urlpatterns = _core_urlpatterns + _static_urlpatterns
