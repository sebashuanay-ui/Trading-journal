"""Utilidades compartidas: descarga de MNQ=F (Yahoo Finance) y armado de documentos por sesión CME (18:00 ET del día previo → 17:00 ET)."""
import json
import os
import time
from datetime import timedelta

import pandas as pd
import requests

H = {"User-Agent": "Mozilla/5.0"}
SYM = "MNQ=F"


def bajar(iv, rango=None, p1=None, p2=None):
    u = f"https://query1.finance.yahoo.com/v8/finance/chart/{SYM}?interval={iv}&includePrePost=true"
    u += f"&range={rango}" if rango else f"&period1={p1}&period2={p2}"
    for k in range(4):
        try:
            r = requests.get(u, headers=H, timeout=60)
            j = r.json()["chart"]["result"]
            if not j:
                return pd.DataFrame()
            j = j[0]
            q = j["indicators"]["quote"][0]
            df = pd.DataFrame({x: q[x] for x in ("open", "high", "low", "close", "volume")},
                              index=pd.to_datetime(j.get("timestamp", []), unit="s", utc=True))
            return df.dropna(subset=["open", "high", "low", "close"])
        except Exception:
            time.sleep(2 ** (k + 1))
    return pd.DataFrame()


def sesion(idx):
    et = idx.tz_convert("America/New_York")
    return (et.tz_localize(None) + timedelta(hours=6)).normalize()


def docs(df, tf, por_mes=False):
    out = {}
    if df.empty:
        return out
    df = df[~df.index.duplicated(keep="last")].sort_index()
    s = sesion(df.index)
    clave = s.strftime("%Y-%m") if por_mes else s.strftime("%Y-%m-%d")
    ahora_et = pd.Timestamp.now(tz="America/New_York").tz_localize(None)
    for k in sorted(set(clave)):
        g = df[clave == k]
        if por_mes:
            fin = pd.Timestamp(k + "-01") + pd.offsets.MonthBegin(1) + timedelta(hours=17)
        else:
            fin = pd.Timestamp(k) + timedelta(hours=17)
        out[f"{tf}_{k}"] = {
            "tf": tf, "s": k,
            "t": [int(x.timestamp()) for x in g.index],
            "o": [round(float(x), 2) for x in g.open], "h": [round(float(x), 2) for x in g.high],
            "l": [round(float(x), 2) for x in g.low], "c": [round(float(x), 2) for x in g.close],
            "v": [int(x or 0) for x in g.volume.fillna(0)],
            "completa": bool(ahora_et > fin),
        }
    return out


def live_doc(df1m):
    """Sesión actual con velas de 1 minuto, último precio, máx/mín y cierre previo."""
    df = df1m[~df1m.index.duplicated(keep="last")].sort_index().copy()
    df["ses"] = sesion(df.index).strftime("%Y-%m-%d")
    claves = sorted(df["ses"].unique())
    hoy = claves[-1]
    g = df[df["ses"] == hoy]
    prev = float(df[df["ses"] == claves[-2]].close.iloc[-1]) if len(claves) > 1 else None
    return {"t": int(g.index[-1].timestamp()), "ses": hoy, "last": round(float(g.close.iloc[-1]), 2),
            "prev": round(prev, 2) if prev else None, "hi": round(float(g.high.max()), 2), "lo": round(float(g.low.min()), 2),
            "fuente": "Yahoo Finance MNQ=F", "actualizado": int(time.time()),
            "bars": {"t": [int(x.timestamp()) for x in g.index], "o": [round(float(x), 2) for x in g.open], "h": [round(float(x), 2) for x in g.high],
                     "l": [round(float(x), 2) for x in g.low], "c": [round(float(x), 2) for x in g.close]}}


def guardar(dirp, nombre, doc):
    os.makedirs(dirp, exist_ok=True)
    with open(os.path.join(dirp, nombre + ".json"), "w") as f:
        json.dump(doc, f, separators=(",", ":"))


def leer_indice(path):
    try:
        i = json.load(open(path))
    except Exception:
        i = {}
    for k in ("m1", "m5", "h1"):
        i.setdefault(k, {})
    i.setdefault("fuente", "Yahoo Finance MNQ=F")
    return i
