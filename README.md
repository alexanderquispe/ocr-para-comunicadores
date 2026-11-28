# De la foto al dato · OCR para comunicadores

Repositorio del curso. Aquí aprendemos a convertir PDF escaneados, fotos de documentos y
archivos históricos en **texto y tablas**, conversando con **Claude Cowork**. No hace falta
programar.

Mucha información pública peruana no está en una tabla. Está en resoluciones escaneadas,
bases de licitaciones, actas, recibos y fotos tomadas con el celular. El **OCR**
(reconocimiento óptico de caracteres) convierte esas imágenes en texto. Saber usarlo, y
sobre todo saber **cuándo se equivoca**, es una herramienta de reportería.

## Cómo empezar

1. **Descarga el repositorio.** Usa el botón verde **Code** y luego **Download ZIP**. Descomprímelo
   en Documentos o en el Escritorio.
2. **Ábrelo en Cowork.** Abre la app de escritorio de Claude, entra a **Cowork** y dale acceso
   a la carpeta que descomprimiste (`ocr-para-comunicadores-main`).
3. **Pega el primer pedido:**

   > Lee el archivo CLAUDE.md de esta carpeta y prepara todo para hacer OCR. Cuando termines, dime si la prueba funcionó.

   La primera vez tarda uno o dos minutos, mientras instala el OCR.
4. **Sigue con los pedidos de [`guias/pedidos.md`](guias/pedidos.md).**

## Cómo es cada sesión

| Hora | Qué hacemos |
|---|---|
| 1.ª | Exposición: cómo lee una máquina y dónde se equivoca |
| 2.ª | Trabajo en parejas o tríos con un documento ([consigna](guias/trabajo-y-presentacion.md)) |
| 3.ª | Presentaciones: 5 minutos por grupo y 2 de preguntas |

## Los documentos de práctica

Están en `documentos/ejemplos/`, ordenados de fácil a casi imposible.

| Archivo | Qué es | Qué mirar |
|---|---|---|
| `01_resolucion_mache.pdf` | Resolución municipal impresa (2016) | Lee casi todo, pero confunde un cero con una «o» con 98 % de confianza |
| `02_archivo_historico.pdf` | *Mercurio Peruano* (1791), recibo de teléfono (1895) y tarjeta de Ricardo Palma (1912) | La imprenta colonial, los formularios llenados a pluma, la letra cursiva |
| `03_billetes_hiperinflacion.pdf` | Once billetes de intis (1987–1990) | Armar una tabla de monto, fecha y serie sin tipear nada |
| `04_calle_y_carteles.pdf` | Placa de la Calle Capón, pizarra de menú y cartel pintado a mano | El OCR lee todo lo que ve… y no ve algunas cosas |
| `05_acta_independencia.pdf` | Acta de la Independencia (1821) | El límite: un manuscrito que el OCR no puede leer |
| `06_licitacion_ilo.pdf` | Portada de las bases de una licitación pública (SEACE, 2026) | La página viene girada; ojo con la errata del original |

## Audio: de la voz al texto

La segunda parte del curso usa la misma lógica con grabaciones: entrevistas, conferencias de
prensa, audios de WhatsApp o videos. Las transcribe **Whisper** en tu computadora y Claude
trabaja con el texto: busca citas, separa a quienes hablan, arma subtítulos y tablas.

1. Pega el primer pedido de audio:

   > Lee el archivo CLAUDE.md de esta carpeta y prepara todo para transcribir audio. Cuando termines, dime si la prueba funcionó.

   La primera vez baja el modelo de transcripción (814 MB) y puede tardar varios minutos.
2. Sigue con los pedidos de [`guias/pedidos-audio.md`](guias/pedidos-audio.md).
3. Los audios de práctica y los consejos para grabar están en [`audio/README.md`](audio/README.md).
   Tus grabaciones van en la carpeta `audio/`.

Por cada audio, Claude deja en `salidas/` la transcripción con el minuto y segundo de cada
frase, los subtítulos (`.srt`), una tabla de palabras con su probabilidad y un resumen con los
fragmentos dudosos y, si lo pides, cuánto habla cada persona.

Claude no puede escuchar: lee lo que escribió Whisper. **Cada cita se escucha en su minuto
antes de publicarla.**

## Trae tus propios documentos

Déjalos en la carpeta `documentos/`. Funcionan PDF (escaneados o no) e imágenes (JPG, PNG).
Algunas ideas:

- resoluciones y normas en PDF escaneado de un ministerio o una municipalidad;
- bases o contratos de una licitación pública (SEACE);
- páginas de diarios o revistas antiguos digitalizados;
- afiches, volantes, carteles o boletas fotografiados con el celular.

Cuidado con los documentos que traen datos personales (DNI, teléfonos, direcciones): no los
pongas en tus tablas ni en tu presentación si no son imprescindibles.

## Qué obtienes

Por cada documento, Claude deja una carpeta en `salidas/` con:

- **la página con cajas**: cada línea que encontró el OCR, en **azul** si está seguro,
  **ámbar** si duda y **naranja** si casi no pudo leer;
- **el texto** de cada página y del documento completo;
- **una tabla de líneas** con su confianza, para saber qué revisar a mano;
- y las tablas en Excel o las diapositivas que le pidas.

## Seis reglas para no equivocarse

1. **Primero una muestra.** Prueba una página antes de procesar cien.
2. **La confianza es una alarma, no una garantía.** Un número puede salir mal con 99 % de confianza.
3. **Lo que la máquina no ve, falta sin avisar.** Compara siempre con el original.
4. **Los modelos de lenguaje inventan.** Cuando Claude «mira» una imagen lee mejor la letra a
   mano, pero puede escribir texto que suena bien y no está en el papel.
5. **La redundancia valida gratis.** Si un dato aparece dos veces, compara las dos lecturas.
6. **La persona decide.** El OCR propone; tú verificas y firmas.

## Cómo funciona por dentro

El OCR usa los modelos **PP-OCRv6 de [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)**
(gratuitos y de código abierto), ejecutados con [RapidOCR](https://github.com/RapidAI/RapidOCR)
en tu computadora: no cobra por página y tus documentos no se envían a ningún servicio de OCR.
Claude sí lee los resultados para conversar contigo, así que lo que él ve pasa por los
servidores de Anthropic, como cualquier conversación con Claude.

El motor está en `herramientas/ocr.py` y las instrucciones que sigue Claude, en `CLAUDE.md`.

El audio lo transcribe **Whisper large-v3-turbo** (de OpenAI, abierto) con
[faster-whisper](https://github.com/SYSTRAN/faster-whisper), también en tu computadora. Para
separar a quienes hablan se usa un modelo de huellas de voz de
[3D-Speaker](https://github.com/modelscope/3D-Speaker) con
[sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx). Los modelos se bajan una sola vez a la
carpeta `modelos/`. El motor está en `herramientas/audio.py`.

## Si algo no funciona

- **Claude no puede instalar el OCR.** Pídele: *«Lee tú las páginas mirando las imágenes
  (modo B de CLAUDE.md)»*. Funciona sin instalar nada, pero sin números de confianza.
- **El documento es muy largo.** Pide primero cinco páginas.
- **El texto sale como basura.** Puede estar girado, ser un manuscrito o tener poca
  resolución. Pregúntale a Claude qué pasó y qué propone.
- **No se baja el modelo de audio.** Si un compañero ya lo tiene, copia su carpeta `modelos/`
  dentro de la tuya. También puedes pedir el modelo rápido (484 MB).
- **La transcripción va muy lenta.** Pide un tramo (*«solo del minuto 2 al 5»*) o el modelo
  rápido.

Los créditos de las imágenes y los audios están en [`CREDITOS.md`](CREDITOS.md).
