"""Páginas del comprador: buscar productos (sin cuenta) y apartarlos (con cuenta)."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

import reglas
import servicio
from auth import requiere_rol
from db import get_db
from reglas import ErrorRegla

bp = Blueprint("comprador", __name__, url_prefix="/comprar")


@bp.route("/")
def catalogo():
    """Cualquiera puede ver los productos; para apartar hay que entrar."""
    filtros = {
        "buscar": request.args.get("buscar", "").strip(),
        "categoria": request.args.get("categoria", ""),
        "max_dias": request.args.get("max_dias", ""),
        "precio_max": request.args.get("precio_max", ""),
    }
    try:
        lotes = servicio.catalogo(get_db(), **filtros)
    except ValueError:
        flash("Revisa los filtros: los días y el precio deben ser números.", "error")
        lotes = servicio.catalogo(get_db())
    return render_template("comprador_catalogo.html", lotes=lotes, filtros=filtros, categorias=reglas.CATEGORIAS)


@bp.post("/apartar/<int:lote_id>")
@requiere_rol("comprador")
def apartar(lote_id):
    try:
        reserva_id = servicio.reservar(
            get_db(), lote_id, "compra", g.usuario["nombre"], request.form.get("cantidad"), usuario_id=g.usuario["id"]
        )
        flash(f"¡Listo! Tu apartado es el #{reserva_id}. Recógelo en la tienda y di ese número.", "exito")
        return redirect(url_for("comprador.apartados"))
    except ErrorRegla as error:
        flash(str(error), "error")
    return redirect(request.referrer or url_for("comprador.catalogo"))


@bp.route("/mis-apartados")
@requiere_rol("comprador")
def apartados():
    return render_template("comprador_apartados.html", apartados=servicio.apartados_de_usuario(get_db(), g.usuario["id"]))


@bp.post("/mis-apartados/<int:reserva_id>/cancelar")
@requiere_rol("comprador")
def cancelar(reserva_id):
    if not servicio.reserva_es_de_usuario(get_db(), reserva_id, g.usuario["id"]):
        abort(404)
    try:
        servicio.cancelar_reserva(get_db(), reserva_id)
        flash("Cancelaste tu apartado.", "aviso")
    except ErrorRegla as error:
        flash(str(error), "error")
    return redirect(url_for("comprador.apartados"))
