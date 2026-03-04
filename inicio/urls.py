from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='registration/login.html'),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('', views.index, name='index'),
    path('actividades/', views.actividades, name='actividades'),
    path('nueva-actividad/', views.nueva_actividad, name='nueva_actividad'),
    path('busqueda-avanzada/', views.busqueda_avanzada, name='busqueda_avanzada'),
    path('reportes/', views.reportes, name='reportes'),
    path('generador-ia/', views.generador_ia, name='generador_ia'),
    path('historial/', views.historial, name='historial'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('configuracion/', views.configuracion, name='configuracion'),

    # Compatibilidad con enlaces antiguos *.html (por si algún link quedó sin migrar)
    path('index.html', views.index),
    path('actividades.html', views.actividades),
    path('nueva-actividad.html', views.nueva_actividad),
    path('busqueda-avanzada.html', views.busqueda_avanzada),
    path('reportes.html', views.reportes),
    path('generador-ia.html', views.generador_ia),
    path('historial.html', views.historial),
    path('usuarios.html', views.usuarios),
    path('configuracion.html', views.configuracion),
]
