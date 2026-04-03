from django.urls import path

from . import views

urlpatterns = [
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/descargar-csv/', views.descargar_reporte_csv, name='reportes_descargar_csv'),
    path('reportes.html', views.reportes),
]
