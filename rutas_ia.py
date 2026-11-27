"""Páginas donde la tienda usa Gemini: registrar con foto o dictado, alertas, WhatsApp y recomendaciones.

Regla de oro: Gemini propone, la tienda revisa y confirma antes de guardar.
"""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

import gemini
import reglas
import servicio
from auth import requiere_rol
from db import get_db
from reglas import ErrorRegla

bp = Blueprint("ia", __name__, url_prefix="/tienda/ia")

CAMPOS = ["producto", "categoria", "cantidad", "unidad", "precio", "fecha_caducidad", "fecha_estimada", "nota"]


def tienda_id():
    return g.usuario["tienda_id"]


def mostrar_confirmacion(productos, simulado=False, aviso=None):
    return render_template(
        "ia_confirmar.html", productos=productos, simulado=simulado, aviso=aviso,
        categorias=reglas.CATEGORIAS, unidades=reglas.UNIDADES,
    )


@bp.route("/capturar")
@requiere_rol("tienda")
def capturar():
    return render_template("ia_capturar.html", simulado=gemini.modo_simulado(), modelo=gemini.nombre_modelo())


@bp.post("/capturar/foto")
@requiere_rol("tienda")
def capturar_foto():
    archivo = request.files.get("foto")
    if not archivo or not archivo.filename:
        flash("Elige o toma una foto primero.", "error")
        return redirect(url_for("ia.capturar"))
    if not (archivo.mimetype or "").startswith("image/"):
        flash("El archivo debe ser una imagen (JPG o PNG).", "error")
        return redirect(url_for("ia.capturar"))
    respuesta = gemini.leer_foto(archivo.read(), archivo.mimetype, servicio.hoy(get_db()))
    if not respuesta.contenido:
        flash("Gemini no encontró productos en la foto. Intenta con más luz o más cerca de la etiqueta.", "error")
        return redirect(url_for("ia.capturar"))
    return mostrar_confirmacion(respuesta.contenido, respuesta.simulado, respuesta.aviso)


@bp.post("/capturar/texto")
@requiere_rol("tienda")
def capturar_texto():
    texto = (request.form.get("texto") or "").strip()
    if not texto:
        flash("Dicta o escribe qué productos quieres registrar.", "error")
        return redirect(url_for("ia.capturar"))
    respuesta = gemini.leer_texto(texto[:1000], servicio.hoy(get_db()))
    if not respuesta.contenido:
        flash("No se entendieron productos en el texto. Prueba con: 'me sobraron 12 bolillos y 4 leches'.", "error")
        return redirect(url_for("ia.capturar"))
    return mostrar_confirmacion(respuesta.contenido, respuesta.simulado, respuesta.aviso)


@bp.post("/capturar/guardar")
@requiere_rol("tienda")
def guardar():
    """Guarda las filas marcadas. Las que tengan errores se vuelven a mostrar para corregirlas."""
    con = get_db()
    guardados, pendientes = [], []
    for i in range(request.form.get("total", type=int, default=0)):
        if not request.form.get(f"incluir_{i}"):
            continue
        fila = {campo: request.form.get(f"{campo}_{i}", "") for campo in CAMPOS}
        try:
            servicio.crear_lote(con, tienda_id(), fila, capturado_con_ia=True)
            guardados.append(fila["producto"])
        except ErrorRegla as error:
            fila["error"] = str(error)
            fila["fecha_estimada"] = fila["fecha_estimada"] in ("1", "on")
            pendientes.append(fila)
    if guardados:
        flash(f"Se registraron {len(guardados)} producto(s): {', '.join(guardados)}.", "exito")
    if pendientes:
        flash("Corrige los productos marcados y vuelve a guardar.", "error")
        return mostrar_confirmacion(pendientes)
    if not guardados:
        flash("No marcaste ningún producto para guardar.", "aviso")
    return redirect(url_for("tienda.panel"))


def productos_por_caducar(con):
    return [l for l in servicio.lotes_de_tienda(con, tienda_id())
            if l["cantidad_disponible"] > 0 and (l["estado"] == "donacion" or (l["estado"] == "venta" and l["dias"] <= 2))]


@bp.route("/alerta")
@requiere_rol("tienda")
def alerta():
    con = get_db()
    tienda = servicio.obtener_tienda(con, tienda_id())
    lotes = productos_por_caducar(con)
    respuesta = gemini.redactar_alerta(tienda["nombre"], lotes) if lotes else gemini.Respuesta("No hay productos por caducar hoy.")
    return render_template("ia_texto.html", titulo="Alerta del día", respuesta=respuesta, compartir=False)


@bp.route("/whatsapp")
@requiere_rol("tienda")
def whatsapp():
    con = get_db()
    tienda = servicio.obtener_tienda(con, tienda_id())
    ofertas = [l for l in servicio.lotes_de_tienda(con, tienda_id())
               if l["estado"] == "venta" and l["descuento"] and l["cantidad_disponible"] > 0]
    if not ofertas:
        flash("Hoy no hay productos con descuento para compartir.", "aviso")
        return redirect(url_for("tienda.panel"))
    respuesta = gemini.mensaje_ofertas(tienda["nombre"], tienda["zona"], ofertas)
    return render_template("ia_texto.html", titulo="Ofertas para WhatsApp", respuesta=respuesta, compartir=True)


@bp.route("/recomendaciones")
@requiere_rol("tienda")
def recomendaciones():
    con = get_db()
    tienda = servicio.obtener_tienda(con, tienda_id())
    respuesta = gemini.recomendaciones(tienda["nombre"], servicio.impacto(con, tienda_id()))
    return render_template("ia_texto.html", titulo="Recomendaciones de Gemini", respuesta=respuesta, compartir=False)
