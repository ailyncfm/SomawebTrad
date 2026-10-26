# app/pdf/scheduling.py
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
    draw_labeled_text_box,
)


def _score_sum(items: List[Dict[str, Any]]) -> int:
    return sum(int(it.get("selected", 0)) for it in items if int(it.get("selected", 0)) in (1, 2, 3))


def _note_from_score(score: int, max_score: int) -> float:
    if max_score <= 0:
        return 1.0
    return min(5.0, 1.0 + 4.0 * (score / max_score))


def build_scheduling_example_data() -> Dict[str, Any]:
    
    return {
        "title": "Confirmación de rol - Reunión de Programación SOMA",
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
        # Override (opcional) para que el test calce con el PDF ejemplo
        "score": 38,
        "nota": 4.2,
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
                        "selected": 2,
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
                        "question": "Programa propuesto para la semana N+1, con balance de carga por día/turno: Programación",
                        "options": [
                            "No presenta una propuesta de programa",
                            "Presenta un programa, pero el balance de carga no está completo",
                            "Presenta un programa completo (con balance de carga por día/turno)",
                        ],
                        "selected": 1,
                    },
                    {
                        "question": "Logística final de recursos (planificación/abastecimiento)",
                        "options": [
                            "El programa no considera la logística de abastecimiento",
                            "El programa considera parcialmente la logística de abastecimiento",
                            "El programa considera toda la logística de abastecimiento necesaria",
                        ],
                        "selected": 2,
                    },
                    {
                        "question": "Lista de actividades y riesgos críticos de las tareas (planificación/ejecución)",
                        "options": [
                            "No se presenta lista de actividades y riesgos críticos de las tareas",
                            "Se presenta lista incompleta de actividades y riesgos críticos de las tareas",
                            "Se presenta lista de actividades y riesgos críticos de las tareas",
                        ],
                        "selected": 2,
                    },
                    {
                        "question": "Solicitud de equipos de apoyo (planificación)",
                        "options": [
                            "No se presenta la solicitud de equipos de apoyos requeridos",
                            "Se presenta la solicitud de algunos equipos apoyos requeridos",
                            "Se presenta la solicitud de equipos de apoyo requerido",
                        ],
                        "selected": 3,
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
                            "Se controla asistencia, pero no se realiza reflexión o viceversa",
                            "Se controla la asistencia y se realiza la reflexión",
                        ],
                        "selected": 3,
                    },
                    {
                        "question": "Presentar actividades de la Gantt para N+1: El equipo…",
                        "options": [
                            "No revisa en conjunto la carta Gantt",
                            "Se revisa en conjunto la carta Gantt sin cuestionamientos",
                            "Se revisa en conjunto la carta Gantt de manera crítica, velando por eliminar las interferencias de recursos",
                        ],
                        "selected": 1,
                    },
                    {
                        "question": "Señalar actividades críticas y plan de inspección para seguridad: El equipo…",
                        "options": [
                            "No revisa en conjunto las actividades críticas y los planes de inspección propuestos",
                            "Revisa en conjunto las actividades críticas y los planes de inspección sin cuestionar",
                            "Revisa en conjunto las actividades críticas y analiza los planes de inspección antes de aprobarlos",
                        ],
                        "selected": 2,
                    },
                    {
                        "question": "Presenta plan de control de residuos: El equipo…",
                        "options": [
                            "No revisa el plan de control de residuos",
                            "Revisa el plan de control de residuos sin cuestionamientos",
                            "Revisa en conjunto el plan de control de residuos antes de aprobarlo",
                        ],
                        "selected": 3,
                    },
                    {
                        "question": "Presenta análisis técnicos",
                        "options": [
                            "No revisa los análisis técnicos",
                            "Revisa los análisis técnicos sin cuestionamientos",
                            "Revisa en conjunto los análisis técnicos antes de aprobarlos",
                        ],
                        "selected": 2,
                    },
                    {
                        "question": "Presentar layout de distribución de recursos",
                        "options": [
                            "No revisa el layout de distribución de recursos",
                            "Revisa el layout de distribución de recursos sin cuestionamientos",
                            "Revisa en conjunto y cuestiona el layout de distribución de recursos antes de aprobarlo",
                        ],
                        "selected": 1,
                    },
                    {
                        "question": "Presentar Gantt de preparativos y Gantt de aseos",
                        "options": [
                            "No revisa el Gantt de preparativos y el Gantt de aseos",
                            "Revisa el Gantt de preparativos y el Gantt de aseos sin cuestionamientos",
                            "Revisa en conjunto y cuestiona el Gantt de preparativos y el Gantt de aseos antes de aprobarlos",
                        ],
                        "selected": 2,
                    },
                    {
                        "question": "Presentar plan de tránsito",
                        "options": [
                            "No revisa el plan de tránsito",
                            "Revisa el plan de tránsito sin cuestionamientos",
                            "Revisa en conjunto y cuestiona el plan de tránsito antes de aprobarlo",
                        ],
                        "selected": 3,
                    },
                    {
                        "question": "Cierre formal: programación…",
                        "options": [
                            "No solicita a los participantes la confirmación de programa N+1 para oficializar y congelar, pero no de manera formal",
                            "Solicita a los participantes la validación del programa N+1 para oficializar y congelar, pero no de manera formal",
                            "Solicita a los participantes la validación del programa N+1 para oficializar y congelar",
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
                        "selected": 2,
                    },
                    {
                        "question": "Preparación: La preparación de la información refleja la importancia que dan los participantes a la priorización",
                        "options": [
                            "La preparación necesaria es nula y se le da poca importancia en todo el equipo",
                            "Uno o más asistentes no prepara la información y no entiende su importancia",
                            "Todos aportan la información necesaria y de la manera esperada",
                        ],
                        "selected": 1,
                    },
                    {
                        "question": "Motivación a la priorización: El equipo entiende que el principal objetivo es la priorización",
                        "options": [
                            "Se discute poco o nada de priorización",
                            "La priorización se discute parcialmente",
                            "El equipo cuestiona y analiza la priorización en cada etapa de la reunión",
                        ],
                        "selected": 2,
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
        ],
        "participants": [
            {"area": "CONFIABILIDAD", "responsable": "RESPONSABLE_EJEMPLO1", "si": False, "no": True},
            {"area": "PLANIFICADOR", "responsable": "RESPONSABLE_EJEMPLO2", "si": True, "no": False},
            {"area": "PROGRAMADOR", "responsable": "RESPONSABLE_EJEMPLO3", "si": False, "no": True},
            {"area": "EJECUTOR", "responsable": "RESPONSABLE_EJEMPLO4", "si": False, "no": True},
            {"area": "OPERACIONES", "responsable": "RESPONSABLE_EJEMPLO5", "si": True, "no": False},
            {"area": "GSYS", "responsable": "RESPONSABLE_EJEMPLO6", "si": True, "no": False},
            {"area": "ELÉCTRICOS", "responsable": "RESPONSABLE_EJEMPLO7", "si": True, "no": False},
            {"area": "ABASTECIMIENTO", "responsable": "RESPONSABLE_EJEMPLO8", "si": False, "no": True},
            {"area": "EECC", "responsable": "RESPONSABLE_EJEMPLO9", "si": True, "no": False},
            {"area": "OTRO", "responsable": "RESPONSABLE_EJEMPLO10", "si": True, "no": False},
        ],
    }


def render_scheduling_pdf(c, data: Dict[str, Any], base_dir: str):
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
            y_top = draw_eval_item_row(
                c, x, y_top, w,
                question=it["question"], options=it["options"],
                selected=int(it["selected"]), row_h=row_h,
            ) - 0.05 * cm
        y_top -= 0.25 * cm

    checklist = data.get("checklist") or []
    if checklist:
        need_h = measure_checklist_table_height(c, w, checklist)
        ensure_space((need_h / cm) + 0.6)
        y_top = draw_checklist_table(c, x, y_top, w, checklist)

    acts_criticas = str(data.get("chk_acts_criticas_comentario", "") or "")
    if acts_criticas:
        ensure_space(2.0)
        y_top = draw_labeled_text_box(c, x, y_top, w, "Comentario actividades críticas:", acts_criticas)

    all_items: List[Dict[str, Any]] = []
    for s in data["sections"]:
        all_items.extend(s["items"])
    score_calc = _score_sum(all_items)
    max_score = 3 * len(all_items)
    nota_calc = _note_from_score(score_calc, max_score)
    score = int(data.get("score", score_calc))
    nota = float(data.get("nota", nota_calc))

    fb_h = measure_feedback_block_height(
        w, data["feedback"]["fortalezas"], data["feedback"]["oportunidades"], data["feedback"]["plan"],
    )
    ensure_space((fb_h / cm) + 0.8)
    y_top = draw_feedback_block(
        c, x, y_top, w,
        fortalezas=data["feedback"]["fortalezas"],
        oportunidades=data["feedback"]["oportunidades"],
        plan=data["feedback"]["plan"],
        suma=score, nota=nota,
    )

    c.showPage()
    y_top = draw_header(c, style, data["title"], "", "", "", logo_dir, show_meta=False)
    y_top = draw_commitments_table(c, x, y_top - 0.2 * cm, w, data["commitments"])
    draw_participants_table(c, x, y_top - 0.2 * cm, w, data["participants"])