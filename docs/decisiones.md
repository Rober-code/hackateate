# Alternativas y decisiones

## Alternativas existentes que comparamos

| Alternativa | Qué hace | Qué hueco deja | Fuente |
| --- | --- | --- | --- |
| Proceso actual de la tienda | Rebajar a mano, avisar por WhatsApp o tirar | Sin registro ni aviso anticipado; nadie sabe cuánto se pierde | Entrevistas del equipo [COMPLETAR] |
| Cheaf | App que vende excedentes de supermercados, panaderías y restaurantes en "paquetes sorpresa" con 50 a 65 % de descuento, que se recogen en el local | El comprador no elige el producto, el descuento es fijo y no gestiona fechas ni lo que no se vende | [Forbes Argentina](https://www.forbesargentina.com/negocios/que-cheaf-app-rescate-alimentos-desembarca-argentina-n67383/amp) · [App Store](https://apps.apple.com/MX/app/id1527621516) |
| Red BAMX (bancos de alimentos) | Recibe donativos de cadenas de autoservicio con convenio | Pensada para donantes con volumen; una tienda pequeña no tiene un canal práctico | [Presentación BAMX en ANTAD](https://antad.net/wp-content/uploads/2019/11/6.-banco-de-alimentos-8-noviembre.pdf) |
| Hoja de cálculo o inventario del punto de venta | Registra existencias | No alerta por fecha, no baja precios ni conecta con compradores u organizaciones | — |

## Formas de resolver el problema que consideramos

| Opción | Por qué sí o por qué no |
| --- | --- |
| Solo un registro de mermas (tablero) | Hace visible el problema, pero no mueve el producto. Lo incluimos como el último escalón (tablero de impacto). |
| Solo venta con descuento | Ya existe (Cheaf) y deja sin salida lo que no se vende. |
| Solo donación | Las tiendas pierden todo el valor y muchas no donan por falta de tiempo. |
| **Escalera: descuento → donación → medición** | **Elegida:** recupera dinero primero, rescata lo que queda y mide el resultado. |

## Decisiones técnicas

| Decisión | Alternativa descartada | Por qué |
| --- | --- | --- |
| Flask + SQLite | React + API + PostgreSQL | El equipo empieza a programar; un solo lenguaje y nada que instalar aparte. |
| Precio con regla fija | Precio calculado por la IA | Explicable, comprobable con pruebas y ajustable por la tienda. |
| Gemini sugiere y la tienda confirma | Guardar directo lo que lee la IA | La IA puede leer mal una fecha; la responsabilidad sobre el alimento es de la tienda. |
| Dictado con el reconocimiento de voz del navegador + Gemini para interpretar | Mandar el audio a Gemini | Los navegadores graban en formatos distintos; así funciona en Chrome sin convertir audio. |
| Enlace `wa.me` | API de WhatsApp Business | Funciona hoy, gratis y sin trámites. |
| Cuentas con rol (comprador, tienda, organización) | Una sola vista para todos | Cada quien ve solo lo suyo; una tienda no puede entregar apartados de otra. |
| Catálogo visible sin cuenta | Pedir cuenta para todo | Menos fricción: se ve primero qué hay y la cuenta se pide solo al apartar. |
| Contraseñas cifradas (hash) y protección de formularios (CSRF) | Guardar contraseñas tal cual | Seguridad básica que cualquier sistema con cuentas debe tener. |
| Asistente con Gemini que recibe el catálogo del día | Preguntas frecuentes fijas | Responde preguntas reales ("¿hay leche?") sin inventar, porque solo usa los datos que le damos. |

## Cambios por lo que aprendimos

| Fecha | Qué descubrimos | Qué cambiamos |
| --- | --- | --- |
| [COMPLETAR] | | |
