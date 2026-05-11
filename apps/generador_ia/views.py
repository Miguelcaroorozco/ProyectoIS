import json
import os
import urllib.error
import urllib.request

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

    model = (os.environ.get('OLLAMA_MODEL') or 'llama3.2:3b').strip() or 'llama3.2:3b'

    actividad = _buscar_actividad(actividad_ref)
    resumen = _resumen_bd()

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
