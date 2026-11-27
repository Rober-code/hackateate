"""Asistente de dudas (chatbot) con Gemini, disponible en todas las páginas.

El navegador manda la pregunta y los últimos mensajes; el servidor arma el contexto
(qué es Rescata, quién pregunta y qué productos hay hoy) y le pide la respuesta a Gemini.
"""
from flask import Blueprint, g, jsonify, request, session

import gemini
import servicio
from db import get_db

bp = Blueprint("chat", __name__, url_prefix="/chat")

LIMITE_POR_SESION = 40      # protege la cuota de Gemini
MAX_CARACTERES = 500
MAX_HISTORIAL = 6


def limpiar_historial(historial):
    """Acepta solo mensajes con la forma esperada y recorta lo largo."""
    limpio = []
    for m in (historial if isinstance(historial, list) else [])[-MAX_HISTORIAL:]:
        if isinstance(m, dict) and m.get("rol") in ("persona", "asistente"):
            limpio.append({"rol": m["rol"], "texto": str(m.get("texto", ""))[:MAX_CARACTERES]})
    return limpio


def armar_contexto(con, usuario):
    """Lo que el asistente necesita saber para responder bien a esta persona."""
    extra = ""
    if usuario is None:
        quien = "visitante sin cuenta"
    elif usuario["rol"] == "comprador":
        quien = f"{usuario['nombre']}, comprador"
        pendientes = [a for a in servicio.apartados_de_usuario(con, usuario["id"]) if a["estado"] == "pendiente"]
        if pendientes:
            extra = "\nSus apartados pendientes:\n" + "\n".join(
                f"- #{a['id']} {a['cantidad']} {a['unidad']} de {a['producto']} en {a['tienda']}" for a in pendientes
            )
    elif usuario["rol"] == "tienda":
        quien = f"{usuario['nombre']}, encargada(o) de la tienda {usuario['tienda']}"
        lotes = [l for l in servicio.lotes_de_tienda(con, usuario["tienda_id"]) if l["estado"] != "cerrado"]
        extra = "\nProductos de su tienda:\n" + (
            "\n".join(f"- {l['producto']}: quedan {l['cantidad_disponible']}, faltan {l['dias']} día(s), estado {l['estado']}"
                      for l in lotes) or "(ninguno)"
        )
    else:
        quien = f"{usuario['nombre']}, de la organización {usuario['organizacion']}"
    return {
        "quien": quien,
        "hoy": servicio.hoy(con).isoformat(),
        "catalogo": servicio.catalogo(con),
        "donacion": servicio.lotes_en_donacion(con),
        "extra": extra,
    }


@bp.post("/mensaje")
def mensaje():
    datos = request.get_json(silent=True) or {}
    texto = str(datos.get("mensaje", "")).strip()[:MAX_CARACTERES]
    if not texto:
        return jsonify(error="Escribe una pregunta."), 400

    usados = session.get("chat_usados", 0)
    if usados >= LIMITE_POR_SESION:
        return jsonify(respuesta="Llegaste al límite de preguntas de esta sesión. Si necesitas más ayuda, pregunta directamente en la tienda.",
                       simulado=False)
    session["chat_usados"] = usados + 1

    respuesta = gemini.responder_chat(texto, limpiar_historial(datos.get("historial")), armar_contexto(get_db(), g.usuario))
    contenido = respuesta.contenido or "No tengo una respuesta para eso. Intenta preguntarlo de otra forma."
    return jsonify(respuesta=contenido, simulado=respuesta.simulado, aviso=respuesta.aviso)
