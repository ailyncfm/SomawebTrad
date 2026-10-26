from app import create_app
from app.extensions import db
from app.models import Reunion, Compromiso, Participante

app = create_app()
with app.app_context():
    n_comp = Compromiso.query.delete()
    n_part = Participante.query.delete()
    n_reun = Reunion.query.delete()
    db.session.commit()
    print(f"Eliminados: {n_reun} reuniones, {n_comp} compromisos, {n_part} participantes.")