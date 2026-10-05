"""Arma _site/ para GitHub Pages: index.html + data/ del repo + precio en vivo y sesión de hoy recién descargados.
Si Yahoo falla, se publica el último data/live.json guardado (el sitio lo marca como retrasado)."""
import datetime
import json
import os
import shutil
import sys

from mnq_lib import bajar, docs, guardar, leer_indice, live_doc

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(R, "_site")
shutil.rmtree(S, ignore_errors=True)
os.makedirs(S)
shutil.copy(os.path.join(R, "index.html"), S)
open(os.path.join(S, ".nojekyll"), "w").close()
shutil.copytree(os.path.join(R, "data"), os.path.join(S, "data"))
D = os.path.join(S, "data")

df = bajar("1m", "5d")
if df.empty:
    print("Aviso: Yahoo no respondió; se publica el último live.json guardado.", file=sys.stderr)
else:
    live = live_doc(df)
    json.dump(live, open(os.path.join(D, "live.json"), "w"), separators=(",", ":"))
    m1 = docs(df, "m1")
    idx = leer_indice(os.path.join(D, "index.json"))
    for k, v in m1.items():
        if len(v["t"]) < 300 and v["completa"]:
            continue
        guardar(D, k, v)
        idx["m1"][v["s"]] = {"n": len(v["t"]), "completa": v["completa"]}
    idx["actualizado"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    json.dump(idx, open(os.path.join(D, "index.json"), "w"), separators=(",", ":"))
    print("Último precio", live["last"], "sesión", live["ses"], len(live["bars"]["t"]), "velas")
