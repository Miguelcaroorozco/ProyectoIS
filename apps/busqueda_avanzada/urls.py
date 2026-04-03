from django.urls import path

from . import views

urlpatterns = [
    path('busqueda-avanzada/', views.busqueda_avanzada, name='busqueda_avanzada'),
    path('busqueda-avanzada.html', views.busqueda_avanzada),
]
