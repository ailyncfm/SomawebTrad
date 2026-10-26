import os
import click
from pathlib import Path
from flask import Flask
from datetime import timedelta


from app.extensions import db, login_manager, limiter, migrate

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "cambia-esto-por-una-clave-larga-y-aleatoria-en-produccion"
    )

    # Cookies de sesion seguras.
    # SESSION_COOKIE_SECURE solo se activa si la app corre detras de HTTPS real
    # (en produccion, exportar FORCE_HTTPS=1). En desarrollo local por HTTP
    # dejarlo en False, porque el navegador descarta cookies "Secure" sobre HTTP.
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FORCE_HTTPS", "0") == "1"
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
    # Ruta de la base de datos: por defecto SQLite dentro de storage/
    # (mismo patrón que los PDFs de ejemplo/backup). Si más adelante se
    # define Postgres, basta con setear la variable de entorno DATABASE_URL
    # sin tocar código.
    base_dir = Path(app.root_path).resolve().parent
    storage_dir = base_dir / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    default_db_path = storage_dir / "soma.sqlite3"

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", f"sqlite:///{default_db_path}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from app import models  # noqa: F401  (registra los modelos para que Alembic los detecte)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login_form"
    login_manager.login_message = "Debes iniciar sesión para acceder a esta página."
    login_manager.login_message_category = "info"
    limiter.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Usuario
        return Usuario.query.get(int(user_id))
    
    from app.qr_store import init_db as init_qr_db
    init_qr_db() 

    app.config["APP_VERSION"] = "1.0.0"

    @app.context_processor
    def inject_globals():
        return {"app_version": app.config["APP_VERSION"]}

        
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.web import web_bp
    app.register_blueprint(web_bp)

    @app.cli.command("seed-organizacion")
    def seed_organizacion_command():
        """Carga Gerencia/Superintendencia/Área desde app/data/organizacion.py (idempotente)."""
        from app.seeds.organizacion import seed_organizacion
        seed_organizacion()

    @app.cli.command("create-admin")
    @click.option("--email", prompt=True)
    @click.option("--nombre", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin_command(email, nombre, password):
        """Crea un usuario admin, o promueve a admin uno existente con ese correo."""
        from app.models import Usuario

        email = (email or "").strip().lower()
        nombre = (nombre or "").strip()

        user = Usuario.query.filter_by(email=email).first()
        if user:
            user.rol = "admin"
            db.session.commit()
            click.echo(f"Usuario existente {email} promovido a admin.")
            return

        if len(password) < 10:
            click.echo("La contraseña debe tener al menos 10 caracteres.")
            return

        user = Usuario(email=email, nombre=nombre, rol="admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Usuario admin {email} creado.")

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)
        if app.config["SESSION_COOKIE_SECURE"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.errorhandler(500)
    def handle_internal_error(e):
        app.logger.error(f"Error interno no controlado: {e}")
        return "Ocurrió un error. Intenta nuevamente o contacta a soporte.", 500

    @app.errorhandler(404)
    def handle_not_found(e):
        return "La página que buscas no existe.", 404

    @app.errorhandler(429)
    def handle_rate_limit(e):
        return "Demasiados intentos. Espera unos minutos antes de volver a intentar.", 429

    return app