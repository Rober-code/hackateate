# Cómo funciona Rescata (para defender el proyecto)

Cada integrante debe poder explicar el recorrido completo y, con más detalle, la parte que le toca. Lean este documento con el código abierto al lado. Para el detalle de cada versión, vean `docs/guias/`.

## El recorrido de una visita

1. El navegador pide una página, por ejemplo `/tienda/`.
2. `app.py` recibe la visita y, antes que nada:
   - revisa el código CSRF si es un formulario (`revisar_csrf`);
   - mueve cada producto al escalón que le toca según su fecha (`servicio.actualizar_estados`);
   - carga a la persona que inició sesión (`auth.cargar_usuario`).
3. La ruta (`rutas_tienda.py`) revisa el rol con `@requiere_rol("tienda")` y pide los datos a `servicio.py`.
4. `servicio.py` consulta la base (`db.py`) y usa `reglas.py` para calcular días restantes, descuento y precio.
5. La ruta manda los datos a una plantilla de `templates/`, que arma la pantalla.

## Archivo por archivo

| Archivo | Qué hace | Responsable sugerido |
| --- | --- | --- |
| `schema.sql` | Crea las tablas: `tiendas`, `organizaciones`, `usuarios`, `lotes`, `reservas`, `resultados`, `config` | Backend |
| `db.py` | Abre y cierra la conexión a SQLite; crea la base con datos demo si no existe | Backend |
| `datos_demo.py` | Tiendas, organizaciones, cuentas y productos ficticios | Backend |
| `reglas.py` | Reglas puras: días restantes, descuentos, escalón según fecha, validaciones | Backend |
| `servicio.py` | Crear cuentas, guardar productos, apartar, cancelar, entregar, cerrar lotes, calcular impacto | Backend |
| `auth.py` | Crear cuenta, entrar, salir, `requiere_rol` | Backend |
| `rutas_tienda.py` | Panel, registro a mano, entregar/cancelar, impacto, ajustes | Frontend |
| `rutas_comprador.py` | Catálogo con filtros, apartar, mis apartados | Frontend |
| `rutas_organizacion.py` | Donativos del día y apartarlos con hora | Frontend |
| `rutas_ia.py` | Registrar con foto o dictado, alerta, WhatsApp, recomendaciones | Gemini |
| `rutas_chat.py` | Asistente: arma el contexto y responde en JSON | Gemini |
| `gemini.py` | Llamadas a Gemini, salida estructurada, instrucciones del asistente y modo simulado | Gemini |
| `rutas_demo.py` | "Avanzar 1 día" y "Reiniciar demo" | Integración |
| `templates/` | Pantallas. `base.html` es el marco común; `_componentes.html` tiene íconos y piezas repetidas | Frontend |
| `static/estilos.css` | Todo el diseño, con colores en variables | Frontend |
| `static/chat.js`, `static/dictado.js` | Ventana del asistente y dictado por voz | Frontend / Gemini |
| `probar_gemini.py` | Diagnóstico de la clave, el modelo y los errores de Gemini | Gemini |
| `tests/` | 83 pruebas automáticas | Todos |

## Las ideas técnicas que más preguntan

### ¿Cómo funcionan las cuentas?

Al crear cuenta se guarda el **hash** de la contraseña (`generate_password_hash`), nunca la contraseña. Al entrar se compara con `check_password_hash`. Si coincide, se guarda el id del usuario en la **sesión** (una cookie firmada con `SECRET_KEY`). Cada página protegida usa `@requiere_rol(...)`: sin sesión manda a "Entrar"; con el rol equivocado responde 403. Además, una tienda solo puede entregar apartados de sus propios productos (`reserva_es_de_tienda`).

### ¿Qué es el CSRF?

Cada formulario lleva un código secreto de la sesión (`{{ csrf() }}`). Si llega un formulario sin ese código (por ejemplo, desde otra página web que intente hacerse pasar por el usuario), se rechaza con error 400. El chat manda el código en el encabezado `X-CSRF-Token`.

### ¿Cómo evitan que dos personas aparten la misma unidad?

En `servicio.reservar()` el descuento de unidades es una sola instrucción SQL con condición:

```sql
UPDATE lotes SET cantidad_disponible = cantidad_disponible - ?
WHERE id = ? AND estado = ? AND cantidad_disponible >= ?
```

Si otra persona ya apartó esas unidades, no se modifica ninguna fila y la app responde "Alguien más apartó este producto". La prueba `test_dos_apartados_no_superan_lo_disponible` lo comprueba.

### ¿Cómo funciona la escalera?

`reglas.estado_por_fecha(dias)`: con 1 día o más está en venta; el día que caduca (0) pasa a donación; ya caducado (−1) se cierra. `reglas.porcentaje_descuento()` da 0 % con más de 5 días, el descuento de la tienda para 3 a 5 días y el mayor para 1 o 2. Al cerrarse (`servicio.cerrar_lote()`), los apartados que nadie recogió se cancelan y lo sobrante se registra como desechado.

### ¿Qué hace Gemini exactamente?

- **Captura:** `gemini.leer_foto()` manda la imagen con instrucciones y un esquema (`response_schema`) para que responda en JSON con producto, categoría, cantidad, unidad y fecha. `_normalizar()` corrige lo raro (categorías inexistentes, fechas mal escritas, productos caducados). **Nada se guarda sin que la tienda lo revise.**
- **Asistente:** `rutas_chat.armar_contexto()` junta quién pregunta, los productos de hoy y, si es tienda, sus propios productos. `gemini.responder_chat()` manda eso con instrucciones que le prohíben inventar productos o precios, certificar alimentos o pedir datos personales. El navegador manda los últimos 6 mensajes para que recuerde la conversación, y hay un límite de 40 preguntas por sesión para cuidar la cuota.
- **Si Gemini falla:** `_generar()` reintenta cuando Google está saturado (503), usa el modelo de respaldo si sigue fallando o no hay cuota (429), y reabre la conexión si se cerró.
- **Modo simulado:** si no hay clave, si `GEMINI_MOCK=true` o si nada de lo anterior funciona, `_con_respaldo()` devuelve respuestas de ejemplo y la pantalla muestra el motivo.

## Preguntas que probablemente harán (y cómo responder)

- **¿Por qué no deja la IA decidir el precio?** Una regla fija se puede explicar, probar y ajustar. La IA ayuda donde ahorra tiempo: capturar, redactar y responder dudas.
- **¿Qué pasa si Gemini lee mal la fecha?** La tienda la ve y la corrige antes de guardar. Medimos cuántas leyó bien: [COMPLETAR].
- **¿Y si el asistente inventa algo?** Solo recibe los datos reales del catálogo y tiene instrucciones de no inventar; aun así puede equivocarse, y lo dice en su encabezado.
- **¿Cómo saben que un alimento donado es apto?** La app no lo certifica: solo ofrece productos que no han caducado y la tienda decide.
- **¿Qué es simulado en la demo?** El reloj, las tiendas, organizaciones y cuentas (ficticias), y Gemini cuando aparece la etiqueta "simulado".
- **¿Quién paga?** La tienda, porque recupera dinero de lo que antes tiraba. Ver `docs/plan-negocio.md`.
- **¿En qué se diferencian de Cheaf?** Cheaf vende paquetes sorpresa con descuento fijo. Rescata maneja la fecha de cada producto, baja el precio por etapas y, si no se vende, lo dona, midiendo el resultado.
