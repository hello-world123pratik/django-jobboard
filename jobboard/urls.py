"""
URL configuration for jobboard project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Use Django's default admin (DO NOT override)
    path('admin/', admin.site.urls),

    # Your app routes
    path('', include('jobs.urls')),

    # Authentication (login/logout)
    path('accounts/', include('django.contrib.auth.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)