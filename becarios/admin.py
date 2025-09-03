# becarios/admin.py

from django.contrib import admin
from .models import Becario


@admin.register(Becario)
class BecarioAdmin(admin.ModelAdmin):
    list_display = ("apellido", "nombre", "dni", "pin", "activo")
    list_filter = ("activo",)
    search_fields = ("apellido", "nombre", "dni", "pin")
    ordering = ("apellido", "nombre")


admin.site.site_header = "Administración de Becarios"
