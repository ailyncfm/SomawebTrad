# app/pdf/components.py
from __future__ import annotations

import os
from typing import Dict, Any, List, Optional

from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics

from app.pdf.base_layout import (
    PageStyle,
    draw_section_bar,
    ORANGE,
    ORANGE_SOFT_BG,
    TEXT_DARK,
    MUTED,
    BORDER_LIGHT,
    TABLE_HEADER_BG,
    DEFAULT_RADIUS,
)


def _set_stroke(c, stroke_color=BORDER_LIGHT, line_width: float = 1.0):
    c.setStrokeColor(stroke_color)
    c.setLineWidth(line_width)


def draw_box(
    c,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill_color=None,
    stroke: int = 1,
    stroke_color=BORDER_LIGHT,
    line_width: float = 1.0,
    radius: float = DEFAULT_RADIUS,
):
    c.saveState()
    _set_stroke(c, stroke_color=stroke_color, line_width=line_width)
    if fill_color is None:
        c.setFillColor(colors.white)
        if radius > 0:
            c.roundRect(x, y, w, h, radius, stroke=stroke, fill=0)
        else:
            c.rect(x, y, w, h, stroke=stroke, fill=0)
    else:
        c.setFillColor(fill_color)
        if radius > 0:
            c.roundRect(x, y, w, h, radius, stroke=stroke, fill=1)
        else:
            c.rect(x, y, w, h, stroke=stroke, fill=1)
    c.restoreState()


def draw_image_if_exists(c, path: str, x: float, y: float, w: float, h: float):
    if not path or not os.path.isfile(path):
        return
    c.saveState()
    c.drawImage(path, x, y, width=w, height=h, preserveAspectRatio=True, mask="auto")
    c.restoreState()


def _wrap_text_lines(text: str, font_name: str, font_size: float, max_width: float) -> List[str]:
    text = (text or "").strip()
    if not text:
        return [""]

    def w(s: str) -> float:
        return pdfmetrics.stringWidth(s, font_name, font_size)

    words = text.split()
    lines: List[str] = []
    cur = ""
    for word in words:
        tentative = (cur + " " + word).strip() if cur else word
        if w(tentative) <= max_width:
            cur = tentative
            continue
        if cur:
            lines.append(cur)
            cur = ""
        if w(word) <= max_width:
            cur = word
            continue
        chunk = ""
        for ch in word:
            t2 = chunk + ch
            if w(t2) <= max_width:
                chunk = t2
            else:
                if chunk:
                    lines.append(chunk)
                chunk = ch
        if chunk:
            cur = chunk
    if cur:
        lines.append(cur)
    return lines


def _draw_wrapped_text_block(
    c,
    x: float,
    y: float,
    w: float,
    h: float,
    lines: List[str],
    *,
    font_name: str,
    font_size: float,
    leading: float,
    align: str = "left",
    valign: str = "top",
    pad: float = 0.18 * cm,
):
    c.saveState()
    c.setFont(font_name, font_size)
    block_h = max(1, len(lines)) * leading
    if valign == "middle":
        y_top = y + (h + block_h) / 2.0
    else:
        y_top = y + h - pad
    y_cursor = y_top - font_size
    for line in lines:
        if align == "center":
            lw = pdfmetrics.stringWidth(line, font_name, font_size)
            x_line = x + pad + max(0.0, (w - 2 * pad - lw) / 2.0)
        else:
            x_line = x + pad
        c.drawString(x_line, y_cursor, line)
        y_cursor -= leading
        if y_cursor < (y + pad - font_size):
            break
    c.restoreState()


# =========================
# HEADER
# =========================

def draw_header(
    c,
    style: PageStyle,
    title: str,
    fecha: str,
    hora: str,
    area: str,
    logo_dir: str,
    show_meta: bool = True,
) -> float:
    """
    show_meta=True  -> dibuja logos + titulo + fila Fecha/Hora/Area (solo primera pagina)
    show_meta=False -> dibuja solo logos + titulo (paginas siguientes), mas compacto
    """
    pw, ph = style.pagesize
    x0 = style.margin_left
    content_w = pw - style.margin_left - style.margin_right
    y_top = ph - style.margin_top

    logo_h = 0.95 * cm
    codelco = os.path.join(logo_dir, "codelco.png")
    doa = os.path.join(logo_dir, "doa.png")
    draw_image_if_exists(c, codelco, x0, y_top - logo_h, 3.3 * cm, logo_h)
    draw_image_if_exists(c, doa, x0 + 3.6 * cm, y_top - logo_h, 3.3 * cm, logo_h)

    # Titulo: centrado en TODO el ancho de contenido (debajo de los logos)
    font_sizes = [14, 13, 12, 11]
    avail_w = content_w - 1.0 * cm
    title_lines: List[str] = []
    chosen_size = font_sizes[-1]
    for fs in font_sizes:
        wrapped = _wrap_text_lines(title, style.font_bold, fs, avail_w)
        chosen_size = fs
        title_lines = wrapped
        if len(wrapped) <= 2:
            break
    if len(title_lines) > 2:
        title_lines = title_lines[:2]
        if title_lines[-1] and not title_lines[-1].endswith("…"):
            s = title_lines[-1].rstrip()
            title_lines[-1] = (s[:-1] + "…") if len(s) > 1 else (s + "…")

    c.saveState()
    c.setFillColor(TEXT_DARK)
    c.setFont(style.font_bold, chosen_size)
    center_x = x0 + content_w / 2.0
    y_title = y_top - logo_h - 0.55 * cm
    line_step = chosen_size * 1.25
    for i, ln in enumerate(title_lines):
        c.drawCentredString(center_x, y_title - i * line_step, ln)
    c.restoreState()

    extra_down = max(0.0, (len(title_lines) - 1) * line_step)
    y = y_title - extra_down - 0.35 * cm

    if not show_meta:
        c.setStrokeColor(BORDER_LIGHT)
        c.setLineWidth(1)
        c.line(x0, y, pw - style.margin_right, y)
        return y - 0.45 * cm

    # Fecha | Hora | Area (solo primera pagina)
    gap = 0.3 * cm
    col_w = (content_w - 2 * gap) / 3.0
    box_h = 0.75 * cm
    cy_label = y - 0.10 * cm
    cy_box = cy_label - 0.4 * cm - box_h

    for i, (lab, val) in enumerate([("Fecha", fecha), ("Hora", hora), ("Área", area)]):
        cx = x0 + i * (col_w + gap)
        c.setFillColor(MUTED)
        c.setFont(style.font_bold, 9)
        c.drawString(cx, cy_label - 0.30 * cm, lab)
        draw_box(c, cx, cy_box, col_w, box_h)
        c.setFillColor(TEXT_DARK)
        c.setFont(style.font, 9)
        c.drawString(cx + 0.15 * cm, cy_box + 0.25 * cm, str(val or ""))

    return cy_box - 0.4 * cm


# =========================
# OBSERVADORES (con barra naranja, sin Id, "Cargo" en vez de "Denominación posición")
# =========================

def draw_observer_block(c, x: float, y_top: float, w: float, observer: Dict[str, Any], idx: int) -> float:
    style = PageStyle()
    bar_h = 0.55 * cm
    y_bar = y_top - bar_h
    draw_section_bar(c, x, y_bar, w, bar_h, f"Observador {idx}")
    y_top = y_bar - 0.2 * cm

    row_h = 0.75 * cm
    pad = 0.15 * cm
    col1_w = w * 0.52
    col2_w = w - col1_w

    rows = [
        ("Nombre", "nombre", "Gerencia", "gerencia"),
        ("Superintendencia", "superintendencia", "SAP", "sap"),
        ("E-mail", "email", "Cargo", "posicion"),
    ]
    for (l1, k1, l2, k2) in rows:
        y = y_top - row_h
        c.setFillColor(MUTED)
        c.setFont(style.font, 9)
        c.drawString(x + pad, y + 0.25 * cm, l1)
        draw_box(c, x + 3.5 * cm, y + 0.12 * cm, col1_w - 3.7 * cm, row_h - 0.22 * cm)
        val1 = str(observer.get(k1, "") or "")
        c.setFillColor(TEXT_DARK)
        c.drawString(x + 3.65 * cm, y + 0.25 * cm, val1)

        c.setFillColor(MUTED)
        c.drawString(x + col1_w + pad, y + 0.25 * cm, l2)
        draw_box(c, x + col1_w + 3.8 * cm, y + 0.12 * cm, col2_w - 4.0 * cm, row_h - 0.22 * cm)
        val2 = str(observer.get(k2, "") or "")
        c.setFillColor(TEXT_DARK)
        c.drawString(x + col1_w + 3.95 * cm, y + 0.25 * cm, val2)
        y_top = y
    return y_top - 0.25 * cm


def draw_area_row(c, x: float, y_top: float, w: float, area: str) -> float:
    """Se mantiene por compatibilidad, pero ya no se usa: el area ahora va en el header."""
    style = PageStyle()
    row_h = 0.75 * cm
    pad = 0.15 * cm
    y = y_top - row_h
    c.setFillColor(MUTED)
    c.setFont(style.font, 9)
    c.drawString(x + pad, y + 0.25 * cm, "Área")
    draw_box(c, x + 1.0 * cm, y + 0.12 * cm, w - 1.0 * cm, row_h - 0.22 * cm)
    c.setFillColor(TEXT_DARK)
    c.drawString(x + 1.15 * cm, y + 0.25 * cm, area or "")
    return y - 0.35 * cm


def draw_scale_row(c, x: float, y_top: float, w: float) -> float:
    style = PageStyle()
    row_h = 0.75 * cm
    q_w = w * 0.40
    opt_w = (w - q_w) / 3.0
    y = y_top - row_h
    draw_box(c, x, y, q_w, row_h, fill_color=TABLE_HEADER_BG, stroke=1, radius=0)
    for i in range(3):
        draw_box(c, x + q_w + i * opt_w, y, opt_w, row_h, fill_color=TABLE_HEADER_BG, stroke=1, radius=0)
    c.setFillColor(MUTED)
    c.setFont(style.font_bold, 9)
    c.drawString(x + 0.3 * cm, y + row_h / 2.0 - 3, "Pregunta / Nota")
    for i, lab in enumerate(["1", "2", "3"]):
        cell_x = x + q_w + i * opt_w
        lw = pdfmetrics.stringWidth(lab, style.font_bold, 9)
        c.drawString(cell_x + (opt_w - lw) / 2.0, y + row_h / 2.0 - 3, lab)
    return y - 0.15 * cm


# =========================
# EVALUATION ROW (compacta, sin checkbox: celda seleccionada se colorea)
# =========================

def measure_eval_item_row_height(
    c,
    total_w: float,
    question: str,
    options: List[str],
    *,
    min_h: float = 0.85 * cm,
    q_ratio: float = 0.40,
    q_font_size: float = 8.0,
    opt_font_size: float = 7.5,
    leading_mult: float = 1.15,
) -> float:
    style = PageStyle()
    q_w = total_w * q_ratio
    opt_w = (total_w - q_w) / 3.0
    pad = 0.14 * cm

    q_lines = _wrap_text_lines(question, style.font_bold, q_font_size, max(1.0, q_w - 2 * pad))
    q_leading = q_font_size * leading_mult
    q_h = pad + max(1, len(q_lines)) * q_leading + pad

    opt_leading = opt_font_size * leading_mult
    opt_max_h = 0.0
    for opt in (options or [])[:3]:
        avail = max(1.0, opt_w - 2 * pad)
        lines = _wrap_text_lines(opt, style.font, opt_font_size, avail)
        h = pad + max(1, len(lines)) * opt_leading + pad
        opt_max_h = max(opt_max_h, h)

    return max(min_h, q_h, opt_max_h)


def draw_eval_item_row(
    c,
    x: float,
    y_top: float,
    w: float,
    *,
    question: str,
    options: List[str],
    selected: int,
    row_h: Optional[float] = None,
) -> float:
    style = PageStyle()
    q_ratio = 0.40
    q_w = w * q_ratio
    opt_w = (w - q_w) / 3.0
    if row_h is None:
        row_h = measure_eval_item_row_height(c, w, question, options)
    y = y_top - row_h
    pad = 0.14 * cm
    q_font_size = 8.0
    opt_font_size = 7.5
    leading_mult = 1.15
    q_leading = q_font_size * leading_mult
    opt_leading = opt_font_size * leading_mult

    draw_box(c, x, y, q_w, row_h, fill_color=colors.white, stroke=1, radius=0)
    c.setFillColor(TEXT_DARK)
    q_lines = _wrap_text_lines(question, style.font_bold, q_font_size, max(1.0, q_w - 2 * pad))
    _draw_wrapped_text_block(
        c, x, y, q_w, row_h, q_lines,
        font_name=style.font_bold, font_size=q_font_size, leading=q_leading,
        align="left", valign="middle", pad=pad
    )

    for i, opt in enumerate((options or [])[:3]):
        cell_x = x + q_w + i * opt_w
        checked = (i + 1) == int(selected)
        if checked:
            draw_box(c, cell_x, y, opt_w, row_h, fill_color=ORANGE_SOFT_BG, stroke=1, stroke_color=ORANGE, radius=0)
        else:
            draw_box(c, cell_x, y, opt_w, row_h, fill_color=colors.white, stroke=1, radius=0)

        avail_w = max(1.0, opt_w - 2 * pad)
        lines = _wrap_text_lines(opt, style.font, opt_font_size, avail_w)
        c.setFillColor(ORANGE if checked else TEXT_DARK)
        _draw_wrapped_text_block(
            c, cell_x, y, opt_w, row_h, lines,
            font_name=style.font_bold if checked else style.font,
            font_size=opt_font_size, leading=opt_leading,
            align="left", valign="middle", pad=pad
        )
    return y


# =========================
# FEEDBACK (sin cambios de layout, solo paleta ya aplicada antes)
# =========================

def measure_feedback_block_height(w: float, fortalezas: str, oportunidades: str, plan: str) -> float:
    style = PageStyle()
    left_w = w * 0.78
    label_w = left_w * 0.33
    value_w = left_w - label_w
    base_row = 0.95 * cm
    pad = 0.18 * cm
    f_lines = _wrap_text_lines(fortalezas, style.font, 9.0, max(1.0, value_w - 2 * pad))
    o_lines = _wrap_text_lines(oportunidades, style.font, 9.0, max(1.0, value_w - 2 * pad))
    f_h = max(base_row, (len(f_lines) * 10.0) + 2 * pad)
    o_h = max(base_row, (len(o_lines) * 10.0) + 2 * pad)
    plan_lines = _wrap_text_lines(plan, style.font, 9.0, max(1.0, value_w - 2 * pad))
    plan_leading = 9.0 * 1.15
    plan_h = max(3.1 * cm, (len(plan_lines) * plan_leading) + 2 * pad)
    bar_h = 0.6 * cm
    return bar_h + f_h + o_h + plan_h + 0.25 * cm


def draw_feedback_block(
    c,
    x: float,
    y_top: float,
    w: float,
    *,
    fortalezas: str,
    oportunidades: str,
    plan: str,
    suma: float,
    nota: float,
) -> float:
    style = PageStyle()
    bar_h = 0.6 * cm
    y_bar = y_top - bar_h
    draw_section_bar(c, x, y_bar, w, bar_h, "Feedback")
    y_top = y_bar - 0.18 * cm

    left_w = w * 0.78
    right_w = w - left_w
    label_w = left_w * 0.33
    value_w = left_w - label_w
    base_row = 0.95 * cm
    pad = 0.18 * cm

    f_lines = _wrap_text_lines(fortalezas, style.font, 9.0, max(1.0, value_w - 2 * pad))
    o_lines = _wrap_text_lines(oportunidades, style.font, 9.0, max(1.0, value_w - 2 * pad))
    f_h = max(base_row, (len(f_lines) * (9.0 * 1.15)) + 2 * pad)
    o_h = max(base_row, (len(o_lines) * (9.0 * 1.15)) + 2 * pad)
    plan_lines = _wrap_text_lines(plan, style.font, 9.0, max(1.0, value_w - 2 * pad))
    plan_leading = 9.0 * 1.15
    plan_h = max(3.1 * cm, (len(plan_lines) * plan_leading) + 2 * pad)

    y = y_top - f_h
    draw_box(c, x, y, label_w, f_h, fill_color=TABLE_HEADER_BG, stroke=1)
    draw_box(c, x + label_w, y, value_w, f_h, fill_color=colors.white, stroke=1)
    c.setFillColor(MUTED)
    c.setFont(style.font_bold, 9)
    c.drawString(x + 0.2 * cm, y + f_h - 0.55 * cm, "Fortalezas de la reunión:")
    c.setFillColor(TEXT_DARK)
    _draw_wrapped_text_block(
        c, x + label_w, y, value_w, f_h, f_lines,
        font_name=style.font, font_size=9.0, leading=9.0 * 1.15,
        align="left", valign="middle", pad=pad
    )

    score_x = x + left_w
    score_top = y_top
    score_cell_h = base_row

    y_score1 = score_top - score_cell_h
    draw_box(c, score_x, y_score1, right_w, score_cell_h, fill_color=TABLE_HEADER_BG, stroke=1)
    c.setFillColor(MUTED)
    c.setFont(style.font_bold, 9)
    c.drawString(score_x + 0.2 * cm, y_score1 + 0.28 * cm, "Suma del puntaje")

    y_score1v = y_score1 - score_cell_h
    draw_box(c, score_x, y_score1v, right_w, score_cell_h, fill_color=colors.white, stroke=1)
    c.setFillColor(ORANGE)
    c.setFont(style.font_bold, 11)
    c.drawString(score_x + 0.25 * cm, y_score1v + 0.28 * cm, f"{float(suma):.1f}")

    y_score2 = y_score1v - score_cell_h
    draw_box(c, score_x, y_score2, right_w, score_cell_h, fill_color=TABLE_HEADER_BG, stroke=1)
    c.setFillColor(MUTED)
    c.setFont(style.font_bold, 9)
    c.drawString(score_x + 0.2 * cm, y_score2 + 0.28 * cm, "Nota")

    y_score2v = y_score2 - score_cell_h
    draw_box(c, score_x, y_score2v, right_w, score_cell_h, fill_color=colors.white, stroke=1)
    c.setFillColor(ORANGE)
    c.setFont(style.font_bold, 11)
    c.drawString(score_x + 0.25 * cm, y_score2v + 0.28 * cm, f"{nota:.1f}")

    y2 = y - o_h
    draw_box(c, x, y2, label_w, o_h, fill_color=TABLE_HEADER_BG, stroke=1)
    draw_box(c, x + label_w, y2, value_w, o_h, fill_color=colors.white, stroke=1)
    c.setFillColor(MUTED)
    c.setFont(style.font_bold, 9)
    c.drawString(x + 0.2 * cm, y2 + o_h - 0.55 * cm, "Oportunidades de la reunión:")
    c.setFillColor(TEXT_DARK)
    _draw_wrapped_text_block(
        c, x + label_w, y2, value_w, o_h, o_lines,
        font_name=style.font, font_size=9.0, leading=9.0 * 1.15,
        align="left", valign="middle", pad=pad
    )

    y3 = y2 - plan_h
    draw_box(c, x, y3, label_w, plan_h, fill_color=TABLE_HEADER_BG, stroke=1)
    draw_box(c, x + label_w, y3, value_w, plan_h, fill_color=colors.white, stroke=1)
    c.setFillColor(MUTED)
    c.setFont(style.font_bold, 9)
    c.drawString(x + 0.2 * cm, y3 + plan_h - 0.55 * cm, "Plan")
    c.setFillColor(TEXT_DARK)
    _draw_wrapped_text_block(
        c, x + label_w, y3, value_w, plan_h, plan_lines,
        font_name=style.font, font_size=9.0, leading=plan_leading,
        align="left", valign="top", pad=pad
    )
    return y3 - 0.35 * cm


# =========================
# Tablas finales (titulos ahora en caja naranja, igual que las demas secciones)
# =========================

def draw_commitments_table(c, x: float, y_top: float, w: float, commitments: List[Dict[str, Any]]) -> float:
    style = PageStyle()
    bar_h = 0.55 * cm
    y_bar = y_top - bar_h
    draw_section_bar(c, x, y_bar, w, bar_h, "Compromisos")
    y_top = y_bar - 0.2 * cm

    header_h = 0.9 * cm
    row_h = 1.05 * cm
    cols = [
        ("Acción propuesta", 0.36),
        ("Responsable", 0.16),
        ("Fecha\nCompromiso", 0.12),
        ("Estado de la\nacción", 0.16),
        ("Evidencia de\ncierre", 0.20),
    ]
    xs = [x]
    for _, r in cols:
        xs.append(xs[-1] + w * r)

    y = y_top - header_h
    for i, (name, _) in enumerate(cols):
        draw_box(c, xs[i], y, xs[i + 1] - xs[i], header_h, fill_color=TABLE_HEADER_BG, stroke=1, radius=0)
        c.setFillColor(MUTED)
        c.setFont(style.font_bold, 9)
        _draw_wrapped_text_block(
            c, xs[i], y, xs[i + 1] - xs[i], header_h,
            _wrap_text_lines(name, style.font_bold, 9, (xs[i + 1] - xs[i]) - 0.3 * cm),
            font_name=style.font_bold, font_size=9, leading=10,
            align="center", valign="middle", pad=0.0
        )
    y_top = y

    for row in commitments:
        y = y_top - row_h
        vals = [
            str(row.get("accion", "") or ""),
            str(row.get("responsable", "") or ""),
            str(row.get("fecha", "") or ""),
            str(row.get("estado", "") or ""),
            str(row.get("evidencia", "") or ""),
        ]
        for i, v in enumerate(vals):
            draw_box(c, xs[i], y, xs[i + 1] - xs[i], row_h, fill_color=colors.white, stroke=1, radius=0)
            c.setFillColor(TEXT_DARK)
            _draw_wrapped_text_block(
                c, xs[i], y, xs[i + 1] - xs[i], row_h,
                _wrap_text_lines(v, style.font, 9, (xs[i + 1] - xs[i]) - 0.35 * cm),
                font_name=style.font, font_size=9, leading=10,
                align="left", valign="middle", pad=0.18 * cm
            )
        y_top = y
    return y_top - 0.45 * cm


def draw_participants_table(c, x: float, y_top: float, w: float, participants: List[Dict[str, Any]]) -> float:
    style = PageStyle()
    bar_h = 0.55 * cm
    y_bar = y_top - bar_h
    draw_section_bar(c, x, y_bar, w, bar_h, "Participantes")
    y_top = y_bar - 0.2 * cm

    header_h = 0.9 * cm
    row_h = 0.9 * cm
    cols = [
        ("Área", 0.22),
        ("Responsable", 0.38),
        ("Asistencia", 0.20),
        ("Conformidad", 0.20),
    ]
    xs = [x]
    for _, r in cols:
        xs.append(xs[-1] + w * r)

    y = y_top - header_h
    for i, (name, _) in enumerate(cols):
        draw_box(c, xs[i], y, xs[i + 1] - xs[i], header_h, fill_color=TABLE_HEADER_BG, stroke=1, radius=0)
        c.setFillColor(MUTED)
        c.setFont(style.font_bold, 9)
        _draw_wrapped_text_block(
            c, xs[i], y, xs[i + 1] - xs[i], header_h, [name],
            font_name=style.font_bold, font_size=9, leading=10,
            align="center", valign="middle", pad=0.1 * cm
        )
    y_top = y

    for p in participants:
        y = y_top - row_h
        for i in range(4):
            draw_box(c, xs[i], y, xs[i + 1] - xs[i], row_h, fill_color=colors.white, stroke=1, radius=0)

        c.setFillColor(TEXT_DARK)
        _draw_wrapped_text_block(
            c, xs[0], y, xs[1] - xs[0], row_h,
            _wrap_text_lines(str(p.get("area", "") or ""), style.font, 9, (xs[1] - xs[0]) - 0.3 * cm),
            font_name=style.font, font_size=9, leading=10,
            align="left", valign="middle", pad=0.15 * cm
        )
        _draw_wrapped_text_block(
            c, xs[1], y, xs[2] - xs[1], row_h,
            _wrap_text_lines(str(p.get("responsable", "") or ""), style.font, 9, (xs[2] - xs[1]) - 0.3 * cm),
            font_name=style.font, font_size=9, leading=10,
            align="left", valign="middle", pad=0.15 * cm
        )

        asistencia_text = "SI" if p.get("si") else ("NO" if p.get("no") else "—")

        conforme = p.get("conforme")
        if p.get("no"):
            # No asistió -> Conforme quedó bloqueado en el formulario
            conformidad_text = "Sin información"
        elif conforme is True:
            conformidad_text = "SI"
        elif conforme is False:
            conformidad_text = "NO"
        else:
            # Fila vacia, o asistio "Si" pero sin responder conformidad
            conformidad_text = "—"

        c.setFont(style.font_bold, 9)
        c.setFillColor(TEXT_DARK)
        _draw_wrapped_text_block(
            c, xs[2], y, xs[3] - xs[2], row_h, [asistencia_text],
            font_name=style.font_bold, font_size=9, leading=10,
            align="center", valign="middle", pad=0.1 * cm
        )
        _draw_wrapped_text_block(
            c, xs[3], y, xs[4] - xs[3], row_h,
            _wrap_text_lines(conformidad_text, style.font_bold, 9, (xs[4] - xs[3]) - 0.2 * cm),
            font_name=style.font_bold, font_size=9, leading=10,
            align="center", valign="middle", pad=0.1 * cm
        )

        y_top = y
    return y_top - 0.2 * cm


# =========================
# CHECKLIST DE SEGURIDAD (titulo en caja naranja, igual que las demas secciones)
# =========================

def measure_checklist_row_height(
    c,
    w: float,
    question: str,
    comentario: str,
    *,
    min_h: float = 0.9 * cm,
    num_w: float = 0.9 * cm,
    req_ratio: float = 0.42,
    si_w: float = 1.3 * cm,
    no_w: float = 1.3 * cm,
    font_size: float = 8.5,
    leading_mult: float = 1.15,
) -> float:
    style = PageStyle()
    req_w = w * req_ratio
    comment_w = w - num_w - req_w - si_w - no_w
    pad = 0.15 * cm
    req_lines = _wrap_text_lines(question, style.font, font_size, max(1.0, req_w - 2 * pad))
    com_lines = _wrap_text_lines(comentario or "", style.font, font_size, max(1.0, comment_w - 2 * pad))
    leading = font_size * leading_mult
    req_h = pad * 2 + max(1, len(req_lines)) * leading
    com_h = pad * 2 + max(1, len(com_lines)) * leading
    return max(min_h, req_h, com_h)


def measure_checklist_table_height(c, w: float, items: List[Dict[str, Any]]) -> float:
    total = 0.55 * cm + 0.2 * cm + 0.8 * cm  # barra + gap + header
    for item in items:
        total += measure_checklist_row_height(
            c, w, item.get("question", ""), item.get("comentario", "")
        )
    return total + 0.3 * cm


def draw_checklist_table(c, x: float, y_top: float, w: float, items: List[Dict[str, Any]]) -> float:
    style = PageStyle()
    bar_h = 0.55 * cm
    y_bar = y_top - bar_h
    draw_section_bar(c, x, y_bar, w, bar_h, "Checklist de seguridad")
    y_top = y_bar - 0.2 * cm

    num_w = 0.9 * cm
    req_w = w * 0.42
    si_w = 1.3 * cm
    no_w = 1.3 * cm
    comment_w = w - num_w - req_w - si_w - no_w

    xs = [x]
    for width in [num_w, req_w, si_w, no_w, comment_w]:
        xs.append(xs[-1] + width)

    header_h = 0.8 * cm
    y = y_top - header_h
    headers = ["N°", "Requisito", "SI", "NO", "Comentario"]
    for i, name in enumerate(headers):
        draw_box(c, xs[i], y, xs[i + 1] - xs[i], header_h, fill_color=TABLE_HEADER_BG, stroke=1, radius=0)
        c.setFillColor(MUTED)
        c.setFont(style.font_bold, 9)
        _draw_wrapped_text_block(
            c, xs[i], y, xs[i + 1] - xs[i], header_h, [name],
            font_name=style.font_bold, font_size=9, leading=10,
            align="center", valign="middle", pad=0.1 * cm
        )
    y_top = y

    for idx, item in enumerate(items, start=1):
        question = item.get("question", "")
        comentario = item.get("comentario", "")
        row_h = measure_checklist_row_height(c, w, question, comentario)
        y = y_top - row_h

        for i in range(5):
            draw_box(c, xs[i], y, xs[i + 1] - xs[i], row_h, fill_color=colors.white, stroke=1, radius=0)

        c.setFillColor(TEXT_DARK)
        _draw_wrapped_text_block(
            c, xs[0], y, xs[1] - xs[0], row_h, [str(idx)],
            font_name=style.font_bold, font_size=9, leading=10,
            align="center", valign="middle", pad=0.0
        )

        req_lines = _wrap_text_lines(question, style.font, 8.5, max(1.0, (xs[2] - xs[1]) - 0.3 * cm))
        _draw_wrapped_text_block(
            c, xs[1], y, xs[2] - xs[1], row_h, req_lines,
            font_name=style.font, font_size=8.5, leading=8.5 * 1.15,
            align="left", valign="middle", pad=0.15 * cm
        )

        cb = 0.32 * cm
        for j, key in enumerate(["si", "no"]):
            cell_x = xs[2 + j]
            cell_w = xs[3 + j] - cell_x
            cb_x = cell_x + cell_w / 2.0 - cb / 2.0
            cb_y = y + row_h / 2.0 - cb / 2.0
            checked = bool(item.get(key))
            c.saveState()
            c.setStrokeColor(ORANGE if checked else BORDER_LIGHT)
            c.setLineWidth(1.0)
            radius = min(2.0, cb / 3.0)
            c.roundRect(cb_x, cb_y, cb, cb, radius, stroke=1, fill=0)
            if checked:
                c.setStrokeColor(ORANGE)
                c.setLineWidth(1.3)
                c.line(cb_x + cb * 0.18, cb_y + cb * 0.55, cb_x + cb * 0.42, cb_y + cb * 0.25)
                c.line(cb_x + cb * 0.42, cb_y + cb * 0.25, cb_x + cb * 0.82, cb_y + cb * 0.78)
            c.restoreState()

        com_lines = _wrap_text_lines(comentario, style.font, 8.5, max(1.0, (xs[5] - xs[4]) - 0.3 * cm))
        c.setFillColor(TEXT_DARK)
        _draw_wrapped_text_block(
            c, xs[4], y, xs[5] - xs[4], row_h, com_lines,
            font_name=style.font, font_size=8.5, leading=8.5 * 1.15,
            align="left", valign="middle", pad=0.15 * cm
        )
        y_top = y

    return y_top - 0.3 * cm


def draw_labeled_text_box(c, x: float, y_top: float, w: float, label: str, text: str) -> float:
    style = PageStyle()
    pad = 0.18 * cm
    lines = _wrap_text_lines(text, style.font, 9.0, max(1.0, w - 2 * pad))
    leading = 9.0 * 1.15
    box_h = max(0.9 * cm, pad * 2 + (len(lines) + 1) * leading)
    y = y_top - box_h
    draw_box(c, x, y, w, box_h, fill_color=colors.white, stroke=1)
    c.setFillColor(MUTED)
    c.setFont(style.font_bold, 9)
    c.drawString(x + pad, y + box_h - 0.35 * cm, label)
    c.setFillColor(TEXT_DARK)
    _draw_wrapped_text_block(
        c, x, y, w, box_h - leading, lines,
        font_name=style.font, font_size=9.0, leading=leading,
        align="left", valign="top", pad=pad
    )
    return y - 0.3 * cm