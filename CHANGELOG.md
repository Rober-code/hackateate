# Cambios por versión

## v0.2 · Cuentas y flujo mínimo
- Crear cuenta como comprador, tienda u organización; entrar y salir. Las contraseñas se guardan cifradas.
- Cada página revisa el rol: una tienda solo ve y entrega lo suyo; un comprador solo cancela sus apartados.
- La tienda registra productos (producto, categoría, cantidad, unidad, precio, caducidad).
- Catálogo público con filtros (texto, categoría, días para caducar, precio); para apartar hay que entrar.
- "Mis apartados" para el comprador; la tienda marca entregado o cancela.
- No se puede apartar más de lo disponible, ni aunque dos personas aparten al mismo tiempo.
- Pruebas automáticas con pytest.

## v0.1 · Base y diseño
- Estructura del proyecto en Python con Flask y base de datos SQLite.
- Tablas: tiendas, organizaciones, usuarios, lotes, reservas, resultados y configuración.
- Página de inicio: cómo funciona, para quién es, cómo usamos la IA, con cifras en vivo de la base.
- Diseño propio pensado primero para celular, con íconos y colores en un solo archivo de estilos.
- Protección de formularios (CSRF), `.gitignore` y `.env.example` para que ninguna clave se suba a GitHub.
