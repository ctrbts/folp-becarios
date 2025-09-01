# fichajes/models.py

from django.db import models
from usuarios.models import (
    Becario,
)  # Asegúrate de que la importación coincida con tu estructura


class Marcacion(models.Model):
    """
    Representa un registro de fichaje (entrada/salida) para un becario.
    """

    class EstadoMarcacion(models.TextChoices):
        CORRECTA = "CORRECTA", "Correcta"
        CIERRE_AUTOMATICO = "CIERRE_AUTOMATICO", "Cierre Automático por Olvido"
        REQUIERE_REVISION = "REQUIERE_REVISION", "Requiere Revisión"
        CORREGIDA_ADMIN = "CORREGIDA_ADMIN", "Corregida por Admin"

    becario = models.ForeignKey(
        Becario, on_delete=models.CASCADE, related_name="marcaciones"
    )

    entrada = models.DateTimeField(help_text="Fecha y hora de entrada.")
    salida = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de salida. Nulo si el becario aún no ha fichado la salida.",
    )

    estado = models.CharField(
        max_length=20, choices=EstadoMarcacion.choices, default=EstadoMarcacion.CORRECTA
    )

    observaciones_admin = models.TextField(
        blank=True,
        help_text="Notas del administrador sobre esta marcación (ej. motivo de corrección).",
    )

    @property
    def horas_trabajadas(self):
        """Calcula la duración total de la marcación si está cerrada."""
        if self.entrada and self.salida:
            # Devuelve un objeto timedelta
            return self.salida - self.entrada
        return None

    def __str__(self):
        return f"Marcación de {self.becario} - {self.entrada.strftime('%d/%m/%Y')}"

    class Meta:
        verbose_name = "Marcación"
        verbose_name_plural = "Marcaciones"
        ordering = ["-entrada"]  # Muestra las más recientes primero
