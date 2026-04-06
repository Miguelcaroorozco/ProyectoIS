import csv
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render


TIPOS_REPORTE = {
    'general': 'Reporte General',
    'tipologia': 'Por Tipologia',
    'programa': 'Por Programa',
    'mensual': 'Mensual',
    'anual': 'Anual',
    'personalizado': 'Personalizado',
}


def _filas_reporte(tipo_reporte, usuario):
    ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return [
        {
            'tipo': TIPOS_REPORTE.get(tipo_reporte, TIPOS_REPORTE['general']),
            'usuario': usuario.username,
            'correo': usuario.email or '',
            'estado': 'Sin actividades registradas',
            'fecha': ahora,
        }
    ]


@login_required
def reportes(request):
    tipo_reporte = request.GET.get('tipo', 'general')
    if tipo_reporte not in TIPOS_REPORTE:
        tipo_reporte = 'general'

    filas = _filas_reporte(tipo_reporte, request.user)

    contexto = {
        'tipos_reporte': TIPOS_REPORTE,
        'tipo_reporte': tipo_reporte,
        'filas_reporte': filas,
        'mostrar_reporte': request.GET.get('accion') == 'ver',
    }
    return render(request, 'reportes/reportes.html', contexto)


@login_required
def descargar_reporte_csv(request):
    tipo_reporte = request.GET.get('tipo', 'general')
    if tipo_reporte not in TIPOS_REPORTE:
        tipo_reporte = 'general'

    filas = _filas_reporte(tipo_reporte, request.user)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename="reporte_{tipo_reporte}_{request.user.username}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(['Tipo de Reporte', 'Usuario', 'Correo', 'Estado', 'Fecha'])
    for fila in filas:
        writer.writerow([
            fila['tipo'],
            fila['usuario'],
            fila['correo'],
            fila['estado'],
            fila['fecha'],
        ])

    return response
