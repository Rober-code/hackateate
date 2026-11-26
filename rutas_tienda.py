"""Páginas de la tienda: ver sus productos, registrar nuevos y entregar apartados."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

import reglas
import servicio
from auth import requiere_rol
from db import get_db
from reglas import ErrorRegla

bp = Blueprint("tienda", __name__, url_prefix="/tienda")


def tienda_id():
    """La tienda de la cuenta que inició sesión."""
    return g.usuario["tienda_id"]


@bp.route("/")
@requiere_rol("tienda")
def panel():
    con = get_db()
    return render_template(
        "tienda_panel.html",
        tienda=servicio.obtener_tienda(con, tienda_id()),
        lotes=servicio.lotes_de_tienda(con, tienda_id()),
        reservas=servicio.reservas_pendientes(con, tienda_id()),
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@requiere_rol("tienda")
def nuevo():
    if request.method == "POST":
        try:
            servicio.crear_lote(get_db(), tienda_id(), request.form)
            flash(f"Se registró: {request.form['producto']}.", "exito")
            return redirect(url_for("tienda.panel"))
        except ErrorRegla as error:
            flash(str(error), "error")
    return render_template(
        "tienda_nuevo.html", categorias=reglas.CATEGORIAS, unidades=reglas.UNIDADES, datos=request.form
    )


def revisar_que_sea_mia(reserva_id):
    if not servicio.reserva_es_de_tienda(get_db(), reserva_id, tienda_id()):
        abort(404)


@bp.post("/apartados/<int:reserva_id>/entregar")
@requiere_rol("tienda")
def entregar(reserva_id):
    revisar_que_sea_mia(reserva_id)
    try:
        servicio.confirmar_recogida(get_db(), reserva_id)
        flash("Entrega registrada.", "exito")
    except ErrorRegla as error:
        flash(str(error), "error")
    return redirect(url_for("tienda.panel"))


@bp.post("/apartados/<int:reserva_id>/cancelar")
@requiere_rol("tienda")
def cancelar(reserva_id):
    revisar_que_sea_mia(reserva_id)
    try:
        servicio.cancelar_reserva(get_db(), reserva_id)
        flash("Apartado cancelado; las unidades volvieron a estar disponibles.", "aviso")
    except ErrorRegla as error:
        flash(str(error), "error")
    return redirect(url_for("tienda.panel"))
