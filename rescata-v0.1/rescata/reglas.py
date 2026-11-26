"""Reglas del negocio, escritas como funciones simples para poder probarlas.

Aquí no hay base de datos ni páginas web: solo cálculos. Así es fácil
explicarlas al jurado y comprobarlas con pruebas automáticas (carpeta tests/).
"""
from datetime import date, timedelta

CATEGORIAS = [
    "Lácteos",
    "Panadería",
    "Frutas y verduras",
    "Carnes y embutidos",
    "Comida preparada",
    "Abarrotes",
    "Bebidas",
    "Otro",
]

UNIDADES = ["pieza", "paquete", "kg", "litro"]


class ErrorRegla(ValueError):
    """Error que se le muestra a la persona usuaria (por ejemplo: 'Solo quedan 3 piezas')."""


def hoy_simulado(dias_simulados, hoy_real=None):
    """La demo puede 'adelantar el reloj'. Esta es la fecha que usa toda la app."""
    return (hoy_real or date.today()) + timedelta(days=int(dias_simulados))


def dias_restantes(fecha_caducidad, hoy):
    """Días que faltan para caducar. 0 = caduca hoy, negativo = ya caducó."""
    return (date.fromisoformat(fecha_caducidad) - hoy).days
