"""
URL configuration for legal_platform project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

# Non-prefixed URLs (for API, admin, and language switch)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # Language switcher
    path('accounts/', include('allauth.urls')),  # Social authentication URLs
]

# Language-prefixed URLs (main app) - includes all supported languages
urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    prefix_default_language=False,  # Don't prefix English (default)
)

# Also include core URLs without language prefix for default English
urlpatterns += [
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
