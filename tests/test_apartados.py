"""Pruebas del flujo registrar -> apartar -> entregar.

Son los casos que la guía del reto pide probar: dos apartados sobre el mismo lote,
una cancelación, una cantidad inválida y no apartar más de lo existente.
"""
from datetime import timedelta

import pytest

import servicio
from reglas import ErrorRegla
from test_cuentas import entrar


def nuevo_lote(con, cantidad=5, dias=10, precio=20, tienda=1):
    return servicio.crear_lote(con, tienda, {
        "producto": "Yogur de prueba", "categoria": "Lácteos", "unidad": "pieza",
        "cantidad": str(cantidad), "precio": str(precio),
        "fecha_caducidad": (servicio.hoy(con) + timedelta(days=dias)).isoformat(),
    })


def disponible(con, lote_id):
    return con.execute("SELECT cantidad_disponible FROM lotes WHERE id = ?", (lote_id,)).fetchone()[0]


def test_registrar_lote(con):
    assert disponible(con, nuevo_lote(con, cantidad=7)) == 7


def test_no_se_registra_producto_caducado(con):
    with pytest.raises(ErrorRegla):
        servicio.crear_lote(con, 1, {"producto": "Leche", "cantidad": "1", "precio": "10",
                                     "fecha_caducidad": (servicio.hoy(con) - timedelta(days=1)).isoformat()})


def test_dos_apartados_no_superan_lo_disponible(con):
    lote_id = nuevo_lote(con, cantidad=5)
    servicio.reservar(con, lote_id, "compra", "Ana", "3")
    with pytest.raises(ErrorRegla, match="Solo quedan 2"):
        servicio.reservar(con, lote_id, "compra", "Luis", "3")
    servicio.reservar(con, lote_id, "compra", "Luis", "2")
    assert disponible(con, lote_id) == 0


def test_cantidad_invalida_no_cambia_nada(con):
    lote_id = nuevo_lote(con, cantidad=5)
    with pytest.raises(ErrorRegla):
        servicio.reservar(con, lote_id, "compra", "Ana", "-1")
    assert disponible(con, lote_id) == 5


def test_cancelar_devuelve_unidades(con):
    lote_id = nuevo_lote(con, cantidad=5)
    reserva_id = servicio.reservar(con, lote_id, "compra", "Ana", "4")
    servicio.cancelar_reserva(con, reserva_id)
    assert disponible(con, lote_id) == 5
    with pytest.raises(ErrorRegla):
        servicio.cancelar_reserva(con, reserva_id)  # no se cancela dos veces


def test_entrega_queda_como_vendida(con):
    lote_id = nuevo_lote(con, cantidad=5, dias=10, precio=20)
    servicio.confirmar_recogida(con, servicio.reservar(con, lote_id, "compra", "Ana", "2"))
    fila = con.execute("SELECT destino, cantidad, monto FROM resultados WHERE lote_id = ?", (lote_id,)).fetchone()
    assert (fila["destino"], fila["cantidad"], fila["monto"]) == ("vendido", 2, 40.0)


def test_catalogo_es_publico(cliente):
    for ruta in ["/comprar/", "/comprar/?max_dias=2&categoria=Lácteos&buscar=leche&precio_max=50"]:
        assert cliente.get(ruta).status_code == 200


def test_para_apartar_hay_que_entrar(cliente):
    assert "/entrar" in cliente.post("/comprar/apartar/1", data={"cantidad": "1"}).headers["Location"]


def test_comprador_aparta_y_ve_sus_apartados(cliente):
    entrar(cliente, "comprador@demo.mx")
    texto = cliente.post("/comprar/apartar/1", data={"cantidad": "2"}, follow_redirects=True).get_data(as_text=True)
    assert "Tu apartado es el #1" in texto and "Yogur natural" in texto
    texto = cliente.post("/comprar/mis-apartados/1/cancelar", follow_redirects=True).get_data(as_text=True)
    assert "Cancelaste tu apartado" in texto


def test_tienda_entrega_y_solo_ve_lo_suyo(cliente):
    entrar(cliente, "comprador@demo.mx")
    cliente.post("/comprar/apartar/1", data={"cantidad": "1"})   # lote de la tienda 1
    cliente.post("/comprar/apartar/7", data={"cantidad": "1"})   # lote de la panadería (tienda 2)
    cliente.post("/salir")

    entrar(cliente, "tienda@demo.mx")
    panel = cliente.get("/tienda/").get_data(as_text=True)
    assert "Yogur natural" in panel and "Bolillo" not in panel
    assert cliente.post("/tienda/apartados/2/entregar").status_code == 404   # no es suyo
    texto = cliente.post("/tienda/apartados/1/entregar", follow_redirects=True).get_data(as_text=True)
    assert "Entrega registrada" in texto


def test_tienda_registra_producto(cliente):
    entrar(cliente, "tienda@demo.mx")
    hoy = cliente.get("/tienda/nuevo").status_code
    assert hoy == 200
    with cliente.application.app_context():
        from db import get_db
        fecha = (servicio.hoy(get_db()) + timedelta(days=4)).isoformat()
    texto = cliente.post("/tienda/nuevo", data={"producto": "Crema 200 ml", "categoria": "Lácteos", "cantidad": "3",
                                                "unidad": "pieza", "precio": "22", "fecha_caducidad": fecha},
                         follow_redirects=True).get_data(as_text=True)
    assert "Se registró: Crema 200 ml" in texto
