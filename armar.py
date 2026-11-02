#!/usr/bin/env python3
"""Arma datos.js a partir de notas/*.json y verifica cada nota.

Uso: python3 armar.py   (desde la carpeta del sitio)
"""
import json, glob, os, re, sys

SECCIONES = ["poder", "tecnologia", "estado", "policiales", "economia", "sociedad",
             "territorio", "mundo", "ideas", "ciencia", "historia", "cultura"]
FORMATOS = ["Ensayo", "Opinión", "Noticia", "Análisis", "Crónica", "Entrevista", "Reseña", "Investigación",
            "Cuento", "Poema", "Novela", "Video", "Audio", "Imágenes"]
OBLIG = ["id", "seccion", "formato", "titulo", "bajada", "autor", "fecha", "imagen", "alt",
         "resumido", "extendido", "completo"]

def palabras(x):
    if isinstance(x, list):
        return sum(palabras(i) for i in x)
    if isinstance(x, dict):
        return sum(palabras(v) for v in x.values())
    return len(re.sub(r"^## ", "", str(x)).split())

errores, notas, ids = [], [], set()
for ruta in sorted(glob.glob("notas/*.json")):
    try:
        n = json.load(open(ruta, encoding="utf-8"))
    except Exception as e:
        errores.append(f"{ruta}: JSON inválido ({e})"); continue
    for k in OBLIG:
        if not n.get(k):
            errores.append(f"{ruta}: falta «{k}»")
    if n.get("seccion") not in SECCIONES:
        errores.append(f"{ruta}: sección desconocida «{n.get('seccion')}»")
    if n.get("formato") not in FORMATOS:
        errores.append(f"{ruta}: formato desconocido «{n.get('formato')}»")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", n.get("fecha", "")):
        errores.append(f"{ruta}: fecha con formato AAAA-MM-DD")
    if not re.fullmatch(r"[a-z0-9-]+", n.get("id", "")):
        errores.append(f"{ruta}: id solo con minúsculas, números y guiones")
    if n.get("id") in ids:
        errores.append(f"{ruta}: id repetido «{n['id']}»")
    ids.add(n.get("id"))
    if n.get("imagen") and not os.path.exists(n["imagen"]):
        errores.append(f"{ruta}: no existe la imagen {n['imagen']}")
    if n.get("formato") == "Investigación" and not n.get("investigacion"):
        errores.append(f"{ruta}: una Investigación necesita «investigacion» (resumen, palabras_clave, metodo)")
    for k in ("referencias", "bibliografia"):
        if k in n and not (isinstance(n[k], list) and all(isinstance(x, str) and x.strip() for x in n[k])):
            errores.append(f"{ruta}: «{k}» tiene que ser una lista de textos")
    citas = [int(x) for t in n.get("completo", []) for g in re.findall(r"\[(\d+(?:[,–-]\s?\d+)*)\]", t) for x in re.split(r"[,–-]\s?", g)]
    if citas and max(citas) > len(n.get("referencias", [])):
        errores.append(f"{ruta}: hay una cita [{max(citas)}] pero solo {len(n.get('referencias', []))} referencias")
    for c in n.get("correcciones", []):
        if not (isinstance(c, dict) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", c.get("fecha", "")) and c.get("texto")):
            errores.append(f"{ruta}: cada corrección necesita «fecha» (AAAA-MM-DD) y «texto»")
    f = n.get("formato")
    if f == "Novela" and not (n.get("obra") and isinstance(n.get("capitulo"), int)):
        errores.append(f"{ruta}: una Novela necesita «obra» (id de la novela) y «capitulo» (número)")
    if f in ("Video", "Audio") and not isinstance(n.get("medio"), dict):
        errores.append(f"{ruta}: un {f} necesita «medio» con «url» (YouTube, Vimeo, Spotify o SoundCloud)")
    if f == "Imágenes":
        gal = n.get("galeria")
        if not (isinstance(gal, list) and gal and all(isinstance(g, dict) and g.get("src") for g in gal)):
            errores.append(f"{ruta}: Imágenes necesita «galeria» con al menos una imagen (src y pie)")
        else:
            for g in gal:
                if not os.path.exists(g["src"]):
                    errores.append(f"{ruta}: no existe la imagen {g['src']}")
    for t in n.get("completo", []) + n.get("extendido", []):
        mm = re.match(r"^!\[(.*)\]\((.+)\)$", t)
        if mm and not os.path.exists(mm.group(2)):
            errores.append(f"{ruta}: no existe la figura {mm.group(2)}")
    n["palabras"] = [
        palabras(n.get("resumido", [])) + palabras(n.get("bajada", "")),
        palabras(n.get("extendido", [])),
        palabras(n.get("completo", [])) + palabras(n.get("investigacion", {})),
    ]
    notas.append(n)

if errores:
    print("\n".join(errores)); sys.exit(1)

notas.sort(key=lambda n: n["fecha"], reverse=True)
# El texto completo de cada nota va en su propio archivo (se descarga al abrir el nivel Completo)
# y el buscador usa textos.json, que se descarga en la primera búsqueda.
import shutil
shutil.rmtree("completos", ignore_errors=True)
os.makedirs("completos")
textos = {}
livianas = []
def plano(t):
    t = re.sub(r"^(#+ |> )", "", t)
    t = re.sub(r"^!\[(.*)\]\(.+\)$", r"\1", t)
    t = re.sub(r"\s*\[\d+(?:[,\-–]\s*\d+)*\]", "", t)
    return t.replace("**", "")
for n in notas:
    comp = {k: n.get(k, []) for k in ("completo", "referencias", "bibliografia")}
    with open(f"completos/{n['id']}.json", "w", encoding="utf-8") as f:
        json.dump(comp, f, ensure_ascii=False, separators=(",", ":"))
    textos[n["id"]] = "\n".join(plano(t) for t in comp["completo"])
    livianas.append({k: v for k, v in n.items() if k not in comp})
with open("textos.json", "w", encoding="utf-8") as f:
    json.dump(textos, f, ensure_ascii=False, separators=(",", ":"))
with open("datos.js", "w", encoding="utf-8") as f:
    f.write("window.NOTAS=" + json.dumps(livianas, ensure_ascii=False, separators=(",", ":")) + ";\n")
print(f"datos.js: {len(notas)} notas")
