"""Pruebas de la página de inicio y de la protección de formularios."""


def test_inicio_responde(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    assert "Rescata" in respuesta.get_data(as_text=True)


def test_pagina_que_no_existe(cliente):
    assert cliente.get("/no-existe").status_code == 404


def test_formulario_sin_codigo_csrf_se_rechaza(app):
    app.config["CSRF"] = True
    assert app.test_client().post("/").status_code == 400
