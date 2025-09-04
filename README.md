# Guía de Despliegue: Proyecto de Fichaje de Becarios
Este documento detalla el proceso para desplegar la aplicación Django en un servidor de producción Ubuntu 22.04 LTS, utilizando Gunicorn, Nginx y PostgreSQL.

## Prerrequisitos
Un servidor con Ubuntu 22.04 LTS.

Un usuario no-root con privilegios sudo.

Un nombre de dominio apuntando a la IP del servidor (recomendado).

El código del proyecto en un repositorio Git.

## Fase 1: Preparación del Servidor

1.1. Actualizar e Instalar Dependencias del Sistema

    sudo apt update && sudo apt upgrade -y
    sudo apt install python3-venv python3-pip postgresql postgresql-contrib nginx git -y

1.2. Configurar Firewall Básico (UFW)

    sudo ufw allow OpenSSH
    sudo ufw allow 'Nginx Full'
    sudo ufw enable

1.3. Configurar Base de Datos PostgreSQL

# Inicia la consola de PostgreSQL

    sudo -u postgres psql

# Dentro de la consola de psql, ejecuta:
    
    CREATE DATABASE controlbecarios_db;
    CREATE USER controlbecarios_user WITH PASSWORD '<una_contraseña_muy_segura>';
    ALTER ROLE controlbecarios_user SET client_encoding TO 'utf8';
    ALTER ROLE controlbecarios_user SET default_transaction_isolation TO 'read committed';
    ALTER ROLE controlbecarios_user SET timezone TO 'UTC';

# Asigna la propiedad de la base de datos al usuario (otorga todos los permisos necesarios)

    ALTER DATABASE controlbecarios_db OWNER TO controlbecarios_user;

# Sal de la consola

    \q

## Fase 2: Despliegue de la Aplicación

2.1. Clonar el Repositorio

# Clona tu proyecto desde Git

    git clone <URL_de_tu_repositorio>
    cd <nombre_de_la_carpeta_del_proyecto>

2.2. Crear Entorno Virtual e Instalar Dependencias

# Crea y activa el entorno virtual

    python3 -m venv venv
    source venv/bin/activate

# Instala las dependencias desde tu archivo de requerimientos

    pip install -r requirements.txt

# Asegúrate de que gunicorn y otros paquetes de producción estén en requirements.txt o instálalos

    pip install gunicorn python-dotenv psycopg2-binary

2.3. Configurar Variables de Entorno (.env)

Crea el archivo .env en la raíz del proyecto.

    nano .env

Pega y ajusta tu configuración de producción:

    DJANGO_SECRET_KEY='<tu_clave_secreta_generada_aqui>'
    DJANGO_ENV='production'
    DJANGO_DEBUG=False
    DJANGO_ALLOWED_HOSTS='tudominio.com,www.tudominio.com,tu_ip_del_servidor'
    DATABASE_URL='postgres://controlbecarios_user:<una_contraseña_muy_segura>@localhost:5432/controlbecarios_db'

2.4. Ejecutar Comandos de Django

# Aplica las migraciones a la base de datos de producción

    python manage.py migrate

# Recolecta todos los archivos estáticos en la carpeta /staticfiles

    python manage.py collectstatic --noinput

# Crea un superusuario para el panel de administración

    python manage.py createsuperuser

## Fase 3: Configuración de Servicios

3.1. Gunicorn (Servidor de Aplicación)

Crea el archivo de servicio de systemd.

    sudo nano /etc/systemd/system/gunicorn.service

Pega la siguiente configuración (ajusta User y WorkingDirectory si es necesario):

[Unit]
Description=gunicorn daemon for folp-becarios
After=network.target

[Service]
User=<tu_usuario> # ej. soporte
Group=www-data
RuntimeDirectory=gunicorn
WorkingDirectory=/home/<tu_usuario>/<nombre_de_la_carpeta_del_proyecto>
Environment="DJANGO_ENV=production"
ExecStart=/home/<tu_usuario>/<nombre_de_la_carpeta_del_proyecto>/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/gunicorn/gunicorn.sock config.wsgi:application

[Install]
WantedBy=multi-user.target

Inicia y habilita el servicio:

    sudo systemctl start gunicorn
    sudo systemctl enable gunicorn

3.2. Nginx (Servidor Web y Reverse Proxy)

Crea el archivo de configuración de Nginx:

    sudo nano /etc/nginx/sites-available/folp-becarios

Pega la siguiente configuración (reemplaza tudominio.com y las rutas):

    server {
        listen 80;
        server_name tudominio.com www.tudominio.com;
    
        location /static/ {
            alias /home/<tu_usuario>/<nombre_de_la_carpeta_del_proyecto>/staticfiles/;
        }
    
        location / {
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_pass http://unix:/run/gunicorn/gunicorn.sock;
        }
    }
    
Desactiva el sitio por defecto y activa el tuyo:

# Puede que el archivo 'default' no exista si es una instalación limpia

    sudo rm /etc/nginx/sites-enabled/default
    sudo ln -s /etc/nginx/sites-available/folp-becarios /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx

## Fase 4: Securización y Tareas Finales

4.1. Configurar HTTPS con Let's Encrypt

    sudo apt install certbot python3-certbot-nginx -y
    sudo certbot --nginx -d tudominio.com -d www.tudominio.com

4.2. Configurar Tarea Programada (Cron)

Edita el crontab del usuario:

    crontab -e

Añade la línea para la tarea de cierre de fichajes:

    1 19 * * 1-5 /home/<tu_usuario>/<nombre_de_la_carpeta_del_proyecto>/venv/bin/python /home/<tu_usuario>/<nombre_de_la_carpeta_del_proyecto>/manage.py cerrar_fichajes

4.3. Configuración para Proxmox (Si se usa LXC en red privada)

En el anfitrión Proxmox, crea las reglas de reenvío de puertos.

# Habilita el reenvío de IP

    echo 1 > /proc/sys/net/ipv4/ip_forward

# Crea las reglas (reemplaza <IP_DEL_CONTENEDOR>)

    iptables -t nat -A PREROUTING -i vmbr0 -p tcp --dport 80 -j DNAT --to <IP_DEL_CONTENEDOR>:80
    iptables -t nat -A PREROUTING -i vmbr0 -p tcp --dport 443 -j DNAT --to <IP_DEL_CONTENEDOR>:443

# Haz las reglas persistentes
    
    sudo apt-get install iptables-persistent

# (Acepta guardar las reglas cuando se te pregunte)

Con estos pasos, tienes una guía completa y reproducible para el despliegue de tu aplicación.
