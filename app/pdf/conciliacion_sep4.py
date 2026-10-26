# app/pdf/conciliacion_sep4.py
from __future__ import annotations

import re
from typing import Any, Dict, List

from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from app.pdf.base_layout import (
    PageStyle,
    LIGHTGRAY,
    WHITE,
    wrap_text,
    draw_box,
    draw_section_bar,
    draw_table_grid,
    draw_cell_text,
    draw_checkbox,
    draw_image_if_exists,
)
from app.pdf.components import (
    measure_feedback_block_height,
    draw_feedback_block,
    draw_commitments_table,
    draw_participants_table,
)

FORM_TITLE = "Conciliación SEP-4"


# ---------------------------------------------------------------------------
# Datos de ejemplo / schema real
# ---------------------------------------------------------------------------
def build_conciliacion_sep4_example_data() -> Dict[str, Any]:
    def o(v: int, text: str) -> Dict[str, Any]:
        return {"value": v, "text": text}

    def item(q: str, malo: str, regular: str, bueno: str) -> Dict[str, Any]:
        return {
            "question": q,
            "options": [o(1, malo), o(2, regular), o(3, bueno)],
            "selected": 0,
        }

    return {
        "title": FORM_TITLE,
        "codigo": "",
        "fecha": "",
        "division": "El Teniente",
        "evaluador": "",
        "turno": "",
        "detenciones_revisadas": "",
        "detenciones_conciliadas": "",
        "detenciones_pendientes": "",
        "horas_detencion_pendientes": "",
        "sections": [
            {
                "name": "Aspectos generales",
                "items": [
                    item(
                        "Ejecución: La reunión…",
                        "No se realizó y/o se reagendó",
                        "Se realizó, pero tarde o se extendió",
                        "Se realizó de acuerdo con el horario y la duración planificada",
                    ),
                    item(
                        "Asistencia: A la reunión asisten… (operaciones, confiabilidad, SEP-4)",
                        "No se presentaron participantes claves",
                        "Faltaron 1-2 participantes claves",
                        "Estaban todos los relevantes",
                    ),
                ],
            },
            {
                "name": "Inputs",
                "items": [
                    item(
                        "Operaciones llegó con información de las principales detenciones ocurridas durante el período",
                        "No presentó información o era insuficiente",
                        "Presentó información parcial",
                        "Presentó información completa para las detenciones relevantes",
                    ),
                    item(
                        "Confiabilidad llegó con información de las principales detenciones ocurridas durante el período",
                        "No presentó información o era insuficiente",
                        "Presentó información parcial",
                        "Presentó información completa para las detenciones relevantes",
                    ),
                    item(
                        "Mantenimiento llegó con información de las principales detenciones ocurridas durante el período",
                        "No presentó información o era insuficiente",
                        "Presentó información parcial",
                        "Presentó información completa para las detenciones relevantes",
                    ),
                    item(
                        "Imputador DOA-CIO llegó con el listado de imputaciones y antecedentes a revisar",
                        "No presentó información o era insuficiente",
                        "Presentó información parcial",
                        "Presentó información completa para las detenciones relevantes",
                    ),
                    item(
                        "Los equipos llegaron con contexto e información consistente para realizar la conciliación",
                        "Existen diferencias importantes entre los antecedentes presentados",
                        "Existen algunas diferencias que dificultan la revisión",
                        "La información presentada es consistente entre los equipos",
                    ),
                ],
            },
            {
                "name": "Desarrollo",
                "items": [
                    item(
                        "Se revisaron las detenciones prioritarias de la semana",
                        "No se revisaron los casos relevantes",
                        "Se revisó solo una parte de los casos relevantes",
                        "Se revisaron todos los casos identificados",
                    ),
                    item(
                        "Se logró acordar la imputación de las detenciones analizadas",
                        "La mayoría de los casos quedó sin acuerdo",
                        "Algunos casos quedaron sin acuerdo",
                        "Se logró acuerdo en todos los casos revisados",
                    ),
                    item(
                        "Cuando existieron diferencias de criterio, estas fueron gestionadas adecuadamente",
                        "No se logró avanzar en los desacuerdos",
                        "Se identificaron responsables para resolver algunos desacuerdos",
                        "Los desacuerdos fueron resueltos",
                    ),
                ],
            },
            {
                "name": "Mentalidades y comportamientos",
                "items": [
                    item(
                        "Las áreas participaron activamente para comprender las diferencias y alcanzar acuerdos de imputación",
                        "Predominó una postura poco colaborativa",
                        "Existió colaboración parcial",
                        "Existió una colaboración abierta y constructiva",
                    ),
                    item(
                        "Las decisiones se basaron en antecedentes y evidencias disponibles",
                        "Las decisiones se tomaron sin evidencia suficiente",
                        "Solo algunos casos contaban con respaldo adecuado",
                        "Los acuerdos se sustentaron en información verificable",
                    ),
                    item(
                        "Los participantes mantuvieron una actitud orientada al consenso y resolución de discrepancias",
                        "No hubo disposición al consenso",
                        "Existió disposición parcial",
                        "Se buscó activamente llegar a acuerdos y resolver diferencias",
                    ),
                ],
            },
        ],
        "participants": [
            {"area": "CONFIABILIDAD"},
            {"area": "OPERACIONES"},
            {"area": "MANTENIMIENTO"},
            {"area": "SEP-4"},
        ],
        "observers": [],
        "feedback": {"fortalezas": "", "oportunidades": "", "plan": ""},
        "commitments": [],
    }


# ---------------------------------------------------------------------------
# Helpers de render (adaptados de process_5s.py)
# ---------------------------------------------------------------------------
def _as_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _fmt_fecha(s: str) -> str:
    s = (s or "").strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        y, m, d = s.split("-")
        return f"{d}/{m}/{y}"
    return s


def _nota_calidad(nota):
    """Clasifica la nota (escala 1.0-7.0). Misma logica que routes.py:
    todo en 'malo' = 3.0, todo en 'regular' = 5.0, todo en 'bueno' = 7.0."""
    if nota is None:
        return None
    if nota < 5.0:
        return "Baja calidad"
    if nota < 6.0:
        return "Aceptable"
    return "Buena calidad"


def _calc_score_sep4(sections: List[Dict[str, Any]]):
    """Misma formula que _calc_meeting_score en routes.py (debe mantenerse
    sincronizada): N/A (selected=0) no cuenta ni en el total ni en el maximo."""
    total = 0
    max_total = 0
    for sec in (sections or []):
        for it in (sec.get("items") or []):
            sel = _as_int(it.get("selected"), 1)
            opts = it.get("options") or []
            max_opt = len(opts) if opts else 3
            if sel == 0:
                continue
            total += sel
            max_total += max_opt
    if max_total == 0:
        return 0, None
    pct = total / max_total
    return total, round(1.0 + pct * 6.0, 1)


def _draw_header_sep4(
    c: canvas.Canvas,
    style: PageStyle,
    data: Dict[str, Any],
    base_dir: str,
    *,
    show_info: bool,
) -> float:
    pw, ph = style.pagesize
    x0 = style.margin_left
    y_top = ph - style.margin_top

    img_dir = f"{base_dir}/app/static/img"
    codelco = f"{img_dir}/codelco.png"
    doa = f"{img_dir}/doa.png"

    draw_image_if_exists(c, codelco, x0, y_top - 1.05 * cm, 3.3 * cm, 0.95 * cm)
    draw_image_if_exists(c, doa, x0 + 3.6 * cm, y_top - 1.05 * cm, 3.3 * cm, 0.95 * cm)

    title = str(data.get("title") or FORM_TITLE)

    title_x_left = x0 + 7.2 * cm
    title_x_right = pw - style.margin_right
    avail_w = max(1.0, title_x_right - title_x_left)

    font_sizes = [13, 12, 11, 10]
    title_lines: List[str] = []
    chosen_size = font_sizes[-1]
    for fs in font_sizes:
        wrapped = wrap_text(title, style.font_bold, fs, avail_w)
        chosen_size = fs
        title_lines = wrapped
        if len(wrapped) <= 2:
            break

    if len(title_lines) > 2:
        title_lines = title_lines[:2]
        if title_lines[-1] and not title_lines[-1].endswith("…"):
            s = title_lines[-1].rstrip()
            title_lines[-1] = (s[:-1] + "…") if len(s) > 1 else (s + "…")

    c.setFont(style.font_bold, chosen_size)
    center_x = title_x_left + avail_w / 2.0
    y_title = y_top - 0.95 * cm
    line_step = chosen_size * 1.25

    for i, ln in enumerate(title_lines):
        c.drawCentredString(center_x, y_title - i * line_step, ln)

    fecha = _fmt_fecha(str(data.get("fecha") or ""))
    content_bottom = y_title - (len(title_lines) - 1) * line_step
    if fecha:
        c.setFont(style.font, 9)
        last_y = y_title - (len(title_lines) - 1) * line_step
        date_y = min(y_top - 1.45 * cm, last_y - 12)
        c.drawRightString(pw - style.margin_right, date_y, f"Fecha: {fecha}")
        content_bottom = min(content_bottom, date_y)

    sep_y = min(y_top - 2.05 * cm, content_bottom - 0.35 * cm)
    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(1)
    c.line(style.margin_left, sep_y, pw - style.margin_right, sep_y)

    y = sep_y - 0.40 * cm

    if not show_info:
        return y

    w = pw - style.margin_left - style.margin_right
    col_w = w / 3.0
    row_h = 0.95 * cm

    div = str(data.get("division") or "")
    sec = str(data.get("evaluador") or "")
    tur = str(data.get("turno") or "")
    ger = str(data.get("gerencia") or "")
    sup = str(data.get("superintendencia") or "")
    area = str(data.get("area") or "")

    labels_1 = [("DIVISIÓN", div), ("SECTOR", sec), ("TURNO", tur)]
    labels_2 = [("GERENCIA", ger), ("SUPERINTENDENCIA", sup), ("ÁREA", area)]

    def cell(ix: int, iy: int, label: str, value: str):
        cx = style.margin_left + ix * col_w
        cy = y - (iy + 1) * row_h
        draw_box(c, cx, cy, col_w, row_h, fill_color=WHITE, stroke=1)
        c.setFont(style.font_bold, 8.5)
        c.drawString(cx + 0.20 * cm, cy + row_h - 0.35 * cm, f"{label}:")
        draw_cell_text(
            c, cx, cy, col_w, row_h - 0.1 * cm, value,
            font_name=style.font, font_size=9, padding=0.20 * cm, valign="bottom",
        )

    for i, (lab, val) in enumerate(labels_1):
        cell(i, 0, lab, val)
    for i, (lab, val) in enumerate(labels_2):
        cell(i, 1, lab, val)

    return y - 2 * row_h - 0.45 * cm

def _draw_detenciones_block(c: canvas.Canvas, style: PageStyle, x: float, y: float, w: float, data: Dict[str, Any]) -> float:
    bar_h = 0.55 * cm
    draw_section_bar(c, x, y - bar_h, w, bar_h, "Detenciones")
    y = y - bar_h - 0.15 * cm

    col_w = w / 2.0
    row_h = 0.95 * cm
    labels_1 = [
        ("DETENCIONES REVISADAS", str(data.get("detenciones_revisadas") or "")),
        ("DETENCIONES CONCILIADAS", str(data.get("detenciones_conciliadas") or "")),
    ]
    labels_2 = [
        ("PENDIENTES DE ACUERDO", str(data.get("detenciones_pendientes") or "")),
        ("HORAS DE DETENCIÓN PENDIENTES DE CONCILIACIÓN", str(data.get("horas_detencion_pendientes") or "")),
    ]

    def cell(ix: int, iy: int, label: str, value: str):
        cx = x + ix * col_w
        cy = y - (iy + 1) * row_h
        draw_box(c, cx, cy, col_w, row_h, fill_color=WHITE, stroke=1)
        c.setFont(style.font_bold, 8.5)
        c.drawString(cx + 0.20 * cm, cy + row_h - 0.35 * cm, f"{label}:")
        draw_cell_text(
            c, cx, cy, col_w, row_h - 0.1 * cm, value,
            font_name=style.font, font_size=9, padding=0.20 * cm, valign="bottom",
        )

    for i, (lab, val) in enumerate(labels_1):
        cell(i, 0, lab, val)
    for i, (lab, val) in enumerate(labels_2):
        cell(i, 1, lab, val)

    return y - 2 * row_h - 0.35 * cm


def _measure_row_height(style: PageStyle, q: str, opts: List[str], col_w_question: float, col_w_opt: float) -> float:
    pad = 0.18 * cm
    q_font = 8.7
    opt_font = 7.6
    q_lead = q_font * 1.25
    o_lead = opt_font * 1.25

    q_lines = wrap_text(q, style.font, q_font, max(1.0, col_w_question - 2 * pad))
    o_lines_max = 1
    for t in opts:
        cb = 0.32 * cm
        gap = 0.10 * cm
        max_w = max(1.0, col_w_opt - cb - gap - 3 * pad)
        lines = wrap_text(t, style.font, opt_font, max_w)
        o_lines_max = max(o_lines_max, len(lines))

    h_q = len(q_lines) * q_lead + 2 * pad
    h_o = o_lines_max * o_lead + 2 * pad
    return max(1.10 * cm, h_q, h_o)


def _draw_table_header_sep4(c: canvas.Canvas, style: PageStyle, x: float, y_top: float, col_ws: List[float]) -> float:
    row_h = 0.80 * cm
    y = y_top - row_h

    cx = x
    for wd in col_ws:
        draw_box(c, cx, y, wd, row_h, fill_color=LIGHTGRAY, stroke=1)
        cx += wd

    headers = ["N°", "ITEM EVALUADO", "1 (Malo)", "2 (Regular)", "3 (Bueno)", "N/A", "Puntuación"]
    cx = x
    for i, htxt in enumerate(headers):
        draw_cell_text(
            c, cx, y, col_ws[i], row_h, htxt,
            font_name=style.font_bold, font_size=9, padding=0.18 * cm, valign="middle",
        )
        cx += col_ws[i]

    return y - 0.10 * cm


def render_conciliacion_sep4_pdf(c: canvas.Canvas, data: Dict[str, Any], base_dir: str) -> None:
    style = PageStyle()
    pw, _ph = style.pagesize

    x0 = style.margin_left
    w = pw - style.margin_left - style.margin_right

    col_ws = [0.70 * cm, 6.90 * cm, 2.20 * cm, 2.20 * cm, 2.20 * cm, 2.20 * cm, 1.60 * cm]

    def new_page(*, show_info: bool) -> float:
        c.showPage()
        return _draw_header_sep4(c, style, data, base_dir, show_info=show_info)

    y = _draw_header_sep4(c, style, data, base_dir, show_info=True)

    # --- Detenciones (datos para KPI) ---
    if y - 1.5 * cm < style.margin_bottom:
        y = new_page(show_info=False)
    y = _draw_detenciones_block(c, style, x0, y, w, data)

    # --- Secciones de evaluación (igual motor visual que 5S) ---
    sections = data.get("sections") or []
    for sec in sections:
        sec_name = str(sec.get("name") or "")
        items = list(sec.get("items") or [])

        min_needed = 0.60 * cm + 0.80 * cm + 1.20 * cm
        if y - min_needed < style.margin_bottom:
            y = new_page(show_info=False)

        bar_h = 0.55 * cm
        draw_section_bar(c, x0, y - bar_h, w, bar_h, sec_name)
        y = y - bar_h - 0.15 * cm

        y = _draw_table_header_sep4(c, style, x0, y, col_ws)

        subtotal = 0
        for idx, it in enumerate(items, start=1):
            q = str(it.get("question") or "")
            opts = it.get("options") or []
            opt_texts = [str(o.get("text") or "") for o in opts[:3]]

            sel = _as_int(it.get("selected"), 0)
            if sel not in (0, 1, 2, 3):
                sel = 0

            row_h = _measure_row_height(style, q, opt_texts, col_ws[1], col_ws[2])
            if y - row_h < style.margin_bottom:
                y = new_page(show_info=False)
                draw_section_bar(c, x0, y - bar_h, w, bar_h, sec_name)
                y = y - bar_h - 0.15 * cm
                y = _draw_table_header_sep4(c, style, x0, y, col_ws)

            y_row = y - row_h
            draw_table_grid(c, x0, y_row, col_ws, [row_h], stroke=1)

            draw_cell_text(
                c, x0, y_row, col_ws[0], row_h, str(idx),
                font_name=style.font_bold, font_size=9, padding=0.18 * cm, valign="middle",
            )
            draw_cell_text(
                c, x0 + col_ws[0], y_row, col_ws[1], row_h, q,
                font_name=style.font, font_size=8.7, padding=0.18 * cm, valign="middle",
            )

            for j in range(3):
                cell_x = x0 + col_ws[0] + col_ws[1] + j * col_ws[2]
                txt = opt_texts[j] if j < len(opt_texts) else ""

                cb = 0.32 * cm
                cb_x = cell_x + 0.18 * cm
                cb_y = y_row + row_h - cb - 0.22 * cm
                draw_checkbox(c, cb_x, cb_y, size=cb, checked=(sel == (j + 1)))

                left = 0.18 * cm + cb + 0.10 * cm
                draw_cell_text(
                    c, cell_x + left, y_row, col_ws[2] - left, row_h, txt,
                    font_name=style.font, font_size=7.6, padding=0.18 * cm, valign="top",
                )

            cell_x_na = x0 + col_ws[0] + col_ws[1] + 3 * col_ws[2]
            cb = 0.32 * cm
            cb_x = cell_x_na + 0.18 * cm
            cb_y = y_row + row_h - cb - 0.22 * cm
            draw_checkbox(c, cb_x, cb_y, size=cb, checked=(sel == 0))

            pts = sel
            draw_cell_text(
                c, x0 + sum(col_ws[:-1]), y_row, col_ws[-1], row_h, str(pts),
                font_name=style.font_bold, font_size=10, padding=0.18 * cm, valign="middle",
            )

            subtotal += pts
            y = y_row

        sub_h = 0.75 * cm
        if y - sub_h < style.margin_bottom:
            y = new_page(show_info=False)
            draw_section_bar(c, x0, y - bar_h, w, bar_h, sec_name)
            y = y - bar_h - 0.15 * cm
            y = _draw_table_header_sep4(c, style, x0, y, col_ws)

        y_sub = y - sub_h
        draw_table_grid(c, x0, y_sub, col_ws, [sub_h], stroke=1)
        draw_cell_text(
            c, x0 + col_ws[0] + col_ws[1] + 3 * col_ws[2], y_sub, col_ws[5], sub_h, "Sub-total",
            font_name=style.font_bold, font_size=9, padding=0.18 * cm, valign="middle",
        )
        draw_cell_text(
            c, x0 + sum(col_ws[:-1]), y_sub, col_ws[-1], sub_h, str(subtotal),
            font_name=style.font_bold, font_size=10, padding=0.18 * cm, valign="middle",
        )

        y = y_sub - 0.25 * cm

    # --- Feedback + Nota (con clasificación de calidad) ---
    suma, nota = _calc_score_sep4(sections)
    calidad = _nota_calidad(nota)

    fb = data.get("feedback") or {}
    fortalezas = str(fb.get("fortalezas", "") or "")
    oportunidades = str(fb.get("oportunidades", "") or "")
    plan = str(fb.get("plan", "") or "")

    need_fb = measure_feedback_block_height(w, fortalezas, oportunidades, plan)
    if y - need_fb < style.margin_bottom:
        y = new_page(show_info=False)
    y = draw_feedback_block(
        c, x0, y, w,
        fortalezas=fortalezas, oportunidades=oportunidades, plan=plan,
        suma=suma, nota=nota,
    )

    if calidad:
        if y - 0.6 * cm < style.margin_bottom:
            y = new_page(show_info=False)
        c.setFont(style.font_bold, 9)
        c.drawRightString(pw - style.margin_right, y - 0.20 * cm, f"Calidad de la reunión: {calidad}")
        y -= 0.60 * cm

    # --- Compromisos ---
    commitments = data.get("commitments") or []
    if commitments:
        if y - 5.0 * cm < style.margin_bottom:
            y = new_page(show_info=False)
        y = draw_commitments_table(c, x0, y, w, commitments)

    # --- Participantes ---
    participants = data.get("participants") or []
    if participants:
        if y - 4.0 * cm < style.margin_bottom:
            y = new_page(show_info=False)
        y = draw_participants_table(c, x0, y, w, participants)