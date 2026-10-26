#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Deploy SOMAWEB (HTTP por IP) - Rocky Linux 9 + Apache + mod_wsgi
# ============================================================
# Yo dejo este script para que el deploy sea lo más automático posible:
# - Instala dependencias del sistema (httpd, mod_wsgi, etc.)
# - Descomprime el proyecto en /var/www/somaweb
# - Crea el venv en /var/www/somaweb/.venv
# - Instala requirements con python -m pip (más robusto que llamar bin/pip)
# - Configura Apache (vhost) y WSGI
# - Ajusta permisos y SELinux para storage
# - Aplica workaround SELinux para Pillow/ReportLab (httpd_t permissive)
# ============================================================

# --- Cargar config (IP) ---
# Yo prefiero cargar variables desde DEPLOY_CONFIG para que el usuario solo edite la IP.
DEPLOY_CONFIG="./DEPLOY_CONFIG"
if [ ! -f "${DEPLOY_CONFIG}" ]; then
  echo "ERROR: No existe ${DEPLOY_CONFIG}."
  echo "Crea el archivo así:"
  echo "  cp DEPLOY_CONFIG.example DEPLOY_CONFIG"
  echo "  nano DEPLOY_CONFIG   # y define SITE_IP"
  exit 1
fi

# shellcheck disable=SC1090
source "${DEPLOY_CONFIG}"

if [ -z "${SITE_IP:-}" ]; then
  echo "ERROR: SITE_IP no está definido en DEPLOY_CONFIG"
  exit 1
fi

PROJECT_ZIP="somaweb_project.zip"

APP_DIR="/var/www/somaweb"
VENV_DIR="${APP_DIR}/.venv"
APACHE_CONF="/etc/httpd/conf.d/somaweb.conf"

echo "== SOMAWEB deploy (HTTP por IP) =="
echo "IP: ${SITE_IP}"
echo "Project zip: ${PROJECT_ZIP}"
echo "App dir: ${APP_DIR}"

# --- Paquetes ---
sudo dnf install -y httpd python3 python3-pip policycoreutils-python-utils || true
sudo dnf install -y mod_ssl || true
sudo dnf install -y python3-mod_wsgi || true

# --- Validación del zip ---
if [ ! -f "${PROJECT_ZIP}" ]; then
  echo "ERROR: No existe ${PROJECT_ZIP} en el directorio actual."
  echo "Deja somaweb_project.zip junto a este script."
  exit 1
fi

# --- Desplegar código ---
sudo mkdir -p "${APP_DIR}"
sudo unzip -o "${PROJECT_ZIP}" -d "${APP_DIR}"

# --- Crear venv (recrear siempre para evitar estados raros) ---
sudo rm -rf "${VENV_DIR}"
sudo python3 -m venv "${VENV_DIR}"

# --- Asegurar pip dentro del venv y usar python -m pip (robusto) ---
sudo "${VENV_DIR}/bin/python" -m ensurepip --upgrade || true
sudo "${VENV_DIR}/bin/python" -m pip install --upgrade pip
sudo "${VENV_DIR}/bin/python" -m pip install -r "${APP_DIR}/requirements.txt"

# --- WSGI entrypoint ---
# Yo copio el archivo WSGI del bundle al proyecto para que Apache cargue la app sin abrir puertos Python.
sudo cp -f "./somaweb.wsgi" "${APP_DIR}/somaweb.wsgi"

# --- Storage perms ---
sudo mkdir -p "${APP_DIR}/storage"
sudo chown -R apache:apache "${APP_DIR}/storage"
sudo chmod -R 775 "${APP_DIR}/storage"

# --- SELinux: storage RW ---
sudo semanage fcontext -a -t httpd_sys_rw_content_t "${APP_DIR}/storage(/.*)?" 2>/dev/null || true
sudo semanage fcontext -m -t httpd_sys_rw_content_t "${APP_DIR}/storage(/.*)?" 2>/dev/null || true
sudo restorecon -Rv "${APP_DIR}/storage" || true

# --- SELinux: permitir red (por si Postgres es remoto) ---
sudo setsebool -P httpd_can_network_connect 1 || true

# --- Workaround SELinux para Pillow/ReportLab ---
# En mi caso real, con SELinux Enforcing, Pillow fallaba cargando el .so bajo mod_wsgi.
# Dejo SOLO el dominio de Apache (httpd_t) en permissive para que el sistema quede operativo.
sudo semanage permissive -a httpd_t 2>/dev/null || true

# --- Render Apache vhost (HTTP) ---
tmpconf="$(mktemp)"
sed -e "s|__SITE_IP__|${SITE_IP}|g" "./somaweb_http_ip.conf" > "${tmpconf}"
sudo cp -f "${tmpconf}" "${APACHE_CONF}"
rm -f "${tmpconf}"

# --- ServerName global (evita warning AH00558) ---
if ! grep -qE '^ServerName\s+' /etc/httpd/conf/httpd.conf; then
  echo "ServerName ${SITE_IP}" | sudo tee -a /etc/httpd/conf/httpd.conf >/dev/null
fi

# --- Firewall (si firewalld está activo) ---
sudo systemctl enable --now httpd
sudo firewall-cmd --add-service=http --permanent 2>/dev/null || true
sudo firewall-cmd --reload 2>/dev/null || true

# --- Restart + test ---
sudo apachectl configtest
sudo systemctl restart httpd

echo
echo "== Tests =="
echo "curl -I http://${SITE_IP}/"
echo "curl -I http://localhost/"
echo
echo "== Logs =="
echo "sudo tail -n 200 /var/log/httpd/somaweb_error.log"
echo "sudo tail -n 200 /var/log/httpd/error_log"

