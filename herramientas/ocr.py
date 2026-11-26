"""OCR de PDF e imágenes con los modelos de PaddleOCR (PP-OCRv6) sobre RapidOCR.

Lo ejecuta Claude desde Cowork; los alumnos no necesitan abrir este archivo.

Uso:
    python herramientas/ocr.py --prueba
    python herramientas/ocr.py documentos/ejemplos/02_archivo_historico.pdf --paginas 1
    python herramientas/ocr.py documentos/mi_archivo.pdf
    python herramientas/ocr.py documentos/            (todos los PDF e imágenes de la carpeta)

Opciones:
    --paginas 1-3,5   solo esas páginas (empiezan en 1)
    --dpi 300         resolución al convertir el PDF en imagen
    --umbral 0.90     confianza bajo la cual una línea se marca como dudosa
    --forzar-ocr      hacer OCR aunque la página ya tenga texto seleccionable
    --girar auto      auto, 0, 90, 180 o 270 (auto prueba girar si la lectura sale mal)

Por cada documento escribe en salidas/<documento>/:
    paginas/pagina_001.png        la página como imagen
    pagina_001_cajas.jpg          la página con una caja por línea, coloreada por confianza
    pagina_001.txt                el texto de la página
    texto_completo.txt            todo el texto, con separadores de página
    lineas.csv                    una fila por línea: página, texto, confianza, dudosa, caja
    resumen.md                    resumen por página y la lista de líneas dudosas
"""
from __future__ import annotations

import argparse
import csv
import statistics
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SALIDAS = RAIZ / "salidas"
IMAGENES = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
MIN_TEXTO_NATIVO = 40          # caracteres para considerar que una página ya tiene texto
COLORES = {"alta": (31, 111, 209), "media": (232, 163, 23), "baja": (217, 72, 28)}


def faltan_paquetes() -> list[str]:
    faltan = []
    for modulo, paquete in (("rapidocr", "rapidocr"), ("onnxruntime", "onnxruntime"),
                            ("pymupdf", "pymupdf"), ("PIL", "pillow")):
        try:
            __import__(modulo)
        except ImportError:
            faltan.append(paquete)
    return faltan


_MOTOR = None


def motor():
    global _MOTOR
    if _MOTOR is None:
        from rapidocr import RapidOCR
        _MOTOR = RapidOCR(params={"Global.log_level": "error"})
    return _MOTOR


def nivel(confianza: float, umbral: float) -> str:
    if confianza >= umbral:
        return "alta"
    return "media" if confianza >= 0.70 else "baja"


def ocr_una_vez(imagen) -> dict:
    r = motor()(imagen)
    lineas = []
    for caja, texto, conf in zip(r.boxes if r.boxes is not None else [], r.txts or [], r.scores or []):
        xs, ys = [float(p[0]) for p in caja], [float(p[1]) for p in caja]
        lineas.append({"texto": texto, "confianza": round(float(conf), 3),
                       "caja": [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))],
                       "poligono": [(float(p[0]), float(p[1])) for p in caja]})
    confs = [l["confianza"] for l in lineas]
    return {"lineas": lineas, "imagen": imagen,
            "mediana": statistics.median(confs) if confs else 0.0,
            "dudosas": sum(c < 0.90 for c in confs) / len(confs) if confs else 1.0,
            "puntaje": sum(l["confianza"] * len(l["texto"]) for l in lineas)}


def leer_imagen(ruta: Path, girar: str):
    """OCR de una imagen. Devuelve (líneas, grados girados, imagen PIL usada).

    Con girar="auto", si la lectura sale mal (confianza mediana bajo 0,90 o más de un tercio de
    líneas dudosas) prueba la página girada 90°, 270° y 180°, y se queda con un giro solo si lee
    claramente mejor: así una página difícil pero derecha no termina girada por error."""
    from PIL import Image
    original = Image.open(ruta).convert("RGB")
    if girar != "auto":
        g = int(girar)
        res = ocr_una_vez(original.rotate(g, expand=True) if g else original)
        return res["lineas"], g, res["imagen"]
    base = ocr_una_vez(original)
    mejor, grados = base, 0
    if base["mediana"] < 0.90 or base["dudosas"] > 1 / 3 or len(base["lineas"]) < 3:
        for g in (90, 270, 180):
            res = ocr_una_vez(original.rotate(g, expand=True))
            if res["mediana"] >= mejor["mediana"] + 0.05 and res["puntaje"] > mejor["puntaje"]:
                mejor, grados = res, g
    return mejor["lineas"], grados, mejor["imagen"]


def dibujar(imagen, lineas, umbral: float, destino: Path) -> None:
    from PIL import ImageDraw
    imagen = imagen.copy()
    trazo = max(3, round(max(imagen.size) / 350))
    d = ImageDraw.Draw(imagen)
    for l in lineas:
        d.line(l["poligono"] + [l["poligono"][0]], fill=COLORES[nivel(l["confianza"], umbral)], width=trazo)
    imagen.thumbnail((1800, 1800))
    imagen.save(destino, quality=85)


def paginas_pedidas(texto: str | None, total: int) -> list[int]:
    if not texto:
        return list(range(1, total + 1))
    pedidas = set()
    for parte in texto.split(","):
        a, _, b = parte.strip().partition("-")
        pedidas.update(range(int(a), int(b or a) + 1))
    fuera = sorted(p for p in pedidas if not 1 <= p <= total)
    if fuera:
        print(f"Aviso: el documento tiene {total} páginas; ignoro {fuera}.")
    return sorted(p for p in pedidas if 1 <= p <= total)


def procesar(ruta: Path, args) -> dict:
    nombre = ruta.stem
    carpeta = SALIDAS / nombre
    (carpeta / "paginas").mkdir(parents=True, exist_ok=True)
    filas, resumen, textos = [], [], []

    if ruta.suffix.lower() in IMAGENES:
        fuentes = [(1, None, ruta)]
        total = 1
    else:
        import pymupdf
        doc = pymupdf.open(ruta)
        total = doc.page_count
        fuentes = []
        for n in paginas_pedidas(args.paginas, total):
            pagina = doc[n - 1]
            nativo = pagina.get_text("text").strip()
            png = carpeta / "paginas" / f"pagina_{n:03d}.png"
            pagina.get_pixmap(dpi=args.dpi).save(png)
            fuentes.append((n, nativo, png))

    for n, nativo, png in fuentes:
        t0 = time.time()
        if nativo and len(nativo) >= MIN_TEXTO_NATIVO and not args.forzar_ocr:
            lineas = [{"texto": t.strip(), "confianza": 1.0, "caja": ["", "", "", ""]}
                      for t in nativo.splitlines() if t.strip()]
            origen, grados = "texto_nativo", 0
        else:
            lineas, grados, imagen = leer_imagen(png, args.girar)
            dibujar(imagen, lineas, args.umbral, carpeta / f"pagina_{n:03d}_cajas.jpg")
            origen = "ocr"
        segundos = time.time() - t0
        texto = "\n".join(l["texto"] for l in lineas)
        (carpeta / f"pagina_{n:03d}.txt").write_text(texto + "\n", encoding="utf-8")
        textos.append(f"===== Página {n} =====\n{texto}\n")
        for i, l in enumerate(lineas, 1):
            filas.append({"documento": ruta.name, "pagina": n, "linea": i, "origen": origen,
                          "texto": l["texto"], "confianza": l["confianza"],
                          "dudosa": "sí" if origen == "ocr" and l["confianza"] < args.umbral else "no",
                          "x0": l["caja"][0], "y0": l["caja"][1], "x1": l["caja"][2], "y1": l["caja"][3]})
        confs = [l["confianza"] for l in lineas]
        resumen.append({"pagina": n, "origen": origen, "lineas": len(lineas), "girada": grados,
                        "mediana": round(statistics.median(confs), 3) if confs else None,
                        "dudosas": sum(c < args.umbral for c in confs) if origen == "ocr" else 0,
                        "segundos": round(segundos, 1)})

    (carpeta / "texto_completo.txt").write_text("\n".join(textos), encoding="utf-8")
    with open(carpeta / "lineas.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["documento", "pagina", "linea", "origen", "texto", "confianza",
                                          "dudosa", "x0", "y0", "x1", "y1"])
        w.writeheader()
        w.writerows(filas)
    escribir_resumen(ruta, total, resumen, filas, carpeta, args.umbral)
    return {"documento": ruta.name, "carpeta": carpeta, "paginas": resumen, "filas": filas}


def escribir_resumen(ruta, total, resumen, filas, carpeta, umbral) -> None:
    md = [f"# OCR de {ruta.name}", "",
          f"Páginas del documento: {total}. Procesadas: {len(resumen)}. Umbral de duda: {umbral:.2f}.", "",
          "Colores de las cajas: **azul** = confianza alta (≥ {:.2f}), **ámbar** = media (0,70 a {:.2f}), "
          "**naranja** = baja (< 0,70).".format(umbral, umbral), "",
          "| Página | Origen | Líneas | Confianza mediana | Líneas dudosas | Girada | Segundos |",
          "|---|---|---|---|---|---|---|"]
    for p in resumen:
        origen = "texto seleccionable (sin OCR)" if p["origen"] == "texto_nativo" else "OCR"
        md.append(f"| {p['pagina']} | {origen} | {p['lineas']} | {p['mediana'] if p['mediana'] is not None else '—'} "
                  f"| {p['dudosas']} | {p['girada']}° | {p['segundos']} |")
    dudosas = [f for f in filas if f["dudosa"] == "sí"]
    md += ["", f"## Líneas dudosas ({len(dudosas)})", ""]
    if dudosas:
        md += ["| Página | Línea | Confianza | Texto leído |", "|---|---|---|---|"]
        md += [f"| {f['pagina']} | {f['linea']} | {f['confianza']:.3f} | {f['texto'].replace('|', '/')} |"
               for f in dudosas[:60]]
        if len(dudosas) > 60:
            md.append(f"\n… y {len(dudosas) - 60} más en lineas.csv.")
    else:
        md.append("Ninguna.")
    md += ["", "Recuerda: una confianza alta no garantiza un dato correcto, y lo que el detector no vio no "
           "aparece en ninguna lista. Compara siempre con la imagen."]
    (carpeta / "resumen.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def imprimir(res: dict) -> None:
    print(f"\n{res['documento']} → {res['carpeta'].relative_to(RAIZ)}/")
    for p in res["paginas"]:
        if p["origen"] == "texto_nativo":
            print(f"  página {p['pagina']:>3}: texto seleccionable, {p['lineas']} líneas (no hizo falta OCR)")
        else:
            giro = f", girada {p['girada']}°" if p["girada"] else ""
            print(f"  página {p['pagina']:>3}: {p['lineas']} líneas, confianza mediana {p['mediana']}, "
                  f"{p['dudosas']} dudosas{giro} ({p['segundos']} s)")


def prueba() -> int:
    faltan = faltan_paquetes()
    if faltan:
        print("FALTAN paquetes:", ", ".join(faltan))
        print("Instálalos con: pip install -r herramientas/requirements.txt")
        return 1
    from PIL import Image, ImageDraw, ImageFont
    imagen = Image.new("RGB", (1400, 260), "white")
    d = ImageDraw.Draw(imagen)
    try:
        fuente = ImageFont.load_default(size=64)
    except TypeError:
        fuente = ImageFont.load_default()
    d.text((40, 40), "Resolucion N 018-2026", fill="black", font=fuente)
    d.text((40, 140), "Lima, Bicentenario", fill="black", font=fuente)
    ruta = SALIDAS / "_prueba.png"
    SALIDAS.mkdir(exist_ok=True)
    imagen.save(ruta)
    t0 = time.time()
    lineas, _, _ = leer_imagen(ruta, "0")
    ruta.unlink()
    leido = " | ".join(l["texto"] for l in lineas)
    print(f"Leído en {time.time() - t0:.1f} s: {leido}")
    if "018" in leido and "Bicentenario" in leido:
        print("PRUEBA OK: el OCR funciona.")
        return 0
    print("PRUEBA FALLÓ: el OCR corrió pero no leyó el texto esperado.")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="OCR de PDF e imágenes (modelos PP-OCRv6 de PaddleOCR).")
    ap.add_argument("rutas", nargs="*", type=Path, help="PDF, imágenes o carpetas")
    ap.add_argument("--prueba", action="store_true", help="comprobar que el OCR funciona")
    ap.add_argument("--paginas", help="por ejemplo 1-3,5")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--umbral", type=float, default=0.90)
    ap.add_argument("--forzar-ocr", action="store_true")
    ap.add_argument("--girar", default="auto", choices=["auto", "0", "90", "180", "270"])
    args = ap.parse_args()

    if args.prueba:
        return prueba()
    if not args.rutas:
        ap.print_help()
        return 1
    faltan = faltan_paquetes()
    if faltan:
        print("Faltan paquetes:", ", ".join(faltan), "→ pip install -r herramientas/requirements.txt")
        return 1

    archivos = []
    for r in args.rutas:
        if r.is_dir():
            archivos += sorted(p for p in r.iterdir() if p.suffix.lower() in IMAGENES | {".pdf"})
        elif r.exists():
            archivos.append(r)
        else:
            print(f"No existe: {r}")
    if not archivos:
        print("No encontré PDF ni imágenes.")
        return 1
    for a in archivos:
        try:
            imprimir(procesar(a, args))
        except Exception as e:                      # un archivo dañado no detiene a los demás
            print(f"\n{a.name}: ERROR {type(e).__name__}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
