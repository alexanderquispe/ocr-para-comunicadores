# Pedidos de audio listos para copiar en Cowork

El orden es el mismo que con los documentos: **preparar → muestra → contexto → completo →
verificar → presentar**. La diferencia es que Claude no puede escuchar: lee lo que escribió
Whisper. Escuchar y verificar te toca a ti.

## 1 · Preparar

> Lee el archivo CLAUDE.md de esta carpeta y prepara todo para transcribir audio. Cuando termines, dime si la prueba funcionó.

La primera vez baja el modelo de transcripción (814 MB): puede tardar varios minutos.

## 2 · Muestra primero

> Transcribe solo el primer minuto de audio/ejemplos/02_dos_vendedoras.ogg. Muéstrame el texto con los minutos y las palabras dudosas. No sigas hasta que yo lo apruebe.

**Qué observar:** escucha el segundo 0:10. ¿Cómo escribió los nombres de las vendedoras?
¿Los marcó como dudosos?

## 3 · Darle contexto

> Vuelve a transcribir el mismo minuto, pero dale como contexto los nombres «Isabel Vásquez, Elsa Barrientos». Compara las dos versiones en una tabla.

**Qué observar:** los nombres propios, los lugares y las siglas son lo que más falla, y casi
siempre los conocemos antes de grabar.

## 4 · ¿Quién habla? y las citas

> Transcribe la entrevista completa separando a las personas que hablan (son tres). Dime cuánto habla cada una y arma una tabla en Excel con las cinco frases más citables, con su minuto y segundo. Marca todas como «pendiente» hasta que yo las escuche.

**Qué observar:** los números de hablante los pone la máquina; escucha para saber quién es
quién. Verifica cada cita en su minuto y corrige la tabla.

## 5 · Cuando el modelo inventa

> Transcribe audio/ejemplos/05_silencio_y_ruido.wav sin quitar los silencios y luego quitándolos. ¿Qué escribió en cada caso?

> Transcribe los primeros 40 segundos de audio/ejemplos/04_quechua_shansha.ogg. ¿Está en quechua lo que escribió? ¿Cuántos fragmentos salieron dudosos?

**Qué observar:** en el silencio no hay nada que transcribir, y aun así aparece una frase.
Con el quechua, el texto suena a castellano correcto, pero nadie lo dijo.

## 6 · Presentar

> Con lo que hicimos, prepárame tres diapositivas para contar en cinco minutos: el audio, qué salió bien, qué falló y cuánto confío en las citas.

---

## Más pedidos útiles

**Tu propia entrevista**

> Dejé mi entrevista en la carpeta audio/. Transcribe los dos primeros minutos. Hablamos dos personas y los nombres propios que aparecen son: [nombres, lugares, siglas].

**Subtítulos para un video**

> Genera los subtítulos de audio/mi_video.mp4 y dime en qué minutos conviene revisarlos antes de publicarlos.

**Un borrador de nota**

> Con la transcripción, escribe un borrador de nota de 300 palabras. Usa solo citas textuales que estén en la transcripción, cada una con su minuto, y no cambies ninguna palabra dentro de las comillas.

**Buscar un tema**

> ¿En qué minutos se habla de [tema]? Dame cada fragmento con su tiempo.

**Medir cuánto hay que revisar**

> ¿Cuántas palabras quedaron dudosas? Si escucho solo los fragmentos dudosos, ¿cuántos minutos de audio tengo que revisar?

**Más rápido**

> La transcripción va muy lenta. Usa el modelo rápido y dime qué se pierde.
