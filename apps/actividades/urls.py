from django.urls import path

from . import views

urlpatterns = [
    path('actividades/', views.actividades, name='actividades'),

    path('actividades.html', views.actividades),
]
