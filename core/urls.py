# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Cuando alguien visite la raíz del sitio (''), se ejecutará la vista 'vista_fichaje'
    path("", views.vista_fichaje, name="fichaje"),
]
