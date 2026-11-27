"""Reglas del negocio, escritas como funciones simples para poder probarlas.

Aquí no hay base de datos ni páginas web: solo cálculos. Así es fácil
explicarlas al jurado y comprobarlas con pruebas automáticas (carpeta tests/).
"""
from datetime import date, timedelta

CATEGORIAS = [
    "Lácteos",
    "Panadería",
    "Frutas y verduras",
    "Carnes y embutidos",
    "Comida preparada",
    "Abarrotes",
    "Bebidas",
    "Otro",
]

UNIDADES = ["pieza", "paquete", "kg", "litro"]


class ErrorRegla(ValueError):
    """Error que se le muestra a la persona usuaria (por ejemplo: 'Solo quedan 3 piezas')."""


def hoy_simulado(dias_simulados, hoy_real=None):
    """La demo puede 'adelantar el reloj'. Esta es la fecha que usa toda la app."""
    return (hoy_real or date.today()) + timedelta(days=int(dias_simulados))


def dias_restantes(fecha_caducidad, hoy):
    """Días que faltan para caducar. 0 = caduca hoy, negativo = ya caducó."""
    return (date.fromisoformat(fecha_caducidad) - hoy).days


# ------------------------------------------------------------- escalera de rescate
#
#   más de 5 días  -> precio normal
#   3 a 5 días     -> descuento_3_5 (por defecto 20 %)
#   1 a 2 días     -> descuento_1_2 (por defecto 40 %)
#   día que caduca -> ya no se vende: se ofrece a organizaciones (donación)
#   ya caducó      -> se cierra; lo que quedó se registra como desechado
#
# Los porcentajes son un EJEMPLO para validar con las tiendas; cada tienda puede cambiarlos.

def porcentaje_descuento(dias, descuento_3_5=20, descuento_1_2=40):
    if dias > 5:
        return 0
    if dias >= 3:
        return descuento_3_5
    if dias >= 1:
        return descuento_1_2
    return 0  # el día que caduca ya no se vende


def precio_con_descuento(precio, porcentaje):
    return round(precio * (100 - porcentaje) / 100, 2)


def estado_por_fecha(dias):
    """En qué escalón debe estar un lote según los días que le quedan."""
    if dias >= 1:
        return "venta"
    if dias == 0:
        return "donacion"
    return "cerrado"


def porcentaje_rescatado(vendido, donado, desechado):
    """De todo lo que ya tuvo un final, qué porcentaje se vendió o se donó."""
    total = vendido + donado + desechado
    if total == 0:
        return None
    return round(100 * (vendido + donado) / total)


def validar_descuentos(texto_3_5, texto_1_2):
    """Los descuentos van de 0 a 90 % y el de 1-2 días no puede ser menor que el de 3-5 días."""
    try:
        d35, d12 = int(texto_3_5), int(texto_1_2)
    except (TypeError, ValueError):
        raise ErrorRegla("Los descuentos deben ser números enteros.")
    if not (0 <= d35 <= 90 and 0 <= d12 <= 90):
        raise ErrorRegla("Los descuentos deben estar entre 0 y 90 %.")
    if d12 < d35:
        raise ErrorRegla("El descuento de 1 o 2 días debe ser igual o mayor que el de 3 a 5 días.")
    return d35, d12


# ------------------------------------------------------------- validaciones

def validar_cantidad(texto):
    """Convierte lo que escribió la persona en un número entero mayor que cero."""
    try:
        cantidad = int(str(texto).strip())
    except (TypeError, ValueError):
        raise ErrorRegla("La cantidad debe ser un número entero.")
    if cantidad <= 0:
        raise ErrorRegla("La cantidad debe ser mayor que cero.")
    return cantidad


def validar_precio(texto):
    try:
        precio = round(float(str(texto).strip().replace("$", "").replace(",", "")), 2)
    except (TypeError, ValueError):
        raise ErrorRegla("El precio debe ser un número, por ejemplo 18.50.")
    if precio < 0:
        raise ErrorRegla("El precio no puede ser negativo.")
    return precio


def validar_fecha(texto):
    try:
        return date.fromisoformat(str(texto).strip()).isoformat()
    except ValueError:
        raise ErrorRegla("La fecha de caducidad debe tener el formato AAAA-MM-DD.")


def validar_email(texto):
    email = (texto or "").strip().lower()
    usuario, _, dominio = email.partition("@")
    if not usuario or "." not in dominio or " " in email:
        raise ErrorRegla("Escribe un correo válido, por ejemplo nombre@correo.com.")
    return email


def validar_contrasena(contrasena, confirmacion):
    if len(contrasena or "") < 8:
        raise ErrorRegla("La contraseña debe tener al menos 8 caracteres.")
    if contrasena != confirmacion:
        raise ErrorRegla("Las contraseñas no coinciden.")


def validar_reserva(estado_lote, tipo, cantidad, disponible):
    """Decide si se puede apartar 'cantidad' unidades de un lote.

    - Los compradores solo apartan lotes en venta.
    - Las organizaciones solo apartan lotes que ya pasaron a donación.
    - Nunca se aparta más de lo disponible.
    """
    if estado_lote == "cerrado":
        raise ErrorRegla("Este producto ya no está disponible.")
    if tipo == "compra" and estado_lote != "venta":
        raise ErrorRegla("Este producto ya pasó a donación y no se puede comprar.")
    if tipo == "donacion" and estado_lote != "donacion":
        raise ErrorRegla("Este producto todavía está a la venta; se ofrece para donación el día que caduca.")
    if disponible <= 0:
        raise ErrorRegla("Ya no quedan unidades disponibles.")
    if cantidad > disponible:
        raise ErrorRegla(f"Solo quedan {disponible} disponibles.")
