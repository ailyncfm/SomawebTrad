# SOMAWEB - Deploy (HTTP por IP) - Rocky Linux 9 + Apache + mod_wsgi

## Qué hay en este entregable
- somaweb_project.zip       -> código del proyecto (sin venv)
- deploy_rocky_http_ip.sh   -> script de despliegue (1 comando)
- somaweb_http_ip.conf      -> VirtualHost Apache (HTTP)
- somaweb.wsgi              -> entry WSGI para Apache
- DEPLOY_CONFIG.example     -> plantilla para configurar IP

## Deploy (lo mínimo)
1) Descomprimir este entregable en el servidor.
2) Crear DEPLOY_CONFIG:
   cp DEPLOY_CONFIG.example DEPLOY_CONFIG
   nano DEPLOY_CONFIG
   (editar SITE_IP)

3) Ejecutar:
   sudo bash deploy_rocky_http_ip.sh

4) Probar:
   curl -I http://<IP>/

## Logs
- /var/log/httpd/somaweb_error.log
- /var/log/httpd/somaweb_access.log

## Nota SELinux
En este entorno, Pillow/ReportLab bajo mod_wsgi dio 500 con SELinux enforcing.
Lo que me funcionó estable fue dejar SOLO httpd_t en permissive:
  semanage permissive -a httpd_t
(el script lo aplica automáticamente).
