# /var/www/somaweb/somaweb.wsgi
# ============================================================
# Entry point WSGI para Apache/mod_wsgi
# ------------------------------------------------------------
# Aquí no abro puertos Python: Apache recibe en 80 y llama este script.
# Yo cargo el proyecto y expongo 'application' como WSGI app.
# ============================================================

import sys

# Agrego la ruta del proyecto al path de Python
sys.path.insert(0, "/var/www/somaweb")

# Cargo variables de entorno desde .env si existe (opcional).
# Esto me permite configurar SECRET_KEY, DATABASE_URL, etc. sin hardcodear.
try:
    from dotenv import load_dotenv
    load_dotenv("/var/www/somaweb/.env")
except Exception:
    pass

from app import create_app

# 'application' es lo que mod_wsgi busca por convención.
application = create_app()
