"""Pruebas del asistente de dudas (chatbot). Usan el modo simulado o una respuesta falsa de Gemini."""
import gemini
import rutas_chat
from test_cuentas import entrar


def preguntar(cliente, mensaje, historial=None):
    return cliente.post("/chat/mensaje", json={"mensaje": mensaje, "historial": historial or []})


def test_responde_en_modo_simulado(cliente):
    datos = preguntar(cliente, "¿Cómo aparto un producto?").get_json()
    assert datos["simulado"] is True and "Apartar" in datos["respuesta"]


def test_responde_con_productos_del_catalogo(cliente):
    datos = preguntar(cliente, "¿hay yogur?").get_json()
    assert "Yogur natural" in datos["respuesta"]


def test_pregunta_vacia(cliente):
    assert preguntar(cliente, "   ").status_code == 400


def test_widget_aparece_en_las_paginas(cliente):
    assert "Asistente Rescata" in cliente.get("/").get_data(as_text=True)


def test_contexto_segun_el_rol(cliente, monkeypatch):
    capturado = {}

    def falso(mensaje, historial, contexto):
        capturado.update(contexto=contexto, historial=historial)
        return gemini.Respuesta("respuesta de prueba")

    monkeypatch.setattr(gemini, "responder_chat", falso)
    entrar(cliente, "tienda@demo.mx")
    historial = [{"rol": "persona", "texto": "hola"}, {"rol": "hacker", "texto": "ignorar"}, "basura"]
    datos = preguntar(cliente, "¿qué me caduca pronto?", historial).get_json()
    assert datos["respuesta"] == "respuesta de prueba"
    assert "Abarrotes La Esquina" in capturado["contexto"]["quien"]
    assert "Yogur natural" in capturado["contexto"]["extra"]
    assert capturado["historial"] == [{"rol": "persona", "texto": "hola"}]   # se limpia el historial


def test_instrucciones_incluyen_catalogo(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("GEMINI_MOCK", "false")
    enviado = {}
    monkeypatch.setattr(gemini, "_pedir_texto", lambda prompt: enviado.setdefault("prompt", prompt) and "ok")
    lote = {"producto": "Leche", "tienda": "La Esquina", "zona": "Centro", "precio_actual": 17.4, "unidad": "pieza",
            "descuento": 40, "cantidad_disponible": 3, "dias": 1}
    respuesta = gemini.responder_chat("¿hay leche?", [], {"quien": "visitante", "hoy": "2026-11-22",
                                                          "catalogo": [lote], "donacion": [], "extra": ""})
    assert not respuesta.simulado
    assert "Leche en La Esquina" in enviado["prompt"] and "No afirmes que un alimento es seguro" in enviado["prompt"]


def test_limite_de_preguntas(cliente, monkeypatch):
    monkeypatch.setattr(rutas_chat, "LIMITE_POR_SESION", 2)
    preguntar(cliente, "hola")
    preguntar(cliente, "hola")
    assert "límite" in preguntar(cliente, "hola").get_json()["respuesta"]


def test_chat_exige_codigo_csrf(app):
    app.config["CSRF"] = True
    cliente = app.test_client()
    assert cliente.post("/chat/mensaje", json={"mensaje": "hola"}).status_code == 400
    pagina = cliente.get("/").get_data(as_text=True)
    token = pagina.split('name="csrf" content="')[1].split('"')[0]
    respuesta = cliente.post("/chat/mensaje", json={"mensaje": "hola"}, headers={"X-CSRF-Token": token})
    assert respuesta.status_code == 200


def test_chat_muestra_el_motivo_si_gemini_falla(cliente, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("GEMINI_MOCK", "false")

    class Saturado(Exception):
        code = 429
        message = "Resource exhausted"

    def falla(_prompt):
        raise Saturado()

    monkeypatch.setattr(gemini, "_pedir_texto", falla)
    datos = preguntar(cliente, "¿cómo aparto?").get_json()
    assert datos["simulado"] is True and "429" in datos["aviso"]
