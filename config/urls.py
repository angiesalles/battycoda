"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path
from django.core.cache import cache


def health_check(request):
    """Health check endpoint for uptime monitoring."""
    status = {"status": "ok", "checks": {}}

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status["checks"]["database"] = "ok"
    except Exception as e:
        status["checks"]["database"] = f"error: {str(e)}"
        status["status"] = "degraded"

    # Check Redis/cache
    try:
        cache.set("health_check", "ok", 10)
        if cache.get("health_check") == "ok":
            status["checks"]["cache"] = "ok"
        else:
            status["checks"]["cache"] = "error: cache read failed"
            status["status"] = "degraded"
    except Exception as e:
        status["checks"]["cache"] = f"error: {str(e)}"
        status["status"] = "degraded"

    http_status = 200 if status["status"] == "ok" else 503
    return JsonResponse(status, status=http_status)


urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path("hijack/", include("hijack.urls")),
    path("", include("battycoda_app.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
