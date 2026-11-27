"""Pruebas de la integración con Gemini, sin gastar cuota: se usa el modo simulado
o se reemplaza la llamada a Gemini por una respuesta falsa (monkeypatch)."""
import io
from datetime import date, timedelta

import gemini
import servicio
from test_cuentas import entrar

HOY = date(2026, 11, 22)


def test_modo_simulado_sin_clave(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_MOCK", "false")
    assert gemini.modo_simulado()
    respuesta = gemini.leer_foto(b"foto", "image/jpeg", HOY)
    assert respuesta.simulado and len(respuesta.contenido) == 3


def test_normalizar_corrige_valores_raros():
    limpios = gemini._normalizar([
        {"producto": "Leche", "categoria": "Inventada", "cantidad": "tres", "unidad": "caja",
         "fecha_caducidad": "25/11/2026", "fecha_estimada": False},
        {"producto": "", "categoria": "Lácteos"},  # sin nombre: se descarta
        {"producto": "Yogur", "categoria": "Lácteos", "cantidad": 2, "unidad": "pieza",
         "fecha_caducidad": "2026-11-20", "fecha_estimada": False},
        "esto no es un producto",
    ], HOY)
    assert len(limpios) == 2
    leche, yogur = limpios
    assert (leche["categoria"], leche["cantidad"], leche["unidad"], leche["fecha_caducidad"]) == ("Otro", 1, "pieza", "")
    assert yogur["caducado"] is True


def test_usa_la_respuesta_de_gemini_cuando_hay_clave(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("GEMINI_MOCK", "false")
    monkeypatch.setattr(gemini, "_pedir_json", lambda contenidos, esquema: {"productos": [
        {"producto": "Pan dulce", "categoria": "Panadería", "cantidad": 5, "unidad": "pieza",
         "fecha_caducidad": "2026-11-23", "fecha_estimada": True, "nota": "sin fecha impresa"}]})
    respuesta = gemini.leer_texto("me sobraron 5 conchas", HOY)
    assert not respuesta.simulado
    assert respuesta.contenido[0]["producto"] == "Pan dulce"


def test_si_gemini_falla_pasa_a_simulado(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("GEMINI_MOCK", "false")

    def falla(*_):
        raise ConnectionError("sin internet")

    monkeypatch.setattr(gemini, "_pedir_texto", falla)
    respuesta = gemini.recomendaciones("Tienda", {"vendido": 1, "donado": 0, "desechado": 2, "dinero": 10,
                                                  "porcentaje": 33, "por_categoria": []})
    assert respuesta.simulado and "ConnectionError" in respuesta.aviso


def test_solo_la_tienda_usa_las_paginas_de_ia(cliente):
    assert cliente.get("/tienda/ia/capturar").status_code == 302
    entrar(cliente, "comprador@demo.mx")
    assert cliente.get("/tienda/ia/capturar").status_code == 403


def test_registrar_con_foto_y_confirmar(cliente, con):
    entrar(cliente, "tienda@demo.mx")
    pagina = cliente.post("/tienda/ia/capturar/foto", data={"foto": (io.BytesIO(b"x"), "refri.jpg", "image/jpeg")},
                          content_type="multipart/form-data")
    texto = pagina.get_data(as_text=True)
    assert "Revisa lo que encontró Gemini" in texto and "Yogur de fresa" in texto

    fecha = (servicio.hoy(con) + timedelta(days=3)).isoformat()
    datos = {"total": "2",
             "incluir_0": "1", "producto_0": "Yogur de fresa 1 L", "categoria_0": "Lácteos", "cantidad_0": "4",
             "unidad_0": "pieza", "precio_0": "38", "fecha_caducidad_0": fecha,
             "incluir_1": "1", "producto_1": "Leche", "categoria_1": "Lácteos", "cantidad_1": "2",
             "unidad_1": "pieza", "precio_1": "", "fecha_caducidad_1": fecha}
    texto = cliente.post("/tienda/ia/capturar/guardar", data=datos, follow_redirects=True).get_data(as_text=True)
    assert "Se registraron 1 producto(s)" in texto   # el yogur se guardó
    assert "El precio debe ser un número" in texto   # la leche sin precio se vuelve a mostrar
    assert con.execute("SELECT capturado_con_ia FROM lotes WHERE producto = 'Yogur de fresa 1 L'").fetchone()[0] == 1


def test_dictado_y_paginas_de_texto(cliente):
    entrar(cliente, "tienda@demo.mx")
    assert "Bolillo" in cliente.post("/tienda/ia/capturar/texto", data={"texto": "12 bolillos"}).get_data(as_text=True)
    for ruta in ["/tienda/ia/capturar", "/tienda/ia/alerta", "/tienda/ia/whatsapp", "/tienda/ia/recomendaciones"]:
        assert cliente.get(ruta, follow_redirects=True).status_code == 200, ruta
    assert "wa.me" in cliente.get("/tienda/ia/whatsapp").get_data(as_text=True)


class ErrorFalso(Exception):
    def __init__(self, code):
        super().__init__(f"error {code}")
        self.code = code


class ClienteFalso:
    """Simula a Google: responde con los errores indicados por modelo y luego con éxito."""

    def __init__(self, errores_por_modelo):
        self.errores = errores_por_modelo
        self.llamadas = []
        self.models = self

    def generate_content(self, model, contents, config=None):
        self.llamadas.append(model)
        pendientes = self.errores.get(model, [])
        if pendientes:
            raise ErrorFalso(pendientes.pop(0))
        return type("R", (), {"text": f"ok desde {model}"})()


def test_reintenta_si_google_esta_saturado(monkeypatch):
    falso = ClienteFalso({"principal": [503]})
    monkeypatch.setattr(gemini, "_cliente", lambda nuevo=False: falso)
    monkeypatch.setattr(gemini.time, "sleep", lambda s: None)
    monkeypatch.setenv("GEMINI_MODEL", "principal")
    monkeypatch.setenv("GEMINI_MODEL_RESPALDO", "respaldo")
    assert gemini._pedir_texto("hola") == "ok desde principal"
    assert falso.llamadas == ["principal", "principal"]


def test_usa_el_modelo_de_respaldo(monkeypatch):
    falso = ClienteFalso({"principal": [503, 503]})
    monkeypatch.setattr(gemini, "_cliente", lambda nuevo=False: falso)
    monkeypatch.setattr(gemini.time, "sleep", lambda s: None)
    monkeypatch.setenv("GEMINI_MODEL", "principal")
    monkeypatch.setenv("GEMINI_MODEL_RESPALDO", "respaldo")
    assert gemini._pedir_texto("hola") == "ok desde respaldo"


def test_clave_invalida_no_se_reintenta(monkeypatch):
    falso = ClienteFalso({"principal": [400]})
    monkeypatch.setattr(gemini, "_cliente", lambda nuevo=False: falso)
    monkeypatch.setenv("GEMINI_MODEL", "principal")
    monkeypatch.setenv("GEMINI_MODEL_RESPALDO", "respaldo")
    try:
        gemini._pedir_texto("hola")
        assert False, "debió fallar"
    except ErrorFalso as error:
        assert error.code == 400
    assert falso.llamadas == ["principal"]


def test_si_la_conexion_se_cierra_abre_otra(monkeypatch):
    cerrado = ClienteFalso({})
    cerrado.generate_content = lambda **_: (_ for _ in ()).throw(
        RuntimeError("Cannot send a request, as the client has been closed."))
    sano = ClienteFalso({})
    conexiones = {"actual": cerrado}

    def cliente_falso(nuevo=False):
        if nuevo:
            conexiones["actual"] = sano
        return conexiones["actual"]

    monkeypatch.setattr(gemini, "_cliente", cliente_falso)
    monkeypatch.setenv("GEMINI_MODEL", "principal")
    assert gemini._pedir_texto("hola") == "ok desde principal"
