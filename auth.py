"""Cuentas: crear cuenta, entrar y salir, y proteger páginas según el rol.

Roles:
  comprador     busca productos y los aparta
  tienda        registra productos y entrega apartados
  organizacion  recibe donativos
"""
import os
from functools import wraps

from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for

import servicio
from datos_demo import CONTRASENA_DEMO, CUENTAS
from db import get_db
from reglas import ErrorRegla

bp = Blueprint("auth", __name__)


def cargar_usuario():
    """Antes de cada visita: si hay sesión iniciada, carga al usuario en g.usuario."""
    usuario_id = session.get("usuario_id")
    g.usuario = servicio.obtener_usuario(get_db(), usuario_id) if usuario_id else None


def requiere_rol(*roles):
    """Decorador: la página solo se abre con sesión iniciada y con uno de estos roles."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if g.usuario is None:
                flash("Entra a tu cuenta para continuar.", "aviso")
                return redirect(url_for("auth.entrar", siguiente=request.full_path))
            if roles and g.usuario["rol"] not in roles:
                abort(403)
            return vista(*args, **kwargs)
        return envoltura
    return decorador


def pagina_de_inicio(rol):
    """A dónde llevar a cada rol después de entrar."""
    destinos = {"tienda": "tienda.panel", "organizacion": "organizacion.panel", "comprador": "comprador.catalogo"}
    endpoint = destinos.get(rol, "inicio")
    return url_for(endpoint) if endpoint in _vistas() else url_for("inicio")


def _vistas():
    from flask import current_app
    return current_app.view_functions


def destino_seguro(siguiente):
    """Solo se permite regresar a páginas de Rescata (evita redirigir a sitios externos)."""
    if siguiente and siguiente.startswith("/") and not siguiente.startswith("//"):
        return siguiente
    return None


def iniciar_sesion(usuario_id):
    session.clear()
    session["usuario_id"] = usuario_id


@bp.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        try:
            usuario_id = servicio.crear_cuenta(get_db(), request.form)
            iniciar_sesion(usuario_id)
            flash(f"¡Bienvenido(a), {request.form['nombre'].strip()}! Tu cuenta está lista.", "exito")
            return redirect(pagina_de_inicio(request.form["rol"]))
        except ErrorRegla as error:
            flash(str(error), "error")
    rol = request.values.get("rol") or "comprador"
    return render_template("auth_registro.html", rol=rol, datos=request.form)


@bp.route("/entrar", methods=["GET", "POST"])
def entrar():
    siguiente = destino_seguro(request.values.get("siguiente"))
    if request.method == "POST":
        usuario = servicio.autenticar(get_db(), request.form.get("email"), request.form.get("contrasena"))
        if usuario:
            iniciar_sesion(usuario["id"])
            flash(f"Hola, {usuario['nombre']}.", "exito")
            return redirect(siguiente or pagina_de_inicio(usuario["rol"]))
        flash("Correo o contraseña incorrectos.", "error")
    mostrar_demo = os.getenv("MOSTRAR_CUENTAS_DEMO", "true").lower() != "false"
    return render_template(
        "auth_entrar.html", siguiente=siguiente or "", email=request.form.get("email", ""),
        cuentas_demo=CUENTAS if mostrar_demo else [], contrasena_demo=CONTRASENA_DEMO,
    )


@bp.post("/salir")
def salir():
    session.clear()
    flash("Cerraste sesión.", "aviso")
    return redirect(url_for("inicio"))
