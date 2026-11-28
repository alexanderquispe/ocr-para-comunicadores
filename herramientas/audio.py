"""Transcripción de audio y video con Whisper (faster-whisper), en esta computadora.

Lo ejecuta Claude desde Cowork; los alumnos no necesitan abrir este archivo.

Uso:
    python herramientas/audio.py --prueba
    python herramientas/audio.py audio/ejemplos/02_dos_vendedoras.ogg --hasta 1:00
    python herramientas/audio.py audio/mi_entrevista.m4a --contexto "Nombre Apellido, Lugar"
    python herramientas/audio.py audio/            (todos los audios y videos de la carpeta)

Opciones:
    --modelo preciso|rapido   preciso: Whisper large-v3-turbo (baja 814 MB la primera vez)
                              rapido:  Whisper small (484 MB), unas tres veces más rápido
    --desde 1:30 --hasta 3:00 solo ese tramo (minutos:segundos)
    --contexto "..."          nombres propios, lugares, siglas o jerga que el modelo debe conocer
    --idioma es               idioma del audio (es por defecto; auto para que lo detecte)
    --hablantes auto|2|3...   separar quién habla (baja un modelo de 40 MB la primera vez)
    --sin-vad                 no quitar los silencios antes de transcribir
    --umbral 0.50             probabilidad bajo la cual una palabra se marca como dudosa
    --salida NOMBRE           carpeta dentro de salidas/ (por defecto, el nombre del archivo)

Por cada archivo escribe en salidas/<nombre>/:
    transcripcion.txt   el texto, con la marca [mm:ss] de cada fragmento (y el hablante)
    segmentos.csv       una fila por fragmento: inicio, fin, hablante, texto, confianza, dudoso
    palabras.csv        una fila por palabra, con su tiempo y su probabilidad
    subtitulos.srt      subtítulos para video, o para sincronizar en Atlas.ti, NVivo o ELAN
    resumen.md          duración, modelo, fragmentos dudosos y, si se pidió, quién habla cuánto
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import statistics
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SALIDAS = RAIZ / "salidas"
MODELOS_DIR = RAIZ / "modelos"
SR = 16_000
EXTENSIONES = {".mp3", ".m4a", ".wav", ".ogg", ".oga", ".opus", ".flac", ".aac", ".wma", ".amr",
               ".mp4", ".mov", ".m4v", ".webm", ".mkv", ".3gp", ".avi"}

MODELOS = {
    "preciso": {"repo": "Zoont/faster-whisper-large-v3-turbo-int8-ct2", "nombre": "Whisper large-v3-turbo",
                "tamano": "814 MB"},
    "rapido": {"repo": "Systran/faster-whisper-small", "nombre": "Whisper small", "tamano": "484 MB"},
}
HUELLAS_URL = ("https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/"
               "3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx")

# Prueba: una frase de OpenSLR 73 (español peruano, CC BY-SA 4.0)
PRUEBA_AUDIO = RAIZ / "herramientas" / "prueba_voz.wav"
PRUEBA_TEXTO = "La goma de mascar proviene del interior de unos árboles de los que no me sé el nombre"

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")


# ───────────────────────────────────────────────────────── utilidades
def faltan_paquetes(con_hablantes: bool = False) -> list[str]:
    faltan = []
    modulos = [("faster_whisper", "faster-whisper"), ("av", "av"), ("numpy", "numpy")]
    if con_hablantes:
        modulos.append(("sherpa_onnx", "sherpa-onnx"))
    for modulo, paquete in modulos:
        try:
            __import__(modulo)
        except ImportError:
            faltan.append(paquete)
    return faltan


def a_segundos(texto: str | None) -> float | None:
    """'90', '1:30' o '1:02:03' -> segundos."""
    if texto is None:
        return None
    partes = [float(p.replace(",", ".")) for p in str(texto).strip().split(":")]
    total = 0.0
    for p in partes:
        total = total * 60 + p
    return total


def mmss(t: float) -> str:
    t = int(round(t))
    h, resto = divmod(t, 3600)
    m, s = divmod(resto, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def srt_t(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def normalizar(texto: str) -> list[str]:
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-zñ0-9]+", texto)


def nombre_carpeta(ruta: Path, args) -> str:
    if args.salida:
        return re.sub(r"[^\w\-]+", "_", args.salida).strip("_") or ruta.stem
    sufijos = []
    if args.desde is not None or args.hasta is not None:
        sufijos.append("muestra")
    if args.contexto:
        sufijos.append("contexto")
    if args.sin_vad:
        sufijos.append("sin_vad")
    if args.modelo != "preciso":
        sufijos.append(args.modelo)
    return "_".join([ruta.stem] + sufijos)


# ───────────────────────────────────────────────────────── audio
def cargar_audio(ruta: Path):
    """Cualquier audio o video -> numpy float32, mono, 16 kHz."""
    import numpy as np
    from faster_whisper import decode_audio
    try:
        return decode_audio(str(ruta), sampling_rate=SR)
    except Exception:
        pass
    # Lectura tolerante: salta los paquetes dañados en vez de abortar.
    import av
    trozos = []
    with av.open(str(ruta)) as contenedor:
        flujo = next((s for s in contenedor.streams if s.type == "audio"), None)
        if flujo is None:
            raise ValueError("el archivo no tiene pista de audio")
        remuestreo = av.audio.resampler.AudioResampler(format="s16", layout="mono", rate=SR)
        for paquete in contenedor.demux(flujo):
            try:
                cuadros = paquete.decode()
            except Exception:
                continue
            for cuadro in cuadros:
                for r in remuestreo.resample(cuadro):
                    trozos.append(r.to_ndarray().reshape(-1))
    if not trozos:
        raise ValueError("no se pudo leer el audio")
    return np.concatenate(trozos).astype(np.float32) / 32768.0


# ───────────────────────────────────────────────────────── Whisper
_MODELO = {}


def modelo(clave: str):
    if clave not in _MODELO:
        from faster_whisper import WhisperModel
        info = MODELOS[clave]
        cache = MODELOS_DIR / ("models--" + info["repo"].replace("/", "--"))
        if not cache.exists():
            print(f"Descargando el modelo {info['nombre']} ({info['tamano']}, solo la primera vez)…", flush=True)
        try:
            _MODELO[clave] = WhisperModel(info["repo"], device="cpu", compute_type="int8",
                                          download_root=str(MODELOS_DIR), cpu_threads=os.cpu_count() or 4)
        except Exception as e:
            raise SystemExit(
                f"No se pudo cargar el modelo {info['nombre']}: {type(e).__name__}: {e}\n"
                "Si es un problema de conexión, se puede copiar la carpeta modelos/ desde otra computadora "
                "que ya lo tenga, o probar con --modelo rapido.")
    return _MODELO[clave]


def transcribir(audio, args, duracion: float, desplazamiento: float = 0.0):
    m = modelo(args.modelo)
    idioma = None if args.idioma == "auto" else args.idioma
    segs, info = m.transcribe(
        audio, language=idioma, task="transcribe", beam_size=5,
        vad_filter=not args.sin_vad, vad_parameters={"min_silence_duration_ms": 300},
        word_timestamps=True, condition_on_previous_text=False,
        hotwords=args.contexto or None,
    )
    fragmentos, ultimo_aviso = [], 0.0
    for s in segs:
        palabras = [{"inicio": w.start + desplazamiento, "fin": w.end + desplazamiento,
                     "palabra": w.word.strip(), "prob": float(w.probability)}
                    for w in (s.words or []) if w.word.strip()]
        fragmentos.append({"inicio": s.start + desplazamiento, "fin": s.end + desplazamiento,
                           "texto": s.text.strip(), "palabras": palabras,
                           "prob_silencio": float(s.no_speech_prob)})
        if s.end - ultimo_aviso >= 60:
            ultimo_aviso = s.end
            print(f"  … {mmss(s.end)} de {mmss(duracion)}", flush=True)
    if not args.sin_vad:
        pegar_a_la_voz(fragmentos, audio, desplazamiento)
    return fragmentos, info


def pegar_a_la_voz(fragmentos: list[dict], audio, desplazamiento: float):
    """Whisper suele adelantar el inicio de la primera palabra tras una pausa (se «come» el
    silencio). Se corrige con el detector de voz: si una palabra empieza en un silencio, su inicio
    pasa al momento en que vuelve la voz."""
    import bisect
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    regiones = [(r["start"] / SR + desplazamiento, r["end"] / SR + desplazamiento)
                for r in get_speech_timestamps(audio, VadOptions(min_silence_duration_ms=300))]
    if not regiones:
        return
    inicios = [a for a, _ in regiones]

    def region(t: float) -> int:
        return bisect.bisect_right(inicios, t) - 1

    for f in fragmentos:
        ps = f["palabras"]
        for w in ps:
            i = region(w["inicio"])
            en_voz = i >= 0 and w["inicio"] <= regiones[i][1]
            if not en_voz and i + 1 < len(regiones) and regiones[i + 1][0] < w["fin"]:
                w["inicio"] = regiones[i + 1][0]
        # La primera palabra de un fragmento suele quedar pegada al final del anterior, aunque la
        # segunda ya esté después de una pausa: entonces la primera también va después de la pausa.
        if len(ps) >= 2:
            i, j = region(ps[0]["inicio"]), region(ps[1]["inicio"])
            if j > i >= 0 and regiones[j][0] < ps[1]["inicio"]:
                ps[0]["inicio"] = regiones[j][0]
                ps[0]["fin"] = max(min(ps[0]["fin"], ps[1]["inicio"]), ps[0]["inicio"])
                if ps[0]["fin"] <= ps[0]["inicio"]:
                    ps[0]["fin"] = ps[1]["inicio"]
        if f["palabras"]:
            f["inicio"] = f["palabras"][0]["inicio"]
            f["fin"] = max(f["palabras"][-1]["fin"], f["inicio"])


# ───────────────────────────────────────────────────────── ¿quién habla?
def modelo_huellas() -> Path:
    """ERes2Net (3D-Speaker) en ONNX: convierte un tramo de voz en un vector de números, la «huella» de la voz."""
    destino = MODELOS_DIR / "hablantes" / "3dspeaker_eres2net_base_16k.onnx"
    if not destino.exists():
        print("Descargando el modelo de huellas de voz (40 MB, solo la primera vez)…", flush=True)
        destino.parent.mkdir(parents=True, exist_ok=True)
        tmp = destino.with_suffix(".parcial")
        try:
            urllib.request.urlretrieve(HUELLAS_URL, tmp)
        except Exception as e:
            raise SystemExit(f"No se pudo bajar el modelo de hablantes: {type(e).__name__}: {e}")
        tmp.rename(destino)
    return destino


def huellas(audio, fragmentos: list[dict], desplazamiento: float):
    import numpy as np
    import sherpa_onnx
    config = sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=str(modelo_huellas()), num_threads=os.cpu_count() or 4)
    extractor = sherpa_onnx.SpeakerEmbeddingExtractor(config)
    filas = []
    for f in fragmentos:
        x = audio[int((f["inicio"] - desplazamiento) * SR):int((f["fin"] - desplazamiento) * SR)]
        if len(x) < SR // 2:  # el modelo necesita al menos medio segundo
            x = np.pad(x, (0, SR // 2 - len(x)))
        s = extractor.create_stream()
        s.accept_waveform(SR, x)
        s.input_finished()
        filas.append(np.array(extractor.compute(s), dtype=np.float32))
    E = np.vstack(filas)
    return E / np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-9)


def agrupar(E, n: int | None, umbral: float):
    """Agrupamiento jerárquico (enlace promedio, distancia coseno). Devuelve una etiqueta por fila."""
    import numpy as np
    N = len(E)
    D = 1.0 - E @ E.T
    np.fill_diagonal(D, np.inf)
    tam = np.ones(N)
    vivos = np.ones(N, dtype=bool)
    etiqueta = np.arange(N)
    while vivos.sum() > 1:
        if n is not None and vivos.sum() <= n:
            break
        sub = np.where(vivos)[0]
        M = D[np.ix_(sub, sub)]
        i, j = divmod(int(np.argmin(M)), len(sub))
        if n is None and M[i, j] > umbral:
            break
        a, b = sub[i], sub[j]
        fila = (tam[a] * D[a] + tam[b] * D[b]) / (tam[a] + tam[b])
        D[a], D[:, a] = fila, fila
        D[a, a] = np.inf
        D[b], D[:, b] = np.inf, np.inf
        tam[a] += tam[b]
        vivos[b] = False
        etiqueta[etiqueta == b] = a
    return etiqueta


def poner_hablantes(audio, fragmentos: list[dict], n: int | None, desplazamiento: float,
                    umbral: float = 0.8, min_dur: float = 1.0) -> int:
    """Pone HABLANTE 1, 2… a cada fragmento.

    1. Huella de voz de cada fragmento.
    2. Agrupa las huellas parecidas. Si no se sabe cuántas personas hay, el umbral decide.
    3. Los fragmentos de menos de 1 s («sí», «ajá») dan huellas poco fiables: no votan al
       agrupar y después van al grupo más parecido.
    """
    import numpy as np
    if not fragmentos:
        return 0
    E = huellas(audio, fragmentos, desplazamiento)
    largos = np.array([f["fin"] - f["inicio"] >= min_dur for f in fragmentos])
    if largos.sum() < 2:
        largos[:] = True
    if n == 1 or len(fragmentos) < 2:
        etiquetas = np.zeros(len(fragmentos), dtype=int)
    else:
        base = agrupar(E[largos], n, umbral)
        grupos = sorted(set(base.tolist()))
        centros = np.vstack([E[largos][base == g].mean(axis=0) for g in grupos])
        etiquetas = (E @ centros.T).argmax(axis=1)
        etiquetas[largos] = [grupos.index(g) for g in base]
    # Numerar en el orden en que hablan: HABLANTE 1 es quien habla primero.
    orden = {}
    for e in etiquetas.tolist():
        orden.setdefault(e, len(orden) + 1)
    for f, e in zip(fragmentos, etiquetas.tolist()):
        f["hablante"] = orden[e]
        for w in f["palabras"]:
            w["hablante"] = orden[e]
    return len(orden)


# ───────────────────────────────────────────────────────── salidas
def calificar(fragmentos: list[dict], umbral: float):
    for f in fragmentos:
        probs = [w["prob"] for w in f["palabras"]]
        f["confianza"] = round(statistics.mean(probs), 3) if probs else 0.0
        f["dudosas"] = [w for w in f["palabras"] if w["prob"] < umbral]
        f["dudoso"] = bool(f["dudosas"]) or f["confianza"] < 0.80


def etiqueta(f: dict) -> str:
    return f"HABLANTE {f['hablante']}: " if f.get("hablante") else ""


def escribir(fragmentos: list[dict], destino: Path, ruta: Path, meta: dict):
    destino.mkdir(parents=True, exist_ok=True)
    with open(destino / "transcripcion.txt", "w", encoding="utf-8") as fh:
        anterior = None
        for f in fragmentos:
            if meta["hablantes"] and anterior is not None and f.get("hablante") != anterior:
                fh.write("\n")
            fh.write(f"[{mmss(f['inicio'])}] {etiqueta(f)}{f['texto']}\n")
            anterior = f.get("hablante")

    with open(destino / "segmentos.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["archivo", "fragmento", "inicio", "fin", "inicio_s", "fin_s", "hablante", "texto",
                    "confianza", "dudoso", "palabras_dudosas"])
        for i, f in enumerate(fragmentos, 1):
            dudosas = "; ".join(f"{d['palabra']} ({d['prob']:.2f})" for d in f["dudosas"])
            w.writerow([ruta.name, i, mmss(f["inicio"]), mmss(f["fin"]), round(f["inicio"], 2), round(f["fin"], 2),
                        f"HABLANTE {f['hablante']}" if f.get("hablante") else "", f["texto"],
                        f["confianza"], "sí" if f["dudoso"] else "no", dudosas])

    with open(destino / "palabras.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["fragmento", "inicio", "inicio_s", "fin_s", "hablante", "palabra", "probabilidad", "dudosa"])
        for i, f in enumerate(fragmentos, 1):
            for p in f["palabras"]:
                w.writerow([i, mmss(p["inicio"]), round(p["inicio"], 2), round(p["fin"], 2),
                            f"HABLANTE {p['hablante']}" if p.get("hablante") else "", p["palabra"],
                            round(p["prob"], 3), "sí" if p["prob"] < meta["umbral"] else "no"])

    with open(destino / "subtitulos.srt", "w", encoding="utf-8") as fh:
        for i, f in enumerate(fragmentos, 1):
            fh.write(f"{i}\n{srt_t(f['inicio'])} --> {srt_t(f['fin'])}\n{etiqueta(f)}{f['texto']}\n\n")

    escribir_resumen(fragmentos, destino, ruta, meta)


def resumen_hablantes(fragmentos: list[dict]) -> list[dict]:
    datos = {}
    anterior = None
    for f in fragmentos:
        h = f.get("hablante")
        if not h:
            continue
        d = datos.setdefault(h, {"hablante": h, "segundos": 0.0, "turnos": 0, "palabras": 0})
        d["segundos"] += f["fin"] - f["inicio"]
        d["palabras"] += len(f["palabras"])
        if h != anterior:
            d["turnos"] += 1
        anterior = h
    for d in datos.values():
        d["ppm"] = round(d["palabras"] / (d["segundos"] / 60)) if d["segundos"] > 0 else 0
    return [datos[k] for k in sorted(datos)]


def escribir_resumen(fragmentos: list[dict], destino: Path, ruta: Path, meta: dict):
    dudosos = [f for f in fragmentos if f["dudoso"]]
    n_palabras = sum(len(f["palabras"]) for f in fragmentos)
    n_dudosas = sum(len(f["dudosas"]) for f in fragmentos)
    lineas = [
        f"# {ruta.name}", "",
        "| | |", "|---|---|",
        f"| Duración procesada | {mmss(meta['duracion'])} (de {mmss(meta['desde'])} a {mmss(meta['hasta'])}) |",
        f"| Modelo | {MODELOS[meta['modelo']]['nombre']} ({meta['modelo']}) |",
        f"| Idioma | {meta['idioma']} |",
        f"| Quitar silencios (VAD) | {'no' if meta['sin_vad'] else 'sí'} |",
        f"| Contexto | {meta['contexto'] or '—'} |",
        f"| Fragmentos | {len(fragmentos)} ({len(dudosos)} dudosos) |",
        f"| Palabras | {n_palabras} ({n_dudosas} con probabilidad menor que {meta['umbral']:.2f}) |",
        f"| Tiempo de proceso | {meta['segundos']:.0f} s ({meta['duracion'] / max(meta['segundos'], 0.1):.1f} veces más rápido que el audio) |",
        "",
    ]
    if meta["hablantes"]:
        lineas += ["## Quién habla", "",
                   "| Hablante | Tiempo de habla | Turnos | Palabras | Palabras por minuto |",
                   "|---|---|---|---|---|"]
        for d in resumen_hablantes(fragmentos):
            lineas.append(f"| HABLANTE {d['hablante']} | {mmss(d['segundos'])} | {d['turnos']} | {d['palabras']} | {d['ppm']} |")
        lineas += ["", "Los números de hablante los pone la máquina: hay que escuchar para saber quién es quién.", ""]
    lineas += ["## Fragmentos dudosos", "",
               "Revisar escuchando el audio en ese minuto. La probabilidad baja es una alarma; "
               "una probabilidad alta no garantiza que la palabra sea correcta.", ""]
    if not dudosos:
        lineas.append("Ninguno.")
    for f in dudosos:
        palabras = ", ".join(f"«{d['palabra']}» ({d['prob']:.2f})" for d in f["dudosas"]) or "confianza media baja"
        lineas.append(f"- **[{mmss(f['inicio'])}]** {etiqueta(f)}{f['texto']}  \n  dudosas: {palabras}")
    (destino / "resumen.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")


# ───────────────────────────────────────────────────────── proceso
def procesar(ruta: Path, args) -> dict:
    t0 = time.perf_counter()
    audio = cargar_audio(ruta)
    total = len(audio) / SR
    desde = a_segundos(args.desde) or 0.0
    hasta = min(a_segundos(args.hasta) or total, total)
    if desde >= hasta:
        raise SystemExit(f"El tramo pedido ({mmss(desde)} a {mmss(hasta)}) está fuera del audio ({mmss(total)}).")
    audio = audio[int(desde * SR):int(hasta * SR)]
    duracion = len(audio) / SR
    print(f"{ruta.name}: {mmss(duracion)} de audio", flush=True)

    fragmentos, info = transcribir(audio, args, duracion, desplazamiento=desde)
    n_hablantes = None
    if args.hablantes:
        n = None if args.hablantes == "auto" else int(args.hablantes)
        n_hablantes = poner_hablantes(audio, fragmentos, n, desplazamiento=desde)
    calificar(fragmentos, args.umbral)

    segundos = time.perf_counter() - t0
    idioma = info.language if args.idioma == "auto" else args.idioma
    if args.idioma == "auto":
        idioma = f"{info.language} (detectado, probabilidad {info.language_probability:.2f})"
    meta = {"duracion": duracion, "desde": desde, "hasta": hasta, "modelo": args.modelo, "idioma": idioma,
            "sin_vad": args.sin_vad, "contexto": args.contexto, "umbral": args.umbral, "segundos": segundos,
            "hablantes": bool(args.hablantes)}
    destino = SALIDAS / nombre_carpeta(ruta, args)
    escribir(fragmentos, destino, ruta, meta)
    return {"ruta": ruta, "destino": destino, "fragmentos": fragmentos, "meta": meta, "n_hablantes": n_hablantes}


def imprimir(r: dict):
    m, fr = r["meta"], r["fragmentos"]
    dudosos = sum(f["dudoso"] for f in fr)
    print(f"\n== {r['ruta'].name}  ({mmss(m['duracion'])} de audio en {m['segundos']:.0f} s)")
    print(f"   {len(fr)} fragmentos, {dudosos} dudosos" +
          (f", {r['n_hablantes']} hablantes" if r["n_hablantes"] else ""))
    for f in fr[:8]:
        marca = " (?)" if f["dudoso"] else ""
        print(f"   [{mmss(f['inicio'])}] {etiqueta(f)}{f['texto']}{marca}")
    if len(fr) > 8:
        print(f"   … ({len(fr) - 8} fragmentos más)")
    try:
        carpeta = r["destino"].relative_to(RAIZ)
    except ValueError:
        carpeta = r["destino"]
    print(f"   Resultados en {carpeta}/")


def prueba():
    faltan = faltan_paquetes(con_hablantes=False)
    if faltan:
        raise SystemExit("Faltan paquetes: " + ", ".join(faltan))
    args = argparse.Namespace(modelo=PRUEBA_MODELO, idioma="es", sin_vad=False, contexto=None)
    audio = cargar_audio(PRUEBA_AUDIO)
    modelo(args.modelo)
    t0 = time.perf_counter()
    fragmentos, _ = transcribir(audio, args, len(audio) / SR)
    texto = " ".join(f["texto"] for f in fragmentos)
    ref, hip = normalizar(PRUEBA_TEXTO), set(normalizar(texto))
    acierto = sum(p in hip for p in ref) / len(ref)
    print(f"Modelo: {MODELOS[args.modelo]['nombre']}")
    print(f"Esperado: {PRUEBA_TEXTO}")
    print(f"Leído:    {texto}")
    print(f"Palabras reconocidas: {acierto:.0%} · {time.perf_counter() - t0:.1f} s")
    if acierto < 0.8:
        raise SystemExit("PRUEBA FALLIDA: la transcripción no coincide con lo esperado.")
    print("PRUEBA OK")


PRUEBA_MODELO = "preciso"


def main():
    global PRUEBA_MODELO
    p = argparse.ArgumentParser(description="Transcribe audio o video con Whisper, en esta computadora.")
    p.add_argument("entrada", nargs="?", help="archivo de audio o video, o una carpeta")
    p.add_argument("--prueba", action="store_true", help="comprueba que la instalación funciona")
    p.add_argument("--modelo", choices=sorted(MODELOS), default="preciso")
    p.add_argument("--desde", default=None)
    p.add_argument("--hasta", default=None)
    p.add_argument("--contexto", default=None)
    p.add_argument("--idioma", default="es")
    p.add_argument("--hablantes", default=None, help="auto o el número de personas")
    p.add_argument("--sin-vad", action="store_true")
    p.add_argument("--umbral", type=float, default=0.50)
    p.add_argument("--salida", default=None)
    args = p.parse_args()

    if args.prueba:
        PRUEBA_MODELO = args.modelo
        prueba()
        return
    if not args.entrada:
        p.error("falta el archivo o la carpeta (o --prueba)")
    if args.hablantes and args.hablantes != "auto" and not args.hablantes.isdigit():
        p.error("--hablantes debe ser auto o un número")
    faltan = faltan_paquetes(con_hablantes=bool(args.hablantes))
    if faltan:
        raise SystemExit("Faltan paquetes: " + ", ".join(faltan) +
                         ". Instálalos con herramientas/requirements-audio.txt")

    entrada = Path(args.entrada)
    if not entrada.is_absolute() and not entrada.exists():
        entrada = RAIZ / entrada
    if entrada.is_dir():
        archivos = sorted(a for a in entrada.iterdir() if a.suffix.lower() in EXTENSIONES)
        if args.salida and len(archivos) > 1:
            p.error("--salida solo sirve con un archivo")
    elif entrada.exists():
        archivos = [entrada]
    else:
        raise SystemExit(f"No existe: {args.entrada}")
    if not archivos:
        raise SystemExit(f"No hay audios ni videos en {args.entrada}")

    for ruta in archivos:
        try:
            imprimir(procesar(ruta, args))
        except SystemExit:
            raise
        except Exception as e:
            print(f"\n== {ruta.name}: no se pudo procesar ({type(e).__name__}: {e})", file=sys.stderr)


if __name__ == "__main__":
    main()
