# fichajes/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("", views.vista_fichaje, name="fichaje"),
]
