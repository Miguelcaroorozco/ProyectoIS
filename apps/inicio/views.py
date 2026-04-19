from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from apps.actividades.models import Actividad


@login_required
def index(request):
	actividades_usuario = Actividad.objects.filter(creado_por=request.user)
	ahora = timezone.localtime()

	totales = actividades_usuario.aggregate(
		total_participantes=Sum('numero_participantes'),
		total_horas=Sum('horas_dedicadas'),
	)

	actividades_mes = actividades_usuario.filter(
		fecha_inicio__year=ahora.year,
		fecha_inicio__month=ahora.month,
	).count()

	meses_es = [
		'enero',
		'febrero',
		'marzo',
		'abril',
		'mayo',
		'junio',
		'julio',
		'agosto',
		'septiembre',
		'octubre',
		'noviembre',
		'diciembre',
	]

	contexto = {
		'total_actividades': actividades_usuario.count(),
		'actividades_mes': actividades_mes,
		'mes_actual': meses_es[ahora.month - 1],
		'total_participantes': totales['total_participantes'] or 0,
		'total_horas': totales['total_horas'] or 0,
		'actividades_recientes': actividades_usuario.select_related('creado_por')[:5],
	}

	return render(request, 'index.html', contexto)



