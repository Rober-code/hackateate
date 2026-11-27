# Plan de negocio y viabilidad

> Regla del taller: toda cifra necesita fuente. Si es una estimación, se muestra la fórmula, los datos de entrada y los supuestos. Nada de cifras inventadas.

## Problema
[COMPLETAR con la evidencia de las entrevistas.]

## Segmento de clientes
Tiendas de abarrotes, misceláneas y panaderías independientes en [COMPLETAR: zona]. Número de negocios en la zona: [COMPLETAR con el directorio DENUE de INEGI, indicando fecha de consulta].

## Propuesta de valor
La tienda toma una foto y Rescata se encarga de rescatar el producto: lo vende con descuento por etapas, si no se vende lo dona, y le muestra cuánto dejó de tirar.

## Competidores
Ver [`decisiones.md`](decisiones.md): proceso actual, Cheaf, Red BAMX, hoja de cálculo.

**Diferenciador:** es la única opción que revisamos que junta control de caducidad, descuento automático por etapas y donación en un mismo flujo pensado para la tienda pequeña.

## Ingresos (a validar)
Opciones: suscripción mensual baja para la tienda o comisión por producto vendido con descuento. Compradores y organizaciones lo usan gratis.

**Fórmula:** ingreso mensual estimado = tiendas que aceptarían pagar × precio mensual propuesto.
- Tiendas que aceptarían pagar: [COMPLETAR con entrevistas y conteo de la zona].
- Precio propuesto: [COMPLETAR], justificado con lo que una tienda dice perder por semana en mermas: [COMPLETAR].
- El resultado es una proyección, no una venta.

## Costos principales
| Costo | De dónde sale el dato |
| --- | --- |
| Hosting de la app | Página de precios del servicio elegido [COMPLETAR con enlace y fecha] |
| Gemini API | Nivel gratuito para pruebas; pago por tokens en producción. [Precios vigentes](https://ai.google.dev/pricing) [COMPLETAR fecha de consulta] |
| Capacitación y soporte a tiendas | Horas del equipo [COMPLETAR] |

## Adquisición de usuarios
Las tiendas entrevistadas son las primeras; después, tienda por tienda en la misma zona, porque los compradores buscan productos cerca.

## Por qué ahora
La [Ley General de la Alimentación Adecuada y Sostenible](https://www.diputados.gob.mx/LeyesBiblio/pdf/LGAAS.pdf) (DOF 17/04/2024) busca evitar el desperdicio de alimentos. [COMPLETAR: verificar si ya se publicó su reglamento y qué obliga a los comercios.]

## Riesgos
| Riesgo | Cómo lo mitigamos |
| --- | --- |
| Las tiendas no registran todos los días | Registro con foto o voz en segundos |
| Gemini lee mal fechas | Confirmación humana obligatoria |
| No hay organizaciones que recojan a tiempo | Acuerdos de horario fijo; registro de lo no recogido |
| Responsabilidad sobre inocuidad | Solo productos no caducados; la tienda decide |
| La tienda no quiere pagar | Alternativa: que lo financie una universidad o municipio |

## Próximos pasos
Piloto de 2 semanas con [COMPLETAR] tiendas, medir el % rescatado contra una semana sin la app, y validar el precio.
