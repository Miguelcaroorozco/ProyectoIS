import json
import os
import re
import unicodedata
import urllib.error
import urllib.request
from urllib.parse import urlencode
from datetime import date, timedelta

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


def _normalize_gemini_model_name(model: str) -> str:
    """Normalize GEMINI_MODEL values to the format expected by the Gemini REST API.

    Accepts common variants like:
    - "Gemini-2.5-Flash" -> "gemini-2.5-flash"
    - "models/gemini-1.5-flash" -> "gemini-1.5-flash"
    - ".../models/gemini-2.0-flash:generateContent" -> "gemini-2.0-flash"
    """

    raw = (model or '').strip()
    if not raw:
        return ''

    # Remove any endpoint suffix like ":generateContent".
    raw = raw.split(':', 1)[0].strip()

    # If a full path was provided, keep the last segment.
    if '/' in raw:
        raw = raw.rsplit('/', 1)[-1].strip()

    # Strip optional "models/" prefix.
    if raw.lower().startswith('models/'):
        raw = raw[7:].strip()

    # Normalize casing and separators.
    # Keep token separation: spaces become dashes (so "Flash Lite" -> "flash-lite").
    raw = re.sub(r'\s+', '-', raw)
    raw = raw.replace('_', '-')
    raw = raw.lower()
    raw = re.sub(r'-{2,}', '-', raw).strip('-')

    # Some users write "gemini" with different casing/prefixes.
    if raw.startswith('gemini') and not raw.startswith('gemini-'):
        # e.g. "gemini2.5-flash" -> "gemini-2.5-flash"
        raw = 'gemini-' + raw[len('gemini') :].lstrip('-')

    # Final sanity check: Gemini model names are typically lowercase and contain letters/numbers/dots/dashes.
    # If the value is still clearly not a model id, keep it as-is to let the API return a detailed error.
    return raw


@login_required
def generador_ia(request):
    return render(request, 'generador_ia/generador-ia.html')


def _gemini_request(*, payload: dict, model: str, timeout_seconds: int = 60) -> dict:
    api_key = (os.environ.get('GEMINI_API_KEY') or '').strip()
    if not api_key:
        raise RuntimeError('GEMINI_API_KEY no está configurado.')

    base_url = (os.environ.get('GEMINI_BASE_URL') or 'https://generativelanguage.googleapis.com').rstrip('/')
    model = _normalize_gemini_model_name(model) or 'gemini-1.5-flash'

    # API v1beta: generateContent
    # https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=...
    query = urlencode({'key': api_key})
    url = f'{base_url}/v1beta/models/{model}:generateContent?{query}'

    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode('utf-8')
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        # Intentar leer el cuerpo del error para un mensaje más útil.
        body = ''
        try:
            body = (e.read() or b'').decode('utf-8', errors='replace')
        except Exception:
            body = ''

        detail = ''
        if body:
            try:
                parsed = json.loads(body)
                detail = (parsed.get('error') or {}).get('message') or ''
            except Exception:
                detail = body[:400]

        msg = f'Gemini API error (HTTP {getattr(e, "code", "?")}): {detail}'.strip()
        if 'unexpected model name format' in msg.lower():
            msg += ' (Tip: configura GEMINI_MODEL como "gemini-2.5-flash" o "gemini-1.5-flash"; sin "Gemini-" y en minúsculas.)'
        raise RuntimeError(msg)


def _gemini_extract_text(result: dict) -> str:
    if not isinstance(result, dict):
        return ''

    candidates = result.get('candidates')
    if not candidates or not isinstance(candidates, list):
        return ''

    content = (candidates[0] or {}).get('content') or {}
    parts = content.get('parts')
    if not parts or not isinstance(parts, list):
        return ''

    text = (parts[0] or {}).get('text')
    return (text or '').strip()


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


def _norm_msg(msg: str) -> str:
    msg = str(msg or '').strip().lower()
    msg = ''.join(c for c in unicodedata.normalize('NFKD', msg) if not unicodedata.combining(c))
    msg = re.sub(r'\s+', ' ', msg).strip()
    return msg


def _detect_tipologia_from_message(norm_msg: str):
    # Tipologías conocidas por el modelo.
    # Nota: si en la BD existen valores fuera de choices, este filtro podría no encontrarlos.
    # Aun así, para consultas como "tipo taller" buscamos "taller".
    tip_keywords = {
        'taller': 'taller',
        'seminario': 'seminario',
        'curso': 'curso',
        'otro': 'otro',
    }
    for k, v in tip_keywords.items():
        if re.search(rf'\b{re.escape(k)}\b', norm_msg):
            return v
    return None


def _try_answer_activity_list_questions(mensaje: str):
    """Answer simple listing questions directly from DB.

    Returns a plain-text response string or None if not recognized.
    """
    norm = _norm_msg(mensaje)
    if not norm:
        return None

    wants_names = False
    if ('nombres' in norm and 'actividad' in norm) or re.search(r'\b(lista|listado)\b.*\bactividades\b', norm):
        wants_names = True
    if re.search(r'\b(dime|muestrame|muestreme|cuales son|cu\w+les son)\b.*\bactividades\b', norm):
        wants_names = True

    tip = None
    if 'tipologia' in norm or re.search(r'\btipo\b', norm):
        tip = _detect_tipologia_from_message(norm)

    # Filtrado por tipología (por ejemplo: "actividades tipo taller").
    if tip and (('actividad' in norm) or ('actividades' in norm)):
        qs = Actividad.objects.filter(tipologia__iexact=tip).order_by('-fecha_inicio', '-id')
        nombres = list(qs.values_list('nombre', flat=True))
        if not nombres:
            return f"No hay actividades con tipología '{tip}'."
        lines = [f"Actividades con tipología '{tip}' ({len(nombres)}):"]
        lines.extend([f"- {n}" for n in nombres])
        return "\n".join(lines)

    # Lista de nombres (todas)
    if wants_names:
        qs = Actividad.objects.order_by('-fecha_inicio', '-id')
        nombres = list(qs.values_list('nombre', flat=True))
        if not nombres:
            return 'No hay actividades registradas.'
        lines = [f"Actividades registradas ({len(nombres)}):"]
        lines.extend([f"- {n}" for n in nombres])
        return "\n".join(lines)

    return None


def _is_create_activity_intent(user_text: str) -> bool:
    if not user_text:
        return False

    def _norm(s: str) -> str:
        s = str(s or '').strip().lower()
        # Strip accents to make regex matching robust (créala -> creala).
        s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
        return s

    txt = _norm(user_text)

    if re.match(r'^/(crear_actividad|crear-actividad|crearactividad|crear|actividad)\b', txt):
        return True

    # Aceptar variantes comunes:
    # - "crea actividad"
    # - "crea una actividad"
    # - "crea la/esa/esta actividad"
    # - "registra esa actividad" / "guarda la actividad"
    if re.match(
        r'^(crea|crear|registra|registrar|agrega|agregar|guarda|guardar)\s+actividad\b',
        txt,
    ):
        return True

    if re.match(
        r'^(crea|crear|registra|registrar|agrega|agregar|guarda|guardar)\s+(una|la|esta|esa)\s+actividad\b',
        txt,
    ):
        return True

    # Frases naturales:
    # - "quiero que crees esa actividad"
    # - "puedes crear esa actividad"
    # - "por favor crea esa actividad"
    if re.search(r'\b(crea|crear|crees|registre|registrar|guardes|guardar|agregues|agregar)\b', txt) and re.search(
        r'\bactividad\b',
        txt,
    ):
        if re.search(r'\b(quiero|puedes|podrias|por favor|necesito|haz)\b', txt):
            return True

    # Imperativo directo con pronombres:
    # - "creala" / "creala tu" / "creala tu mismo"
    if re.match(r'^(creala|creala\s+tu|creala\s+tu\s+mismo|creala\s+por\s+mi)\b', txt):
        return True

    return False


def _is_delegated_create_intent(user_text: str) -> bool:
    """True when the user explicitly delegates missing choices to the assistant."""
    if not user_text:
        return False
    s = str(user_text).strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

    # Examples: "creala tu", "creala tu mismo", "quiero que tu mismo la crees",
    # "dejalo a tu gusto", "a tu gusto".
    if re.search(r'\b(creala|crea)\b', s) and re.search(r'\btu\b', s):
        return True
    if re.search(r'\btu\s+mismo\b', s) or re.search(r'\btu\s+misma\b', s):
        return True
    if re.search(r'\b(a tu gusto|como quieras|como quiera|tu decides|tu elige)\b', s):
        return True
    return False


def _is_contextual_create_intent(*, mensaje: str, cleaned_messages: list) -> bool:
    """Detect create intent when the message is deictic ('la crees') and the chat contains an activity proposal."""
    if not mensaje or not cleaned_messages:
        return False

    msg = str(mensaje).strip().lower()
    msg = ''.join(c for c in unicodedata.normalize('NFKD', msg) if not unicodedata.combining(c))

    # If the user did not mention "actividad" but refers to "la" and a creation verb.
    if 'actividad' in msg:
        return False

    if re.search(r'\b(la|esa|esta)\b', msg) is None:
        return False

    if re.search(r'\b(crees|crearla|creala|registrarla|registrala|guardarla|guardala)\b', msg) is None:
        return False

    # Look for a recent proposal structure.
    recent = cleaned_messages[-10:]
    proposal_hits = 0
    for m in recent:
        txt = (m.get('content') or '').strip().lower()
        if not txt:
            continue
        if 'nombre:' in txt:
            proposal_hits += 1
        if 'objetivo:' in txt:
            proposal_hits += 1
        if 'descripci' in txt:
            proposal_hits += 1
    return proposal_hits >= 2


def _build_activity_request_from_history(*, mensaje: str, cleaned_messages: list) -> str:
    """Build a better extraction prompt for activity creation.

    If the user says something generic like "crea esa actividad", we attach the
    recent chat context so Gemini can extract the actual fields.
    """

    msg = (mensaje or '').strip()
    if not cleaned_messages:
        return msg

    # Heurística: si el mensaje refiere (esta/esa/la) actividad, usar contexto.
    # No dependemos del largo del mensaje, porque frases como "quiero que crees esa actividad"
    # también necesitan el contexto.
    generic = re.search(r'\b(esta|esa|la)\s+actividad\b', msg.lower()) is not None

    if not generic:
        return msg

    recent = cleaned_messages[-10:]
    lines = []
    for m in recent:
        role = (m.get('role') or '').strip().lower()
        content = (m.get('content') or '').strip()
        if not content:
            continue
        tag = 'USUARIO' if role == 'user' else 'ASISTENTE'
        lines.append(f'{tag}: {content}')

    contexto = '\n'.join(lines).strip()
    if not contexto:
        return msg

    return (
        'Usa la siguiente conversación para construir los campos de la actividad. '\
        'La última instrucción del usuario es crear/guardar la actividad descrita.\n\n'
        + contexto
    )


def _is_defaults_followup_intent(*, mensaje: str, cleaned_messages: list) -> bool:
    """Detect follow-up like 'eso lo dejo a tu gusto' after missing-fields prompt."""
    msg = (mensaje or '').strip().lower()
    msg = ''.join(c for c in unicodedata.normalize('NFKD', msg) if not unicodedata.combining(c))
    if not msg:
        return False

    if re.search(r'\b(a tu gusto|a su gusto|como quieras|como quiera|lo dejo a tu gusto|dejalo a tu gusto|dejalo)\b', msg) is None:
        return False

    # If the assistant previously asked for missing fields, treat this as consent to fill defaults.
    for m in reversed(cleaned_messages[-6:]):
        if (m.get('role') or '') != 'assistant':
            continue
        content = (m.get('content') or '').strip().lower()
        if 'puedo crear la actividad, pero no se especificó' in content:
            return True
        if 'envíame un nuevo mensaje empezando con "crear actividad"' in content:
            return True

    return False


def _parse_iso_date(value: str):
    if not value:
        return None
    s = str(value).strip()

    # Accept common variants besides YYYY-MM-DD:
    # - YYYY/MM/DD
    # - YYYY.MM.DD
    # - YYYY MM DD
    m = re.match(r'^(\d{4})[-\s\./](\d{1,2})[-\s\./](\d{1,2})$', s)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _mes_es_from_date(d: date) -> str:
    mapping = {
        1: 'enero',
        2: 'febrero',
        3: 'marzo',
        4: 'abril',
        5: 'mayo',
        6: 'junio',
        7: 'julio',
        8: 'agosto',
        9: 'septiembre',
        10: 'octubre',
        11: 'noviembre',
        12: 'diciembre',
    }
    return mapping.get(int(d.month), 'mayo')


def _periodo_from_date(d: date) -> str:
    # Heurística simple: semestre 1 (ene-jun), semestre 2 (jul-dic)
    semestre = 1 if int(d.month) <= 6 else 2
    return f'{int(d.year)}-{semestre}'


def _extract_activity_payload_with_gemini(
    *,
    model: str,
    resumen: dict,
    user_request: str,
    allow_defaults: bool = False,
    timeout_seconds: int = 60,
) -> dict:
    base_rules = (
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
        "- No inventes fechas: si no están, usa ''. "
    )

    if allow_defaults:
        system = (
            base_rules
            + "- Si el usuario dice 'a tu gusto' o similar, puedes completar campos no críticos con valores razonables. "
            + "- Puedes elegir defaults para: mes, periodo, fecha_inicio, fecha_fin, tipologia, modalidad, programa, nombre, descripcion, objetivo, recursos_utilizados, resultados, observaciones. "
            + "- Para campos numéricos usa 0 si no se indican. "
            + "- Para 'mes': si hay 'fecha_inicio', usa el mes de esa fecha; si no, usa 'mayo' como default. "
            + "- Para 'programa': si no se especifica, usa 'Ingeniería de Sistemas'. "
            + "- Para 'periodo': si hay 'fecha_inicio', usa YYYY-1 o YYYY-2 según el mes; si no, usa el año actual con '-1'. "
            + "- Para fechas: si no se especifican, elige una fecha de inicio próxima (ej. la próxima semana) y usa la misma fecha para 'fecha_fin' si no se indica duración. "
        )
    else:
        system = base_rules + "- Si un dato no se especifica, usa string vacío '' o 0 para números. "

    user = (
        f"Totales del sistema (por si sirve de contexto, no inventes datos): {json.dumps(resumen, ensure_ascii=False)}\n"
        f"Solicitud del usuario: {user_request}" 
    )

    payload = {
        'systemInstruction': {'parts': [{'text': system}]},
        'contents': [
            {'role': 'user', 'parts': [{'text': user}]},
        ],
        'generationConfig': {
            'temperature': 0.2,
            'maxOutputTokens': 1024,
            # Intentamos forzar JSON cuando esté soportado.
            'responseMimeType': 'application/json',
        },
    }
    return _gemini_request(payload=payload, model=model, timeout_seconds=timeout_seconds)


def _gemini_chat_text(
    *,
    model: str,
    system: str,
    cleaned_messages: list,
    timeout_seconds: int = 60,
) -> str:
    # Gemini API usa roles: user / model. Mapeamos assistant -> model.
    contents = []
    for msg in cleaned_messages:
        role = (msg.get('role') or '').strip()
        text = (msg.get('content') or '').strip()
        if not text:
            continue
        if role == 'user':
            contents.append({'role': 'user', 'parts': [{'text': text}]})
        else:
            contents.append({'role': 'model', 'parts': [{'text': text}]})

    payload = {
        'systemInstruction': {'parts': [{'text': system}]},
        'contents': contents,
        'generationConfig': {
            'temperature': 0.4,
            'maxOutputTokens': 1024,
        },
    }
    result = _gemini_request(payload=payload, model=model, timeout_seconds=timeout_seconds)
    return _gemini_extract_text(result)


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

    model = _normalize_gemini_model_name(os.environ.get('GEMINI_MODEL') or '') or 'gemini-1.5-flash'

    actividad = _buscar_actividad(actividad_ref)
    resumen = _resumen_bd()

    # Respuestas directas desde BD para preguntas frecuentes (sin IA).
    direct = _try_answer_activity_list_questions(mensaje)
    if direct:
        return JsonResponse({'ok': True, 'respuesta': direct})

    allow_defaults = False
    create_intent = _is_create_activity_intent(mensaje)

    if not create_intent and _is_contextual_create_intent(mensaje=mensaje, cleaned_messages=cleaned_messages):
        create_intent = True

    if create_intent and _is_delegated_create_intent(mensaje):
        allow_defaults = True

    if not create_intent and _is_defaults_followup_intent(mensaje=mensaje, cleaned_messages=cleaned_messages):
        create_intent = True
        allow_defaults = True

    if create_intent:
        try:
            user_request = _build_activity_request_from_history(mensaje=mensaje, cleaned_messages=cleaned_messages)
            raw = _extract_activity_payload_with_gemini(
                model=model,
                resumen=resumen,
                user_request=user_request,
                allow_defaults=allow_defaults,
            )
            content = _gemini_extract_text(raw)
            extracted = json.loads(content) if content else {}
        except urllib.error.URLError:
            return JsonResponse(
                {
                    'ok': False,
                    'error': (
                        'No pude conectarme a Gemini. Verifica tu conexión a Internet y '
                        'que `GEMINI_API_KEY` esté configurada correctamente en tu `.env`.'
                    ),
                },
                status=502,
            )
        except RuntimeError as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)
        except json.JSONDecodeError:
            extracted = _extract_first_json_object(content) or {}
        except Exception:
            return JsonResponse({'ok': False, 'error': 'Error preparando la actividad con IA.'}, status=500)

        fields = _coerce_activity_fields(extracted)

        # If the user explicitly allowed defaults ("a tu gusto" follow-up),
        # complete missing/invalid required fields with safe defaults.
        if allow_defaults:
            today = date.today()
            default_start = today + timedelta(days=7)

            # Dates
            fi_obj = _parse_iso_date(fields.get('fecha_inicio_raw') or '')
            ff_obj = _parse_iso_date(fields.get('fecha_fin_raw') or '')
            if not fi_obj:
                fi_obj = default_start
                fields['fecha_inicio_raw'] = fi_obj.strftime('%Y-%m-%d')
            if not ff_obj:
                ff_obj = fi_obj
                fields['fecha_fin_raw'] = ff_obj.strftime('%Y-%m-%d')

            # Period
            if not (fields.get('periodo') or '').strip():
                fields['periodo'] = _periodo_from_date(fi_obj)

            # Month
            if not (fields.get('mes') or '').strip():
                fields['mes'] = _mes_es_from_date(fi_obj)

            # Program
            if not (fields.get('programa') or '').strip():
                fields['programa'] = 'Ingeniería de Sistemas'

            # Tipología / modalidad must be within allowed choices
            allowed_tipologias = {t for t, _ in Actividad.TIPOLOGIAS}
            allowed_modalidades = {m for m, _ in Actividad.MODALIDADES}
            if (fields.get('tipologia') or '') not in allowed_tipologias:
                fields['tipologia'] = 'otro'
            if (fields.get('modalidad') or '') not in allowed_modalidades:
                fields['modalidad'] = 'presencial'

            if not (fields.get('nombre') or '').strip():
                fields['nombre'] = 'Actividad generada por IA'

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
            creado_con_ia=True,
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
        "Si necesitas listas, usa guiones '-' y títulos con ':' (por ejemplo: Nombre: ...). "
        "No afirmes que una actividad fue creada/guardada en el sistema a menos que el backend lo confirme con un ID."
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

    try:
        # Inyectamos el contexto como un mensaje del sistema y dejamos el historial.
        system_with_context = system + "\n\n" + "Contexto del sistema:\n" + user_prompt
        content = _gemini_chat_text(
            model=model,
            system=system_with_context,
            cleaned_messages=cleaned_messages,
        )
    except urllib.error.URLError:
        return JsonResponse(
            {
                'ok': False,
                'error': (
                    'No pude conectarme a Gemini. Verifica tu conexión a Internet y '
                    'que `GEMINI_API_KEY` esté configurada correctamente en tu `.env`.'
                ),
            },
            status=502,
        )
    except RuntimeError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Error generando respuesta con IA.'}, status=500)

    if not content:
        return JsonResponse({'ok': False, 'error': 'Gemini respondió vacío.'}, status=502)

    content = _normalize_ai_plain_text(content)

    return JsonResponse({'ok': True, 'respuesta': content})
