from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from apps.actividades.models import Actividad


@login_required
def index(request):
	# En el inicio se muestran todas las actividades registradas.
	actividades_qs = Actividad.objects.all()
	ahora = timezone.localtime()

	totales = actividades_qs.aggregate(
		total_participantes=Sum('numero_participantes'),
		total_horas=Sum('horas_dedicadas'),
	)

	# "Este mes" se basa en la fecha de inicio de la actividad.
	actividades_mes = actividades_qs.filter(
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
		'total_actividades': actividades_qs.count(),
		'actividades_mes': actividades_mes,
		'mes_actual': meses_es[ahora.month - 1],
		'total_participantes': totales['total_participantes'] or 0,
		'total_horas': totales['total_horas'] or 0,
		'actividades_recientes': actividades_qs.select_related('creado_por').order_by('-fecha_creacion', '-id'),
	}

	return render(request, 'index.html', contexto)



