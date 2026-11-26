-- Esquema de la base de datos de Rescata (SQLite).
-- Se ejecuta completo al iniciar la base: borra las tablas y las vuelve a crear.

DROP TABLE IF EXISTS resultados;
DROP TABLE IF EXISTS reservas;
DROP TABLE IF EXISTS lotes;
DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS organizaciones;
DROP TABLE IF EXISTS tiendas;
DROP TABLE IF EXISTS config;

-- Ajustes generales. 'dias_simulados' = cuántos días se adelantó el reloj de la demo.
CREATE TABLE config (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);

-- Negocios que publican productos. Cada tienda elige sus porcentajes de descuento.
CREATE TABLE tiendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    zona TEXT NOT NULL DEFAULT '',
    descuento_3_5 INTEGER NOT NULL DEFAULT 20,  -- % cuando faltan 3 a 5 días
    descuento_1_2 INTEGER NOT NULL DEFAULT 40   -- % cuando faltan 1 o 2 días
);

-- Organizaciones que reciben donativos (comedores, albergues, bancos de alimentos).
CREATE TABLE organizaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    zona TEXT NOT NULL DEFAULT ''
);

-- Cuentas. Cada cuenta tiene un rol; si es tienda u organización, apunta a su registro.
-- La contraseña NUNCA se guarda tal cual: se guarda su "hash" (una huella irreversible).
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('comprador', 'tienda', 'organizacion')),
    tienda_id INTEGER REFERENCES tiendas(id),
    organizacion_id INTEGER REFERENCES organizaciones(id),
    creado_en TEXT NOT NULL
);

-- Un lote = un producto con la misma fecha de caducidad (ej. "12 yogures que caducan el 25").
CREATE TABLE lotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tienda_id INTEGER NOT NULL REFERENCES tiendas(id),
    producto TEXT NOT NULL,
    categoria TEXT NOT NULL,
    cantidad_inicial INTEGER NOT NULL CHECK (cantidad_inicial > 0),
    cantidad_disponible INTEGER NOT NULL CHECK (cantidad_disponible >= 0),
    unidad TEXT NOT NULL DEFAULT 'pieza',
    precio_original REAL NOT NULL CHECK (precio_original >= 0),
    fecha_caducidad TEXT NOT NULL,                    -- formato AAAA-MM-DD
    fecha_estimada INTEGER NOT NULL DEFAULT 0,        -- 1 = la estimó la IA, no venía impresa
    capturado_con_ia INTEGER NOT NULL DEFAULT 0,      -- 1 = se registró con foto o dictado
    estado TEXT NOT NULL DEFAULT 'venta'
        CHECK (estado IN ('venta', 'donacion', 'cerrado')),
    creado_en TEXT NOT NULL
);

-- Apartados de compradores (tipo 'compra') o de organizaciones (tipo 'donacion').
CREATE TABLE reservas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lote_id INTEGER NOT NULL REFERENCES lotes(id),
    usuario_id INTEGER REFERENCES usuarios(id),       -- quién apartó
    tipo TEXT NOT NULL CHECK (tipo IN ('compra', 'donacion')),
    receptor TEXT NOT NULL,                           -- nombre de quien recoge
    organizacion_id INTEGER REFERENCES organizaciones(id),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario REAL NOT NULL DEFAULT 0,          -- precio con descuento al momento de apartar
    hora_recogida TEXT,
    estado TEXT NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'recogida', 'cancelada')),
    creada_en TEXT NOT NULL
);

-- Qué pasó al final con cada parte de un lote. De aquí sale el tablero de impacto.
CREATE TABLE resultados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lote_id INTEGER NOT NULL REFERENCES lotes(id),
    destino TEXT NOT NULL CHECK (destino IN ('vendido', 'donado', 'desechado')),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    monto REAL NOT NULL DEFAULT 0,                    -- dinero recuperado (solo si se vendió)
    fecha TEXT NOT NULL
);
