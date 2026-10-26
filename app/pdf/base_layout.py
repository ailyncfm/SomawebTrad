# app/pdf/base_layout.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Tuple, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth


def hex_to_color(hex_code: str) -> colors.Color:
    """Convierte un color hex (#RRGGBB) a reportlab.lib.colors.Color (0-1)."""
    h = hex_code.lstrip("#")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return colors.Color(r, g, b)


# ===== Paleta (igual que las variables --primary, --border, --muted de app.css) =====
ORANGE = hex_to_color("#F97316")          # --primary (barra naranjo, acentos)
ORANGE_SOFT_BG = hex_to_color("#FFF7ED")  # fondo de .section-bar en la web
TEXT_DARK = hex_to_color("#111827")       # --text
MUTED = hex_to_color("#6B7280")           # --muted
BORDER_LIGHT = hex_to_color("#E5E7EB")    # --border
TABLE_HEADER_BG = hex_to_color("#F9FAFB") # fondo de <th> en la web

DARKGRAY = colors.Color(0.25, 0.25, 0.25)
LIGHTGRAY = colors.Color(0.92, 0.92, 0.92)
BLACK = colors.black
WHITE = colors.white

# Radio de esquinas por defecto para cajas tipo "input" (equivalente visual
# al border-radius:12px de los inputs web, escalado a un tamano razonable en PDF)
DEFAULT_RADIUS = 3.0


@dataclass
class PageStyle:
    pagesize: Tuple[float, float] = A4
    margin_left: float = 1.5 * cm
    margin_right: float = 1.5 * cm
    margin_top: float = 1.2 * cm
    margin_bottom: float = 1.2 * cm
    font: str = "Helvetica"
    font_bold: str = "Helvetica-Bold"


def image_exists(path: str) -> bool:
    try:
        return os.path.isfile(path) and os.path.getsize(path) > 0
    except Exception:
        return False


def draw_image_if_exists(c, path: str, x: float, y: float, w: float, h: float):
    if image_exists(path):
        c.drawImage(path, x, y, width=w, height=h, preserveAspectRatio=True, mask="auto")


def wrap_text(text: str, font_name: str, font_size: float, max_width: float) -> List[str]:
    if not text:
        return [""]
    lines_out: List[str] = []
    for raw_line in str(text).splitlines():
        words = raw_line.split()
        if not words:
            lines_out.append("")
            continue
        cur = words[0]
        for w in words[1:]:
            test = cur + " " + w
            if stringWidth(test, font_name, font_size) <= max_width:
                cur = test
            else:
                lines_out.append(cur)
                cur = w
        lines_out.append(cur)
    return lines_out


def draw_section_bar(c, x: float, y: float, w: float, h: float, title: str):
    """
    Estilo alineado con .section-bar del CSS web:
    fondo naranjo palido + borde naranjo + texto oscuro en negrita.
    (antes: bloque naranjo solido con texto negro en mayusculas)
    """
    radius = min(6.0, h / 2.0)
    c.saveState()
    c.setFillColor(ORANGE_SOFT_BG)
    c.setStrokeColor(ORANGE)
    c.setLineWidth(1.0)
    c.roundRect(x, y, w, h, radius, stroke=1, fill=1)
    c.setFillColor(TEXT_DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 0.3 * cm, y + h / 2.0 - 3.2, str(title))
    c.restoreState()


def draw_box(
    c,
    x: float,
    y: float,
    w: float,
    h: float,
    fill_color=None,
    stroke=1,
    radius: float = DEFAULT_RADIUS,
    stroke_color=BORDER_LIGHT,
):
    """
    Caja tipo "input" del formulario web: esquinas redondeadas y borde
    gris suave (antes: rectangulo recto con borde negro).
    Si radius=0, se comporta igual que un rect() normal (compatibilidad).
    """
    c.saveState()
    c.setStrokeColor(stroke_color)
    if fill_color is not None:
        c.setFillColor(fill_color)
        if radius > 0:
            c.roundRect(x, y, w, h, radius, stroke=stroke, fill=1)
        else:
            c.rect(x, y, w, h, stroke=stroke, fill=1)
        c.setFillColor(BLACK)
    else:
        if radius > 0:
            c.roundRect(x, y, w, h, radius, stroke=stroke, fill=0)
        else:
            c.rect(x, y, w, h, stroke=stroke, fill=0)
    c.restoreState()


def draw_table_grid(c, x: float, y: float, col_widths: List[float], row_heights: List[float], stroke=1):
    total_w = sum(col_widths)
    total_h = sum(row_heights)
    c.setStrokeColor(BORDER_LIGHT)
    draw_box(c, x, y, total_w, total_h, fill_color=None, stroke=stroke, radius=0)
    cx = x
    for w in col_widths[:-1]:
        cx += w
        c.line(cx, y, cx, y + total_h)
    cy = y
    for h in row_heights[:-1]:
        cy += h
        c.line(x, cy, x + total_w, cy)


def draw_cell_text(
    c,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    font_name: str = "Helvetica",
    font_size: float = 9,
    padding: float = 0.2 * cm,
    valign: str = "middle",
):
    c.setFont(font_name, font_size)
    max_w = max(1, w - 2 * padding)
    lines = wrap_text(text, font_name, font_size, max_w)
    line_h = font_size * 1.15
    text_h = len(lines) * line_h
    if valign == "top":
        start_y = y + h - padding - line_h
    elif valign == "bottom":
        start_y = y + padding
    else:
        start_y = y + (h - text_h) / 2 + (len(lines) - 1) * line_h
    ty = start_y
    for ln in lines:
        c.drawString(x + padding, ty, ln)
        ty -= line_h


def draw_checkbox(c, x: float, y: float, size: float = 0.32 * cm, checked: bool = False):
    c.saveState()
    c.setStrokeColor(BORDER_LIGHT if not checked else ORANGE)
    c.setLineWidth(1.0)
    radius = min(2.5, size / 3.0)
    c.roundRect(x, y, size, size, radius, stroke=1, fill=0)
    if checked:
        c.setStrokeColor(ORANGE)
        c.setLineWidth(1.4)
        c.line(x + size * 0.18, y + size * 0.55, x + size * 0.42, y + size * 0.25)
        c.line(x + size * 0.42, y + size * 0.25, x + size * 0.82, y + size * 0.78)
    c.restoreState()