import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Desarrollo local. El modo debug SOLO se activa si exportas
    # FLASK_DEBUG=1 antes de correr este archivo — nunca por defecto,
    # para evitar que el debugger interactivo de Werkzeug quede expuesto
    # por accidente (permite ejecutar código arbitrario desde el navegador).
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)