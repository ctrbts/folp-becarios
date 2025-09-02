# core/middleware.py

from django.http import HttpResponseForbidden


class IPRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # --- CONFIGURACIÓN ---
        # Añade aquí la dirección IP estática de la PC de la mesa de entradas.
        # '127.0.0.1' es la IP local, necesaria para que puedas probarlo en tu computadora.
        self.allowed_ips = ["127.0.0.1", "163.10.29.154"]  # ¡REEMPLAZAR con la IP real!

    def __call__(self, request):
        # Queremos aplicar esta restricción solo a la página de fichaje ('/').
        # Excluimos el panel de administración ('/admin/') para que el admin pueda acceder remotamente.
        if not request.path.startswith("/admin/"):
            # Obtenemos la IP del cliente que hace la petición.
            client_ip = request.META.get("REMOTE_ADDR")

            if client_ip not in self.allowed_ips:
                # Si la IP no está en nuestra lista, devolvemos un error 403 Forbidden.
                return HttpResponseForbidden(
                    "Acceso denegado. Solo se puede fichar desde la ubicación autorizada."
                )

        # Si la IP es válida o la ruta es del admin, la petición continúa su curso normal.
        response = self.get_response(request)
        return response
