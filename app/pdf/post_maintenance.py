# app/pdf/post_maintenance.py
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


def _score_sum(items: List[Dict[str, Any]]) -> int:
    return sum(int(it.get("selected", 0)) for it in items if int(it.get("selected", 0)) in (1, 2, 3))


def _note_from_score(score: int, max_score: int) -> float:
    if max_score <= 0:
        return 1.0
    return min(5.0, 1.0 + 4.0 * (score / max_score))


def build_post_maintenance_example_data() -> Dict[str, Any]:
    
    return {
        "title": "Confirmación de rol - Reunión de Post Mantención SOMA",
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
        # Si viene score/nota, se respeta (para calzar con PDF ejemplo)
        "score": 29,
        "nota": 4.2,        "sections": [
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
                        "question": "Actividades planificadas ejecutadas, no ejecutadas, retrasos, reprocesos, actividades no planificadas, emergencias (ejecución y planificación)",
                        "options": [
                            "No presentan una lista de trabajos ejecutados versus planificados",
                            "Se presenta una lista de trabajos ejecutados versus planificados",
                            "Se presenta una lista de trabajos ejecutados versus planificados (completa)",
                        ],
                        "selected": 3,
                    },
                    {
                        "question": "Registro de desempeño (ejecución), adherencia al programa y plan matriz (ejecución y planificación) y costo según plan vs costo real (planificación)",
                        "options": [
                            "No se realiza el desempeño del mantenimiento realizado con indicadores",
                            "Se analiza desempeño en base a algunos indicadores",
                            "Se analiza desempeño en base a indicadores de resultado (KPI’s)",
                        ],
                        "selected": 1,
                    },
                ],
            },
            {
                "name": "DESARROLLO",
                "items": [
                    {
                        "question": "Presentación de desviaciones y desempeño general rutinario N+1",
                        "options": [
                            "No se conocen las desviaciones y el desempeño general N+1",
                            "Se conoce el desempeño, pero no se analizan las desviaciones",
                            "Se presentan el desempeño y se analizan las desviaciones de N+1",
                        ],
                        "selected": 2,
                    },
                    {
                        "question": "Presentación en detalle de desviaciones mayores y análisis de causas",
                        "options": [
                            "No se identifican las principales desviaciones",
                            "Se identifican las principales desviaciones, pero no se identifican las causas raíz",
                            "Se identifican las principales desviaciones y sus causas raíz",
                        ],
                        "selected": 1,
                    },
                    {
                        "question": "Presentación de elementos de seguridad y análisis de causas",
                        "options": [
                            "No se analizan las desviaciones en seguridad",
                            "Se analizan las desviaciones en seguridad, pero no se identifican las causas raíz",
                            "Se analizan las desviaciones en seguridad y se identifican las causas raíz",
                        ],
                        "selected": 3,
                    },
                    {
                        "question": "Presentación y debate de oportunidades de mejora",
                        "options": [
                            "No se discute acerca de oportunidades de mejora",
                            "Se discute escasamente sobre oportunidades de mejora",
                            "Se da relevancia a identificar oportunidades para mejorar",
                        ],
                        "selected": 2,
                    },
                    {
                        "question": "Compromisos: Cierre de reunión",
                        "options": [
                            "Se cierra la reunión sin compromisos",
                            "Se cierra la reunión con compromisos informales",
                            "Se realiza cierre de reunión repasando los compromisos",
                        ],
                        "selected": 1,
                    },
                    {
                        "question": "Entregables de la reunión:\n• Análisis desempeño (de planificación y ejecución)\n• Análisis técnico (confiabilidad)\n• Reparables y repuestos utilizados y no utilizados\n• Compromisos (RdP, seguimiento, nuevos estándares)\n• Oportunidades de mejora",
                        "options": [
                            "No se da importancia al cumplimiento de las reglas",
                            "Uno o más integrantes no respeta las reglas y refleja falta de entendimiento de la importancia de la reunión",
                            "El equipo completo respeta las reglas y es reflejo de la importancia que dan a la reunión",
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
                            "Uno o más integrantes no respeta las reglas y refleja falta de entendimiento de la importancia de la reunión",
                            "El equipo completo respeta las reglas y es reflejo de la importancia que dan a la reunión",
                        ],
                        "selected": 3,
                    },
                    {
                        "question": "Preparación: La preparación de la información refleja la importancia que dan los participantes al análisis post-mantenimiento",
                        "options": [
                            "La preparación necesaria es nula y se le da poca importancia en todo el equipo",
                            "Uno o más asistentes no prepara la información y no entiende su importancia",
                            "Todos aportan la información necesaria y de la manera esperada",
                        ],
                        "selected": 2,
                    },
                    {
                        "question": "Motivación a la priorización: El equipo entiende que el principal objetivo es mejorar",
                        "options": [
                            "Se discute poco o nada de oportunidades de mejora",
                            "Las oportunidades de mejora se discuten parcialmente",
                            "El equipo identifica y analiza las oportunidades de mejora en cada etapa de la reunión",
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
                        "selected": 3,
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
            {"area": "CONFIABILIDAD", "responsable": "RESPONSABLE_EJEMPLO1", "si": True, "no": False},
            {"area": "PLANIFICADOR", "responsable": "RESPONSABLE_EJEMPLO2", "si": False, "no": True},
            {"area": "PROGRAMADOR", "responsable": "RESPONSABLE_EJEMPLO3", "si": True, "no": False},
            {"area": "EJECUTOR", "responsable": "RESPONSABLE_EJEMPLO4", "si": True, "no": False},
            {"area": "OPERACIONES", "responsable": "RESPONSABLE_EJEMPLO5", "si": True, "no": False},
            {"area": "GSYS", "responsable": "RESPONSABLE_EJEMPLO6", "si": False, "no": True},
            {"area": "ELÉCTRICOS", "responsable": "RESPONSABLE_EJEMPLO7", "si": False, "no": True},
            {"area": "ABASTECIMIENTO", "responsable": "RESPONSABLE_EJEMPLO8", "si": True, "no": False},
            {"area": "EECC", "responsable": "RESPONSABLE_EJEMPLO9", "si": True, "no": False},
            {"area": "OTRO", "responsable": "RESPONSABLE_EJEMPLO10", "si": True, "no": False},
        ],
    }


def render_post_maintenance_pdf(c, data: Dict[str, Any], base_dir: str):
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