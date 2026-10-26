# app/pdf/planning.py
from __future__ import annotations

from typing import Dict, Any, List
from reportlab.lib.units import cm

from app.pdf.base_layout import PageStyle, draw_section_bar
from app.pdf.components import (
    draw_header,
    draw_observer_block,
    draw_area_row,
    draw_scale_row,
    draw_eval_item_row,
    measure_eval_item_row_height,
    draw_feedback_block,
    measure_feedback_block_height,
    draw_commitments_table,
    draw_participants_table,
    measure_checklist_table_height,
    draw_checklist_table,
)


def _calc_grade_1_to_5(points: float, pmin: float, pmax: float, exigencia: float = 0.60) -> float:
    """
    Nota 1.0 a 5.0 con exigencia:
      - Nota 4.0 al llegar a (exigencia * pmax)
      - Nota 1.0 en pmin
      - Nota 5.0 en pmax
    """
    nmin, naprob, nmax = 1.0, 4.0, 5.0

    if pmax <= pmin:
        return nmin

    preq = exigencia * pmax

    if points <= preq:
        denom = (preq - pmin)
        grade = naprob if denom <= 0 else (nmin + ((points - pmin) / denom) * (naprob - nmin))
    else:
        denom = (pmax - preq)
        grade = naprob if denom <= 0 else (naprob + ((points - preq) / denom) * (nmax - naprob))

    grade = max(nmin, min(nmax, grade))
    return round(grade, 1)


def _compute_scoring_fallback(data: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback por si alguien llama el renderer sin data['scoring'] (ej: example_data)."""
    points_obt = 0.0
    points_min = 0.0
    points_max = 0.0
    n_questions = 0

    for sec in (data.get("sections") or []):
        for it in (sec.get("items") or []):
            opts = it.get("options") or []
            n_opts = len(opts)
            if n_opts <= 0:
                continue
            n_questions += 1
            points_min += 1
            points_max += n_opts
            try:
                sel = int(it.get("selected") or 1)
            except Exception:
                sel = 1
            # clamp a 1..n_opts
            sel = max(1, min(n_opts, sel))
            points_obt += float(sel)

    nota_final = _calc_grade_1_to_5(points_obt, points_min, points_max, exigencia=0.60)

    return {
        "n_preguntas": n_questions,
        "puntaje_obtenido": round(points_obt, 1),
        "puntaje_minimo": round(points_min, 1),
        "puntaje_maximo": round(points_max, 1),
        "exigencia": 0.60,
        "nota_final": float(nota_final),
    }


def build_planning_example_data() -> Dict[str, Any]:
    return {
        "title": "Confirmación de rol - Reunión de Planificación SOMA",
        "fecha": "02/03/2026",
        "hora": "10:10",
        "area": "AREA_EJEMPLO",
        "observers": [
            {
                "id": "ID_EJEMPLO1",
                "nombre": "NOMBRE_OBSERVADOR1",
                "gerencia": "GERENCIA_EJEMPLO1",
                "superintendencia": "SUPERINTENDENCIA_EJEMPLO1",
                "sap": "SAP_EJEMPLO1",
                "email": "CORREO@EJEMPLO.CL",
                "posicion": "EJEMPLO1",
            },
            {
                "id": "ID_EJEMPLO2",
                "nombre": "NOMBRE_OBSERVADOR2",
                "gerencia": "GERENCIA_EJEMPLO2",
                "superintendencia": "SUPERINTENDENCIA_EJEMPLO2",
                "sap": "SAP_EJEMPLO2",
                "email": "CORREO@EJEMPLO.CL",
                "posicion": "EJEMPLO2",
            },
        ],
        "sections": [
            {
                "name": "ASPECTOS GENERALES",
                "items": [
                    {
                        "question": "Ejecución: La reunión…",
                        "options": [
                            "No se realizó y/o se reagendó",
                            "Se realizó, pero tarde o se extendió",
                            "Se realizó de acuerdo con el horario y la duración planificada",
                        ],
                        "selected": 1,
                    },
                    {
                        "question": "Asistencia: A la reunión asisten... (planificación, confiabilidad, operación, ej. mantenimiento, abastecimiento, EECC y prevencionistas)",
                        "options": [
                            "No se presentaron más de 3 participantes claves",
                            "Faltaron 1-2 participantes claves",
                            "Estaban todos los relevantes",
                        ],
                        "selected": 2,
                    },
                ],
            },
            {
                "name": "INPUTS",
                "items": [
                    {
                        "question": "Plan de mantenimiento semanal propuesto: Planificación…",
                        "options": [
                            "No se presenta una propuesta de plan de mantenimiento semanal",
                            "Presenta un plan de mantenimiento semanal, pero no está completo",
                            "Presenta un plan de mantenimiento semanal completo",
                        ],
                        "selected": 3,
                    },
                    {
                        "question": "Balance consolidado (análisis de factibilidad de las Ots) realizado por planificación: El plan…",
                        "options": [
                            "No incluye un análisis de factibilidad en función de los recursos disponibles",
                            "El análisis de factibilidad es incompleto",
                            "El plan es factible según análisis de recursos requeridos versus disponibles",
                        ],
                        "selected": 2,
                    },
                ],
            },
            {
                "name": "DESARROLLO",
                "items": [
                    {
                        "question": "Presentación, asistencia y reflexión:",
                        "options": [
                            "No se controla la asistencia y no se realiza reflexión",
                            "Se controla la asistencia, pero no se realiza reflexión (o viceversa)",
                            "Se controla la asistencia y se realiza reflexión",
                        ],
                        "selected": 1,
                    },
                    {
                        "question": "Entrega de propuesta de plan de mantenimiento para N-2 (de acuerdo con el análisis de factibilidad y las iteraciones con criticidad): El equipo…",
                        "options": [
                            "No revisa en conjunto la propuesta de plan mensual",
                            "Revisa el plan semanal sin cuestionamientos",
                            "Revisa el plan de manera crítica, en cuanto a exigencia y factibilidad",
                        ],
                        "selected": 2,
                    },
                    {
                        "question": "Presentación de actividades que no quedan en el plan (última instancia de apelación):",
                        "options": [
                            "No son presentadas",
                            "Son presentadas sin cuestionamientos",
                            "El equipo debate para asegurar que las tareas necesarias sean incluidas",
                        ],
                        "selected": 3,
                    },
                    {
                        "question": "Aprobación de todos los integrantes (firma de superintendentes):",
                        "options": [
                            "No solicita a los participantes la confirmación del plan de mantenimiento",
                            "Se solicita a los participantes la validación del plan de mantenimiento, pero no formalmente",
                            "Se solicita a los participantes la validación formal del plan de mantenimiento para luego solicitar firmas de SI",
                        ],
                        "selected": 2,
                    },
                ],
            },
            {
                "name": "MENTALIDADES Y COMPORTAMIENTOS",
                "items": [
                    {
                        "question": "Respeto por las reglas de la reunión: Los asistentes…",
                        "options": [
                            "No dan importancia al cumplimiento de las reglas",
                            "Uno o más integrantes no respeta las reglas y refleja una falta de entendimiento de la importancia de la reunión",
                            "El equipo completo respeta las reglas y es reflejo de la importancia que dan a la reunión",
                        ],
                        "selected": 1,
                    },
                    {
                        "question": "Preparación: La preparación de la información refleja la importancia que dan los participantes a la planificación",
                        "options": [
                            "La preparación necesaria es nula y se le da poca importancia en todo el equipo",
                            "Uno o más asistentes no prepara la información y no entiende su importancia",
                            "Todos aportan la información necesaria y de la manera esperada",
                        ],
                        "selected": 2,
                    },
                    {
                        "question": "Motivación a la priorización: El equipo entiende que el principal objetivo es la de planificar el plan semanal",
                        "options": [
                            "Se discute poco o nada de planificación",
                            "La planificación se discute parcialmente",
                            "El equipo cuestiona y debate para lograr un plan semanal exigente, pero alcanzable",
                        ],
                        "selected": 3,
                    },
                    {
                        "question": "La comunicación: ¿La comunicación de los participantes refleja entendimiento y convicción?",
                        "options": [
                            "Se observa lenguaje de desaprobación en el equipo",
                            "Uno o más integrantes muestran lenguaje de desaprobación",
                            "El equipo muestra un lenguaje positivo, colaborativo y alineado con el objetivo de la reunión",
                        ],
                        "selected": 2,
                    },
                ],
            },
        ],
        "feedback": {
            "fortalezas": "FORTALEZAS_REUNION_EJEMPLO",
            "oportunidades": "OPORTUNIDADES_REUNION_EJEMPLO",
            "plan": "PLAN_ACCION_EJEMPLO",
        },
        "commitments": [
            {"accion": "ACCION_1", "responsable": "RESPONSABLE_1", "fecha": "03/03/2027", "estado": "PENDIENTE", "evidencia": "FOTO_1"},
            {"accion": "ACCION_2", "responsable": "RESPONSABLE_2", "fecha": "03/03/2028", "estado": "CERRADA", "evidencia": "DOC_1"},
        ],
        "participants": [
            {"area": "CONFIABILIDAD", "responsable": "RESPONSABLE_EJEMPLO1", "si": True, "no": False},
            {"area": "PLANIFICADOR", "responsable": "RESPONSABLE_EJEMPLO2", "si": False, "no": True},
            {"area": "PROGRAMADOR", "responsable": "RESPONSABLE_EJEMPLO3", "si": True, "no": False},
            {"area": "EJECUTOR", "responsable": "RESPONSABLE_EJEMPLO4", "si": False, "no": True},
            {"area": "OPERACIONES", "responsable": "RESPONSABLE_EJEMPLO5", "si": True, "no": False},
            {"area": "GSYS", "responsable": "RESPONSABLE_EJEMPLO6", "si": True, "no": False},
            {"area": "ELÉCTRICOS", "responsable": "RESPONSABLE_EJEMPLO7", "si": False, "no": True},
            {"area": "ABASTECIMIENTO", "responsable": "RESPONSABLE_EJEMPLO8", "si": False, "no": True},
            {"area": "EECC", "responsable": "RESPONSABLE_EJEMPLO9", "si": True, "no": False},
            {"area": "OTRO", "responsable": "RESPONSABLE_EJEMPLO10", "si": True, "no": False},
        ],
    }

def render_planning_pdf(c, data: Dict[str, Any], base_dir: str):
    style = PageStyle()
    pw, ph = style.pagesize
    x = style.margin_left
    w = pw - style.margin_left - style.margin_right
    logo_dir = f"{base_dir}/app/static/img"

    y_top = draw_header(
        c, style, data["title"], data["fecha"], data["hora"],
        data.get("area", ""), logo_dir, show_meta=True,
    )

    y_top = draw_observer_block(c, x, y_top, w, data["observers"][0], idx=1)
    y_top = draw_observer_block(c, x, y_top, w, data["observers"][1], idx=2)
    y_top = draw_scale_row(c, x, y_top, w)

    def ensure_space(min_space_cm: float):
        nonlocal y_top
        if y_top < (style.margin_bottom + min_space_cm * cm):
            c.showPage()
            y_top = draw_header(c, style, data["title"], "", "", "", logo_dir, show_meta=False)

    for sec in data["sections"]:
        ensure_space(2.0)
        bar_h = 0.6 * cm
        y_bar = y_top - bar_h
        draw_section_bar(c, x, y_bar, w, bar_h, sec["name"])
        y_top = y_bar - 0.25 * cm
        for it in sec["items"]:
            row_h = measure_eval_item_row_height(c, w, it["question"], it["options"])
            ensure_space((row_h / cm) + 0.9)
            y_top = (
                draw_eval_item_row(
                    c, x, y_top, w,
                    question=it["question"], options=it["options"],
                    selected=int(it["selected"]), row_h=row_h,
                ) - 0.05 * cm
            )
        y_top -= 0.25 * cm

    checklist = data.get("checklist") or []
    if checklist:
        need_h = measure_checklist_table_height(c, w, checklist)
        ensure_space((need_h / cm) + 0.6)
        y_top = draw_checklist_table(c, x, y_top, w, checklist)

    sc = (data or {}).get("scoring") or _compute_scoring_fallback(data)
    try:
        puntaje_obt = float(sc.get("puntaje_obtenido", 0.0))
    except Exception:
        puntaje_obt = 0.0
    try:
        nota = float(sc.get("nota_final", 1.0))
    except Exception:
        nota = 1.0
    nota = max(1.0, min(5.0, nota))

    fb_h = measure_feedback_block_height(
        w, data["feedback"]["fortalezas"], data["feedback"]["oportunidades"], data["feedback"]["plan"],
    )
    ensure_space((fb_h / cm) + 0.8)
    y_top = draw_feedback_block(
        c, x, y_top, w,
        fortalezas=data["feedback"]["fortalezas"],
        oportunidades=data["feedback"]["oportunidades"],
        plan=data["feedback"]["plan"],
        suma=puntaje_obt, nota=nota,
    )

    c.showPage()
    y_top = draw_header(c, style, data["title"], "", "", "", logo_dir, show_meta=False)
    y_top = draw_commitments_table(c, x, y_top - 0.2 * cm, w, data["commitments"])
    draw_participants_table(c, x, y_top - 0.2 * cm, w, data["participants"])