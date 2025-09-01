CREATE DATABASE becarios_db;
CREATE USER becarios_user WITH PASSWORD 'becarios_pasS';
ALTER ROLE becarios_user SET client_encoding TO 'utf8';
ALTER ROLE becarios_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE becarios_user SET timezone TO 'America/Argentina/Buenos_Aires';
GRANT ALL PRIVILEGES ON DATABASE becarios_db TO becarios_user;
\q

ALTER DATABASE becarios_db OWNER TO becarios_user;

---

[Unit]
Description=gunicorn daemon for folp-becarios

# Se asegura de que la red esté disponible antes de iniciar

After=network.target

[Service]

# Usuario con el que se ejecutará el proceso. En tu caso es root.

User=root

# Directorio de trabajo del proyecto

WorkingDirectory=/root/folp-becarios

# El comando que inicia Gunicorn. Apunta al archivo gunicorn.sock que creará.

ExecStart=/root/folp-becarios/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/root/folp-becarios/gunicorn.sock control_becarios.wsgi:application

[Install]

# Iniciar el servicio en el boot del sistema

WantedBy=multi-user.target

---

# /etc/nginx/sites-available/folp-becarios

server {
listen 80; # Reemplaza esto con tu dominio o la IP de tu servidor
server_name 163.10.29.152;

    # Sirve los archivos estáticos directamente
    location /static/ {
        root /root/folp-becarios;
    }

    # Sirve los archivos de medios (si los tuvieras)
    location /media/ {
        root /root/folp-becarios;
    }

    # Pasa el resto de las peticiones a Gunicorn
    location / {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/root/folp-becarios/gunicorn.sock;
    }

}

---

# Variables para desarrollo local (.env)

# Ponle un valor cualquiera, no importa en desarrollo.

# Puedes generar una con python manage.py shell -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

DJANGO_SECRET_KEY='django-insecure-unaclavededesarrollocualquiera'

# El entorno en el que estamos

DJANGO_ENV='development'

# Habilita el modo debug en desarrollo

DJANGO_DEBUG=True

# Hosts permitidos en desarrollo

DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost'

# Usamos SQLite en desarrollo para simplicidad

DATABASE_URL='sqlite:///db.sqlite3'

---

# Variables para producción (/root/folp-becarios/.env)

DJANGO_SECRET_KEY='tu_clave_secreta_real_y_muy_larga_aqui'

# Identifica el entorno como producción

DJANGO_ENV='production'

# El modo debug SIEMPRE debe ser False en producción

DJANGO_DEBUG=False

# Tu dominio o IP del servidor

DJANGO_ALLOWED_HOSTS='tudominio.com,www.tudominio.com'

# La URL de conexión a PostgreSQL

DATABASE_URL='postgres://controlbecarios_user:una_contraseña_muy_segura@localhost:5432/controlbecarios_db'
