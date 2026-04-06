from django.urls import path

from . import views

urlpatterns = [
    path('actividades/', views.actividades, name='actividades'),
    path('nueva-actividad/', views.nueva_actividad, name='nueva_actividad'),

    path('actividades.html', views.actividades),
    path('nueva-actividad.html', views.nueva_actividad),
]
