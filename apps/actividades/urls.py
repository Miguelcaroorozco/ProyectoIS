from django.urls import path

from . import views

urlpatterns = [
    path('actividades/', views.actividades, name='actividades'),
    path('nueva-actividad/', views.nueva_actividad, name='nueva_actividad'),

	path('actividades/<int:pk>/editar/', views.editar_actividad, name='editar_actividad'),
	path('actividades/<int:pk>/eliminar/', views.eliminar_actividad, name='eliminar_actividad'),

    path('api/programas-por-facultad/', views.programas_por_facultad, name='programas_por_facultad'),
]
