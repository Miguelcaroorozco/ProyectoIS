from django.urls import path

from . import views

urlpatterns = [
    path('generador-ia/', views.generador_ia, name='generador_ia'),
    path('generador-ia/api/', views.generador_ia_api, name='generador_ia_api'),
    path('generador-ia.html', views.generador_ia),
]
