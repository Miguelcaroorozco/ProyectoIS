from io import BytesIO
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from apps.actividades.models import Actividad


TIPOS_REPORTE = {
    'general': 'Reporte General',
    'tipologia': 'Por Tipologia',
    'programa': 'Por Programa',
    'mensual': 'Mensual',
    'anual': 'Anual',
    'personalizado': 'Personalizado',
}


def _parse_anio(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _filtrar_actividades(tipo_reporte, filtros):
    actividades = Actividad.objects.all()

    tipologia = filtros.get('tipologia', '').strip()
    programa = filtros.get('programa', '').strip()
    mes = filtros.get('mes', '').strip()
    anio = _parse_anio(filtros.get('anio', '').strip())
    fecha_inicio = filtros.get('fecha_inicio', '').strip()
    fecha_fin = filtros.get('fecha_fin', '').strip()

    if tipo_reporte == 'tipologia' and tipologia:
        actividades = actividades.filter(tipologia=tipologia)

    if tipo_reporte == 'programa' and programa:
        actividades = actividades.filter(programa__icontains=programa)

    if tipo_reporte == 'mensual':
        if mes:
            actividades = actividades.filter(mes=mes)
        if anio:
            actividades = actividades.filter(fecha_inicio__year=anio)

    if tipo_reporte == 'anual' and anio:
        actividades = actividades.filter(fecha_inicio__year=anio)

    if tipo_reporte == 'personalizado':
        if fecha_inicio:
            actividades = actividades.filter(fecha_inicio__gte=fecha_inicio)
        if fecha_fin:
            actividades = actividades.filter(fecha_fin__lte=fecha_fin)

    return actividades


def _construir_filtros(request):
    return {
        'tipologia': request.GET.get('tipologia', ''),
        'programa': request.GET.get('programa', ''),
        'mes': request.GET.get('mes', ''),
        'anio': request.GET.get('anio', ''),
        'fecha_inicio': request.GET.get('fecha_inicio', ''),
        'fecha_fin': request.GET.get('fecha_fin', ''),
    }


def _querystring_excel(tipo_reporte, filtros):
    parametros = {'tipo': tipo_reporte}
    for clave, valor in filtros.items():
        if valor:
            parametros[clave] = valor
    return urlencode(parametros)


def _crear_libro_excel(tipo_reporte, actividades):
    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Reporte'

    encabezados = [
        'Tipo de Reporte',
        'Nombre Actividad',
        'Programa',
        'Tipologia',
        'Modalidad',
        'Periodo',
        'Fecha Inicio',
        'Fecha Fin',
        'Participantes',
        'Horas',
    ]
    hoja.append(encabezados)

    encabezado_fill = PatternFill(fill_type='solid', fgColor='1F4E78')
    encabezado_font = Font(bold=True, color='FFFFFF')

    for indice_columna in range(1, len(encabezados) + 1):
        celda = hoja.cell(row=1, column=indice_columna)
        celda.fill = encabezado_fill
        celda.font = encabezado_font
        celda.alignment = Alignment(horizontal='center')

    for actividad in actividades:
        hoja.append([
            TIPOS_REPORTE.get(tipo_reporte, TIPOS_REPORTE['general']),
            actividad.nombre,
            actividad.programa,
            actividad.get_tipologia_display(),
            actividad.get_modalidad_display(),
            actividad.periodo,
            actividad.fecha_inicio.strftime('%Y-%m-%d') if actividad.fecha_inicio else '',
            actividad.fecha_fin.strftime('%Y-%m-%d') if actividad.fecha_fin else '',
            actividad.numero_participantes,
            actividad.horas_dedicadas,
        ])

    for columna in hoja.columns:
        longitud_maxima = max(len(str(celda.value)) if celda.value is not None else 0 for celda in columna)
        hoja.column_dimensions[columna[0].column_letter].width = min(max(longitud_maxima + 2, 12), 45)

    return libro


@login_required
def reportes(request):
    tipo_reporte = request.GET.get('tipo', 'general')
    if tipo_reporte not in TIPOS_REPORTE:
        tipo_reporte = 'general'

    filtros = _construir_filtros(request)
    mostrar_reporte = request.GET.get('accion') == 'ver'

    actividades = _filtrar_actividades(tipo_reporte, filtros) if mostrar_reporte else Actividad.objects.none()
    totales = actividades.aggregate(
        total_participantes=Sum('numero_participantes'),
        total_horas=Sum('horas_dedicadas'),
    )

    programas_disponibles = (
        Actividad.objects.order_by('programa')
        .values_list('programa', flat=True)
        .distinct()
    )

    anios_disponibles = sorted(
        {actividad.fecha_inicio.year for actividad in Actividad.objects.only('fecha_inicio')},
        reverse=True,
    )

    contexto = {
        'tipos_reporte': TIPOS_REPORTE,
        'tipo_reporte': tipo_reporte,
        'mostrar_reporte': mostrar_reporte,
        'filtros': filtros,
        'tipologias': Actividad.TIPOLOGIAS,
        'meses': Actividad.MESES,
        'programas_disponibles': programas_disponibles,
        'anios_disponibles': anios_disponibles,
        'actividades': actividades,
        'total_actividades': actividades.count(),
        'total_participantes': totales['total_participantes'] or 0,
        'total_horas': totales['total_horas'] or 0,
        'querystring_excel': _querystring_excel(tipo_reporte, filtros),
    }
    return render(request, 'reportes/reportes.html', contexto)


@login_required
def descargar_reporte_excel(request):
    tipo_reporte = request.GET.get('tipo', 'general')
    if tipo_reporte not in TIPOS_REPORTE:
        tipo_reporte = 'general'

    filtros = _construir_filtros(request)
    actividades = _filtrar_actividades(tipo_reporte, filtros)

    libro = _crear_libro_excel(tipo_reporte, actividades)
    buffer = BytesIO()
    libro.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = (
        f'attachment; filename="reporte_{tipo_reporte}_{request.user.username}.xlsx"'
    )

    return response
