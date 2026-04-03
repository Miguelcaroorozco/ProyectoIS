from django.urls import path

from . import views

urlpatterns = [
    path('nueva-actividad/', views.nueva_actividad, name='nueva_actividad'),
    path('nueva-actividad.html', views.nueva_actividad),
]
