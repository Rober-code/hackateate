# Cambios por versión

## v0.5 · Asistente de dudas
- Chat flotante en todas las páginas, para visitantes, compradores, tiendas y organizaciones.
- Gemini responde con el contexto de Rescata, el rol de quien pregunta y los productos disponibles hoy.
- Reglas en las instrucciones: no inventar productos ni precios, no certificar que un alimento es apto, no pedir datos personales.
- Preguntas sugeridas según el rol, límite de 40 preguntas por sesión y respuestas de ejemplo en modo simulado.
- Si Gemini no responde, la respuesta muestra el motivo en una nota.

## v0.4 · Gemini en la tienda
- Registro con foto (una etiqueta o el refrigerador completo): Gemini devuelve la lista de productos con fecha en JSON (salida estructurada) y la tienda la revisa antes de guardar.
- Registro por dictado o texto ("me sobraron 12 bolillos y 4 leches").
- Fechas estimadas para productos sin fecha impresa, siempre marcadas como "estimada".
- Alerta del día, mensaje de ofertas para WhatsApp (enlace wa.me) y recomendaciones a partir del tablero de impacto.
- Modo simulado: sin clave, con GEMINI_MOCK=true o si Gemini falla, la app sigue funcionando y avisa el motivo en pantalla.
- Reintento si Google está saturado, modelo de respaldo (GEMINI_MODEL_RESPALDO) y una sola conexión que se reabre si se cierra.
- `probar_gemini.py`: diagnóstico de la clave, del modelo y de los errores.

## v0.3 · Escalera de rescate
- Descuento automático según los días que faltan: 20 % de 3 a 5 días y 40 % con 1 o 2 días.
- Ajustes de la tienda: nombre, zona y porcentajes de descuento (validados).
- El día que caduca, el producto deja de venderse y las organizaciones lo apartan con hora de recogida.
- Al caducar, el lote se cierra: lo no recogido se registra como desechado.
- Tablero de impacto: % rescatado, vendido, donado, desechado, dinero recuperado y desglose por categoría.
- Alertas en el panel de la tienda y barra de demo para adelantar el reloj o reiniciar los datos.

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
