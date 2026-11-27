// Asistente de dudas: abre la ventana, manda la pregunta al servidor y muestra la respuesta.
(function () {
  const boton = document.getElementById("chat-boton");
  const panel = document.getElementById("chat-panel");
  const cerrar = document.getElementById("chat-cerrar");
  const lista = document.getElementById("chat-mensajes");
  const formulario = document.getElementById("chat-form");
  const entrada = document.getElementById("chat-texto");
  const sugerencias = document.getElementById("chat-sugerencias");
  const tokenCsrf = document.querySelector('meta[name="csrf"]').content;
  const historial = []; // últimos mensajes, para que el asistente recuerde la conversación

  function abrir(abierto) {
    panel.hidden = !abierto;
    boton.setAttribute("aria-expanded", String(abierto));
    if (abierto) entrada.focus();
  }

  function agregar(texto, quien, simulado, aviso) {
    const burbuja = document.createElement("div");
    burbuja.className = "burbuja " + quien;
    burbuja.textContent = texto; // textContent evita que se ejecute HTML escrito por alguien
    if (simulado) {
      const nota = document.createElement("span");
      nota.className = "simulado";
      nota.textContent = aviso || "Respuesta simulada (sin Gemini)";
      burbuja.appendChild(nota);
    }
    lista.appendChild(burbuja);
    lista.scrollTop = lista.scrollHeight;
    return burbuja;
  }

  async function preguntar(texto) {
    texto = texto.trim();
    if (!texto) return;
    agregar(texto, "yo");
    sugerencias.hidden = true;
    entrada.value = "";
    const escribiendo = document.createElement("div");
    escribiendo.className = "escribiendo";
    escribiendo.textContent = "Escribiendo…";
    lista.appendChild(escribiendo);

    try {
      const respuesta = await fetch(formulario.dataset.url, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": tokenCsrf },
        body: JSON.stringify({ mensaje: texto, historial: historial.slice(-6) }),
      });
      const datos = await respuesta.json();
      const contestacion = datos.respuesta || datos.error || "No pude responder. Intenta de nuevo.";
      agregar(contestacion, "bot", datos.simulado, datos.aviso);
      if (datos.aviso) console.warn("Asistente:", datos.aviso);
      historial.push({ rol: "persona", texto: texto }, { rol: "asistente", texto: contestacion });
    } catch (error) {
      agregar("No hay conexión con el servidor. Revisa que la app siga abierta.", "bot");
    } finally {
      escribiendo.remove();
    }
  }

  boton.addEventListener("click", function () { abrir(panel.hidden); });
  cerrar.addEventListener("click", function () { abrir(false); });
  formulario.addEventListener("submit", function (evento) {
    evento.preventDefault();
    preguntar(entrada.value);
  });
  sugerencias.querySelectorAll("button").forEach(function (b) {
    b.addEventListener("click", function () { preguntar(b.textContent); });
  });
})();
