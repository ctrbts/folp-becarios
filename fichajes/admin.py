# fichajes/admin.py

import csv
from datetime import timedelta
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path
from .models import Marcacion


@admin.register(Marcacion)
class MarcacionAdmin(admin.ModelAdmin):
    list_display = ("becario", "entrada", "salida", "estado", "horas_trabajadas")
    list_filter = ("estado", "entrada")
    search_fields = ("becario__apellido", "becario__nombre")
    readonly_fields = ("horas_trabajadas",)

    # --- INICIO DE LA LÓGICA DE REPORTES ---

    def get_urls(self):
        """
        Añade nuestra URL personalizada para el reporte al conjunto de URLs del admin.
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                "reporte/",
                self.admin_site.admin_view(self.vista_reporte),
                name="fichajes_reporte",
            ),
        ]
        return custom_urls + urls

    def vista_reporte(self, request):
        """
        La vista que maneja tanto la página del formulario como la exportación a CSV.
        """
        if request.method == "POST":
            # Si se envió el formulario, generamos el CSV
            start_date = request.POST.get("start_date")
            end_date = request.POST.get("end_date")

            # Filtramos las marcaciones en el rango de fechas que estén completas
            queryset = Marcacion.objects.filter(
                entrada__date__range=[start_date, end_date],
                salida__isnull=False
            ).exclude(
                estado=Marcacion.EstadoMarcacion.REQUIERE_REVISION
            ).order_by('becario__apellido', 'entrada')

            # Creamos la respuesta HTTP con la cabecera para CSV
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="reporte_fichajes_{start_date}_a_{end_date}.csv"'
            )

            writer = csv.writer(response)
            # Escribimos la fila de encabezado del CSV
            writer.writerow(
                [
                    "Apellido",
                    "Nombre",
                    "DNI",
                    "Fecha",
                    "Hora Entrada",
                    "Hora Salida",
                    "Horas Trabajadas",
                    "Estado",
                ]
            )

            # Escribimos los datos de cada marcación
            for marcacion in queryset:
                horas_trabajadas_str = "0:00:00"
                if marcacion.horas_trabajadas:
                    # Formateamos el timedelta para que sea legible
                    total_seconds = marcacion.horas_trabajadas.total_seconds()
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    horas_trabajadas_str = (
                        f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
                    )

                writer.writerow(
                    [
                        marcacion.becario.apellido,
                        marcacion.becario.nombre,
                        marcacion.becario.dni,
                        marcacion.entrada.strftime("%Y-%m-%d"),
                        marcacion.entrada.strftime("%H:%M:%S"),
                        marcacion.salida.strftime("%H:%M:%S"),
                        horas_trabajadas_str,
                        marcacion.get_estado_display(),  # Muestra el texto legible del estado
                    ]
                )

            return response

        # Si el método es GET, mostramos la página con el formulario
        context = dict(
            self.admin_site.each_context(request),
        )
        return render(request, "admin/fichajes/reporte.html", context)
