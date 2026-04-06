from django.urls import path

from . import views

urlpatterns = [
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/descargar-excel/', views.descargar_reporte_excel, name='reportes_descargar_excel'),
    path('reportes/descargar-csv/', views.descargar_reporte_excel),
    path('reportes.html', views.reportes),
]
