# Pedidos listos para copiar en Cowork

Cópialos tal cual o adáptalos a tu documento. Lo importante no es la redacción exacta sino
el orden: **preparar → muestra → documento completo → tabla → verificación → presentación**.

## 1 · Preparar

> Lee el archivo CLAUDE.md de esta carpeta y prepara todo para hacer OCR. Cuando termines, dime si la prueba funcionó.

## 2 · Muestra primero

> Haz OCR solo de la página 1 de documentos/ejemplos/02_archivo_historico.pdf. Muéstrame la imagen con las cajas, el texto y las líneas dudosas. No sigas hasta que yo lo apruebe.

**Qué observar:** las cajas naranjas son líneas que el OCR casi no pudo leer. ¿Hay texto en la
imagen que no tiene ninguna caja?

## 3 · De texto a tabla

> Haz OCR de documentos/ejemplos/03_billetes_hiperinflacion.pdf y arma una tabla con el monto, la fecha y el número de serie de cada billete. Todo dato debe aparecer tal cual en el texto del OCR; si no aparece, márcalo como "sin verificar". Guárdala en Excel en salidas/.

**Qué observar:** el número de serie aparece dos veces en cada billete. ¿Coinciden siempre las
dos lecturas?

## 4 · Contrastar con la lectura de Claude

> Ahora lee tú la misma página mirando la imagen, sin el OCR, y compara las dos versiones en una tabla. Donde no puedas leer, escribe [ilegible]: no adivines.

**Qué observar:** ¿dónde lee mejor Claude? ¿Escribió algo que no está en la imagen?

## 5 · Presentar

> Con lo que hicimos, prepárame tres diapositivas para contar en cinco minutos: el documento, qué salió bien, qué falló y cuánto confío en el dato final.

---

## Más pedidos útiles

**Archivo histórico**

> Haz OCR de las páginas 1 a 3 de mi documento y transcríbelas respetando la ortografía original. Separa las columnas si las hay y marca con [ilegible] lo que no se pueda leer.

**El texto que ya traía el PDF**

> Revisa si mi PDF ya tiene texto seleccionable. Si lo tiene, compáralo con un OCR nuevo de la página 1 (usa --forzar-ocr) y dime cuál está mejor.

**Buscar datos en muchos documentos**

> Haz OCR de todos los PDF de la carpeta documentos/ y arma una tabla con la fecha, la entidad y el monto que aparece en cada uno, con la página y la línea de donde salió cada dato.

**Medir la calidad**

> ¿Qué porcentaje de las líneas quedó como dudoso en cada página? Si mandara a revisión humana todas las líneas bajo 0,90 de confianza, ¿cuántas tendría que revisar?

**Una página que salió mal**

> La página 2 salió como basura. Dime por qué crees que pasó (girada, manuscrito, poca resolución, fondo) y prueba una solución.
