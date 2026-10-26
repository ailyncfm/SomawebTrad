# somaweb/app/pdf/prioritization.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from app.pdf.base_layout import PageStyle, draw_section_bar
from app.pdf.components import (
    draw_header,
    draw_observer_block,
    draw_area_row,
    draw_scale_row,
    measure_eval_item_row_height,
    draw_eval_item_row,
    measure_feedback_block_height,
    draw_feedback_block,
    draw_commitments_table,
    draw_participants_table,
    measure_checklist_table_height,
    draw_checklist_table,
)


def build_prioritization_example_data() -> Dict[str, Any]:
    # OJO: esto es “plantilla base” para que el formulario funcione.
    # Si ya tienes tu set real de preguntas, lo reemplazamos por el tuyo.
    return {
        "title": "Confirmación de rol - Reunión de Priorización SOMA",
        "participants": [
            {"area": "Operaciones", "responsable": "", "si": False, "no": False},
            {"area": "Mantenimiento", "responsable": "", "si": False, "no": False},
            {"area": "SSO", "responsable": "", "si": False, "no": False},
        ],
        "sections": [
            {
                "name": "Criterios de Priorización",
                "items": [
                    {
                        "question": "Impacto en seguridad / fatalidad",
                        "options": ["Bajo", "Medio", "Alto"],
                    },
                    {
                        "question": "Impacto en continuidad operacional",
                        "options": ["Bajo", "Medio", "Alto"],
                    },
                    {
                        "question": "Probabilidad de ocurrencia",
                        "options": ["Baja", "Media", "Alta"],
                    },
                ],
            },
            {
                "name": "Condición Actual",
                "items": [
                    {
                        "question": "Controles actuales implementados",
                        "options": ["No", "Parcial", "Sí"],
                    },
                    {
                        "question": "Evidencia disponible / trazabilidad",
                        "options": ["No", "Parcial", "Sí"],
                    },
                ],
            },
        ],
    }


def _ensure_space(
    c: canvas.Canvas,
    style: PageStyle,
    y_top: float,
    needed_h: float,
    *,
    title: str,
    logo_dir: str,
) -> float:
    if y_top - needed_h >= style.margin_bottom:
        return y_top
    c.showPage()
    y_top = draw_header(c, style, title, "", "", "", logo_dir, show_meta=False)
    return y_top


def _calc_score(sections: List[Dict[str, Any]]) -> Tuple[float, float]:
    total = 0.0
    n_items = 0
    for sec in sections:
        for it in (sec.get("items") or []):
            try:
                total += float(it.get("selected", 1))
            except Exception:
                total += 1.0
            n_items += 1
    max_possible = float(max(1, n_items * 3))
    pct = total / max_possible
    nota = 1.0 + pct * 6.0
    return total, nota


def render_prioritization_pdf(c: canvas.Canvas, data: Dict[str, Any], base_dir: str):
    style = PageStyle()
    pw, ph = style.pagesize
    x = style.margin_left
    w = pw - style.margin_left - style.margin_right
    logo_dir = f"{base_dir}/app/static/img"

    title = str(data.get("title", "Formulario SOMA - Priorización"))
    fecha = str(data.get("fecha", ""))
    hora = str(data.get("hora", ""))
    area = str(data.get("area", "") or "")

    y_top = draw_header(c, style, title, fecha, hora, area, logo_dir, show_meta=True)

    observers = data.get("observers") or []
    for idx, obs in enumerate(observers[:2], start=1):
        y_top = _ensure_space(c, style, y_top, 3.2 * cm, title=title, logo_dir=logo_dir)
        y_top = draw_observer_block(c, x, y_top, w, obs, idx)

    y_top = _ensure_space(c, style, y_top, 1.0 * cm, title=title, logo_dir=logo_dir)
    y_top = draw_scale_row(c, x, y_top, w)

    sections = data.get("sections") or []
    for sec in sections:
        sec_name = str(sec.get("name", "") or "").strip() or "Sección"
        bar_h = 0.6 * cm

        y_top = _ensure_space(c, style, y_top, bar_h + 0.25 * cm, title=title, logo_dir=logo_dir)
        y_bar = y_top - bar_h
        draw_section_bar(c, x, y_bar, w, bar_h, sec_name)
        y_top = y_bar - 0.20 * cm

        for it in (sec.get("items") or []):
            q = str(it.get("question", "") or "")
            opts = list(it.get("options") or [])[:3]
            sel = int(it.get("selected", 1) or 1)

            row_h = measure_eval_item_row_height(c, w, q, opts)
            y_top = _ensure_space(c, style, y_top, row_h + 0.25 * cm, title=title, logo_dir=logo_dir)
            y_top = draw_eval_item_row(c, x, y_top, w, question=q, options=opts, selected=sel, row_h=row_h) - 0.10 * cm

    checklist = data.get("checklist") or []
    if checklist:
        need_h = measure_checklist_table_height(c, w, checklist)
        y_top = _ensure_space(c, style, y_top, need_h + 0.4 * cm, title=title, logo_dir=logo_dir)
        y_top = draw_checklist_table(c, x, y_top, w, checklist)

    fb = data.get("feedback") or {}
    fortalezas = str(fb.get("fortalezas", "") or "")
    oportunidades = str(fb.get("oportunidades", "") or "")
    plan = str(fb.get("plan", "") or "")
    suma, nota = _calc_score(sections)
    need_fb = measure_feedback_block_height(w, fortalezas, oportunidades, plan)
    y_top = _ensure_space(c, style, y_top, need_fb + 0.25 * cm, title=title, logo_dir=logo_dir)
    y_top = draw_feedback_block(
        c, x, y_top, w,
        fortalezas=fortalezas, oportunidades=oportunidades, plan=plan,
        suma=suma, nota=nota,
    )

    commitments = data.get("commitments") or []
    if commitments:
        y_top = _ensure_space(c, style, y_top, 5.0 * cm, title=title, logo_dir=logo_dir)
        y_top = draw_commitments_table(c, x, y_top, w, commitments)

    participants = data.get("participants") or []
    if participants:
        y_top = _ensure_space(c, style, y_top, 4.0 * cm, title=title, logo_dir=logo_dir)
        y_top = draw_participants_table(c, x, y_top, w, participants)