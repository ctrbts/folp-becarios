# usuarios/models.py

from django.db import models


class Becario(models.Model):
    """
    Representa a un becario en el sistema.
    Almacena su información personal y de fichaje.
    """

    pin = models.CharField(
        max_length=8,
        unique=True,
        help_text="PIN numérico único para fichar. Debe ser asignado manualmente.",
    )
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(
        max_length=15, unique=True, help_text="Documento Nacional de Identidad."
    )

    # Horario teórico para calcular ausencias o llegadas tarde en futuros reportes.
    horario_entrada_teorico = models.TimeField()
    horario_salida_teorico = models.TimeField()

    activo = models.BooleanField(
        default=True,
        help_text="Indica si el becario está actualmente activo en el programa.",
    )

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

    class Meta:
        verbose_name = "Becario"
        verbose_name_plural = "Becarios"
