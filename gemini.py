"""Todo lo que hace Gemini en Rescata, en un solo archivo.

Gemini SUGIERE; la persona CONFIRMA. Nada de lo que devuelve se guarda sin que la tienda lo revise.

Usos:
  1. leer_foto()        foto de una etiqueta o de un refrigerador -> lista de productos con fecha
  2. leer_texto()       lo que la tienda dicta o escribe -> lista de productos
  3. redactar_alerta()  aviso del día para la tienda
  4. mensaje_ofertas()  mensaje para compartir por WhatsApp
  5. recomendaciones()  resumen del tablero de impacto en lenguaje sencillo
  6. responder_chat()   asistente que resuelve dudas de cualquier usuario

Modo simulado: si no hay GEMINI_API_KEY en el archivo .env, o si GEMINI_MOCK=true, se usan
respuestas guardadas. También se usa si Gemini falla (sin internet, sin cuota). La pantalla
siempre avisa cuando una respuesta es simulada, para declararlo en la demo.
"""
import json
import os
import time
from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, Field

import reglas

MODELO_POR_DEFECTO = "gemini-3.8-flash"
MODELO_RESPALDO = "gemini-3.5-flash-lite"   # se usa si el principal está saturado o sin cuota


# ------------------------------------------------------------------ forma de las respuestas

class ProductoDetectado(BaseModel):
    producto: str = Field(description="Nombre corto en español con presentación, ej. 'Yogur natural 1 L'")
    categoria: str = Field(description="Una de: " + ", ".join(reglas.CATEGORIAS))
    cantidad: int = Field(description="Unidades visibles o mencionadas")
    unidad: str = Field(description="Una de: " + ", ".join(reglas.UNIDADES))
    fecha_caducidad: Optional[str] = Field(description="AAAA-MM-DD, o null si no se puede saber")
    fecha_estimada: bool = Field(description="true si la fecha NO venía impresa y es una estimación")
    nota: Optional[str] = Field(description="Aclaración breve, ej. 'no se lee el año'")


class ListaProductos(BaseModel):
    productos: list[ProductoDetectado]


class Respuesta:
    """Lo que devuelve cada función: el contenido, si fue simulado y un aviso opcional."""

    def __init__(self, contenido, simulado=False, aviso=None):
        self.contenido = contenido
        self.simulado = simulado
        self.aviso = aviso


# ------------------------------------------------------------------ conexión

def modo_simulado():
    forzado = os.getenv("GEMINI_MOCK", "").strip().lower() in ("1", "true", "si", "sí")
    return forzado or not os.getenv("GEMINI_API_KEY")


def nombre_modelo():
    return os.getenv("GEMINI_MODEL", MODELO_POR_DEFECTO)


_conexion = {"clave": None, "cliente": None}


def _cliente(nuevo=False):
    """Una sola conexión con Gemini para toda la app.

    Se guarda para que no se cierre a media llamada; si cambia la clave o se pide nueva, se vuelve a crear.
    """
    from google import genai  # se importa aquí para que la app funcione aunque no esté instalado

    clave = os.environ["GEMINI_API_KEY"]
    if nuevo or _conexion["cliente"] is None or _conexion["clave"] != clave:
        _conexion.update(clave=clave, cliente=genai.Client(api_key=clave))
    return _conexion["cliente"]


def _modelos():
    """El modelo principal y, si es distinto, el de respaldo."""
    principal = nombre_modelo()
    respaldo = os.getenv("GEMINI_MODEL_RESPALDO", MODELO_RESPALDO).strip()
    return [principal] + ([respaldo] if respaldo and respaldo != principal else [])


def _generar(contenidos, config=None):
    """Llama a Gemini con reintentos.

    - 500/503/504 (Google saturado): espera un momento y reintenta una vez.
    - Si la conexión se cerró, abre una nueva y reintenta.
    - Si sigue fallando, o es 429 (sin cuota) o 404 (modelo no disponible), prueba el modelo de respaldo.
    - Cualquier otro error (por ejemplo, clave inválida) se reporta de inmediato.
    """
    ultimo_error = None
    for modelo in _modelos():
        for intento in range(2):
            try:
                cliente = _cliente()
                return cliente.models.generate_content(model=modelo, contents=contenidos, config=config)
            except Exception as error:
                ultimo_error = error
                if isinstance(error, RuntimeError) and "closed" in str(error) and intento == 0:
                    _cliente(nuevo=True)  # la conexión se cerró: se abre otra y se reintenta
                    continue
                codigo = getattr(error, "code", None)
                if codigo in (500, 503, 504) and intento == 0:
                    time.sleep(1.5)
                    continue
                if codigo in (404, 429, 500, 503, 504):
                    break  # siguiente modelo
                raise
    raise ultimo_error


def _pedir_json(contenidos, esquema):
    """Pide a Gemini una respuesta en JSON que siga el esquema (salida estructurada).

    Devuelve un diccionario de Python. La validación final la hace _normalizar().
    """
    from google.genai import types

    try:
        config = types.GenerateContentConfig(response_mime_type="application/json", response_schema=esquema)
        respuesta = _generar(contenidos, config)
    except Exception as error:
        # Solo si el problema fue el esquema (error 400 o del SDK), pedimos JSON con el esquema escrito
        # en las instrucciones. Si fue otra cosa (sin internet, sin cuota), se reporta el error.
        if getattr(error, "code", 400) != 400:
            raise
        guia = "\nResponde solo con JSON que siga este esquema:\n" + json.dumps(esquema.model_json_schema())
        contenidos = (contenidos + [guia]) if isinstance(contenidos, list) else contenidos + guia
        respuesta = _generar(contenidos, types.GenerateContentConfig(response_mime_type="application/json"))
    datos = json.loads(respuesta.text)
    return {"productos": datos} if isinstance(datos, list) else datos


def _pedir_texto(prompt):
    return (_generar(prompt).text or "").strip()


def _con_respaldo(llamada, respaldo):
    """Intenta Gemini; si no hay clave o falla, usa la respuesta simulada y lo dice."""
    if modo_simulado():
        return Respuesta(respaldo(), simulado=True)
    try:
        return Respuesta(llamada())
    except Exception as error:  # sin internet, sin cuota, clave inválida, respuesta mal formada…
        codigo = getattr(error, "code", "")
        detalle = (getattr(error, "message", "") or str(error))[:180]
        return Respuesta(
            respaldo(), simulado=True,
            aviso=f"Gemini no respondió ({type(error).__name__} {codigo}: {detalle}). "
                  f"Se muestra una respuesta simulada. Para revisar, ejecuta: python probar_gemini.py",
        )


# ------------------------------------------------------------------ limpieza de lo que devuelve

def _entero(valor):
    try:
        return max(1, int(float(valor)))
    except (TypeError, ValueError):
        return 1


def _normalizar(productos, hoy):
    """Asegura que cada producto use categorías, unidades y fechas válidas para la app."""
    limpios = []
    for p in productos[:15]:
        if not isinstance(p, dict):
            continue
        datos = p
        fecha = datos.get("fecha_caducidad")
        try:
            fecha = date.fromisoformat(fecha).isoformat() if fecha else ""
        except ValueError:
            fecha = ""
        limpios.append({
            "producto": str(datos.get("producto") or "").strip()[:80],
            "categoria": datos.get("categoria") if datos.get("categoria") in reglas.CATEGORIAS else "Otro",
            "cantidad": _entero(datos.get("cantidad")),
            "unidad": datos.get("unidad") if datos.get("unidad") in reglas.UNIDADES else "pieza",
            "fecha_caducidad": fecha,
            "fecha_estimada": bool(datos.get("fecha_estimada")),
            "nota": datos.get("nota") or "",
            "precio": "",
            "caducado": bool(fecha) and date.fromisoformat(fecha) < hoy,
        })
    return [p for p in limpios if p["producto"]]


INSTRUCCIONES_PRODUCTOS = """Eres asistente de una tienda de abarrotes en México. Hoy es {hoy}.
Para cada producto alimenticio distinto devuelve:
- producto: nombre corto en español con su presentación (ej. "Leche entera 1 L").
- categoria: exactamente una de {categorias}.
- cantidad: número de unidades (si no se sabe, 1).
- unidad: exactamente una de {unidades}.
- fecha_caducidad: si la fecha de caducidad o consumo preferente está impresa y se lee, escríbela en formato AAAA-MM-DD y pon fecha_estimada=false. Si solo trae día y mes, usa la fecha más próxima a partir de hoy.
- Si la fecha NO está impresa o no se lee (pan, fruta, comida preparada), estima una fecha razonable según el tipo de producto, pon fecha_estimada=true y explica en "nota".
No inventes productos que no aparezcan. Máximo 15 productos."""


def _instrucciones(hoy):
    return INSTRUCCIONES_PRODUCTOS.format(
        hoy=hoy.isoformat(), categorias=reglas.CATEGORIAS, unidades=reglas.UNIDADES
    )


# ------------------------------------------------------------------ 1. foto

def leer_foto(imagen, tipo_mime, hoy):
    def llamada():
        from google.genai import types

        partes = [
            types.Part.from_bytes(data=imagen, mime_type=tipo_mime),
            _instrucciones(hoy) + "\nLa imagen puede ser una sola etiqueta o un refrigerador/anaquel con varios productos.",
        ]
        return _normalizar(_pedir_json(partes, ListaProductos).get("productos", []), hoy)

    def respaldo():
        return _normalizar([
            {"producto": "Yogur de fresa 1 L", "categoria": "Lácteos", "cantidad": 4, "unidad": "pieza",
             "fecha_caducidad": (hoy + timedelta(days=2)).isoformat(), "fecha_estimada": False},
            {"producto": "Leche deslactosada 1 L", "categoria": "Lácteos", "cantidad": 6, "unidad": "pieza",
             "fecha_caducidad": (hoy + timedelta(days=4)).isoformat(), "fecha_estimada": False},
            {"producto": "Queso Oaxaca 500 g", "categoria": "Lácteos", "cantidad": 2, "unidad": "paquete",
             "fecha_caducidad": (hoy + timedelta(days=3)).isoformat(), "fecha_estimada": True,
             "nota": "La etiqueta está tapada; fecha estimada."},
        ], hoy)

    return _con_respaldo(llamada, respaldo)


# ------------------------------------------------------------------ 2. dictado o texto

def leer_texto(texto, hoy):
    def llamada():
        prompt = _instrucciones(hoy) + f'\nLa persona de la tienda dijo: "{texto}"'
        return _normalizar(_pedir_json(prompt, ListaProductos).get("productos", []), hoy)

    def respaldo():
        return _normalizar([
            {"producto": "Bolillo", "categoria": "Panadería", "cantidad": 12, "unidad": "pieza",
             "fecha_caducidad": (hoy + timedelta(days=1)).isoformat(), "fecha_estimada": True,
             "nota": "El pan no trae fecha impresa; se estimó 1 día."},
            {"producto": "Leche entera 1 L", "categoria": "Lácteos", "cantidad": 4, "unidad": "pieza",
             "fecha_caducidad": (hoy + timedelta(days=1)).isoformat(), "fecha_estimada": False},
        ], hoy)

    return _con_respaldo(llamada, respaldo)


# ------------------------------------------------------------------ 3. alerta del día

def _lista(lotes):
    return "\n".join(
        f"- {l['producto']}: {l['cantidad_disponible']} {l['unidad']}, faltan {l['dias']} día(s), "
        f"precio hoy ${l['precio_actual']:.2f}, estado {l['estado']}"
        for l in lotes
    )


def redactar_alerta(tienda, lotes):
    def llamada():
        return _pedir_texto(
            f"Eres asistente de la tienda '{tienda}'. Escribe una alerta breve (máximo 5 líneas, sin markdown) "
            f"para la persona encargada, en español de México, sobre estos productos por caducar, "
            f"con una acción concreta para cada uno. Usa solo estos datos:\n{_lista(lotes)}"
        )

    def respaldo():
        urgentes = [l for l in lotes if l["estado"] == "venta"]
        donacion = [l for l in lotes if l["estado"] == "donacion"]
        lineas = []
        if urgentes:
            lineas.append(f"Hoy tienes {len(urgentes)} producto(s) con el descuento más alto: "
                          + ", ".join(l["producto"] for l in urgentes) + ".")
            lineas.append("Ponlos al frente del mostrador y compártelos por WhatsApp.")
        if donacion:
            lineas.append("En donación hoy: " + ", ".join(l["producto"] for l in donacion)
                          + ". Confirma la hora de recogida con la organización.")
        return "\n".join(lineas) or "No hay productos por caducar hoy."

    return _con_respaldo(llamada, respaldo)


# ------------------------------------------------------------------ 4. mensaje para WhatsApp

def mensaje_ofertas(tienda, zona, lotes):
    def llamada():
        return _pedir_texto(
            f"Escribe un mensaje corto de WhatsApp (máximo 8 líneas, puede llevar 1 o 2 emojis, sin markdown) "
            f"para los vecinos de la tienda '{tienda}' ({zona}), anunciando estos productos con descuento "
            f"porque caducan pronto. Incluye precio de hoy y que se aparten en Rescata. Usa solo estos datos:\n"
            f"{_lista(lotes)}"
        )

    def respaldo():
        lineas = [f"🛒 Ofertas de hoy en {tienda}", "Productos en buen estado que caducan pronto:"]
        lineas += [f"• {l['producto']}: ${l['precio_actual']:.2f} (quedan {l['cantidad_disponible']})" for l in lotes]
        lineas.append("Apártalos en Rescata y recógelos en la tienda. ¡Ayúdanos a no tirar comida!")
        return "\n".join(lineas)

    return _con_respaldo(llamada, respaldo)


# ------------------------------------------------------------------ 5. recomendaciones del tablero

def recomendaciones(tienda, datos):
    resumen = {k: datos[k] for k in ("vendido", "donado", "desechado", "dinero", "porcentaje", "por_categoria")}

    def llamada():
        return _pedir_texto(
            f"Eres asesor de la tienda '{tienda}'. Con estos datos de lo que pasó con sus productos por caducar "
            f"(unidades vendidas con descuento, donadas y desechadas), escribe 3 recomendaciones breves y concretas "
            f"en español de México, numeradas, sin markdown. No inventes cifras que no estén aquí:\n"
            f"{json.dumps(resumen, ensure_ascii=False)}"
        )

    def respaldo():
        if not datos["por_categoria"]:
            return "Aún no hay suficientes datos. Registra productos durante una semana para recibir recomendaciones."
        peor = max(datos["por_categoria"], key=lambda c: c["desechado"])
        return (
            f"1. La categoría con más desechos es {peor['categoria']} ({peor['desechado']} unidades): "
            f"prueba pedir un poco menos o registrarla antes.\n"
            f"2. Comparte las ofertas por WhatsApp cuando falten 2 días; es cuando el descuento es mayor.\n"
            f"3. Acuerda un horario fijo de recogida con una organización para que los donativos no se pierdan."
        )

    return _con_respaldo(llamada, respaldo)


# ------------------------------------------------------------------ 6. asistente (chatbot)

INSTRUCCIONES_CHAT = """Eres "Asistente Rescata", el asistente de la página web Rescata.
Responde en español de México, en máximo 6 líneas, con tono amable y claro. No uses markdown (ni ** ni #).

Qué es Rescata: una página para que las tiendas de barrio vendan con descuento o donen sus productos antes de que caduquen.
Escalera de rescate de cada producto:
- Más de 5 días para caducar: precio normal.
- De 3 a 5 días: primer descuento (20 % por defecto; cada tienda puede cambiarlo en Ajustes).
- 1 o 2 días: descuento mayor (40 % por defecto).
- El día que caduca: ya no se vende; se ofrece a organizaciones (comedores, albergues) que lo apartan con hora de recogida.
- Ya caducado: se cierra y lo que quedó se registra como desechado. El tablero de impacto muestra lo vendido, donado y desechado.

Qué puede hacer cada tipo de cuenta:
- Comprador: buscar en "Productos" con filtros, apartar (necesita cuenta de comprador), ver "Mis apartados", recoger en la tienda diciendo su número de apartado y cancelar si sigue pendiente. Cualquiera puede ver los productos sin cuenta.
- Tienda: registrar productos con foto o voz (Gemini llena los datos y la tienda confirma) o a mano, ver alertas, marcar apartados como entregados, compartir ofertas por WhatsApp, ver su impacto y cambiar descuentos en Ajustes.
- Organización: ver donativos del día, apartarlos con hora de recogida y ver "Mis donativos".
Para crear cuenta: botón "Crear cuenta", elegir comprador, tienda u organización.

Reglas que siempre sigues:
- Usa solo la información de este texto y de los datos de abajo. Si no lo sabes, dilo y sugiere preguntar directamente a la tienda.
- No inventes productos, precios, tiendas, horarios ni cifras.
- No afirmes que un alimento es seguro para comer: eso lo decide la tienda, y la persona revisa el producto al recogerlo.
- Si preguntan algo que no tiene que ver con Rescata o con aprovechar alimentos, responde amablemente que solo puedes ayudar con Rescata.
- Nunca pidas contraseñas ni datos personales.

Persona que pregunta: {quien}
Hoy es {hoy}.

Productos a la venta ahora:
{catalogo}

Productos en donación hoy:
{donacion}
{extra}"""


def _lineas_catalogo(lotes, limite=25):
    if not lotes:
        return "(ninguno)"
    return "\n".join(
        f"- {l['producto']} en {l['tienda']} ({l['zona']}): {l['precio_actual']:.2f} pesos por {l['unidad']}"
        f"{' con ' + str(l['descuento']) + ' % de descuento' if l['descuento'] else ''}, "
        f"quedan {l['cantidad_disponible']}, faltan {l['dias']} día(s)"
        for l in lotes[:limite]
    )


def responder_chat(mensaje, historial, contexto):
    """Responde una pregunta con el contexto de Rescata, el catálogo y el rol de quien pregunta.

    historial: lista de {"rol": "persona"|"asistente", "texto": "..."} con los últimos mensajes.
    contexto: {"quien", "hoy", "catalogo", "donacion", "extra"}.
    """
    def llamada():
        prompt = INSTRUCCIONES_CHAT.format(
            quien=contexto["quien"], hoy=contexto["hoy"],
            catalogo=_lineas_catalogo(contexto["catalogo"]),
            donacion=_lineas_catalogo(contexto["donacion"]),
            extra=contexto.get("extra", ""),
        )
        conversacion = "\n".join(
            f"{'Persona' if m['rol'] == 'persona' else 'Asistente'}: {m['texto']}" for m in historial
        )
        return _pedir_texto(f"{prompt}\n\nConversación:\n{conversacion}\nPersona: {mensaje}\nAsistente:")

    return _con_respaldo(llamada, lambda: _respuesta_frecuente(mensaje, contexto))


def _respuesta_frecuente(mensaje, contexto):
    """Respuestas de ejemplo para el modo simulado, buscando palabras clave."""
    texto = " " + mensaje.lower() + " "

    def tiene(*palabras):
        return any(p in texto for p in palabras)

    if tiene("hola", "buenas", "buenos"):
        return "¡Hola! Soy el asistente de Rescata. Puedo explicarte cómo apartar, cómo funcionan los descuentos o qué productos hay hoy. ¿En qué te ayudo?"
    if tiene("cuenta", "registr", "inscrib", "crear"):
        return "Pulsa \"Crear cuenta\" arriba a la derecha y elige si eres comprador, tienda u organización. Solo necesitas tu nombre, correo y una contraseña de al menos 8 caracteres."
    if tiene("apart", "reserv", "recog", "recojo", "comprar"):
        return ("Entra con tu cuenta de comprador, ve a \"Productos\", elige la cantidad y pulsa \"Apartar\". "
                "Te damos un número de apartado: dilo en la tienda al recoger. Si cambias de opinión, cancélalo en \"Mis apartados\".")
    if tiene("descuento", "precio", "barato", "cuesta"):
        return ("El precio baja solo conforme se acerca la fecha: normal con más de 5 días, 20 % de descuento de 3 a 5 días "
                "y 40 % con 1 o 2 días. Cada tienda puede ajustar sus porcentajes.")
    if tiene("donac", "donar", "donat", "organiza", "comedor", "albergue"):
        return ("El día que un producto caduca deja de venderse y se ofrece a organizaciones. Con una cuenta de organización "
                "lo apartas en \"Donativos\" eligiendo la hora de recogida.")
    if tiene("foto", "gemini", " ia", "inteligencia", "voz", "dict"):
        return ("Las tiendas pueden registrar productos con una foto o dictando. Gemini propone los datos y la tienda los "
                "revisa y pone el precio antes de guardar.")
    if tiene("segur", "apto", "enferm", "malo", "buen estado"):
        return ("La app no certifica que un alimento sea apto: lo decide la tienda, y tú puedes revisarlo al recogerlo. "
                "Si tienes dudas sobre un producto, pregunta directamente en la tienda.")
    disponibles = contexto["catalogo"]
    coincidencias = [l for l in disponibles if any(pal in l["producto"].lower() or pal in l["categoria"].lower()
                                                   for pal in texto.split() if len(pal) > 3)]
    if coincidencias or tiene("hay", "disponible", "producto", "qué tienen", "que tienen"):
        lista = coincidencias or disponibles
        if not lista:
            return "Ahora mismo no hay productos a la venta. Vuelve más tarde o revisa la sección \"Productos\"."
        lineas = [f"• {l['producto']} en {l['tienda']}: ${l['precio_actual']:.2f}" for l in lista[:5]]
        return "Esto hay ahora:\n" + "\n".join(lineas) + "\nPuedes apartarlo en \"Productos\"."
    return ("Puedo ayudarte con cómo apartar, cómo funcionan los descuentos y donaciones, cómo crear tu cuenta "
            "o qué productos hay hoy. ¿Qué te gustaría saber?")
