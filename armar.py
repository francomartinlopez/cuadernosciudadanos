#!/usr/bin/env python3
"""Arma datos.js a partir de notas/*.json y verifica cada nota.

Uso: python3 armar.py   (desde la carpeta del sitio)
"""
import json, glob, os, re, sys

SECCIONES = ["poder", "tecnologia", "estado", "policiales", "economia", "sociedad",
             "territorio", "mundo", "ideas", "ciencia", "historia", "cultura"]
FORMATOS = ["Ensayo", "Opinión", "Noticia", "Análisis", "Crónica", "Entrevista", "Reseña", "Investigación"]
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
    n["palabras"] = [
        palabras(n.get("resumido", [])) + palabras(n.get("bajada", "")),
        palabras(n.get("extendido", [])),
        palabras(n.get("completo", [])) + palabras(n.get("investigacion", {})),
    ]
    notas.append(n)

if errores:
    print("\n".join(errores)); sys.exit(1)

notas.sort(key=lambda n: n["fecha"], reverse=True)
with open("datos.js", "w", encoding="utf-8") as f:
    f.write("window.NOTAS=" + json.dumps(notas, ensure_ascii=False, separators=(",", ":")) + ";\n")
print(f"datos.js: {len(notas)} notas")
