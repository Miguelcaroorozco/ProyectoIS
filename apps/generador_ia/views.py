import json
import os
import re
import urllib.error
import urllib.request
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from apps.actividades.models import Actividad


def _normalize_ai_plain_text(text: str) -> str:
    if not text:
        return ''

    s = str(text).replace('\r\n', '\n').replace('\r', '\n')

    # Remove common markdown wrappers while keeping content.
    s = s.replace('```', '')

    # Bold/italic markers
    s = s.replace('**', '')

    lines = []
    for line in s.split('\n'):
        ln = line.strip()

        # Headings like "### Título"
        while ln.startswith('#'):
            ln = ln[1:].lstrip()

        # Blockquote
        if ln.startswith('>'):
            ln = ln[1:].lstrip()

        # Bullets: "* ", "+ ", "- " => unify to "- "
        if ln.startswith('* '):
            ln = '- ' + ln[2:]
        elif ln.startswith('+ '):
            ln = '- ' + ln[2:]
        # keep "- " as is

        lines.append(ln)

    # Trim excessive blank lines
    out_lines = []
    blank = 0
    for ln in lines:
        if not ln:
            blank += 1
            if blank > 1:
                continue
        else:
            blank = 0
        out_lines.append(ln)

    return '\n'.join(out_lines).strip()


@login_required
def generador_ia(request):
    return render(request, 'generador_ia/generador-ia.html')


def _ollama_request(payload: dict, timeout_seconds: int = 60) -> dict:
    base_url = (os.environ.get('OLLAMA_BASE_URL') or 'http://localhost:11434').rstrip('/')
    url = f'{base_url}/api/chat'

    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
        raw = resp.read().decode('utf-8')
        return json.loads(raw)


def _resumen_bd() -> dict:
    agg = Actividad.objects.aggregate(
        total_actividades=Count('id'),
        total_participantes=Sum('numero_participantes'),
        total_horas=Sum('horas_dedicadas'),
    )
    return {
        'total_actividades': int(agg.get('total_actividades') or 0),
        'total_participantes': int(agg.get('total_participantes') or 0),
        'total_horas': int(agg.get('total_horas') or 0),
    }


def _buscar_actividad(actividad_ref: str):
    if not actividad_ref:
        return None

    ref = str(actividad_ref).strip()
    if not ref:
        return None

    # Intentar por ID
    if ref.isdigit():
        return Actividad.objects.filter(id=int(ref)).first()

    # Intentar por nombre (parcial)
    return Actividad.objects.filter(nombre__icontains=ref).order_by('-fecha_inicio', '-id').first()


def _is_create_activity_intent(user_text: str) -> bool:
    if not user_text:
        return False
    txt = str(user_text).strip().lower()

    if re.match(r'^/(crear_actividad|crear-actividad|crearactividad|crear|actividad)\b', txt):
        return True

    return re.match(
        r'^(crea|crear|registra|registrar|agrega|agregar|guarda|guardar)\s+(una\s+)?actividad\b',
        txt,
    ) is not None


def _parse_iso_date(value: str):
    if not value:
        return None
    s = str(value).strip()
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', s)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _extract_activity_payload_with_ollama(
    *,
    model: str,
    resumen: dict,
    user_request: str,
    timeout_seconds: int = 60,
) -> dict:
    system = (
        "Eres un asistente que convierte solicitudes en una Actividad para un sistema universitario. "
        "Devuelve SOLO JSON válido, sin texto adicional. "
        "Usa exactamente estas llaves: "
        "mes, periodo, fecha_inicio, fecha_fin, tipologia, modalidad, programa, nombre, "
        "descripcion, objetivo, numero_participantes, horas_dedicadas, recursos_utilizados, resultados, observaciones. "
        "Reglas: "
        "- 'mes' debe ser uno de: enero,febrero,marzo,abril,mayo,junio,julio,agosto,septiembre,octubre,noviembre,diciembre. "
        "- 'tipologia' debe ser uno de: taller,seminario,curso,otro. "
        "- 'modalidad' debe ser uno de: presencial,virtual,mixta. "
        "- 'fecha_inicio' y 'fecha_fin' deben venir en formato YYYY-MM-DD. "
        "- Si un dato no se especifica, usa string vacío '' o 0 para números; no inventes fechas. "
    )

    user = (
        f"Totales del sistema (por si sirve de contexto, no inventes datos): {json.dumps(resumen, ensure_ascii=False)}\n"
        f"Solicitud del usuario: {user_request}" 
    )

    payload = {
        'model': model,
        'format': 'json',
        'stream': False,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
    }
    return _ollama_request(payload, timeout_seconds=timeout_seconds)


def _extract_first_json_object(text: str):
    if not text:
        return None
    s = str(text).strip()
    start = s.find('{')
    end = s.rfind('}')
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = s[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _missing_fields_message(missing: list) -> str:
    labels = {
        'mes': 'Mes (ej. mayo)',
        'periodo': 'Periodo (ej. 2026-1)',
        'fecha_inicio_raw': 'Fecha inicio (YYYY-MM-DD)',
        'fecha_fin_raw': 'Fecha fin (YYYY-MM-DD)',
        'tipologia': 'Tipología (taller, seminario, curso, otro)',
        'modalidad': 'Modalidad (presencial, virtual, mixta)',
        'programa': 'Programa',
        'nombre': 'Nombre de la actividad',
        'fecha_inicio(formato YYYY-MM-DD)': 'Fecha inicio (formato YYYY-MM-DD)',
        'fecha_fin(formato YYYY-MM-DD)': 'Fecha fin (formato YYYY-MM-DD)',
        'fecha_fin(no puede ser anterior a fecha_inicio)': 'Fechas (fecha fin no puede ser anterior a fecha inicio)',
        'mes(valor inválido)': 'Mes (valor inválido)',
        'tipologia(valor inválido)': 'Tipología (valor inválido)',
        'modalidad(valor inválido)': 'Modalidad (valor inválido)',
    }

    ordered = []
    for k in (
        'mes',
        'periodo',
        'fecha_inicio_raw',
        'fecha_fin_raw',
        'tipologia',
        'modalidad',
        'programa',
        'nombre',
        'fecha_inicio(formato YYYY-MM-DD)',
        'fecha_fin(formato YYYY-MM-DD)',
        'fecha_fin(no puede ser anterior a fecha_inicio)',
        'mes(valor inválido)',
        'tipologia(valor inválido)',
        'modalidad(valor inválido)',
    ):
        if k in missing:
            ordered.append(k)

    for k in missing:
        if k not in ordered:
            ordered.append(k)

    items = [f"- {labels.get(k, str(k))}" for k in ordered]
    return (
        'Puedo crear la actividad, pero no se especificó (o está inválido) lo siguiente:\n'
        + '\n'.join(items)
        + '\n\nEnvíame un nuevo mensaje empezando con "crear actividad" e incluyendo esos datos.'
    )


def _coerce_activity_fields(data: dict) -> dict:
    if not isinstance(data, dict):
        return {}

    def _s(key: str) -> str:
        return str(data.get(key) or '').strip()

    def _i(key: str) -> int:
        try:
            n = int(data.get(key) or 0)
            return n if n >= 0 else 0
        except (TypeError, ValueError):
            return 0

    return {
        'mes': _s('mes').lower(),
        'periodo': _s('periodo'),
        'fecha_inicio_raw': _s('fecha_inicio'),
        'fecha_fin_raw': _s('fecha_fin'),
        'tipologia': _s('tipologia').lower(),
        'modalidad': _s('modalidad').lower(),
        'programa': _s('programa'),
        'nombre': _s('nombre'),
        'descripcion': _s('descripcion'),
        'objetivo': _s('objetivo'),
        'numero_participantes': _i('numero_participantes'),
        'horas_dedicadas': _i('horas_dedicadas'),
        'recursos_utilizados': _s('recursos_utilizados'),
        'resultados': _s('resultados'),
        'observaciones': _s('observaciones'),
    }


def _validate_activity_fields(fields: dict) -> list:
    missing = []
    for k in ('mes', 'periodo', 'fecha_inicio_raw', 'fecha_fin_raw', 'tipologia', 'modalidad', 'programa', 'nombre'):
        if not (fields.get(k) or '').strip():
            missing.append(k)

    fi = _parse_iso_date(fields.get('fecha_inicio_raw') or '')
    ff = _parse_iso_date(fields.get('fecha_fin_raw') or '')
    if fields.get('fecha_inicio_raw') and not fi:
        missing.append('fecha_inicio(formato YYYY-MM-DD)')
    if fields.get('fecha_fin_raw') and not ff:
        missing.append('fecha_fin(formato YYYY-MM-DD)')
    if fi and ff and ff < fi:
        missing.append('fecha_fin(no puede ser anterior a fecha_inicio)')

    if fields.get('mes') and fields['mes'] not in {m for m, _ in Actividad.MESES}:
        missing.append('mes(valor inválido)')
    if fields.get('tipologia') and fields['tipologia'] not in {t for t, _ in Actividad.TIPOLOGIAS}:
        missing.append('tipologia(valor inválido)')
    if fields.get('modalidad') and fields['modalidad'] not in {m for m, _ in Actividad.MODALIDADES}:
        missing.append('modalidad(valor inválido)')

    return missing


@login_required
@require_POST
def generador_ia_api(request):
    try:
        data = json.loads((request.body or b'{}').decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido.'}, status=400)

    mensaje = (data.get('mensaje') or '').strip()
    messages = data.get('messages')
    actividad_ref = (data.get('actividad_ref') or '').strip()

    if messages is None:
        if not mensaje:
            return JsonResponse({'ok': False, 'error': 'Escribe un mensaje.'}, status=400)
        messages = [{'role': 'user', 'content': mensaje}]

    if not isinstance(messages, list) or not messages:
        return JsonResponse({'ok': False, 'error': 'El historial del chat es inválido.'}, status=400)

    cleaned_messages = []
    for item in messages[-20:]:
        if not isinstance(item, dict):
            continue
        role = (item.get('role') or '').strip()
        content = (item.get('content') or '').strip()
        if role not in {'user', 'assistant'}:
            continue
        if not content:
            continue
        cleaned_messages.append({'role': role, 'content': content})

    if not cleaned_messages or cleaned_messages[-1]['role'] != 'user':
        return JsonResponse({'ok': False, 'error': 'Envía un mensaje del usuario para continuar.'}, status=400)

    if not mensaje:
        mensaje = cleaned_messages[-1]['content']

    model = (os.environ.get('OLLAMA_MODEL') or 'llama3.2:3b').strip() or 'llama3.2:3b'

    actividad = _buscar_actividad(actividad_ref)
    resumen = _resumen_bd()

    if _is_create_activity_intent(mensaje):
        try:
            raw = _extract_activity_payload_with_ollama(
                model=model,
                resumen=resumen,
                user_request=mensaje,
            )
            content = (
                (raw.get('message') or {}).get('content')
                or raw.get('response')
                or ''
            ).strip()
            extracted = json.loads(content) if content else {}
        except urllib.error.URLError:
            return JsonResponse(
                {
                    'ok': False,
                    'error': (
                        'No pude conectarme a Ollama. Verifica que esté corriendo en tu PC: '
                        '`ollama serve` y que exista el modelo configurado.'
                    ),
                },
                status=502,
            )
        except json.JSONDecodeError:
            extracted = _extract_first_json_object(content) or {}
        except Exception:
            return JsonResponse({'ok': False, 'error': 'Error preparando la actividad con IA.'}, status=500)

        fields = _coerce_activity_fields(extracted)
        missing = _validate_activity_fields(fields)
        if not extracted:
            return JsonResponse(
                {
                    'ok': True,
                    'respuesta': _missing_fields_message(
                        ['mes', 'periodo', 'fecha_inicio_raw', 'fecha_fin_raw', 'tipologia', 'modalidad', 'programa', 'nombre']
                    ),
                }
            )

        if missing:
            return JsonResponse({'ok': True, 'respuesta': _missing_fields_message(missing)})

        fi = _parse_iso_date(fields.get('fecha_inicio_raw') or '')
        ff = _parse_iso_date(fields.get('fecha_fin_raw') or '')

        actividad_nueva = Actividad.objects.create(
            mes=fields['mes'],
            periodo=fields['periodo'],
            fecha_inicio=fi,
            fecha_fin=ff,
            tipologia=fields['tipologia'],
            modalidad=fields['modalidad'],
            programa=fields['programa'],
            nombre=fields['nombre'],
            descripcion=fields.get('descripcion') or '',
            objetivo=fields.get('objetivo') or '',
            numero_participantes=fields.get('numero_participantes') or 0,
            horas_dedicadas=fields.get('horas_dedicadas') or 0,
            recursos_utilizados=fields.get('recursos_utilizados') or '',
            resultados=fields.get('resultados') or '',
            observaciones=fields.get('observaciones') or '',
            creado_por=request.user,
        )

        return JsonResponse(
            {
                'ok': True,
                'respuesta': (
                    'Actividad creada correctamente.\n'
                    + f"ID: {actividad_nueva.id}\n"
                    + f"Nombre: {actividad_nueva.nombre}\n"
                    + f"Periodo: {actividad_nueva.periodo}\n"
                    + f"Fechas: {actividad_nueva.fecha_inicio} a {actividad_nueva.fecha_fin}"
                ),
            }
        )

    contexto_actividad = None
    if actividad:
        contexto_actividad = {
            'id': actividad.id,
            'nombre': actividad.nombre,
            'programa': actividad.programa,
            'periodo': actividad.periodo,
            'mes': actividad.mes,
            'tipologia': actividad.tipologia,
            'modalidad': actividad.modalidad,
            'fecha_inicio': str(actividad.fecha_inicio),
            'fecha_fin': str(actividad.fecha_fin),
            'descripcion': actividad.descripcion,
            'objetivo': actividad.objetivo,
            'numero_participantes': actividad.numero_participantes,
            'horas_dedicadas': actividad.horas_dedicadas,
            'recursos_utilizados': actividad.recursos_utilizados,
            'resultados': actividad.resultados,
            'observaciones': actividad.observaciones,
        }

    system = (
        "Eres un asistente para un sistema universitario 'Gestor de actividades'. "
        "Puedes: (1) proponer actividades completas (nombre, objetivo, descripción, recursos, resultados, observaciones), "
        "(2) explicar reportes usando los totales disponibles, y "
        "(3) responder preguntas sobre una actividad específica si se entrega el contexto. "
        "Responde en español, claro y directo. "
        "IMPORTANTE: responde en texto plano (sin Markdown). "
        "No uses asteriscos (* o **), ni listas con '*', ni negritas con '**'. "
        "Si necesitas listas, usa guiones '-' y títulos con ':' (por ejemplo: Nombre: ...)."
    )

    user_parts = [
        f"Totales del sistema: {json.dumps(resumen, ensure_ascii=False)}",
    ]
    if contexto_actividad:
        user_parts.append(
            "Contexto de actividad encontrada (usa esto si preguntan por esa actividad): "
            + json.dumps(contexto_actividad, ensure_ascii=False)
        )
    user_parts.append(f"Solicitud del usuario: {mensaje}")
    user_prompt = "\n\n".join(user_parts)

    payload_messages = [
        {'role': 'system', 'content': system},
        {
            'role': 'system',
            'content': (
                'Contexto del sistema (totales y actividad si aplica). '\
                + user_prompt
            ),
        },
        *cleaned_messages,
    ]

    payload = {
        'model': model,
        'stream': False,
        'messages': payload_messages,
    }

    try:
        result = _ollama_request(payload)
        content = (
            (result.get('message') or {}).get('content')
            or result.get('response')
            or ''
        ).strip()
    except urllib.error.URLError:
        return JsonResponse(
            {
                'ok': False,
                'error': (
                    'No pude conectarme a Ollama. Verifica que esté corriendo en tu PC: '
                    '`ollama serve` y que exista el modelo configurado.'
                ),
            },
            status=502,
        )
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Error generando respuesta con IA.'}, status=500)

    if not content:
        return JsonResponse({'ok': False, 'error': 'Ollama respondió vacío.'}, status=502)

    content = _normalize_ai_plain_text(content)

    return JsonResponse({'ok': True, 'respuesta': content})
