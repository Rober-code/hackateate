"""Controles SOLO para la demo: adelantar el reloj y reiniciar los datos.

En la presentación hay que decir que el reloj es simulado: en la vida real
los días pasan solos y la escalera se aplica igual.
"""
from flask import Blueprint, current_app, flash, redirect, request, session, url_for

import servicio
from db import cerrar_db, get_db, iniciar_bd

bp = Blueprint("demo", __name__, url_prefix="/demo")


@bp.post("/avanzar")
def avanzar():
    resumen = servicio.avanzar_dias(get_db(), 1)
    partes = ["Avanzó 1 día (simulado)."]
    if resumen["a_donacion"]:
        partes.append(f"{resumen['a_donacion']} producto(s) pasaron a donación.")
    if resumen["cerrados"]:
        partes.append(
            f"{resumen['cerrados']} producto(s) caducaron y se cerraron; "
            f"{resumen['desechadas']} unidad(es) quedaron sin rescatar."
        )
    flash(" ".join(partes), "aviso")
    return redirect(request.referrer or url_for("inicio"))


@bp.post("/reiniciar")
def reiniciar():
    cerrar_db()
    iniciar_bd(current_app.config["DATABASE"])
    session.clear()  # las cuentas se vuelven a crear, así que se cierra la sesión
    flash("Demo reiniciada con los datos de prueba.", "aviso")
    return redirect(url_for("inicio"))
