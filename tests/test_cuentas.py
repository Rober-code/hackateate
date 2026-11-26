"""Pruebas de cuentas: registro por rol, entrar, salir y páginas protegidas."""
import servicio
import pytest


def registrar(cliente, **datos):
    base = {"rol": "comprador", "nombre": "Luis", "email": "luis@correo.com",
            "contrasena": "secreta123", "confirmacion": "secreta123"}
    base.update(datos)
    return cliente.post("/registro", data=base, follow_redirects=True)


def entrar(cliente, email, contrasena="rescata123"):
    return cliente.post("/entrar", data={"email": email, "contrasena": contrasena}, follow_redirects=True)


def test_registro_de_comprador(cliente):
    texto = registrar(cliente).get_data(as_text=True)
    assert "Bienvenido(a), Luis" in texto


def test_registro_de_tienda_crea_su_tienda(cliente, con):
    registrar(cliente, rol="tienda", email="mary@correo.com", nombre_negocio="Abarrotes Mary", zona="Centro")
    fila = con.execute("SELECT t.nombre FROM usuarios u JOIN tiendas t ON t.id = u.tienda_id WHERE u.email = ?",
                       ("mary@correo.com",)).fetchone()
    assert fila["nombre"] == "Abarrotes Mary"


def test_registro_de_organizacion(cliente, con):
    registrar(cliente, rol="organizacion", email="org@correo.com", nombre_organizacion="Comedor San Juan")
    assert con.execute("SELECT 1 FROM organizaciones WHERE nombre = 'Comedor San Juan'").fetchone()


@pytest.mark.parametrize("cambio, mensaje", [
    ({"email": "sin-arroba"}, "correo válido"),
    ({"contrasena": "corta", "confirmacion": "corta"}, "al menos 8"),
    ({"confirmacion": "otra-cosa1"}, "no coinciden"),
    ({"rol": "tienda"}, "nombre de tu tienda"),
    ({"email": "tienda@demo.mx"}, "Ya existe una cuenta"),
])
def test_registro_con_errores(cliente, cambio, mensaje):
    assert mensaje in registrar(cliente, **cambio).get_data(as_text=True)


def test_contrasena_se_guarda_cifrada(con):
    fila = con.execute("SELECT password_hash FROM usuarios WHERE email = 'tienda@demo.mx'").fetchone()
    assert "rescata123" not in fila["password_hash"]
    assert servicio.autenticar(con, "tienda@demo.mx", "rescata123") is not None
    assert servicio.autenticar(con, "tienda@demo.mx", "incorrecta") is None


def test_entrar_y_salir(cliente):
    assert "Doña Lupe" in entrar(cliente, "tienda@demo.mx").get_data(as_text=True)
    assert "Cerraste sesión" in cliente.post("/salir", follow_redirects=True).get_data(as_text=True)


def test_contrasena_incorrecta(cliente):
    assert "incorrectos" in entrar(cliente, "tienda@demo.mx", "mala").get_data(as_text=True)


def test_pagina_protegida_pide_entrar(cliente):
    respuesta = cliente.get("/tienda/")
    assert respuesta.status_code == 302 and "/entrar" in respuesta.headers["Location"]


def test_rol_equivocado_no_entra(cliente):
    entrar(cliente, "comprador@demo.mx")
    assert cliente.get("/tienda/").status_code == 403


def test_no_redirige_a_sitios_externos(cliente):
    respuesta = cliente.post("/entrar", data={"email": "comprador@demo.mx", "contrasena": "rescata123",
                                              "siguiente": "https://sitio-malo.com"})
    assert "sitio-malo" not in respuesta.headers["Location"]
