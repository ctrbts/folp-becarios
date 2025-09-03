# fichajes/management/commands/cerrar_fichajes.py

"""
Ejecutar el cierre de fichajes todos los días de Lunes a Viernes a las 23:01
En un servidor Linux, puedes agregar la siguiente línea a tu crontab con 'crontab -e':
1 23 * * 1-5 /ruta/a/tu/entorno/virtual/bin/python /ruta/a/tu/proyecto/manage.py cerrar_fichajes
"""

import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from fichajes.models import Marcacion


class Command(BaseCommand):
    """
    Comando de Django para cerrar automáticamente las marcaciones que quedaron abiertas.
    Busca fichajes sin hora de salida y les asigna las 22:59 hs del día de entrada.
    """

    help = (
        "Cierra todas las marcaciones de entrada que no tengan una salida registrada."
    )

    def handle(self, *args, **options):
        # Obtenemos todas las marcaciones que no tienen hora de salida.
        marcaciones_pendientes = Marcacion.objects.filter(salida__isnull=True)

        # Contamos cuántas se encontraron para informar al final.
        cantidad_pendientes = marcaciones_pendientes.count()

        if cantidad_pendientes == 0:
            self.stdout.write(
                self.style.SUCCESS("No hay marcaciones pendientes por cerrar.")
            )
            return

        self.stdout.write(
            f"Se encontraron {cantidad_pendientes} marcaciones pendientes. Procesando..."
        )

        for marcacion in marcaciones_pendientes:
            # Creamos un objeto datetime para la hora de cierre: 22:59 hs del día de la entrada.
            hora_cierre = timezone.make_aware(
                datetime.datetime.combine(
                    marcacion.entrada.date(), datetime.time(22, 59)
                )
            )

            # Actualizamos el registro
            marcacion.salida = hora_cierre
            marcacion.estado = Marcacion.EstadoMarcacion.CIERRE_AUTOMATICO
            marcacion.save()

            self.stdout.write(
                f'  - Marcación de {marcacion.becario} del {marcacion.entrada.strftime("%d/%m/%Y")} cerrada.'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Proceso finalizado. Se cerraron {cantidad_pendientes} marcaciones."
            )
        )
