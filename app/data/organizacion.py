# app/data/organizacion.py
# Fuente unica de la jerarquia Gerencia -> Superintendencia -> Area.
# Se usa tanto para el desplegable de "Area" (Seccion Datos) como para
# los desplegables en cascada de Gerencia/Superintendencia (Observadores).

ORGANIZACION = {
    "GFUN - Gerencia Fundición": {
        "SFE - Suptcia. Planta de Flotación de Escoria": [
            "U. Planta Tratamiento de Escoria",
        ],
        "SPF - Suptcia. Procesos Fundición": [
            "U. Fusión Conversión",
            "U. Refinación y Moldeo",
        ],
        "SPLF - Suptcia. Plantas Fundición": [
            "U. Plantas Limpieza Gases",
            "U. Plantas Oxígeno y Nitrógeno",
        ],
    },
    "GMIN - Gerencia de Minas": {
        "SMC - Suptcia. Mina Central": [
            "U. Esmeralda",
        ],
        "SMN - Suptcia. Mina Norte": [
            "U. Sub-6",
            "U. Teniente-7",
        ],
        "SMS - Suptcia. Mina Sur": [
            "Suptcia. Mina Sur",
            "U. Diablo Regimiento",
            "U. FFCC Teniente 5",
            "U. Operaciones Pacífico Superior",
        ],
        "STC - Suptcia. Transporte y Chancado": [
            "U. Chancado Primario",
            "U. FFCC Tte. 8",
        ],
    },
    "GPTA - Gerencia de Plantas": {
        "SMP - Suptcia. de Mantenimiento Plantas": [
            "U. Mantención Chancado - GPTA",
            "U. Mantenimiento Filtros y Secado",
            "U. Mantenimiento Molibdeno",
            "U. Mantenimiento Planta Convencional",
            "U. Mantenimiento Planta SAG",
        ],
        "SPP - Suptcia. Productos Comerc": [
            "Suptcia. Productos Comerc",
        ],
    },
    "GRS - Gerencia Rajo - Sewell": {
        "SMSS - Suptcia. Mantención y Servicios": [
            "U. Mantención Rajo-FFCC",
        ],
        "SOS - Suptcia. Operaciones Sewell": [
            "U. Mantención Sewell",
        ],
    },
    "GTRH - Gerencia Tranques Relaves y Rec. Hídricos": {
        "SMRH - Supte. Mtto. Recursos Hídricos y Relaves": [
            "Supte. Mtto. Recursos Hídricos y Relaves",
        ],
    },
}

# Codigo corto por area, usado para el nombre del PDF (GERENCIA-AREA-TIPO-SEMANA_ANIO).
# Revisar y ajustar si alguno no calza con la convencion real.
AREA_CODES = {
    "U. Planta Tratamiento de Escoria": "PTE",
    "U. Fusión Conversión": "FUCO",
    "U. Refinación y Moldeo": "REMO",
    "U. Plantas Limpieza Gases": "PLG",
    "U. Plantas Oxígeno y Nitrógeno": "POAN",
    "U. Esmeralda": "ESM",
    "U. Sub-6": "SUB6",
    "U. Teniente-7": "TT7",
    "Suptcia. Mina Sur": "MS",
    "U. Diablo Regimiento": "DRG",
    "U. FFCC Teniente 5": "TT5",
    "U. Operaciones Pacífico Superior": "PS",
    "U. Chancado Primario": "CHP",
    "U. FFCC Tte. 8": "TT8",
    "U. Mantención Chancado - GPTA": "CH",
    "U. Mantenimiento Filtros y Secado": "FS",
    "U. Mantenimiento Molibdeno": "MOLI",
    "U. Mantenimiento Planta Convencional": "PMC",
    "U. Mantenimiento Planta SAG": "SAG",
    "Suptcia. Productos Comerc": "PCOM",
    "U. Mantención Rajo-FFCC": "RFFCC",
    "U. Mantención Sewell": "SW",
    "Supte. Mtto. Recursos Hídricos y Relaves": "RHR",
}

def get_all_areas() -> list:
    """
    Lista de areas para el filtro del dashboard, con etiqueta "CODIGO_GERENCIA - Area"
    pero conservando como 'value' el nombre real del area (el mismo que se guarda
    en Reunion.area), en el mismo orden en que aparecen en ORGANIZACION.
    """
    result = []
    seen = set()
    for gerencia_full, supers in ORGANIZACION.items():
        codigo = gerencia_full.split(" - ")[0].strip()
        for area_list in supers.values():
            for area in area_list:
                if area in seen:
                    continue
                seen.add(area)
                result.append({"value": area, "label": f"{codigo} - {area}"})
    return result