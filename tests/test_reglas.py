"""Pruebas de las reglas del negocio (sin base de datos)."""
from datetime import date

import pytest

import reglas
from reglas import ErrorRegla

HOY = date(2026, 11, 22)


def test_dias_restantes():
    assert reglas.dias_restantes("2026-11-25", HOY) == 3
    assert reglas.dias_restantes("2026-11-22", HOY) == 0
    assert reglas.dias_restantes("2026-11-21", HOY) == -1


def test_reloj_simulado_adelanta_dias():
    assert reglas.hoy_simulado(2, HOY) == date(2026, 11, 24)


@pytest.mark.parametrize("texto", ["0", "-3", "abc", "", "2.5"])
def test_cantidad_invalida(texto):
    with pytest.raises(ErrorRegla):
        reglas.validar_cantidad(texto)


def test_cantidad_valida():
    assert reglas.validar_cantidad(" 4 ") == 4


def test_no_se_aparta_mas_de_lo_disponible():
    with pytest.raises(ErrorRegla, match="Solo quedan 3"):
        reglas.validar_reserva("venta", "compra", 5, 3)


def test_comprador_no_aparta_producto_en_donacion():
    with pytest.raises(ErrorRegla):
        reglas.validar_reserva("donacion", "compra", 1, 10)


def test_organizacion_no_aparta_producto_en_venta():
    with pytest.raises(ErrorRegla):
        reglas.validar_reserva("venta", "donacion", 1, 10)


def test_email_se_normaliza():
    assert reglas.validar_email("  Ana@Correo.COM ") == "ana@correo.com"
