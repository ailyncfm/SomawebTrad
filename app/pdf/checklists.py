# app/pdf/checklists.py
from __future__ import annotations
from typing import Dict, List

# Las claves coinciden con el doc_type usado en routes.py:
# "planning", "scheduling", "post", "prioritization"
CHECKLIST_ITEMS: Dict[str, List[str]] = {
    "prioritization": [
        "Las actividades revisadas fueron evaluadas considerando riesgos para las personas, equipos e instalaciones.",
        "Las interferencias y restricciones relevantes fueron identificadas durante la priorización.",
        "Las actividades con requerimientos especiales de seguridad fueron identificadas oportunamente.",
        "La priorización realizada considera los riesgos operacionales y de seguridad asociados.",
    ],
    "planning": [
        "Los riesgos principales de las actividades planificadas fueron considerados durante la asignación de recursos.",
        "Las actividades con requerimientos especiales de seguridad fueron identificadas.",
        "Las condiciones previas necesarias para la ejecución segura fueron consideradas en la planificación.",
        "Las interferencias operacionales relevantes fueron identificadas y gestionadas.",
        "Las necesidades de coordinación entre áreas fueron consideradas en el plan.",
        "Los requerimientos de acceso, aislamiento o control operacional fueron considerados para las actividades planificadas.",
        "Los recursos requeridos para implementar controles de seguridad fueron considerados en la planificación.",
    ],
    "scheduling": [
        "Las actividades programadas fueron secuenciadas considerando riesgos e interferencias operacionales.",
        "Los preparativos de terreno requeridos fueron considerados para las actividades programadas.",
        "Los requerimientos de tránsito, accesos y segregación fueron revisados.",
        "Las actividades que requieren permisos o autorizaciones especiales fueron identificadas.",
        "Los recursos de apoyo necesarios para la ejecución segura fueron considerados en la programación.",
        "Las actividades simultáneas con potencial interferencia fueron coordinadas.",
        "Se revisaron las condiciones (acreditaciones, capacitaciones, etc.) necesarias para el inicio seguro de los trabajos programados.",
        "Se consideraron los requerimientos de emergencia y respuesta ante contingencias cuando corresponde.",
        "Los aspectos de orden, limpieza y gestión de residuos fueron considerados en las actividades programadas.",
    ],
    "post": [
        "Durante la ejecución se identificaron desviaciones de seguridad que fueron analizadas por el equipo.",
        "Las interferencias ocurridas durante la ejecución fueron revisadas y documentadas.",
        "Los controles considerados durante la planificación y programación resultaron efectivos.",
        "Se identificaron oportunidades de mejora para futuras intervenciones.",
        "Las lecciones aprendidas relacionadas con seguridad fueron discutidas por el equipo.",
        "Se definieron acciones y responsables para abordar las brechas detectadas.",
    ],
}