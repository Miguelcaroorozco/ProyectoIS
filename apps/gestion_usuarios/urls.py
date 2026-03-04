from django.urls import path

from . import views

urlpatterns = [
	path('', views.lista_usuarios_view, name='usuarios'),
	path('nuevo/', views.nuevo_usuario_view, name='usuarios_nuevo'),
	path('<int:usuario_id>/editar/', views.editar_usuario_view, name='usuarios_editar'),
]
