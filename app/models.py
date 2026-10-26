# app/models.py
from __future__ import annotations
from datetime import datetime, timedelta
import secrets

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class Usuario(db.Model, UserMixin):
    """
    Login propio con autoregistro (correo corporativo + contraseña).
    Diseñado para que, cuando exista SSO corporativo, solo haya que
    reemplazar el mecanismo de autenticación (login_submit en auth/routes.py)
    sin tocar el resto del sistema (sesiones, roles, historial, etc.).
    """
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    nombre = db.Column(db.String(255), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False, default="")
    rol = db.Column(db.String(20), nullable=False, default="usuario")  # "usuario" | "admin"
    is_active_account = db.Column(db.Boolean, nullable=False, default=True)
    reset_token = db.Column(db.String(64), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reuniones = db.relationship("Reunion", backref="usuario", lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self) -> str:
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token

    def is_reset_token_valid(self, token: str) -> bool:
        return bool(
            token
            and self.reset_token == token
            and self.reset_token_expires
            and self.reset_token_expires > datetime.utcnow()
        )

    @property
    def is_active(self):
        # Flask-Login usa esta propiedad para permitir o no iniciar sesion
        return self.is_active_account

    @property
    def is_admin(self):
        return self.rol == "admin"

    def __repr__(self):
        return f"<Usuario {self.email}>"


class Reunion(db.Model):
    __tablename__ = "reuniones"

    id = db.Column(db.Integer, primary_key=True)
    doc_type = db.Column(db.String(50), nullable=False)  # planning, scheduling, post, prioritization, process_5s
    titulo = db.Column(db.String(255), nullable=True)
    fecha = db.Column(db.String(20), nullable=True)   # DD/MM/AAAA, tal como lo usa el resto del sistema
    hora = db.Column(db.String(10), nullable=True)
    area = db.Column(db.String(255), nullable=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

    pdf_path = db.Column(db.String(500), nullable=True)  # ruta relativa dentro de storage/, para Fase 3
    pdf_filename = db.Column(db.String(255), nullable=True)
    nota = db.Column(db.Float, nullable=True)

    detenciones_revisadas = db.Column(db.Integer, nullable=True)
    detenciones_conciliadas = db.Column(db.Integer, nullable=True)
    detenciones_pendientes = db.Column(db.Integer, nullable=True)
    horas_detencion_pendientes = db.Column(db.Float, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    participantes = db.relationship(
        "Participante", backref="reunion", lazy=True, cascade="all, delete-orphan"
    )
    compromisos = db.relationship(
        "Compromiso", backref="reunion", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "doc_type": self.doc_type,
            "titulo": self.titulo,
            "fecha": self.fecha,
            "hora": self.hora,
            "area": self.area,
            "pdf_filename": self.pdf_filename,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Reunion {self.doc_type} {self.fecha}>"


class Participante(db.Model):
    __tablename__ = "participantes"

    id = db.Column(db.Integer, primary_key=True)
    reunion_id = db.Column(db.Integer, db.ForeignKey("reuniones.id"), nullable=False)

    area = db.Column(db.String(255), nullable=True)
    nombre = db.Column(db.String(255), nullable=True)  # "Responsable" en el formulario actual
    email = db.Column(db.String(255), nullable=True)

    asistio = db.Column(db.Boolean, nullable=True)   # True/False/None (sin responder)
    conforme = db.Column(db.Boolean, nullable=True)  # True/False/None

    origen = db.Column(db.String(20), default="manual")  # "manual" o "qr"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "area": self.area,
            "nombre": self.nombre,
            "email": self.email,
            "asistio": self.asistio,
            "conforme": self.conforme,
            "origen": self.origen,
        }

    def __repr__(self):
        return f"<Participante {self.nombre} ({self.area})>"


class Compromiso(db.Model):
    __tablename__ = "compromisos"

    id = db.Column(db.Integer, primary_key=True)
    reunion_id = db.Column(db.Integer, db.ForeignKey("reuniones.id"), nullable=False)

    accion = db.Column(db.Text, nullable=True)
    responsable = db.Column(db.String(255), nullable=True)
    fecha_compromiso = db.Column(db.String(20), nullable=True)
    estado = db.Column(db.String(100), nullable=True)
    evidencia = db.Column(db.String(255), nullable=True)
    area = db.Column(db.String(255), nullable=True)
    thread_id = db.Column(db.String(36), nullable=True)  # agrupa versiones del mismo compromiso entre reuniones

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "accion": self.accion,
            "responsable": self.responsable,
            "fecha": self.fecha_compromiso,
            "estado": self.estado,
            "evidencia": self.evidencia,
        }

    def __repr__(self):
        return f"<Compromiso {self.accion[:30] if self.accion else ''}>"


    @property
    def is_vencido(self) -> bool:
        from datetime import datetime
        if (self.estado or "").strip().upper() in ("CERRADO", "CANCELADO", "COMPLETADO"):
            return False
        try:
            d = datetime.strptime((self.fecha_compromiso or "").strip(), "%d/%m/%Y")
        except Exception:
            return False
        return d.date() < datetime.today().date()

class Gerencia(db.Model):
    __tablename__ = "gerencias"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False)
    nombre = db.Column(db.String(255), nullable=False)

    superintendencias = db.relationship(
        "Superintendencia", backref="gerencia", lazy=True,
        cascade="all, delete-orphan", order_by="Superintendencia.nombre"
    )

    @property
    def nombre_completo(self):
        return f"{self.codigo} - {self.nombre}"


class Superintendencia(db.Model):
    __tablename__ = "superintendencias"

    id = db.Column(db.Integer, primary_key=True)
    gerencia_id = db.Column(db.Integer, db.ForeignKey("gerencias.id"), nullable=False)
    codigo = db.Column(db.String(20), nullable=False)
    nombre = db.Column(db.String(255), nullable=False)

    areas = db.relationship(
        "AreaTrabajo", backref="superintendencia", lazy=True,
        cascade="all, delete-orphan", order_by="AreaTrabajo.nombre"
    )

    @property
    def nombre_completo(self):
        return f"{self.codigo} - {self.nombre}"


class AreaTrabajo(db.Model):
    __tablename__ = "areas_trabajo"

    id = db.Column(db.Integer, primary_key=True)
    superintendencia_id = db.Column(db.Integer, db.ForeignKey("superintendencias.id"), nullable=False)
    nombre = db.Column(db.String(255), nullable=False)
    codigo_pdf = db.Column(db.String(10), nullable=True)