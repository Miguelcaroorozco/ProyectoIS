from django.urls import path

from .views import configuracion_view

urlpatterns = [
    path('', configuracion_view, name='configuracion'),
]
