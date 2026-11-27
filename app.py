"""Punto de entrada de Rescata.

Para ejecutar:  python app.py   y abrir http://127.0.0.1:5000
"""
import os
import secrets
from datetime import date

from dotenv import load_dotenv
from flask import Flask, abort, g, render_template, request, session

import db
import servicio

load_dotenv()  # lee el archivo .env (ahí va la clave de Gemini, nunca en el código)

DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def formato_fecha(valor):
    """'2026-11-25' -> 'mié 25 nov'"""
    f = date.fromisoformat(valor) if isinstance(valor, str) else valor
    return f"{DIAS[f.weekday()]} {f.day} {MESES[f.month - 1]}"


def formato_dinero(valor):
    return f"${valor:,.2f}"


def token_csrf():
    """Código secreto por sesión que va escondido en cada formulario.

    Evita que otra página web envíe formularios a Rescata haciéndose pasar por el usuario.
    """
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "cambia-esta-clave-en-el-archivo-env"),
        DATABASE=os.path.join(db.CARPETA, "rescata.db"),
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,  # fotos de hasta 10 MB
        CSRF=True,
    )
    if config:
        app.config.update(config)

    db.preparar_app(app)
    app.add_template_filter(formato_fecha, "fecha")
    app.add_template_filter(formato_dinero, "dinero")
    app.jinja_env.globals["token_csrf"] = token_csrf
    # tiene('tienda.panel') -> True si esa página ya existe (sirve para mostrar enlaces solo si existen)
    app.jinja_env.globals["tiene"] = lambda endpoint: endpoint in app.view_functions

    @app.before_request
    def revisar_csrf():
        if app.config["CSRF"] and request.method == "POST":
            enviado = request.form.get("_csrf") or request.headers.get("X-CSRF-Token", "")
            if not enviado or not secrets.compare_digest(enviado, session.get("_csrf", "")):
                abort(400)

    import auth
    import rutas_comprador
    import rutas_demo
    import rutas_ia
    import rutas_organizacion
    import rutas_tienda

    @app.before_request
    def aplicar_escalera():
        """En cada visita, cada producto pasa al escalón que le toca según su fecha."""
        servicio.actualizar_estados(db.get_db())

    app.before_request(auth.cargar_usuario)
    app.register_blueprint(auth.bp)
    app.register_blueprint(rutas_tienda.bp)
    app.register_blueprint(rutas_comprador.bp)
    app.register_blueprint(rutas_organizacion.bp)
    app.register_blueprint(rutas_demo.bp)
    app.register_blueprint(rutas_ia.bp)

    @app.context_processor
    def datos_para_todas_las_paginas():
        con = db.get_db()
        return {"hoy": servicio.hoy(con), "dias_simulados": servicio.dias_simulados(con), "usuario": g.get("usuario")}

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def error(e):
        return render_template("error.html", codigo=e.code), e.code

    @app.route("/")
    def inicio():
        return render_template("inicio.html", stats=servicio.estadisticas_publicas(db.get_db()))

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
