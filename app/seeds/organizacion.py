# app/seeds/organizacion.py
from app.extensions import db
from app.models import Gerencia, Superintendencia, AreaTrabajo
from app.data.organizacion import ORGANIZACION, AREA_CODES


def seed_organizacion():
    """Carga la jerarquía Gerencia -> Superintendencia -> Área desde
    app/data/organizacion.py. Segura de volver a correr: si ya hay
    gerencias cargadas, no hace nada (no duplica ni borra)."""
    if Gerencia.query.count() > 0:
        print("Ya hay datos de organización cargados, no se hace nada.")
        return

    for gerencia_full, supers in ORGANIZACION.items():
        codigo_ger, nombre_ger = gerencia_full.split(" - ", 1)
        g = Gerencia(codigo=codigo_ger.strip(), nombre=nombre_ger.strip())
        db.session.add(g)
        db.session.flush()

        for super_full, areas in supers.items():
            codigo_sup, nombre_sup = super_full.split(" - ", 1)
            s = Superintendencia(
                gerencia_id=g.id, codigo=codigo_sup.strip(), nombre=nombre_sup.strip()
            )
            db.session.add(s)
            db.session.flush()

            for area_nombre in areas:
                a = AreaTrabajo(
                    superintendencia_id=s.id,
                    nombre=area_nombre,
                    codigo_pdf=AREA_CODES.get(area_nombre, ""),
                )
                db.session.add(a)

    db.session.commit()
    print(
        "Organización cargada:",
        Gerencia.query.count(), "gerencias,",
        Superintendencia.query.count(), "superintendencias,",
        AreaTrabajo.query.count(), "áreas.",
    )