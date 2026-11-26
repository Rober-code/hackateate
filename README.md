# Rescata

Página web para que las tiendas de barrio vendan con descuento o donen sus productos antes de que caduquen.

> Versión 0.2: cuentas por rol (comprador, tienda, organización), registro de productos, catálogo con filtros y apartados.

Cuentas de demostración (contraseña `rescata123`): `tienda@demo.mx`, `panaderia@demo.mx`, `comprador@demo.mx`, `comedor@demo.mx`.

Cómo funciona lo que agrega esta versión: [`docs/guias/v0.2.md`](docs/guias/v0.2.md).

## Cómo ejecutarlo

1. Instala [Python 3.10 o más nuevo](https://www.python.org/downloads/) (en Windows marca "Add Python to PATH").
2. En una terminal dentro de esta carpeta:

   ```
   pip install -r requirements.txt
   python app.py
   ```

3. Abre http://127.0.0.1:5000

La primera vez se crea `rescata.db` con datos de demostración.

## Pruebas automáticas

```
python -m pytest
```
