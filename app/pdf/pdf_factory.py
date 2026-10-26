
# somaweb/app/pdf/pdf_factory.py
from __future__ import annotations

from typing import Any, Callable, Dict

from reportlab.pdfgen import canvas

from app.pdf.planning import render_planning_pdf, build_planning_example_data
from app.pdf.scheduling import render_scheduling_pdf, build_scheduling_example_data
from app.pdf.post_maintenance import (
    render_post_maintenance_pdf,
    build_post_maintenance_example_data,
)
from app.pdf.prioritization import (
    render_prioritization_pdf,
    build_prioritization_example_data,
)

from app.pdf.conciliacion_sep4 import (
    render_conciliacion_sep4_pdf,
    build_conciliacion_sep4_example_data,
)

RenderFn = Callable[[canvas.Canvas, Dict[str, Any], str], Any]
BuildFn = Callable[[], Dict[str, Any]]


def _normalize_doc_type(doc_type: str) -> str:
    t = (doc_type or "").strip().lower()
    aliases = {
        # Planning
        "planning": "planning",
        "planificacion": "planning",
        "planificación": "planning",
        # Scheduling
        "scheduling": "scheduling",
        "programacion": "scheduling",
        "programación": "scheduling",
        # Post Maintenance
        "post": "post_maintenance",
        "post_maintenance": "post_maintenance",
        "postmantenimiento": "post_maintenance",
        "post-mantenimiento": "post_maintenance",
        # Prioritization
        "prioritization": "prioritization",
        "priorizacion": "prioritization",
        "priorización": "prioritization",
        # Conciliación SEP-4
        "conciliacion_sep4": "conciliacion_sep4",
        "sep4": "conciliacion_sep4",
    }
    return aliases.get(t, t)


_RENDERERS: Dict[str, RenderFn] = {
    "planning": render_planning_pdf,
    "scheduling": render_scheduling_pdf,
    "post_maintenance": render_post_maintenance_pdf,
    "prioritization": render_prioritization_pdf,
    "conciliacion_sep4": render_conciliacion_sep4_pdf,
}

_BUILDERS: Dict[str, BuildFn] = {
    "planning": build_planning_example_data,
    "scheduling": build_scheduling_example_data,
    "post_maintenance": build_post_maintenance_example_data,
    "prioritization": build_prioritization_example_data,
    "conciliacion_sep4": build_conciliacion_sep4_example_data,
}

def render_pdf(doc_type: str, c: canvas.Canvas, data: Dict[str, Any], base_dir: str) -> None:
    t = _normalize_doc_type(doc_type)
    fn = _RENDERERS.get(t)
    if not fn:
        raise ValueError(f"Tipo de documento no soportado aún: {doc_type!r}")
    fn(c, data, base_dir)


def example_data(doc_type: str) -> Dict[str, Any]:
    t = _normalize_doc_type(doc_type)
    fn = _BUILDERS.get(t)
    if not fn:
        raise ValueError(f"Tipo de documento no soportado aún: {doc_type!r}")
    return fn()


