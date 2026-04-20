from django.urls import path

from . import views

urlpatterns = [
    path('', views.admin_inicio, name='admin_panel'),
    path('usuarios/', views.admin_usuarios, name='admin_usuarios'),
    path('usuarios/nuevo/', views.admin_usuarios_nuevo, name='admin_usuarios_nuevo'),
    path('usuarios/<int:usuario_id>/editar/', views.admin_usuarios_editar, name='admin_usuarios_editar'),
    path('facultades/', views.admin_facultades, name='admin_facultades'),
    path('programas/', views.admin_programas, name='admin_programas'),
]
