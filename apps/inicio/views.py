from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def index(request):
	return render(request, 'index.html')


@login_required
def actividades(request):
	return render(request, 'actividades.html')


@login_required
def nueva_actividad(request):
	return render(request, 'nueva-actividad.html')


@login_required
def busqueda_avanzada(request):
	return render(request, 'busqueda-avanzada.html')


@login_required
def reportes(request):
	return render(request, 'reportes.html')


@login_required
def generador_ia(request):
	return render(request, 'generador-ia.html')


@login_required
def historial(request):
	return render(request, 'historial.html')



