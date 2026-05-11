from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Force password reset to use the app UI even if the user ends up
    # on the Django admin login/reset screens.
    path(
        'admin/password_reset/',
        RedirectView.as_view(pattern_name='autenticacion:password_reset', permanent=False),
    ),
    path(
        'admin/password_reset/done/',
        RedirectView.as_view(
            pattern_name='autenticacion:password_reset_done', permanent=False
        ),
    ),
    path(
        'admin/reset/<uidb64>/<token>/',
        RedirectView.as_view(
            pattern_name='autenticacion:password_reset_confirm', permanent=False
        ),
    ),
    path(
        'admin/reset/done/',
        RedirectView.as_view(
            pattern_name='autenticacion:password_reset_complete', permanent=False
        ),
    ),
    path('admin/', admin.site.urls),
    path('', include(('core.autenticacion.urls', 'autenticacion'), namespace='autenticacion')),
    path('administracion/', include('core.administracion.urls')),
    path('configuracion/', include('apps.configuracion.urls')),
    path('', include('apps.actividades.urls')),
    path('', include('apps.busqueda_avanzada.urls')),
    path('', include('apps.reportes.urls')),
    path('', include('apps.historial.urls')),
    path('', include('apps.generador_ia.urls')),
    path('', include('apps.inicio.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
