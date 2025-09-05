#!/bin/bash

# ===================================================================================
# Script de Aprovisionamiento para Despliegue de Proyectos Django
# Creado por: Jarvis (Tu Principal Technical Partner)
# Versión: 1.1 (Versión Interactiva)
# Probado en: Ubuntu 22.04 LTS
# ===================================================================================

# Salir inmediatamente si un comando falla
set -e

### ### RECOPILACIÓN INTERACTIVA DE VARIABLES ### ###
echo "--- Por favor, introduce los datos de configuración del proyecto ---"

read -p "Nombre de la carpeta del proyecto (ej: folp-becarios): " PROJECT_NAME
read -p "Nombre de la carpeta de configuración de Django (donde está wsgi.py, ej: config): " CONFIG_DIR_NAME
read -p "Usuario no-root que ejecutará la aplicación (ej: soporte): " DEPLOY_USER
read -p "Tu nombre de dominio o IP (ej: misitio.com o 192.10.10.100): " DOMAIN_NAME

echo ""
echo "--- Configuración de la Base de Datos ---"
read -p "Nombre de la base de datos (ej: controlbecarios_db): " DB_NAME
read -p "Usuario para la base de datos (ej: controlbecarios_user): " DB_USER

# Bucle para solicitar y confirmar la contraseña de forma segura
while true; do
    read -s -p "Contraseña para el usuario de la BD: " DB_PASSWORD
    echo
    read -s -p "Confirma la contraseña: " DB_PASSWORD_CONFIRM
    echo
    if [ "$DB_PASSWORD" = "$DB_PASSWORD_CONFIRM" ]; then
        break
    else
        echo "Las contraseñas no coinciden. Inténtalo de nuevo."
    fi
done

echo ""
echo "==========================================================="
echo "### Verificación de la Configuración ###"
echo "Nombre del Proyecto:      $PROJECT_NAME"
echo "Directorio de Config:     $CONFIG_DIR_NAME"
echo "Usuario de Despliegue:    $DEPLOY_USER"
echo "Dominio:                  $DOMAIN_NAME"
echo "Base de Datos:            $DB_NAME"
echo "Usuario de BD:            $DB_USER"
echo "==========================================================="
read -p "¿La configuración es correcta? (s/n) " CONFIRM
if [ "$CONFIRM" != "s" ]; then
    echo "Operación cancelada."
    exit 1
fi

# ===================================================================================

echo "### 1/4 - Iniciando Aprovisionamiento del Servidor Django... ###"

# --- INSTALACIÓN DE DEPENDENCIAS DEL SISTEMA ---
echo ">>> Actualizando e instalando paquetes del sistema (Python, Nginx, PostgreSQL)..."
apt-get update
apt-get upgrade -y
apt-get install -y python3-venv python3-pip nginx git postgresql postgresql-contrib

# --- CONFIGURACIÓN DEL FIREWALL (UFW) ---
echo ">>> Configurando el firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "### 2/4 - Configurando la Base de Datos PostgreSQL... ###"

# --- CREACIÓN DE BASE DE DATOS Y USUARIO ---
echo ">>> Creando base de datos '$DB_NAME' y usuario '$DB_USER'..."
# Ejecuta los comandos como el usuario 'postgres'
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET timezone TO 'UTC';"
sudo -u postgres psql -c "ALTER DATABASE $DB_NAME OWNER TO $DB_USER;"

echo "### 3/4 - Configurando Servicios (Gunicorn y Nginx)... ###"

# --- CREACIÓN DEL ARCHIVO DE SERVICIO DE GUNICORN ---
echo ">>> Creando el archivo de servicio de Gunicorn..."
# La directiva cat <<EOF > ... crea un archivo con el contenido que sigue
cat <<EOF > /etc/systemd/system/gunicorn.service
[Unit]
Description=gunicorn daemon for $PROJECT_NAME
After=network.target

[Service]
User=$DEPLOY_USER
Group=www-data
RuntimeDirectory=gunicorn
WorkingDirectory=/home/$DEPLOY_USER/$PROJECT_NAME
Environment="DJANGO_ENV=production"
ExecStart=/home/$DEPLOY_USER/$PROJECT_NAME/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/gunicorn/gunicorn.sock $CONFIG_DIR_NAME.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

# --- CREACIÓN DE LA CONFIGURACIÓN DE NGINX ---
echo ">>> Creando el archivo de configuración de Nginx..."
cat <<EOF > /etc/nginx/sites-available/$PROJECT_NAME
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;

    location /static/ {
        alias /home/$DEPLOY_USER/$PROJECT_NAME/staticfiles/;
    }

    location /media/ {
        alias /home/$DEPLOY_USER/$PROJECT_NAME/media/;
    }

    location / {
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://unix:/run/gunicorn/gunicorn.sock;
    }
}
EOF

# --- ACTIVACIÓN DE NGINX Y REINICIO DE SERVICIOS ---
echo ">>> Activando el sitio de Nginx..."
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/

# Verifica la sintaxis antes de reiniciar
nginx -t

# Reinicia los servicios para aplicar todos los cambios
systemctl restart nginx
systemctl daemon-reload

echo "### 4/4 - ¡Aprovisionamiento del servidor completado! ###"
echo ""
echo ">>> PRÓXIMOS PASOS:"
echo "1. Clona tu repositorio en /home/$DEPLOY_USER/"
echo "2. Crea y activa el entorno virtual en /home/$DEPLOY_USER/$PROJECT_NAME/venv"
echo "3. Instala las dependencias con 'pip install -r requirements.txt'"
echo "4. Crea tu archivo '.env' con las variables de producción (¡incluyendo la contraseña de BD!)."
echo "5. Ejecuta 'python manage.py migrate', 'collectstatic' y 'createsuperuser'."
echo "6. Inicia el servicio de Gunicorn: 'sudo systemctl start gunicorn' y 'sudo systemctl enable gunicorn'."
echo "7. Configura HTTPS con Certbot."
