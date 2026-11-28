# Créditos

## Imágenes de los documentos de práctica

Las imágenes de `documentos/ejemplos/01` a `05` provienen de
[Wikimedia Commons](https://commons.wikimedia.org) y conservan su licencia original.

| Imagen | Autor | Licencia |
|---|---|---|
| Resolución de alcaldía de Mache | Helder Zavaleta Verde | CC BY 4.0 |
| Billetes de intis (once anversos) | ByRussia45 | CC0 |
| Placa de la Calle Capón | Miguel Angel Chong | CC BY 3.0 |
| Pizarra de menú del restaurante Levaggi, Lince | Dtarazona | CC BY-SA 3.0 |
| *Mercurio Peruano*, 13 de enero de 1791 | Sociedad Académica de Amantes del País | dominio público |
| Recibo de la Peruvian Telephone Company, 1895 | Peruvian Telephone Company | dominio público |
| Tarjeta de Ricardo Palma a Luis Antonio Eguiguren, 1912 | Ricardo Palma; digitalización de Leguicall | dominio público |
| Acta de la Independencia del Perú, 1821 | Manuel Pérez de Tudela | dominio público |
| Cartel «Picante de cuy», Ingenio, Junín | Dtarazona | dominio público |

`06_licitacion_ilo.pdf` es la portada de las bases de la Licitación Pública de Obras
N° 05-2026-C-MPI de la Municipalidad Provincial de Ilo, documento público publicado en el
SEACE.

## Audios de práctica

Los audios `01` a `04` de `audio/ejemplos/` provienen de
[Wikimedia Commons](https://commons.wikimedia.org) y conservan su licencia original.

| Audio | Autor | Licencia | Fuente |
|---|---|---|---|
| `01_vendedora_de_frutas.ogg` | JorgeFlores-pe (Wikimedia Perú) | CC BY-SA 4.0 | [Entrevista 1 en la Av. Rivagüero - El Agustino](https://commons.wikimedia.org/wiki/File:Entrevista_1_en_la_Av._Rivag%C3%BCero_-_El_Agustino.ogg) |
| `02_dos_vendedoras.ogg` | JorgeFlores-pe (Wikimedia Perú) | CC BY-SA 4.0 | [Entrevista 2 en la Av. Rivagüero - El Agustino](https://commons.wikimedia.org/wiki/File:Entrevista_2_en_la_Av._Rivag%C3%BCero_-_El_Agustino.ogg) |
| `03_conferencia_de_prensa.ogg` | QM Keen | CC BY-SA 4.0 | [Entrevista a Aurora Coronado](https://commons.wikimedia.org/wiki/File:Entrevista-Aurora_Coronado-organizaci%C3%B3n_de_mujeres_ind%C3%ADgenas-fiestas_patrias.ogg) |
| `04_quechua_shansha.ogg` | Figuemijun (proyecto *Voces y plantas – Qurakuna Rimaykuy*) | CC BY-SA 4.0 | [Maricela Figueroa - Entrevista sobre Aurinsha, Shansha, Áncash](https://commons.wikimedia.org/wiki/File:Maricela_Figueroa_-_Entrevista_sobre_Aurinsha%2C_Shansha%2C_%C3%81ncash%2C_Per%C3%BA.ogg) |

`05_silencio_y_ruido.wav` es un audio sintético hecho para el curso. `herramientas/prueba_voz.wav`
es una frase del corpus [OpenSLR 73](https://www.openslr.org/73/) de español peruano
(Google, CC BY-SA 4.0).

## Software

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) (Apache 2.0): los modelos PP-OCRv6.
- [RapidOCR](https://github.com/RapidAI/RapidOCR) (Apache 2.0): ejecuta esos modelos con ONNX Runtime.
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) (AGPL 3.0): lee los PDF.
- [Whisper](https://github.com/openai/whisper) (MIT): el modelo de transcripción large-v3-turbo,
  convertido a int8 para CTranslate2 ([Zoont/faster-whisper-large-v3-turbo-int8-ct2](https://huggingface.co/Zoont/faster-whisper-large-v3-turbo-int8-ct2), MIT),
  y Whisper small ([Systran/faster-whisper-small](https://huggingface.co/Systran/faster-whisper-small), MIT).
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT) y
  [CTranslate2](https://github.com/OpenNMT/CTranslate2) (MIT): ejecutan Whisper en CPU. Incluyen el
  detector de voz [Silero VAD](https://github.com/snakers4/silero-vad) (MIT).
- [PyAV](https://github.com/PyAV-Org/PyAV) (BSD): lee los audios y videos.
- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) (Apache 2.0) y el modelo ERes2Net de
  [3D-Speaker](https://github.com/modelscope/3D-Speaker) (Apache 2.0): las huellas de voz para
  separar hablantes.

El material sale de la sesión 10 del curso
[Data Science con Python](https://github.com/d2cml-ai/Data-Science-Python).
