from __future__ import annotations
import os
import io
import re
import unicodedata
import math
from datetime import datetime
from app.models import Gerencia, Superintendencia, AreaTrabajo
from sqlalchemy import func, case
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List
from functools import wraps
from flask_login import login_required, current_user
from app.models import Usuario

from flask import current_app, render_template, request, send_file, url_for, redirect
from jinja2 import TemplateNotFound
from reportlab.pdfgen import canvas

from app.pdf.base_layout import PageStyle
from app.pdf.pdf_factory import render_pdf, example_data
from app.pdf.checklists import CHECKLIST_ITEMS

from . import web_bp

from app.extensions import db
from app.models import Reunion, Compromiso, Participante
import qrcode
from io import BytesIO
from app.qr_store import (
    create_meeting, get_meeting, get_meeting_by_code, add_qr_participant,
    list_qr_participants, update_meeting_commitments, delete_meeting,
)                  
         
from datetime import date



def _project_base_dir() -> str:
                                              
    return str(Path(current_app.root_path).resolve().parent)


def _render_any(names: List[str], **ctx):
    last_exc = None
    for name in names:
        try:
            return render_template(name, **ctx)
        except TemplateNotFound as e:
            last_exc = e
    raise last_exc or TemplateNotFound(names[0])

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        if not current_user.is_admin:
            return "No tienes permisos para acceder a esta página.", 403
        return f(*args, **kwargs)
    return wrapper

def _participant_areas_from_example(ex: Dict[str, Any]) -> List[str]:
    parts = ex.get("participants") or []
    areas: List[str] = []
    for p in parts:
        a = (p or {}).get("area")
        if a:
            areas.append(str(a))
    return areas


def _schema_from_example(ex: Dict[str, Any]) -> List[Dict[str, Any]]:
    return ex.get("sections") or []


def _iso_to_dmy(s: str) -> str:
    """Normaliza fecha YYYY-MM-DD (input date) a DD/MM/AAAA para PDF."""
    s = (s or "").strip()
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        try:
            y, m, d = s.split("-")
            if len(y) == 4 and len(m) == 2 and len(d) == 2:
                return f"{d}/{m}/{y}"
        except Exception:
            return s
    return s


def _safe_int(v):
    try:
        s = str(v).strip()
        return int(s) if s else None
    except Exception:
        return None


def _safe_float(v):
    try:
        s = str(v).strip().replace(",", ".")
        return float(s) if s else None
    except Exception:
        return None


_DOC_LABELS: Dict[str, str] = {
    "planning": "PLAN",
    "scheduling": "PROG",
    "post": "PMT",
    "prioritization": "PRIO",
    "process_5s": "P5S",
    "conciliacion_sep4": "SEP4",
}



def _slug_filename_part(s: str) -> str:
    """Deja un string seguro para nombre de archivo (sin tildes, sin símbolos raros)."""
    s = (s or "").strip()
    if not s:
        return "SIN_DATO"
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^A-Za-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "SIN_DATO"


def _week_year_code(fecha_str: str) -> str:
    """DD/MM/AAAA -> 'SEMANA_AAAA_dos_digitos', ej. 40_26."""
    fecha_str = (fecha_str or "").strip()
    try:
        d = datetime.strptime(fecha_str, "%d/%m/%Y")
        iso_year, iso_week, _ = d.isocalendar()
        return f"{iso_week}_{iso_year % 100:02d}"
    except Exception:
        return "SS_AA"

def _semana_sort_key(semana_code: str):
    """'40_26' -> (2026, 40), para ordenar cronologicamente."""
    try:
        semana, anio = semana_code.split("_")
        return (int(anio), int(semana))
    except Exception:
        return (0, 0)

def _weekly_avg_by_week(reuniones_list):
    """{semana: [notas]} a partir de una lista de reuniones (ignora las sin nota)."""
    semanas = defaultdict(list)
    for r in reuniones_list:
        if r.nota is None:
            continue
        semanas[_week_year_code(r.fecha)].append(r.nota)
    return semanas

def _compromisos_vigentes(compromisos_list):
    """De una lista de compromisos, deja solo el mas reciente (mayor id) por
    cada thread_id; los compromisos sin thread_id se consideran unicos.
    Evita contar varias veces el mismo compromiso cuando se actualizo su
    estado en reuniones posteriores (cada actualizacion genera una fila
    nueva en la base, enlazada por thread_id)."""
    latest_by_key = {}
    for c in sorted(compromisos_list, key=lambda c: c.id):
        key = c.thread_id or f"__sin_thread_{c.id}"
        latest_by_key[key] = c
    return list(latest_by_key.values())

def _filename_from_data(doc_type: str, data: Dict[str, Any]) -> str:
    """Nombre: GERENCIA-AREA-TIPOREUNION-SEMANA_ANIO.pdf

    Los codigos de Gerencia y Area salen de la jerarquia definida en
    app/data/organizacion.py (Gerencia = prefijo antes de " - ";
    Area = AREA_CODES, con fallback a las primeras letras si no esta mapeada).
    """
    gerencia_full = str(data.get("gerencia") or "").strip()
    gerencia_code = gerencia_full.split(" - ")[0].strip() if gerencia_full else "SINGER"

    area_full = str(data.get("area") or "").strip()
    if area_full:
        area_row = AreaTrabajo.query.filter_by(nombre=area_full).first()
        area_code = (area_row.codigo_pdf if area_row and area_row.codigo_pdf else None)
        if not area_code:
            area_code = re.sub(r"[^A-Za-z0-9]", "", area_full).upper()[:4] or "SINAREA"
    else:
        area_code = "SINAREA"

    tipo = _DOC_LABELS.get(doc_type, doc_type).strip() or doc_type
    semana_anio = _week_year_code(str(data.get("fecha") or ""))

    return (
        f"{_slug_filename_part(gerencia_code)}"
        f"-{_slug_filename_part(area_code)}"
        f"-{_slug_filename_part(tipo)}"
        f"-{semana_anio}.pdf"
    )


def _parse_common_form(
    doc_type: str,
    form,
    schema: List[Dict[str, Any]],
    participant_areas: List[str],
) -> Dict[str, Any]:
    base = example_data(doc_type)

    data: Dict[str, Any] = {
        "title": base.get("title", ""),
        "fecha": _iso_to_dmy(form.get("fecha", "")),
        "hora": form.get("hora", ""),
        "area": form.get("area", ""),
        "gerencia": form.get("gerencia", ""),
        "superintendencia": form.get("superintendencia", ""),
        "observers": [
            {
                "id": form.get("obs1_id", ""),
                "nombre": form.get("obs1_nombre", ""),
                "gerencia": form.get("obs1_gerencia", ""),
                "superintendencia": form.get("obs1_superintendencia", ""),
                "sap": form.get("obs1_sap", ""),
                "email": form.get("obs1_email", ""),
                "posicion": form.get("obs1_posicion", ""),
            },
            {
                "id": form.get("obs2_id", ""),
                "nombre": form.get("obs2_nombre", ""),
                "gerencia": form.get("obs2_gerencia", ""),
                "superintendencia": form.get("obs2_superintendencia", ""),
                "sap": form.get("obs2_sap", ""),
                "email": form.get("obs2_email", ""),
                "posicion": form.get("obs2_posicion", ""),
            },
        ],
        "sections": [],
        "feedback": {
            "fortalezas": form.get("fortalezas", ""),
            "oportunidades": form.get("oportunidades", ""),
            "plan": form.get("plan", ""),
        },
        "commitments": [],
        "participants": [],
    }

                                            
    if doc_type == "conciliacion_sep4":
        data["division"] = form.get("division", "")
        data["evaluador"] = form.get("evaluador", "")
        data["turno"] = form.get("turno", "")
        data["detenciones_revisadas"] = form.get("detenciones_revisadas", "")
        data["detenciones_conciliadas"] = form.get("detenciones_conciliadas", "")
        data["detenciones_pendientes"] = form.get("detenciones_pendientes", "")
        data["horas_detencion_pendientes"] = form.get("horas_detencion_pendientes", "")
                                            
    for si, sec in enumerate(schema):
        sec_out = {"name": sec.get("name", ""), "items": []}
        items = sec.get("items") or []

        for ii, it in enumerate(items):
            key = f"s{si}_i{ii}"
            raw = form.get(key, "")
            try:
                sel = int(raw) if (raw is not None and str(raw).strip() != "") else 1
            except Exception:
                sel = 1

            opts = it.get("options") or []
            if doc_type == "conciliacion_sep4":
                if sel < 0 or sel > (len(opts) if opts else 0):
                    sel = 1
            else:
                sel = max(1, min(len(opts) if opts else 1, sel))

            sec_out["items"].append(
                {"question": it.get("question", ""), "options": opts, "selected": sel}
            )

        data["sections"].append(sec_out)

        # ===== Checklist de seguridad =====
    data["checklist"] = []
    checklist_questions = CHECKLIST_ITEMS.get(doc_type, [])
    for i, question in enumerate(checklist_questions):
        raw = (form.get(f"chk_{i}", "") or "").strip().lower()
        comentario = (form.get(f"chk_{i}_comentario", "") or "").strip()
        data["checklist"].append({
            "question": question,
            "si": raw == "si",
            "no": raw == "no",
            "comentario": comentario,
        })

    if doc_type == "scheduling":
        data["chk_acts_criticas_comentario"] = (
            form.get("chk_acts_criticas_comentario", "") or ""
        ).strip()

                          
    c_acc = form.getlist("c_accion[]") if hasattr(form, "getlist") else []
    c_resp = form.getlist("c_responsable[]") if hasattr(form, "getlist") else []
    c_fec = form.getlist("c_fecha[]") if hasattr(form, "getlist") else []
    c_est = form.getlist("c_estado[]") if hasattr(form, "getlist") else []
    c_evi = form.getlist("c_evidencia[]") if hasattr(form, "getlist") else []

    c_area = form.getlist("c_area[]") if hasattr(form, "getlist") else []
    c_thread = form.getlist("c_thread_id[]") if hasattr(form, "getlist") else []

    n = max(len(c_acc), len(c_resp), len(c_fec), len(c_est), len(c_evi))
    for i in range(n):
        row = {
            "accion": (c_acc[i] if i < len(c_acc) else "").strip(),
            "responsable": (c_resp[i] if i < len(c_resp) else "").strip(),
            "fecha": _iso_to_dmy((c_fec[i] if i < len(c_fec) else "")).strip(),
            "estado": (c_est[i] if i < len(c_est) else "").strip(),
            "evidencia": (c_evi[i] if i < len(c_evi) else "").strip(),
            "area": (c_area[i] if i < len(c_area) else "").strip(),
            "thread_id": (c_thread[i] if i < len(c_thread) else "").strip(),
        }
        if any([row["accion"], row["responsable"], row["fecha"], row["estado"], row["evidencia"]]):
            data["commitments"].append(row)

                                    
    for pi, area in enumerate(participant_areas):
        resp = (form.get(f"p_responsable_{pi}", "") or "").strip()
        email = (form.get(f"p_email_{pi}", "") or "").strip()
        asist = (form.get(f"p_asistio_{pi}", "") or "").strip().lower()
        conf_raw = (form.get(f"p_conforme_{pi}", "") or "").strip().lower()
        conforme = True if conf_raw == "si" else (False if conf_raw == "no" else None)
        data["participants"].append(
            {"area": area, "responsable": resp, "email": email, "si": (asist == "si"), "no": (asist == "no"), "conforme": conforme}
        )

    
    # Participantes agregados manualmente con el botón "+" (área duplicada u "Otro")
    extra_indices = set()
    for key in form.keys():
        m = re.match(r"^p_responsable_extra_(\d+)$", key)
        if m:
            extra_indices.add(int(m.group(1)))
    for n in sorted(extra_indices):
        resp = (form.get(f"p_responsable_extra_{n}", "") or "").strip()
        if not resp:
            continue
        area = (form.get(f"p_area_extra_{n}", "") or "").strip()
        email = (form.get(f"p_email_extra_{n}", "") or "").strip()
        asist = (form.get(f"p_asistio_extra_{n}", "") or "").strip().lower()
        conf_raw = (form.get(f"p_conforme_extra_{n}", "") or "").strip().lower()
        conforme = True if conf_raw == "si" else (False if conf_raw == "no" else None)
        data["participants"].append(
            {"area": area, "responsable": resp, "email": email, "si": (asist == "si"), "no": (asist == "no"), "conforme": conforme}
        )

    # Participantes traidos automaticamente desde el QR
    qr_area = form.getlist("qr_p_area[]") if hasattr(form, "getlist") else []
    qr_nombre = form.getlist("qr_p_nombre[]") if hasattr(form, "getlist") else []
    qr_email = form.getlist("qr_p_email[]") if hasattr(form, "getlist") else []
    qr_conforme = form.getlist("qr_p_conforme[]") if hasattr(form, "getlist") else []
    for i in range(len(qr_nombre)):
        nombre = (qr_nombre[i] or "").strip()
        if not nombre:
            continue
        conf_raw = (qr_conforme[i] if i < len(qr_conforme) else "").strip().lower()
        conforme = True if conf_raw == "si" else (False if conf_raw == "no" else None)
        data["participants"].append({
            "area": (qr_area[i] if i < len(qr_area) else "").strip(),
            "responsable": nombre,
            "email": (qr_email[i] if i < len(qr_email) else "").strip(),
            "si": True,
            "no": False,
            "conforme": conforme,
            "origen": "qr",
        })

    # Si un area (manual fija, "+", o QR) ya tiene al menos un participante
    # con datos, no incluir en el PDF las filas vacias de esa misma area
    # (esas filas vacias solo sirven en el formulario web para invitar a
    # completarlas; si nadie las llenó pero SI llegó gente de esa area por
    # otra via, no corresponde mostrar una linea en blanco extra).
    areas_con_datos = {
        (p.get("area") or "").strip().upper()
        for p in data["participants"]
        if (p.get("responsable") or "").strip()
    }
    data["participants"] = [
        p for p in data["participants"]
        if (p.get("responsable") or "").strip()
        or (p.get("area") or "").strip().upper() not in areas_con_datos
    ]

    # Filas completas primero; filas realmente vacias (areas sin ningun
    # participante) al final.
    data["participants"].sort(
        key=lambda p: 0 if (p.get("responsable") or "").strip() else 1
    )

    return data


def _build_pdf_bytes(doc_type: str, data: Dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    style = PageStyle()
    c = canvas.Canvas(buf, pagesize=style.pagesize)
    render_pdf(doc_type, c, data, _project_base_dir())
    c.save()
    return buf.getvalue()

def _pdf_storage_dir() -> Path:
    """
    Carpeta donde se guardan los PDFs generados. Configurable por variable
    de entorno PDF_STORAGE_DIR (para cuando exista el disco/servidor
    definitivo); por defecto usa storage/pdf dentro del proyecto.
    """
    custom = os.environ.get("PDF_STORAGE_DIR")
    base = Path(custom) if custom else Path(_project_base_dir()) / "storage" / "pdf"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _save_pdf_to_storage(pdf_bytes: bytes, filename: str) -> str:
    """Guarda el PDF en disco y devuelve la ruta relativa al proyecto."""
    d = _pdf_storage_dir()
    path = d / filename
    with open(path, "wb") as f:
        f.write(pdf_bytes)
    try:
        return str(path.relative_to(Path(_project_base_dir())))
    except ValueError:
        return str(path)


def _save_meeting_to_db(doc_type: str, data: Dict[str, Any], pdf_filename: str, pdf_relpath: str) -> None:
    usuario_id = current_user.id if current_user.is_authenticated else None
    _, nota = _calc_meeting_score(data.get("sections"))

    reunion = Reunion(
        doc_type=doc_type,
        titulo=data.get("title", "") or "",
        fecha=data.get("fecha", "") or "",
        hora=data.get("hora", "") or "",
        area=(data.get("area") or data.get("evaluador") or data.get("division") or ""),
        pdf_path=pdf_relpath,
        pdf_filename=pdf_filename,
        usuario_id=usuario_id,
        nota=nota,
        detenciones_revisadas=_safe_int(data.get("detenciones_revisadas")),
        detenciones_conciliadas=_safe_int(data.get("detenciones_conciliadas")),
        detenciones_pendientes=_safe_int(data.get("detenciones_pendientes")),
        horas_detencion_pendientes=_safe_float(data.get("horas_detencion_pendientes")),
    )
    db.session.add(reunion)
    db.session.flush()

    for c in (data.get("commitments") or []):
        thread_id = (c.get("thread_id") or "").strip() or None
        db.session.add(Compromiso(
            reunion_id=reunion.id,
            accion=c.get("accion", ""),
            responsable=c.get("responsable", ""),
            fecha_compromiso=c.get("fecha", ""),
            estado=c.get("estado", ""),
            evidencia=c.get("evidencia", ""),
            area=c.get("area", ""),
            thread_id=thread_id,
        ))

    for p in (data.get("participants") or []):
        db.session.add(Participante(
            reunion_id=reunion.id,
            area=p.get("area", ""),
            nombre=p.get("responsable", ""),
            email=p.get("email", ""),
            asistio=True if p.get("si") else (False if p.get("no") else None),
            conforme=p.get("conforme"),
            origen=p.get("origen", "manual"),
        ))

    db.session.commit()


def _organizacion_as_dict():
    result = {}
    for g in Gerencia.query.order_by(Gerencia.codigo).all():
        result[g.nombre_completo] = {
            s.nombre_completo: [a.nombre for a in s.areas]
            for s in g.superintendencias
        }
    return result


def _persist_meeting_safely(doc_type: str, data: Dict[str, Any], pdf_bytes: bytes, filename: str) -> None:
    """
    Guarda el PDF en disco y los datos en la base de datos, sin bloquear
    la descarga del PDF si algo falla aquí (es una funcionalidad secundaria).
    """
    try:
        pdf_relpath = _save_pdf_to_storage(pdf_bytes, filename)
        _save_meeting_to_db(doc_type, data, filename, pdf_relpath)
    except Exception as e:
        current_app.logger.error(f"No se pudo guardar la reunión en BD/storage: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass
                
def _calc_meeting_score(sections):
    total, max_total = 0, 0
    for sec in (sections or []):
        for it in (sec.get("items") or []):
            try:
                sel = int(it.get("selected", 1) or 1)
            except Exception:
                sel = 1
            opts = it.get("options") or []
            max_opt = len(opts) if opts else 3
            if sel == 0:
                continue  # N/A: no cuenta para la nota
            total += sel
            max_total += max_opt
    if max_total == 0:
        return 0, None
    pct = total / max_total
    return total, round(1.0 + pct * 6.0, 1)

def _nota_calidad(nota):
    """Clasifica la nota (escala 1.0-7.0) en una categoria de calidad.

    Referencia: todo en 'malo' = 3.0, todo en 'regular' = 5.0, todo en 'bueno' = 7.0.
    """
    if nota is None:
        return None
    if nota < 5.0:
        return "Baja calidad"
    if nota < 6.0:
        return "Aceptable"
    return "Buena calidad"
    
def _invalidate_qr_session(form) -> None:
    meeting_id = (form.get("qr_meeting_id", "") or "").strip()
    if meeting_id:
        try:
            delete_meeting(meeting_id)
        except Exception as e:
            current_app.logger.error(f"No se pudo invalidar la sesion QR {meeting_id}: {e}")                           
                                       
                           
PRIORITIZATION_SCHEMA: List[Dict[str, Any]] = [
    {
        "name": "Aspectos generales",
        "items": [
            {
                "question": "Ejecución: La reunión…",
                "options": [
                    "No se realizó y/o se reagendó",
                    "Se realizó, pero tarde o se extendió",
                    "Se realizó de acuerdo con el horario y la duración planificada",
                ],
            },
            {
                "question": "Asistencia: A la reunión asisten... (planificación, confiabilidad, operación, ej. mantenimiento, abastecimiento, EECC y prevencionistas)",
                "options": [
                    "No se presentaron más de 3 participantes claves",
                    "Faltaron 1 -2 participantes claves",
                    "Estaban todos los relevantes",
                ],
            },
        ],
    },
    {
        "name": "Inputs",
        "items": [
            {
                "question": "Propuesta de confiabilidad (plan matriz y MonCon): Los ingenieros de confiabilidad y planificación...",
                "options": [
                    "No presentan una lista de actividades pre-priorizadas",
                    "Presentan una lista de actividades pre-priorizadas, pero no está hecha en SAP",
                    "Presentan una lista de actividades pre-priorizadas e identificadas en la plataforma SAP",
                ],
            },
            {
                "question": "Actividades fuera del sistema SAP:",
                "options": [
                    "Las otras áreas traen solicitudes de las tareas del sistema y SIN priorización",
                    "Las otras áreas traen una lista ya priorizada",
                    "No hay actividades propuestas fuera del sistema SAP",
                ],
            },
        ],
    },
    {
        "name": "Desarrollo",
        "items": [
            {
                "question": "Propuesta base de confiabilidad: El equipo…",
                "options": [
                    "No revisa en conjunto la propuesta base",
                    "La revisa en conjunto, pero no se solicita validación",
                    "Revisa en conjunto la propuesta base y se confirma el acuerdo",
                ],
            },
            {
                "question": "Inclusión de actividades no consideradas: Las actividades propuestas…",
                "options": [
                    "No son revisadas en conjunto y se incluyen directamente en el programa",
                    "Son presentadas, pero no se valida la priorización",
                    "Son revisadas en conjunto y se valida su priorización",
                ],
            },
            {
                "question": "Cambios en prioridad según nivel de riesgo discutido: El equipo…",
                "options": [
                    "No discute los niveles de riesgo de las actividades",
                    "Discute niveles de riesgo, pero no son considerados para la priorización",
                    "Discute niveles de riesgo y realiza cambios en las prioridades de acuerdo con ello",
                ],
            },
            {
                "question": "Cierre: Los ingenieros de confiabilidad y planificación…",
                "options": [
                    "No solicitan a los participantes la confirmación de la lista priorizada de tareas",
                    "Solicitan a los participantes la validación de la lista priorizada de tareas, pero no formalmente",
                    "Solicitan a los participantes la validación formal de la lista priorizada de tareas",
                ],
            },
            {
                "question": "Priorización de equipos críticos: Los asistentes…",
                "options": [
                    "No conocen los equipos críticos y no son priorizados",
                    "Conocen los equipos críticos, pero no son priorizados",
                    "Conocen los equipos críticos y velan por su priorización",
                ],
            },
            {
                "question": "Generación de avisos: Para los asistentes…",
                "options": [
                    "La mayor parte de las tareas fuera del plan matriz no tienen un aviso generado",
                    "Sólo algunas tareas se solicitan sin aviso",
                    "El ingreso de tareas sin aviso es muy excepcional",
                ],
            },
        ],
    },
    {
        "name": "Mentalidades y comportamientos",
        "items": [
            {
                "question": "Respeto por las reglas de la reunión: Los asistentes…",
                "options": [
                    "No dan importancia al cumplimiento de las reglas",
                    "Uno o más integrantes no respeta las reglas y refleja una falta de entendimiento de la importancia de la reunión",
                    "El equipo completo respeta las reglas y es reflejo de la importancia que dan a la reunión",
                ],
            },
            {
                "question": "Preparación: La preparación de la información refleja la importancia que dan los participantes a la priorización",
                "options": [
                    "La preparación necesaria es nula y se le da poca importancia en todo el equipo",
                    "Uno o más asistentes no prepara la información y no entiende su importancia",
                    "Todos aportan la información necesaria y de la manera esperada",
                ],
            },
            {
                "question": "Motivación a la priorización: El equipo entiende que el principal objetivo es la priorización",
                "options": [
                    "Se discute poco o nada de priorización",
                    "La priorización se discute parcialmente",
                    "El equipo cuestiona y analiza la priorización en cada etapa de la reunión",
                ],
            },
            {
                "question": "La comunicación: ¿La comunicación de los participantes refleja entendimiento y convicción?",
                "options": [
                    "Se observa lenguaje de desaprobación en el equipo",
                    "Uno o más integrantes muestran lenguaje de desaprobación",
                    "El equipo muestra un lenguaje positivo, colaborativo y alineado con el objetivo de la reunión",
                ],
            },
        ],
    },
]

PRIORITIZATION_PARTICIPANT_AREAS: List[str] = [
    "CONFIABILIDAD",
    "PLANIFICADOR",
    "PROGRAMADOR",
    "EJECUTOR",
    "OPERACIONES",
    "GSYS",
    "ELÉCTRICOS",
    "ABASTECIMIENTO",
    "EECC",
    "OTRO",
]


                           
                           
                       
@web_bp.post("/qr/create")
def qr_create():
    payload = request.get_json(force=True)
    doc_type = payload.get("doc_type", "")
    title = payload.get("title", "")
    fecha = payload.get("fecha", "")
    commitments = payload.get("commitments", [])
    participant_areas = payload.get("participant_areas", [])

    meeting_id = create_meeting(doc_type, title, fecha, commitments, participant_areas)
    join_url = request.host_url.rstrip("/") + url_for("web.asistencia_form", meeting_id=meeting_id)

    meeting = get_meeting(meeting_id)

    return {
        "meeting_id": meeting_id,
        "join_url": join_url,
        "short_code": meeting.get("short_code") if meeting else "",
    }


@web_bp.post("/qr/update/<meeting_id>")
def qr_update(meeting_id):
    meeting = get_meeting(meeting_id)
    if not meeting:
        return {"ok": False, "error": "Reunión no encontrada"}, 404

    payload = request.get_json(force=True)
    commitments = payload.get("commitments", [])
    participant_areas = payload.get("participant_areas")

    update_meeting_commitments(meeting_id, commitments, participant_areas)
    return {"ok": True}


@web_bp.get("/qr/image/<meeting_id>")
def qr_image(meeting_id):
    meeting = get_meeting(meeting_id)
    if not meeting:
        return "Reunión no encontrada", 404

    join_url = request.host_url.rstrip("/") + url_for("web.asistencia_form", meeting_id=meeting_id)
    img = qrcode.make(join_url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@web_bp.get("/asistencia/<meeting_id>")
def asistencia_form(meeting_id):
    meeting = get_meeting(meeting_id)
    if not meeting:
        return "Esta reunión ya no está disponible o el enlace es inválido.", 404
    return _render_any(
        ["asistencia_form.html", "web/asistencia_form.html"],
        meeting=meeting,
        meeting_id=meeting_id,
    )


@web_bp.post("/asistencia/<meeting_id>")
def asistencia_submit(meeting_id):
    meeting = get_meeting(meeting_id)
    if not meeting:
        return "Esta reunión ya no está disponible.", 404

    area = (request.form.get("area", "") or "").strip()
    if area.upper() == "OTRA":
        area_otra = (request.form.get("area_otra", "") or "").strip()
        area = area_otra or "OTRA"

    nombre = (request.form.get("nombre", "") or "").strip()
    email = (request.form.get("email", "") or "").strip()
    conforme = (request.form.get("conforme", "") or "").strip().lower()

    if not nombre:
        return _render_any(
            ["asistencia_form.html", "web/asistencia_form.html"],
            meeting=meeting, meeting_id=meeting_id, error="Ingresa tu nombre.",
        )

    add_qr_participant(meeting_id, area, nombre, email, conforme)
    return _render_any(
        ["asistencia_gracias.html", "web/asistencia_gracias.html"],
        meeting=meeting,
    )


@web_bp.get("/qr/participants/<meeting_id>")
def qr_participants(meeting_id):
    return {"participants": list_qr_participants(meeting_id)}                           
      
@web_bp.get("/asistencia")
def asistencia_codigo_form():
    return _render_any(
        ["asistencia_codigo.html", "web/asistencia_codigo.html"],
        error=None,
    )


@web_bp.post("/asistencia")
def asistencia_codigo_submit():
    code = (request.form.get("codigo", "") or "").strip()
    meeting_id = get_meeting_by_code(code) if code else None

    if not meeting_id:
        return _render_any(
            ["asistencia_codigo.html", "web/asistencia_codigo.html"],
            error="Código incorrecto o la reunión ya no está disponible.",
        )

    return redirect(url_for("web.asistencia_form", meeting_id=meeting_id))


@web_bp.get("/qr/fijo")
def qr_fijo():
    """QR permanente para imprimir y pegar en la sala. Apunta a /asistencia."""
    url = request.host_url.rstrip("/") + url_for("web.asistencia_codigo_form")
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")
                             
@web_bp.get("/")
@login_required
def home():
    return _render_any(["home.html", "web/home.html"])


                           
          
                           
@web_bp.get("/planning")
@login_required
def planning_form():
    ex = example_data("planning")
    schema = _schema_from_example(ex)
    participant_areas = _participant_areas_from_example(ex)
    return _render_any(
        ["planning_form.html", "web/planning_form.html"],
        data=ex,
        schema=schema,
        participant_areas=participant_areas,
        organizacion=_organizacion_as_dict(),
    )


@web_bp.post("/planning/generate")
@login_required
def planning_generate_pdf():
    ex = example_data("planning")
    schema = _schema_from_example(ex)
    participant_areas = _participant_areas_from_example(ex)

    data = _parse_common_form("planning", request.form, schema, participant_areas)
    pdf_bytes = _build_pdf_bytes("planning", data)
    filename = _filename_from_data("planning", data)
    _persist_meeting_safely("planning", data, pdf_bytes, filename)
    _invalidate_qr_session(request.form)



    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


                           
            
                           
@web_bp.get("/scheduling")
@login_required
def scheduling_form():
    ex = example_data("scheduling")
    schema = _schema_from_example(ex)
    participant_areas = _participant_areas_from_example(ex)
    return _render_any(
        ["scheduling_form.html", "web/scheduling_form.html"],
        data=ex,
        schema=schema,
        participant_areas=participant_areas,
        organizacion=_organizacion_as_dict(),
    )


@web_bp.post("/scheduling/generate")
@login_required
def scheduling_generate_pdf():
    ex = example_data("scheduling")
    schema = _schema_from_example(ex)
    participant_areas = _participant_areas_from_example(ex)

    data = _parse_common_form("scheduling", request.form, schema, participant_areas)
    pdf_bytes = _build_pdf_bytes("scheduling", data)
    filename = _filename_from_data("scheduling", data)
    _persist_meeting_safely("scheduling", data, pdf_bytes, filename)
    _invalidate_qr_session(request.form)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


                           
                  
                           
@web_bp.get("/post_maintenance")
@login_required
def post_maintenance_form():
    ex = example_data("post")
    schema = _schema_from_example(ex)
    participant_areas = _participant_areas_from_example(ex)
    return _render_any(
        ["post_maintenance_form.html", "web/post_maintenance_form.html"],
        data=ex,
        schema=schema,
        participant_areas=participant_areas,
        organizacion=_organizacion_as_dict(),
    )


@web_bp.post("/post_maintenance/generate")
@login_required
def post_maintenance_generate_pdf():
    ex = example_data("post")
    schema = _schema_from_example(ex)
    participant_areas = _participant_areas_from_example(ex)

    data = _parse_common_form("post", request.form, schema, participant_areas)
    pdf_bytes = _build_pdf_bytes("post", data)
    filename = _filename_from_data("post", data)
    _persist_meeting_safely("post", data, pdf_bytes, filename)
    _invalidate_qr_session(request.form)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


                           
              
                           
@web_bp.get("/prioritization")
@login_required
def prioritization_form():
    ex = example_data("prioritization")
    schema = PRIORITIZATION_SCHEMA
    participant_areas = PRIORITIZATION_PARTICIPANT_AREAS
    return _render_any(
        ["prioritization_form.html", "web/prioritization_form.html"],
        data=ex,
        schema=schema,
        participant_areas=participant_areas,
        organizacion=_organizacion_as_dict(),
    )


@web_bp.post("/prioritization/generate")
@login_required
def prioritization_generate_pdf():
    ex = example_data("prioritization")
    schema = PRIORITIZATION_SCHEMA
    participant_areas = PRIORITIZATION_PARTICIPANT_AREAS

    data = _parse_common_form("prioritization", request.form, schema, participant_areas)
    pdf_bytes = _build_pdf_bytes("prioritization", data)
    filename = _filename_from_data("prioritization", data)
    _persist_meeting_safely("prioritization", data, pdf_bytes, filename)
    _invalidate_qr_session(request.form)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


                           
             

@web_bp.get("/conciliacion_sep4")
@login_required
def conciliacion_sep4_form():
    ex = example_data("conciliacion_sep4")
    schema = _schema_from_example(ex)
    participant_areas = _participant_areas_from_example(ex)
    return _render_any(
        ["conciliacion_sep4_form.html", "web/conciliacion_sep4_form.html"],
        data=ex,
        schema=schema,
        participant_areas=participant_areas,
        organizacion=_organizacion_as_dict(),
    )


@web_bp.post("/conciliacion_sep4/generate")
@login_required
def conciliacion_sep4_generate_pdf():
    ex = example_data("conciliacion_sep4")
    schema = _schema_from_example(ex)
    participant_areas = _participant_areas_from_example(ex)


    data = _parse_common_form("conciliacion_sep4", request.form, schema, participant_areas)
    data["title"] = ex.get("title", "")

    pdf_bytes = _build_pdf_bytes("conciliacion_sep4", data)
    filename = _filename_from_data("conciliacion_sep4", data)
    _persist_meeting_safely("conciliacion_sep4", data, pdf_bytes, filename)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )

@web_bp.get("/historial")
@login_required
def historial():
    doc_type_filter = request.args.get("tipo", "").strip()

    query = Reunion.query.filter_by(usuario_id=current_user.id)
    if doc_type_filter:
        query = query.filter_by(doc_type=doc_type_filter)

    reuniones = query.order_by(Reunion.created_at.desc()).all()

    return _render_any(
        ["historial.html", "web/historial.html"],
        reuniones=reuniones,
        doc_type_filter=doc_type_filter,
        doc_labels=_DOC_LABELS,
    )


@web_bp.get("/historial/<int:reunion_id>/descargar")
@login_required
def historial_descargar(reunion_id):
    reunion = Reunion.query.get_or_404(reunion_id)

    if reunion.usuario_id != current_user.id:
        return "No tienes permiso para descargar este archivo.", 403

    if not reunion.pdf_path:
        return "El archivo PDF no está disponible.", 404

    full_path = Path(_project_base_dir()) / reunion.pdf_path
    if not full_path.is_file():
        return "El archivo PDF ya no existe en el servidor.", 404

    return send_file(
        str(full_path),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=reunion.pdf_filename or "documento.pdf",
    )

@web_bp.get("/admin")
@login_required
@admin_required
def admin_panel():
    doc_type_filter = request.args.get("tipo", "").strip()
    usuario_filter = request.args.get("usuario", "").strip()

    query = Reunion.query
    if doc_type_filter:
        query = query.filter_by(doc_type=doc_type_filter)
    if usuario_filter:
        query = query.filter_by(usuario_id=int(usuario_filter))

    reuniones = query.order_by(Reunion.created_at.desc()).all()
    usuarios = Usuario.query.order_by(Usuario.nombre).all()

    return _render_any(
        ["admin_panel.html", "web/admin_panel.html"],
        reuniones=reuniones,
        usuarios=usuarios,
        doc_type_filter=doc_type_filter,
        usuario_filter=usuario_filter,
        doc_labels=_DOC_LABELS,
    )


@web_bp.get("/admin/reunion/<int:reunion_id>/descargar")
@login_required
@admin_required
def admin_descargar(reunion_id):
    reunion = Reunion.query.get_or_404(reunion_id)

    if not reunion.pdf_path:
        return "El archivo PDF no está disponible.", 404

    full_path = Path(_project_base_dir()) / reunion.pdf_path
    if not full_path.is_file():
        return "El archivo PDF ya no existe en el servidor.", 404

    return send_file(
        str(full_path),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=reunion.pdf_filename or "documento.pdf",
    )


@web_bp.get("/admin/usuarios")
@login_required
@admin_required
def admin_usuarios():
    busqueda = request.args.get("q", "").strip()

    query = Usuario.query
    if busqueda:
        like = f"%{busqueda}%"
        query = query.filter(
            db.or_(Usuario.nombre.ilike(like), Usuario.email.ilike(like))
        )

    usuarios = query.order_by(Usuario.created_at.desc()).all()
    reuniones_por_usuario = {
        row[0] for row in db.session.query(Reunion.usuario_id).distinct().all()
    }
    return _render_any(
        ["admin_usuarios.html", "web/admin_usuarios.html"],
        usuarios=usuarios,
        reuniones_por_usuario=reuniones_por_usuario,
        busqueda=busqueda,
    )


@web_bp.post("/admin/usuarios/<int:user_id>/toggle_active")
@login_required
@admin_required
def admin_toggle_active(user_id):
    user = Usuario.query.get_or_404(user_id)
    if user.id == current_user.id:
        return "No puedes desactivar tu propia cuenta.", 400
    user.is_active_account = not user.is_active_account
    db.session.commit()
    return redirect(url_for("web.admin_usuarios"))


@web_bp.post("/admin/usuarios/<int:user_id>/toggle_admin")
@login_required
@admin_required
def admin_toggle_role(user_id):
    user = Usuario.query.get_or_404(user_id)
    if user.id == current_user.id:
        return "No puedes cambiar tu propio rol.", 400
    user.rol = "usuario" if user.is_admin else "admin"
    db.session.commit()
    return redirect(url_for("web.admin_usuarios"))

@web_bp.post("/admin/usuarios/<int:user_id>/eliminar")
@login_required
@admin_required
def admin_eliminar_usuario(user_id):
    user = Usuario.query.get_or_404(user_id)

    if user.id == current_user.id:
        return "No puedes eliminar tu propia cuenta.", 400

    tiene_reuniones = Reunion.query.filter_by(usuario_id=user.id).first() is not None
    if tiene_reuniones:
        return "No se puede eliminar: esta cuenta ya generó reuniones. Puedes deshabilitarla en su lugar.", 400

    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("web.admin_usuarios"))


@web_bp.get("/admin/seguimiento")
@login_required
@admin_required
def admin_seguimiento():
    doc_type_filter = request.args.get("tipo", "").strip()
    area_filter = request.args.get("area", "").strip()

    reunion_query = Reunion.query
    if doc_type_filter:
        reunion_query = reunion_query.filter_by(doc_type=doc_type_filter)
    if area_filter:
        reunion_query = reunion_query.filter_by(area=area_filter)
    reuniones = reunion_query.order_by(Reunion.created_at.desc()).all()
    reunion_ids = [r.id for r in reuniones] or [-1]

    total_reuniones = len(reuniones)

    notas = [r.nota for r in reuniones if r.nota is not None]
    nota_promedio = round(sum(notas) / len(notas), 1) if notas else None

    todos_compromisos = _compromisos_vigentes(
        Compromiso.query.filter(Compromiso.reunion_id.in_(reunion_ids)).all()
    )
    total_compromisos = len(todos_compromisos)
    compromisos_vencidos = sum(1 for c in todos_compromisos if c.is_vencido)

    # --- Asistencia por area (compacta) ---
    asistencia_raw = (
        db.session.query(
            Participante.area,
            func.count(Participante.id).label("total"),
            func.sum(case((Participante.asistio == True, 1), else_=0)).label("asistieron"),
        )
        .filter(Participante.reunion_id.in_(reunion_ids))
        .filter(Participante.area != "")
        .group_by(Participante.area)
        .order_by(func.count(Participante.id).desc())
        .all()
    )
    asistencia_por_area = [
        {
            "area": row.area,
            "total": row.total,
            "asistieron": row.asistieron or 0,
            "pct": round(((row.asistieron or 0) / row.total) * 100) if row.total else 0,
        }
        for row in asistencia_raw
    ]
    asistencia_promedio = (
        round(sum(a["pct"] for a in asistencia_por_area) / len(asistencia_por_area))
        if asistencia_por_area else None
    )
    areas_menos_participan = sorted(asistencia_por_area, key=lambda a: a["pct"])[:5]

    # --- Compromisos por estado ---
    counts_por_estado = {}
    for c in todos_compromisos:
        e = (c.estado or "SIN ESTADO").strip().upper()
        counts_por_estado[e] = counts_por_estado.get(e, 0) + 1

    # --- Reuniones por tipo ---
    reuniones_por_tipo = {}
    for r in reuniones:
        label = _DOC_LABELS.get(r.doc_type, r.doc_type)
        reuniones_por_tipo[label] = reuniones_por_tipo.get(label, 0) + 1

    # --- Cumplimiento de compromisos por area (solo si hay filtro de tipo) ---
    cumplimiento_por_area = []
    nota_historica = []
    participacion_tendencia = {}
    if doc_type_filter:
        area_stats = {}
        for c in todos_compromisos:
            a = c.area or "Sin área"
            area_stats.setdefault(a, {"total": 0, "cumplidos": 0})
            area_stats[a]["total"] += 1
            if (c.estado or "").strip().upper() in ("COMPLETADO", "CERRADO"):
                area_stats[a]["cumplidos"] += 1
        cumplimiento_por_area = [
            {"area": a, "pct": round((s["cumplidos"] / s["total"]) * 100) if s["total"] else 0}
            for a, s in area_stats.items()
        ]

        for r in sorted(reuniones, key=lambda r: r.created_at or r.id):
            if r.nota is not None:
                nota_historica.append({"fecha": r.fecha, "nota": r.nota})

        for r in reuniones:
            for p in r.participantes:
                if not p.area:
                    continue
                participacion_tendencia.setdefault(p.area, []).append(1 if p.asistio else 0)

    # --- Reuniones sin compromisos (alerta, siempre visible) ---
    reuniones_sin_compromisos = [r for r in reuniones if len(r.compromisos) == 0]

    # --- Semanas disponibles (global, para el selector de rango en todas las vistas) ---
    todas_las_semanas_nota = sorted(
        {_week_year_code(r.fecha) for r in Reunion.query.filter(Reunion.nota.isnot(None)).all()},
        key=_semana_sort_key,
    )
    semana_inicio = request.args.get("semana_inicio", "").strip()
    semana_fin = request.args.get("semana_fin", "").strip()

    def _aplicar_rango(semanas):
        out = semanas
        if semana_inicio and semana_inicio in out:
            out = out[out.index(semana_inicio):]
        if semana_fin and semana_fin in out:
            out = out[: out.index(semana_fin) + 1]
        return out

    # --- "Semanal divisional" del tipo actual (todas las areas), solo en vista por tipo ---
    nota_semanal_tipo = {"labels": [], "data": []}
    if doc_type_filter:
        reuniones_tipo_todas_areas = (
            Reunion.query.filter_by(doc_type=doc_type_filter).filter(Reunion.nota.isnot(None)).all()
        )
        semanas_tipo = _weekly_avg_by_week(reuniones_tipo_todas_areas)
        labels_tipo = _aplicar_rango(sorted(semanas_tipo.keys(), key=_semana_sort_key))
        nota_semanal_tipo = {
            "labels": labels_tipo,
            "data": [round(sum(semanas_tipo[s]) / len(semanas_tipo[s]), 2) for s in labels_tipo],
        }

    # --- "Semanal del area" seleccionada, solo si hay area_filter (usa reuniones ya filtradas) ---
    nota_semanal_area = {"labels": [], "data": []}
    if area_filter:
        semanas_area = _weekly_avg_by_week(reuniones)
        labels_area = _aplicar_rango(sorted(semanas_area.keys(), key=_semana_sort_key))
        nota_semanal_area = {
            "labels": labels_area,
            "data": [round(sum(semanas_area[s]) / len(semanas_area[s]), 2) for s in labels_area],
        }

    # --- Vista Resumen DET: promedio divisional por tipo de reunion + promedio general ---
    nota_divisional_por_tipo = {"labels": [], "series": []}
    if not doc_type_filter:
        reuniones_para_nota_q = Reunion.query.filter(Reunion.nota.isnot(None))
        if area_filter:
            reuniones_para_nota_q = reuniones_para_nota_q.filter_by(area=area_filter)
        reuniones_para_nota = reuniones_para_nota_q.all()

        notas_por_tipo_semana = defaultdict(lambda: defaultdict(list))
        notas_generales_semana = defaultdict(list)
        for r in reuniones_para_nota:
            semana = _week_year_code(r.fecha)
            tipo_label = _DOC_LABELS.get(r.doc_type, r.doc_type)
            notas_por_tipo_semana[tipo_label][semana].append(r.nota)
            notas_generales_semana[semana].append(r.nota)

        labels_resumen = _aplicar_rango(sorted(notas_generales_semana.keys(), key=_semana_sort_key))

        nota_divisional_por_tipo = {"labels": labels_resumen, "series": []}
        for tipo_label in ["PRIO", "PLAN", "PROG", "PMT"]:
            semanas_tipo2 = notas_por_tipo_semana.get(tipo_label, {})
            nota_divisional_por_tipo["series"].append({
                "label": tipo_label,
                "data": [
                    round(sum(semanas_tipo2[s]) / len(semanas_tipo2[s]), 2) if s in semanas_tipo2 else None
                    for s in labels_resumen
                ],
            })
        nota_divisional_por_tipo["series"].append({
            "label": "Promedio general",
            "data": [
                round(sum(notas_generales_semana[s]) / len(notas_generales_semana[s]), 2) if s in notas_generales_semana else None
                for s in labels_resumen
            ],
        })

    all_areas = [
        {"value": a.nombre, "label": f"{a.superintendencia.gerencia.codigo} - {a.nombre}"}
        for a in AreaTrabajo.query.join(Superintendencia).join(Gerencia).order_by(Gerencia.codigo, AreaTrabajo.nombre).all()
    ]
    area_filter_label = next((a["label"] for a in all_areas if a["value"] == area_filter), area_filter)
    return _render_any(
        ["admin_seguimiento.html", "web/admin_seguimiento.html"],
        doc_type_filter=doc_type_filter,
        area_filter=area_filter,
        area_filter_label=area_filter_label,
        all_areas=all_areas,
        total_reuniones=total_reuniones,
        total_compromisos=total_compromisos,
        compromisos_vencidos=compromisos_vencidos,
        nota_promedio=nota_promedio,
        asistencia_promedio=asistencia_promedio,
        asistencia_por_area=asistencia_por_area,
        areas_menos_participan=areas_menos_participan,
        counts_por_estado=counts_por_estado,
        reuniones_por_tipo=reuniones_por_tipo,
        cumplimiento_por_area=cumplimiento_por_area,
        nota_historica=nota_historica,
        nota_divisional_por_tipo=nota_divisional_por_tipo,
        nota_semanal_tipo=nota_semanal_tipo,
        nota_semanal_area=nota_semanal_area,
        semanas_disponibles=todas_las_semanas_nota,
        semana_inicio=semana_inicio,
        semana_fin=semana_fin,
        reuniones_sin_compromisos=reuniones_sin_compromisos,
        doc_labels=_DOC_LABELS,
    )

@web_bp.get("/compromisos/abiertos")
@login_required
def compromisos_abiertos():
    doc_type = (request.args.get("doc_type", "") or "").strip()
    area = (request.args.get("area", "") or "").strip()
    if not doc_type or not area:
        return {"compromisos": []}

    rows = (
        Compromiso.query
        .join(Reunion, Compromiso.reunion_id == Reunion.id)
        .filter(Reunion.doc_type == doc_type, Compromiso.area == area)
        .order_by(Compromiso.id.asc())
        .all()
    )

    latest_by_key: Dict[str, Compromiso] = {}
    for c in rows:
        key = c.thread_id or str(c.id)
        latest_by_key[key] = c  # por orden ascendente, el ultimo que pisa es el mas reciente

    result = []
    for key, c in latest_by_key.items():
        if (c.estado or "").strip().upper() in ("COMPLETADO", "CANCELADO"):
            continue
        if c.thread_id is None:
            c.thread_id = str(c.id)
            db.session.add(c)
        result.append({
            "thread_id": c.thread_id,
            "accion": c.accion or "",
            "responsable": c.responsable or "",
            "fecha": c.fecha_compromiso or "",
            "estado": c.estado or "",
            "vencido": c.is_vencido,
        })
    db.session.commit()

    return {"compromisos": result}

@web_bp.get("/admin/vencidos")
@login_required
@admin_required
def admin_vencidos():
    doc_type_filter = request.args.get("tipo", "").strip()
    area_filter = request.args.get("area", "").strip()

    query = Reunion.query
    if doc_type_filter:
        query = query.filter_by(doc_type=doc_type_filter)
    if area_filter:
        query = query.filter_by(area=area_filter)
    reuniones = query.all()
    reunion_by_id = {r.id: r for r in reuniones}

    reunion_ids = list(reunion_by_id.keys()) or [-1]
    compromisos = _compromisos_vigentes(
        Compromiso.query.filter(Compromiso.reunion_id.in_(reunion_ids)).all()
    )

    from datetime import datetime
    vencidos = []
    for c in compromisos:
        if not c.is_vencido:
            continue
        r = reunion_by_id.get(c.reunion_id)
        dias = None
        try:
            d = datetime.strptime((c.fecha_compromiso or "").strip(), "%d/%m/%Y")
            dias = (datetime.today().date() - d.date()).days
        except Exception:
            pass
        vencidos.append({
            "compromiso": c,
            "reunion": r,
            "dias_vencido": dias,
        })

    vencidos.sort(key=lambda v: v["dias_vencido"] or 0, reverse=True)

    return _render_any(
        ["admin_vencidos.html", "web/admin_vencidos.html"],
        vencidos=vencidos,
        doc_type_filter=doc_type_filter,
        area_filter=area_filter,
        doc_labels=_DOC_LABELS,
    )    

@web_bp.get("/admin/organizacion")
@login_required
@admin_required
def admin_organizacion():
    gerencias = Gerencia.query.order_by(Gerencia.codigo).all()
    return _render_any(
        ["admin_organizacion.html", "web/admin_organizacion.html"],
        gerencias=gerencias,
    )


@web_bp.post("/admin/organizacion/gerencia")
@login_required
@admin_required
def admin_crear_gerencia():
    codigo = (request.form.get("codigo", "") or "").strip().upper()
    nombre = (request.form.get("nombre", "") or "").strip()
    if codigo and nombre:
        db.session.add(Gerencia(codigo=codigo, nombre=nombre))
        db.session.commit()
    return redirect(url_for("web.admin_organizacion"))


@web_bp.post("/admin/organizacion/gerencia/<int:gerencia_id>/eliminar")
@login_required
@admin_required
def admin_eliminar_gerencia(gerencia_id):
    g = Gerencia.query.get_or_404(gerencia_id)
    db.session.delete(g)
    db.session.commit()
    return redirect(url_for("web.admin_organizacion"))


@web_bp.post("/admin/organizacion/superintendencia")
@login_required
@admin_required
def admin_crear_superintendencia():
    gerencia_id = request.form.get("gerencia_id", type=int)
    codigo = (request.form.get("codigo", "") or "").strip().upper()
    nombre = (request.form.get("nombre", "") or "").strip()
    if gerencia_id and codigo and nombre:
        db.session.add(Superintendencia(gerencia_id=gerencia_id, codigo=codigo, nombre=nombre))
        db.session.commit()
    return redirect(url_for("web.admin_organizacion"))


@web_bp.post("/admin/organizacion/superintendencia/<int:superintendencia_id>/eliminar")
@login_required
@admin_required
def admin_eliminar_superintendencia(superintendencia_id):
    s = Superintendencia.query.get_or_404(superintendencia_id)
    db.session.delete(s)
    db.session.commit()
    return redirect(url_for("web.admin_organizacion"))


@web_bp.post("/admin/organizacion/area")
@login_required
@admin_required
def admin_crear_area():
    superintendencia_id = request.form.get("superintendencia_id", type=int)
    nombre = (request.form.get("nombre", "") or "").strip()
    codigo_pdf = (request.form.get("codigo_pdf", "") or "").strip().upper()
    if superintendencia_id and nombre:
        db.session.add(AreaTrabajo(superintendencia_id=superintendencia_id, nombre=nombre, codigo_pdf=codigo_pdf))
        db.session.commit()
    return redirect(url_for("web.admin_organizacion"))


@web_bp.post("/admin/organizacion/area/<int:area_id>/eliminar")
@login_required
@admin_required
def admin_eliminar_area(area_id):
    a = AreaTrabajo.query.get_or_404(area_id)
    db.session.delete(a)
    db.session.commit()
    return redirect(url_for("web.admin_organizacion"))