"""Diagnóstico de la conexión con Gemini.

Uso (en la carpeta del proyecto):   python probar_gemini.py

Revisa el archivo .env, hace una llamada de prueba y, si falla, muestra el motivo exacto
y los modelos que tu clave sí puede usar. No muestra tu clave completa.
"""
import os

from dotenv import load_dotenv

load_dotenv()

clave = os.getenv("GEMINI_API_KEY", "")
modelo = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
respaldo = os.getenv("GEMINI_MODEL_RESPALDO", "gemini-3.5-flash-lite")

print("1) Archivo .env")
if not os.path.exists(".env"):
    print("   ✗ No encuentro el archivo .env en esta carpeta. ¿Se llama .env.txt? ¿Estás en la carpeta de app.py?")
    raise SystemExit
if not clave:
    print("   ✗ GEMINI_API_KEY está vacía en .env")
    raise SystemExit
if clave != clave.strip() or '"' in clave or "'" in clave:
    print("   ✗ La clave tiene espacios o comillas. Déjala así: GEMINI_API_KEY=AIza... (sin comillas ni espacios)")
    raise SystemExit
print(f"   ✓ Clave encontrada: {clave[:6]}…{clave[-4:]} ({len(clave)} caracteres)")
print(f"   ✓ Modelo: {modelo}  ·  respaldo: {respaldo}")
print(f"   · GEMINI_MOCK = {os.getenv('GEMINI_MOCK', '(vacío)')}  (debe ser false para usar Gemini)")

print("\n2) Librería de Gemini")
try:
    from google import genai
    print("   ✓ google-genai instalada")
except ImportError:
    print("   ✗ Falta instalarla:  python -m pip install -r requirements.txt")
    raise SystemExit

cliente = genai.Client(api_key=clave)

print("\n3) Llamada de prueba")
for nombre in [modelo, respaldo]:
    try:
        respuesta = cliente.models.generate_content(model=nombre, contents="Responde solo la palabra: listo")
        print(f"   ✓ {nombre} respondió: {respuesta.text.strip()}")
    except Exception as error:
        codigo = getattr(error, "code", "")
        mensaje = getattr(error, "message", "") or str(error)
        print(f"   ✗ {nombre} · Error {codigo}: {mensaje[:300]}")
        if codigo == 400 and "API key" in mensaje:
            print("     → La clave no es válida. Cópiala de nuevo en https://aistudio.google.com/apikey")
        elif codigo in (401, 403):
            print("     → La clave no tiene permiso. Crea una nueva en https://aistudio.google.com/apikey")
        elif codigo == 404:
            print("     → Ese modelo no existe o tu clave no lo puede usar. Usa uno de la lista de abajo.")
        elif codigo == 429:
            print("     → Sin cuota para ese modelo. Usa otro de la lista o espera unos minutos.")
        elif codigo in (500, 503, 504):
            print("     → Google está saturado en este momento. No es tu culpa: espera un poco o usa otro modelo.")
        else:
            print("     → Revisa tu conexión a internet y vuelve a intentar.")
print("\n   Si al menos uno respondió, la app ya funciona con Gemini (usa el respaldo cuando el principal falla).")
print("   Reinicia la app después de cambiar el .env (Ctrl + C y python app.py).")

print("\n4) Modelos 'flash' que tu clave puede usar (cópialo en GEMINI_MODEL):")
try:
    nombres = []
    for m in cliente.models.list():
        nombre = (m.name or "").replace("models/", "")
        acciones = getattr(m, "supported_actions", None) or []
        if "flash" in nombre and ("generateContent" in acciones or not acciones) \
                and not any(x in nombre for x in ("tts", "image", "live", "audio", "transcribe")):
            nombres.append(nombre)
    for nombre in sorted(set(nombres)):
        print(f"   - {nombre}")
    if not nombres:
        print("   (no se encontraron; revisa la clave)")
except Exception as error:
    print(f"   No se pudo obtener la lista: {getattr(error, 'message', '') or error}")
