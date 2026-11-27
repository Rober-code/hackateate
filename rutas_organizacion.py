"""Páginas de la organización receptora: ver donativos del día y apartarlos con horario."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

import servicio
from auth import requiere_rol
from db import get_db
from reglas import ErrorRegla

bp = Blueprint("organizacion", __name__, url_prefix="/organizacion")


@bp.route("/")
@requiere_rol("organizacion")
def panel():
    con = get_db()
    return render_template(
        "organizacion_panel.html",
        lotes=servicio.lotes_en_donacion(con),
        donativos=servicio.donativos_de_organizacion(con, g.usuario["organizacion_id"]),
    )


@bp.post("/aceptar/<int:lote_id>")
@requiere_rol("organizacion")
def aceptar(lote_id):
    hora = (request.form.get("hora") or "").strip()
    try:
        if not hora:
            raise ErrorRegla("Indica a qué hora pasarán a recoger.")
        reserva_id = servicio.reservar(
            get_db(), lote_id, "donacion", request.form.get("nombre") or g.usuario["nombre"],
            request.form.get("cantidad"), usuario_id=g.usuario["id"], hora_recogida=hora,
            organizacion_id=g.usuario["organizacion_id"],
        )
        flash(f"Donativo apartado (#{reserva_id}). La tienda ya ve tu horario de recogida.", "exito")
    except ErrorRegla as error:
        flash(str(error), "error")
    return redirect(url_for("organizacion.panel"))
