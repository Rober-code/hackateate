"""Operaciones con la base de datos: todo lo que guarda o cambia información.

Las páginas (archivos rutas_*.py) solo leen el formulario, llaman a estas
funciones y muestran el resultado. Así la lógica queda en un solo lugar.
"""
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

import reglas
from reglas import ErrorRegla


def ahora():
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------- reloj de la demo

def dias_simulados(con):
    fila = con.execute("SELECT valor FROM config WHERE clave = 'dias_simulados'").fetchone()
    return int(fila["valor"]) if fila else 0


def hoy(con):
    """Fecha 'de hoy' para la app (incluye los días adelantados en la demo)."""
    return reglas.hoy_simulado(dias_simulados(con))


# ---------------------------------------------------------------- página de inicio

def estadisticas_publicas(con):
    """Números reales de la base para la página de inicio."""
    return {
        "disponibles": con.execute(
            "SELECT COUNT(*) FROM lotes WHERE estado = 'venta' AND cantidad_disponible > 0"
        ).fetchone()[0],
        "tiendas": con.execute("SELECT COUNT(*) FROM tiendas").fetchone()[0],
        "rescatadas": con.execute(
            "SELECT COALESCE(SUM(cantidad), 0) FROM resultados WHERE destino IN ('vendido', 'donado')"
        ).fetchone()[0],
    }


# ---------------------------------------------------------------- cuentas

def crear_cuenta(con, formulario):
    """Registra una cuenta nueva. Si es tienda u organización, también crea su registro.

    Devuelve el id del usuario nuevo.
    """
    rol = formulario.get("rol")
    if rol not in ("comprador", "tienda", "organizacion"):
        raise ErrorRegla("Elige si eres comprador, tienda u organización.")
    nombre = (formulario.get("nombre") or "").strip()
    if not nombre:
        raise ErrorRegla("Escribe tu nombre.")
    email = reglas.validar_email(formulario.get("email"))
    reglas.validar_contrasena(formulario.get("contrasena"), formulario.get("confirmacion"))
    if con.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone():
        raise ErrorRegla("Ya existe una cuenta con ese correo. Entra con tu contraseña.")

    tienda_id = organizacion_id = None
    zona = (formulario.get("zona") or "").strip()
    if rol == "tienda":
        negocio = (formulario.get("nombre_negocio") or "").strip()
        if not negocio:
            raise ErrorRegla("Escribe el nombre de tu tienda.")
        tienda_id = con.execute("INSERT INTO tiendas (nombre, zona) VALUES (?, ?)", (negocio, zona)).lastrowid
    elif rol == "organizacion":
        organizacion = (formulario.get("nombre_organizacion") or "").strip()
        if not organizacion:
            raise ErrorRegla("Escribe el nombre de tu organización.")
        organizacion_id = con.execute(
            "INSERT INTO organizaciones (nombre, zona) VALUES (?, ?)", (organizacion, zona)
        ).lastrowid

    usuario_id = con.execute(
        """INSERT INTO usuarios (nombre, email, password_hash, rol, tienda_id, organizacion_id, creado_en)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (nombre, email, generate_password_hash(formulario.get("contrasena")), rol, tienda_id, organizacion_id, ahora()),
    ).lastrowid
    con.commit()
    return usuario_id


def autenticar(con, email, contrasena):
    """Devuelve el usuario si el correo y la contraseña coinciden; si no, None."""
    usuario = con.execute("SELECT * FROM usuarios WHERE email = ?", ((email or "").strip().lower(),)).fetchone()
    if usuario and check_password_hash(usuario["password_hash"], contrasena or ""):
        return usuario
    return None


def obtener_usuario(con, usuario_id):
    return con.execute(
        """SELECT u.*, t.nombre AS tienda, o.nombre AS organizacion
           FROM usuarios u
           LEFT JOIN tiendas t ON t.id = u.tienda_id
           LEFT JOIN organizaciones o ON o.id = u.organizacion_id
           WHERE u.id = ?""",
        (usuario_id,),
    ).fetchone()


# ---------------------------------------------------------------- lotes

# Consulta base: cada lote junto con los datos de su tienda.
SELECT_LOTES = """SELECT l.*, t.nombre AS tienda, t.zona AS zona,
                         t.descuento_3_5 AS descuento_3_5, t.descuento_1_2 AS descuento_1_2
                  FROM lotes l JOIN tiendas t ON t.id = l.tienda_id"""


def obtener_tienda(con, tienda_id):
    return con.execute("SELECT * FROM tiendas WHERE id = ?", (tienda_id,)).fetchone()


def enriquecer(lote, fecha_hoy):
    """Convierte una fila de la base en diccionario y le agrega datos calculados."""
    datos = dict(lote)
    datos["dias"] = reglas.dias_restantes(datos["fecha_caducidad"], fecha_hoy)
    datos["descuento"] = 0
    datos["precio_actual"] = datos["precio_original"]
    return datos


def crear_lote(con, tienda_id, formulario, capturado_con_ia=False):
    """Valida los datos de un producto y lo guarda. Devuelve el id nuevo."""
    producto = (formulario.get("producto") or "").strip()
    if not producto:
        raise ErrorRegla("Escribe el nombre del producto.")
    categoria = formulario.get("categoria") or "Otro"
    if categoria not in reglas.CATEGORIAS:
        categoria = "Otro"
    unidad = formulario.get("unidad") or "pieza"
    if unidad not in reglas.UNIDADES:
        unidad = "pieza"
    cantidad = reglas.validar_cantidad(formulario.get("cantidad"))
    precio = reglas.validar_precio(formulario.get("precio"))
    fecha = reglas.validar_fecha(formulario.get("fecha_caducidad"))
    if reglas.dias_restantes(fecha, hoy(con)) < 0:
        raise ErrorRegla(f"{producto}: la fecha ya pasó; un producto caducado no se publica.")
    estimada = 1 if formulario.get("fecha_estimada") in ("1", "on", True) else 0

    cursor = con.execute(
        """INSERT INTO lotes (tienda_id, producto, categoria, cantidad_inicial, cantidad_disponible,
                              unidad, precio_original, fecha_caducidad, fecha_estimada,
                              capturado_con_ia, creado_en)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (tienda_id, producto, categoria, cantidad, cantidad, unidad, precio, fecha,
         estimada, 1 if capturado_con_ia else 0, ahora()),
    )
    con.commit()
    return cursor.lastrowid


def lotes_de_tienda(con, tienda_id):
    filas = con.execute(
        SELECT_LOTES + " WHERE l.tienda_id = ? ORDER BY l.estado = 'cerrado', l.fecha_caducidad, l.producto",
        (tienda_id,),
    ).fetchall()
    fecha_hoy = hoy(con)
    return [enriquecer(f, fecha_hoy) for f in filas]


def catalogo(con, buscar="", categoria="", max_dias="", precio_max=""):
    """Productos que un comprador puede apartar, con filtros opcionales."""
    filas = con.execute(
        SELECT_LOTES + " WHERE l.estado = 'venta' AND l.cantidad_disponible > 0 ORDER BY l.fecha_caducidad, l.producto"
    ).fetchall()
    fecha_hoy = hoy(con)
    lotes = [enriquecer(f, fecha_hoy) for f in filas]
    if buscar:
        lotes = [l for l in lotes if buscar.lower() in l["producto"].lower()]
    if categoria:
        lotes = [l for l in lotes if l["categoria"] == categoria]
    if max_dias not in ("", None):
        lotes = [l for l in lotes if l["dias"] <= int(max_dias)]
    if precio_max not in ("", None):
        lotes = [l for l in lotes if l["precio_actual"] <= float(precio_max)]
    return lotes


# ---------------------------------------------------------------- apartados (reservas)

def reservar(con, lote_id, tipo, receptor, cantidad_texto, usuario_id=None, hora_recogida=None, organizacion_id=None):
    """Aparta unidades de un lote para un comprador o una organización. Devuelve el id de la reserva."""
    cantidad = reglas.validar_cantidad(cantidad_texto)
    receptor = (receptor or "").strip()
    if not receptor:
        raise ErrorRegla("Escribe el nombre de quien va a recoger.")

    lote = con.execute(SELECT_LOTES + " WHERE l.id = ?", (lote_id,)).fetchone()
    if lote is None:
        raise ErrorRegla("Ese producto ya no existe.")
    reglas.validar_reserva(lote["estado"], tipo, cantidad, lote["cantidad_disponible"])
    precio_unitario = enriquecer(lote, hoy(con))["precio_actual"] if tipo == "compra" else 0

    # Descontar en una sola instrucción evita que dos personas aparten la misma unidad
    # al mismo tiempo: si otra reserva ya la tomó, la condición falla y no se descuenta nada.
    estado_esperado = "venta" if tipo == "compra" else "donacion"
    cursor = con.execute(
        """UPDATE lotes SET cantidad_disponible = cantidad_disponible - ?
           WHERE id = ? AND estado = ? AND cantidad_disponible >= ?""",
        (cantidad, lote_id, estado_esperado, cantidad),
    )
    if cursor.rowcount == 0:
        con.rollback()
        raise ErrorRegla("Alguien más apartó este producto hace un momento. Revisa la cantidad disponible.")

    cursor = con.execute(
        """INSERT INTO reservas (lote_id, usuario_id, tipo, receptor, organizacion_id, cantidad,
                                 precio_unitario, hora_recogida, creada_en)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (lote_id, usuario_id, tipo, receptor, organizacion_id, cantidad, precio_unitario, hora_recogida, ahora()),
    )
    con.commit()
    return cursor.lastrowid


def cancelar_reserva(con, reserva_id):
    """Cancela una reserva pendiente y devuelve sus unidades al lote."""
    reserva = con.execute("SELECT * FROM reservas WHERE id = ?", (reserva_id,)).fetchone()
    cursor = con.execute(
        "UPDATE reservas SET estado = 'cancelada' WHERE id = ? AND estado = 'pendiente'", (reserva_id,)
    )
    if reserva is None or cursor.rowcount == 0:
        con.rollback()
        raise ErrorRegla("Ese apartado ya no está pendiente.")
    con.execute(
        "UPDATE lotes SET cantidad_disponible = cantidad_disponible + ? WHERE id = ?",
        (reserva["cantidad"], reserva["lote_id"]),
    )
    con.commit()


def confirmar_recogida(con, reserva_id):
    """La tienda confirma que se entregó: queda registrado como vendido o donado."""
    reserva = con.execute("SELECT * FROM reservas WHERE id = ?", (reserva_id,)).fetchone()
    cursor = con.execute(
        "UPDATE reservas SET estado = 'recogida' WHERE id = ? AND estado = 'pendiente'", (reserva_id,)
    )
    if reserva is None or cursor.rowcount == 0:
        con.rollback()
        raise ErrorRegla("Ese apartado ya no está pendiente.")
    destino = "vendido" if reserva["tipo"] == "compra" else "donado"
    con.execute(
        "INSERT INTO resultados (lote_id, destino, cantidad, monto, fecha) VALUES (?, ?, ?, ?, ?)",
        (reserva["lote_id"], destino, reserva["cantidad"],
         round(reserva["cantidad"] * reserva["precio_unitario"], 2), hoy(con).isoformat()),
    )
    con.commit()


def reserva_es_de_tienda(con, reserva_id, tienda_id):
    return con.execute(
        "SELECT 1 FROM reservas r JOIN lotes l ON l.id = r.lote_id WHERE r.id = ? AND l.tienda_id = ?",
        (reserva_id, tienda_id),
    ).fetchone() is not None


def reserva_es_de_usuario(con, reserva_id, usuario_id):
    return con.execute(
        "SELECT 1 FROM reservas WHERE id = ? AND usuario_id = ?", (reserva_id, usuario_id)
    ).fetchone() is not None


def reservas_pendientes(con, tienda_id):
    return con.execute(
        """SELECT r.*, l.producto, l.unidad, o.nombre AS organizacion
           FROM reservas r
           JOIN lotes l ON l.id = r.lote_id
           LEFT JOIN organizaciones o ON o.id = r.organizacion_id
           WHERE l.tienda_id = ? AND r.estado = 'pendiente'
           ORDER BY r.creada_en""",
        (tienda_id,),
    ).fetchall()


def apartados_de_usuario(con, usuario_id):
    return con.execute(
        """SELECT r.*, l.producto, l.unidad, l.fecha_caducidad, t.nombre AS tienda, t.zona AS zona
           FROM reservas r JOIN lotes l ON l.id = r.lote_id JOIN tiendas t ON t.id = l.tienda_id
           WHERE r.usuario_id = ?
           ORDER BY r.estado != 'pendiente', r.creada_en DESC""",
        (usuario_id,),
    ).fetchall()
