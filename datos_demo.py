"""Datos de DEMOSTRACIÓN (ficticios) para probar la app.

No son tiendas ni personas reales. En la presentación hay que decirlo.
Las fechas se calculan a partir de hoy para que siempre haya productos por caducar.

Cuentas de prueba (todas con la contraseña 'rescata123'):
  tienda@demo.mx      Abarrotes La Esquina
  panaderia@demo.mx   Panadería San José
  comprador@demo.mx   Comprador de prueba
  comedor@demo.mx     Comedor comunitario
"""
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

CONTRASENA_DEMO = "rescata123"

TIENDAS = [
    ("Abarrotes La Esquina (demo)", "Cerca del campus"),
    ("Panadería San José (demo)", "Colonia centro"),
]

ORGANIZACIONES = [
    ("Comedor comunitario (demo)", "Colonia centro"),
    ("Albergue del barrio (demo)", "Cerca del campus"),
]

CUENTAS = [
    # (nombre, email, rol, tienda_id, organizacion_id)
    ("Doña Lupe", "tienda@demo.mx", "tienda", 1, None),
    ("Don José", "panaderia@demo.mx", "tienda", 2, None),
    ("Ana Comprador", "comprador@demo.mx", "comprador", None, None),
    ("Rosa del Comedor", "comedor@demo.mx", "organizacion", None, 1),
]

LOTES = [
    # (tienda, producto, categoría, cantidad, unidad, precio, días para caducar, fecha estimada)
    (1, "Yogur natural 1 L", "Lácteos", 6, "pieza", 42.0, 1, 0),
    (1, "Leche entera 1 L", "Lácteos", 8, "pieza", 29.0, 2, 0),
    (1, "Jamón de pavo 250 g", "Carnes y embutidos", 5, "paquete", 48.0, 4, 0),
    (1, "Plátano", "Frutas y verduras", 3, "kg", 28.0, 3, 1),
    (1, "Queso panela 400 g", "Lácteos", 4, "pieza", 72.0, 5, 0),
    (1, "Ensalada preparada", "Comida preparada", 4, "pieza", 65.0, 2, 1),
    (2, "Bolillo", "Panadería", 20, "pieza", 3.5, 1, 1),
    (2, "Concha de vainilla", "Panadería", 12, "pieza", 12.0, 2, 1),
    (2, "Pan de caja integral", "Panadería", 6, "paquete", 55.0, 7, 0),
]


def sembrar(con, hoy):
    ahora = datetime.now().isoformat(timespec="seconds")
    con.executemany("INSERT INTO tiendas (nombre, zona) VALUES (?, ?)", TIENDAS)
    con.executemany("INSERT INTO organizaciones (nombre, zona) VALUES (?, ?)", ORGANIZACIONES)
    hash_demo = generate_password_hash(CONTRASENA_DEMO)
    for nombre, email, rol, tienda_id, organizacion_id in CUENTAS:
        con.execute(
            """INSERT INTO usuarios (nombre, email, password_hash, rol, tienda_id, organizacion_id, creado_en)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (nombre, email, hash_demo, rol, tienda_id, organizacion_id, ahora),
        )
    for tienda, producto, categoria, cantidad, unidad, precio, dias, estimada in LOTES:
        con.execute(
            """INSERT INTO lotes (tienda_id, producto, categoria, cantidad_inicial, cantidad_disponible,
                                  unidad, precio_original, fecha_caducidad, fecha_estimada, creado_en)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (tienda, producto, categoria, cantidad, cantidad, unidad, precio,
             (hoy + timedelta(days=dias)).isoformat(), estimada, ahora),
        )
    con.commit()
