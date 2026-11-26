"""Operaciones con la base de datos: todo lo que guarda o cambia información.

Las páginas (archivos rutas_*.py) solo leen el formulario, llaman a estas
funciones y muestran el resultado. Así la lógica queda en un solo lugar.
"""
from datetime import datetime

import reglas


def ahora():
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------- reloj de la demo

def dias_simulados(con):
    fila = con.execute("SELECT valor FROM config WHERE clave = 'dias_simulados'").fetchone()
    return int(fila["valor"]) if fila else 0


def hoy(con):
    """Fecha 'de hoy' para la app (incluye los días adelantados en la demo)."""
    return reglas.hoy_simulado(dias_simulados(con))


# ---------------------------------------------------------------- página de inicio

def estadisticas_publicas(con):
    """Números reales de la base para la página de inicio."""
    return {
        "disponibles": con.execute(
            "SELECT COUNT(*) FROM lotes WHERE estado = 'venta' AND cantidad_disponible > 0"
        ).fetchone()[0],
        "tiendas": con.execute("SELECT COUNT(*) FROM tiendas").fetchone()[0],
        "rescatadas": con.execute(
            "SELECT COALESCE(SUM(cantidad), 0) FROM resultados WHERE destino IN ('vendido', 'donado')"
        ).fetchone()[0],
    }
