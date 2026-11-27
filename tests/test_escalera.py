"""Pruebas de la escalera de rescate: descuentos, paso a donación, cierre, impacto y ajustes."""
import pytest

import reglas
import servicio
from reglas import ErrorRegla
from test_apartados import disponible, nuevo_lote
from test_cuentas import entrar


@pytest.mark.parametrize("dias, esperado", [(8, 0), (6, 0), (5, 20), (3, 20), (2, 40), (1, 40), (0, 0)])
def test_porcentaje_descuento(dias, esperado):
    assert reglas.porcentaje_descuento(dias, 20, 40) == esperado


def test_precio_con_descuento():
    assert reglas.precio_con_descuento(42.0, 40) == 25.2


@pytest.mark.parametrize("dias, estado", [(3, "venta"), (1, "venta"), (0, "donacion"), (-1, "cerrado")])
def test_estado_por_fecha(dias, estado):
    assert reglas.estado_por_fecha(dias) == estado


def test_porcentaje_rescatado():
    assert reglas.porcentaje_rescatado(3, 1, 4) == 50
    assert reglas.porcentaje_rescatado(0, 0, 0) is None


@pytest.mark.parametrize("d35, d12", [("50", "30"), ("-1", "40"), ("20", "95"), ("x", "40")])
def test_descuentos_invalidos(d35, d12):
    with pytest.raises(ErrorRegla):
        reglas.validar_descuentos(d35, d12)


def test_apartado_guarda_precio_con_descuento(con):
    lote_id = nuevo_lote(con, cantidad=5, dias=2, precio=50)
    reserva_id = servicio.reservar(con, lote_id, "compra", "Ana", "1")
    precio = con.execute("SELECT precio_unitario FROM reservas WHERE id = ?", (reserva_id,)).fetchone()[0]
    assert precio == 30.0  # 50 con 40 % de descuento


def test_recorrido_completo_de_la_escalera(con):
    lote_id = nuevo_lote(con, cantidad=10, dias=1, precio=20)
    servicio.confirmar_recogida(con, servicio.reservar(con, lote_id, "compra", "Ana", "3"))

    servicio.avanzar_dias(con, 1)  # caduca hoy -> donación
    assert con.execute("SELECT estado FROM lotes WHERE id = ?", (lote_id,)).fetchone()[0] == "donacion"
    with pytest.raises(ErrorRegla):
        servicio.reservar(con, lote_id, "compra", "Luis", "1")  # ya no se vende

    donativo = servicio.reservar(con, lote_id, "donacion", "Comedor", "5", hora_recogida="18:00", organizacion_id=1)
    servicio.confirmar_recogida(con, donativo)
    servicio.reservar(con, lote_id, "donacion", "Albergue", "1", hora_recogida="19:00", organizacion_id=2)

    resumen = servicio.avanzar_dias(con, 1)  # ya caducó -> se cierra
    assert resumen["cerrados"] >= 1
    assert disponible(con, lote_id) == 0
    destinos = dict(con.execute(
        "SELECT destino, SUM(cantidad) FROM resultados WHERE lote_id = ? GROUP BY destino", (lote_id,)
    ).fetchall())
    # 3 vendidas, 5 donadas, 2 sin rescatar (1 sin apartar + 1 apartada que nadie recogió)
    assert destinos == {"vendido": 3, "donado": 5, "desechado": 2}


def test_tablero_de_impacto(con):
    lote_id = nuevo_lote(con, cantidad=4, dias=1, precio=10)
    servicio.confirmar_recogida(con, servicio.reservar(con, lote_id, "compra", "Ana", "2"))
    servicio.avanzar_dias(con, 2)
    datos = servicio.impacto(con, 1)
    assert datos["vendido"] >= 2 and datos["desechado"] >= 2
    assert datos["dinero"] >= 12.0  # 2 x (10 con 40 % de descuento)


def test_ajustes_cambian_el_precio(cliente, con):
    entrar(cliente, "tienda@demo.mx")
    texto = cliente.post("/tienda/ajustes", data={"nombre": "La Esquina", "zona": "Centro",
                                                  "descuento_3_5": "10", "descuento_1_2": "50"},
                         follow_redirects=True).get_data(as_text=True)
    assert "Ajustes guardados" in texto
    lote = servicio.lotes_de_tienda(con, 1)[0]  # el yogur, que caduca mañana
    assert lote["descuento"] == 50


def test_organizacion_aparta_donativo(cliente):
    cliente.post("/demo/avanzar")  # los productos con 1 día pasan a donación
    entrar(cliente, "comedor@demo.mx")
    assert "Apartar donativo" in cliente.get("/organizacion/").get_data(as_text=True)
    texto = cliente.post("/organizacion/aceptar/1", data={"cantidad": "2", "hora": "18:30", "nombre": "Rosa"},
                         follow_redirects=True).get_data(as_text=True)
    assert "Donativo apartado" in texto and "por recoger" in texto


def test_paginas_de_la_escalera(cliente):
    assert cliente.post("/demo/avanzar", follow_redirects=True).status_code == 200
    entrar(cliente, "tienda@demo.mx")
    for ruta in ["/tienda/impacto", "/tienda/ajustes", "/tienda/"]:
        assert cliente.get(ruta).status_code == 200, ruta
    assert cliente.post("/demo/reiniciar", follow_redirects=True).status_code == 200
