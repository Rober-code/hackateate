"""Conexión a la base de datos SQLite.

Flask abre una conexión por cada visita (request) y la cierra al terminar.
Si el archivo de la base no existe, se crea con datos de demostración.
"""
import os
import sqlite3
from datetime import date

from flask import current_app, g

CARPETA = os.path.dirname(os.path.abspath(__file__))


def conectar(ruta):
    """Abre la base y hace que cada fila se pueda leer como diccionario: fila['producto']."""
    con = sqlite3.connect(ruta)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def get_db():
    """Devuelve la conexión de esta visita (la crea la primera vez que se pide)."""
    if "db" not in g:
        g.db = conectar(current_app.config["DATABASE"])
    return g.db


def cerrar_db(_error=None):
    con = g.pop("db", None)
    if con is not None:
        con.close()


def crear_tablas(con):
    with open(os.path.join(CARPETA, "schema.sql"), encoding="utf-8") as archivo:
        con.executescript(archivo.read())
    con.execute("INSERT INTO config (clave, valor) VALUES ('dias_simulados', '0')")
    con.commit()


def iniciar_bd(ruta, con_datos_demo=True, hoy=None):
    """Borra y vuelve a crear la base. Con datos demo agrega tiendas, cuentas y productos de prueba."""
    from datos_demo import sembrar  # se importa aquí para evitar importaciones circulares

    con = conectar(ruta)
    crear_tablas(con)
    if con_datos_demo:
        sembrar(con, hoy or date.today())
    con.close()


def preparar_app(app):
    """Conecta la base con la app de Flask."""
    app.teardown_appcontext(cerrar_db)
    ruta = app.config["DATABASE"]
    if not os.path.exists(ruta):
        iniciar_bd(ruta)
