# core/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from becarios.models import Becario
from fichajes.models import Marcacion
import datetime


def es_horario_valido(becario_time, now_aware):
    """
    Verifica si una marcación está dentro de la tolerancia de +/- 15 minutos.
    Esta versión es robusta y maneja correctamente las zonas horarias.
    """
    tolerancia = datetime.timedelta(minutes=15)

    # 1. Crea un datetime 'naive' para el horario teórico en la fecha actual
    horario_teorico_naive = datetime.datetime.combine(now_aware.date(), becario_time)

    # 2. Convierte ese datetime 'naive' a 'aware' usando la zona horaria actual
    horario_teorico_aware = timezone.make_aware(horario_teorico_naive)

    # 3. Calcula la diferencia absoluta entre la hora actual y la teórica
    diferencia = abs(now_aware - horario_teorico_aware)

    # 4. Comprueba si la diferencia está dentro de la tolerancia
    return diferencia <= tolerancia


def vista_fichaje(request):
    if request.method == "POST":
        pin_ingresado = request.POST.get("pin")
        now = timezone.now()

        # --- VALIDACIÓN 1: Horario de acceso ---
        """ if now.weekday() > 4 or not (
            datetime.time(7, 0) <= now.time() <= datetime.time(20, 0)
        ):
            messages.error(
                request,
                "Error: Solo se puede fichar de Lunes a Viernes de 7:00 a 20:00 hs.",
            )
            return redirect("fichaje") """

        # --- VALIDACIÓN 2: Becario existe (sin cambios) ---
        try:
            becario = Becario.objects.get(pin=pin_ingresado, activo=True)
        except Becario.DoesNotExist:
            messages.error(request, "Error: PIN incorrecto o becario inactivo.")
            return redirect("fichaje")

        marcacion_abierta = Marcacion.objects.filter(
            becario=becario, salida__isnull=True
        ).first()

        # --- LÓGICA DE FICHAJE REVISADA ---
        if marcacion_abierta:
            # --- CASO: FICHAJE DE SALIDA ---
            marcacion_abierta.salida = now

            # REGLA: Validar si la salida está fuera del horario teórico (+/- 15 min)
            if not es_horario_valido(becario.horario_salida_teorico, now):
                marcacion_abierta.estado = Marcacion.EstadoMarcacion.REQUIERE_REVISION
                messages.warning(
                    request,
                    f"🔔 Salida registrada fuera de horario, {becario.nombre}. El registro requiere revisión.",
                )
            else:
                messages.success(
                    request,
                    f"✅ Salida registrada con éxito, {becario.nombre}. ¡Hasta luego!",
                )

            marcacion_abierta.save()
        else:
            # --- CASO: FICHAJE DE ENTRADA ---

            # REGLA: Detectar si ya hubo un fichaje completo hoy (esto es una "entrada duplicada")
            hubo_fichaje_previo_hoy = Marcacion.objects.filter(
                becario=becario, entrada__date=now.date()
            ).exists()

            nueva_marcacion = Marcacion.objects.create(becario=becario, entrada=now)

            # REGLA: Validar si la entrada está fuera del horario teórico (+/- 15 min)
            fuera_de_horario = not es_horario_valido(
                becario.horario_entrada_teorico, now
            )

            if hubo_fichaje_previo_hoy:
                nueva_marcacion.estado = Marcacion.EstadoMarcacion.REQUIERE_REVISION
                messages.warning(
                    request,
                    f"🔔 Se detectó una segunda entrada hoy, {becario.nombre}. El registro requiere revisión.",
                )
            elif fuera_de_horario:
                nueva_marcacion.estado = Marcacion.EstadoMarcacion.REQUIERE_REVISION
                messages.warning(
                    request,
                    f"🔔 Entrada registrada fuera de horario, {becario.nombre}. El registro requiere revisión.",
                )
            else:
                messages.success(
                    request,
                    f"✅ Entrada registrada con éxito, {becario.nombre}. ¡Bienvenido/a!",
                )

            nueva_marcacion.save()

        return redirect("fichaje")

    return render(request, "fichajes/fichaje.html")
