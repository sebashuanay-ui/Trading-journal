"""Archivo diario: guarda en data/ las últimas sesiones de MNQ (1 m y 5 m) y los meses de 1 h, y actualiza data/index.json.
Uso: python3 scripts/update_data.py [N_sesiones=5]"""
import datetime
import os
import sys

from mnq_lib import bajar, docs, guardar, leer_indice

N = int(sys.argv[1]) if len(sys.argv) > 1 else 5
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
idx_path = os.path.join(D, "index.json")
idx = leer_indice(idx_path)

m1 = docs(bajar("1m", "7d"), "m1")
m5 = docs(bajar("5m", "60d"), "m5")
h1 = docs(bajar("60m", "730d"), "h1", por_mes=True)
if not m1 and not m5 and not h1:
    sys.exit("Yahoo no devolvió datos; no se cambia nada.")

ses = sorted({v["s"] for v in m1.values()})[-N:]
nuevos = 0
for k, v in m1.items():
    if v["s"] not in ses:
        continue
    if len(v["t"]) < 300 and v["completa"]:
        continue  # primera sesión truncada por el rango de Yahoo
    prev = idx["m1"].get(v["s"])
    if prev and prev.get("completa") and prev.get("n", 0) >= len(v["t"]):
        continue
    guardar(D, k, v)
    idx["m1"][v["s"]] = {"n": len(v["t"]), "completa": v["completa"]}
    nuevos += 1
for k, v in m5.items():
    if v["s"] in idx["m1"]:
        continue  # ya hay 1 m de esa sesión
    prev = idx["m5"].get(v["s"])
    if prev and prev.get("completa") and prev.get("n", 0) >= len(v["t"]):
        continue
    guardar(D, k, v)
    idx["m5"][v["s"]] = {"n": len(v["t"]), "completa": v["completa"]}
    nuevos += 1
for k, v in h1.items():
    prev = idx["h1"].get(v["s"])
    if prev and prev.get("completa"):
        continue
    guardar(D, k, v)
    idx["h1"][v["s"]] = {"n": len(v["t"]), "completa": v["completa"]}
    nuevos += 1
idx["actualizado"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
import json
json.dump(idx, open(idx_path, "w"), separators=(",", ":"))
print(f"{nuevos} documentos nuevos o actualizados")
