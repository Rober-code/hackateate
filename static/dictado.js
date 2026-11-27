// Dictado por voz con el reconocimiento de voz del navegador (Chrome y Edge).
// El navegador convierte la voz en texto; después Gemini interpreta ese texto.
(function () {
  const Reconocimiento = window.SpeechRecognition || window.webkitSpeechRecognition;
  const boton = document.getElementById("boton-dictar");
  const texto = document.getElementById("texto");
  if (!Reconocimiento || !boton || !texto) return;

  const reconocedor = new Reconocimiento();
  reconocedor.lang = "es-MX";
  reconocedor.continuous = true;
  reconocedor.interimResults = false;

  let escuchando = false;
  boton.hidden = false;
  document.getElementById("ayuda-dictado").textContent = "Pulsa el botón, habla y vuelve a pulsar para terminar.";

  boton.addEventListener("click", function () {
    if (escuchando) {
      reconocedor.stop();
      return;
    }
    reconocedor.start();
  });

  reconocedor.onstart = function () {
    escuchando = true;
    boton.textContent = "■ Terminar dictado";
  };
  reconocedor.onend = function () {
    escuchando = false;
    boton.textContent = "Empezar a dictar";
  };
  reconocedor.onresult = function (evento) {
    for (let i = evento.resultIndex; i < evento.results.length; i++) {
      if (evento.results[i].isFinal) {
        texto.value = (texto.value + " " + evento.results[i][0].transcript).trim();
      }
    }
  };
  reconocedor.onerror = function (evento) {
    document.getElementById("ayuda-dictado").textContent =
      "No se pudo usar el micrófono (" + evento.error + "). Revisa el permiso del navegador o escribe el texto.";
  };
})();
