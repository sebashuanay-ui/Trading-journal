"""Bucle de precio en vivo: cada INTERVALO segundos descarga MNQ=F (Yahoo) y publica live.json en la rama `live`
(un único commit que se reescribe, para no inflar el historial). La página lo lee desde raw.githubusercontent.com.
Uso (desde la raíz del repo): python3 scripts/live_loop.py DURACION_S [INTERVALO_S=60]"""
import datetime
import json
import os
import random
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mnq_lib import bajar, live_doc  # noqa: E402

DUR = int(sys.argv[1]) if len(sys.argv) > 1 else 330
INT = int(sys.argv[2]) if len(sys.argv) > 2 else 60
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WT = os.path.join(os.path.dirname(R), "live-wt")
ET = ZoneInfo("America/New_York")


def abierto(now):
    n = now.astimezone(ET)
    m = n.hour * 60 + n.minute
    wd = n.weekday()  # 0 = lunes
    if wd == 5 or (wd == 4 and m >= 17 * 60) or (wd == 6 and m < 18 * 60):
        return False
    return not (17 * 60 <= m < 18 * 60)


def git(*a, check=True):
    return subprocess.run(["git", *a], cwd=WT, check=check, capture_output=True, text=True)


def preparar():
    subprocess.run(["git", "worktree", "add", "--detach", WT], cwd=R, check=True, capture_output=True)
    r = git("ls-remote", "--exit-code", "--heads", "origin", "live", check=False)
    if r.returncode == 0:
        git("fetch", "--depth=1", "origin", "live")
        git("checkout", "-B", "live", "FETCH_HEAD")
    else:
        git("checkout", "--orphan", "live")
        git("rm", "-rf", "--quiet", ".", check=False)
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")


def publicar(doc, primero):
    """Escribe live.json y lo empuja a la rama live. Con ejecuciones solapadas dos pushes pueden chocar:
    se reintenta con una pausa aleatoria y, si sigue fallando, se registra y se sigue (nunca tumba el trabajo)."""
    with open(os.path.join(WT, "live.json"), "w") as f:
        json.dump(doc, f, separators=(",", ":"))
    git("add", "live.json")
    if primero:
        git("commit", "-q", "-m", "Precio en vivo MNQ", "--allow-empty")
    else:
        git("commit", "-q", "--amend", "--no-edit", "--allow-empty")
    for intento in range(1, 5):
        r = git("push", "-q", "--force", "origin", "HEAD:refs/heads/live", check=False)
        if r.returncode == 0:
            return True
        print(f"Push fallido (intento {intento}): {r.stderr.strip()[:300]}", file=sys.stderr, flush=True)
        time.sleep(random.uniform(2, 7))
    return False


def main():
    if not abierto(datetime.datetime.now(datetime.timezone.utc)):
        print("Mercado cerrado: nada que hacer")
        return
    preparar()
    time.sleep(random.uniform(0, 20))  # desfasa esta ejecución de la anterior para no empujar en el mismo segundo
    fin = time.time() + DUR
    primero = True
    n = 0
    while True:
        t0 = time.time()
        if not abierto(datetime.datetime.now(datetime.timezone.utc)):
            print("Cierre del mercado: fin")
            break
        try:
            df = bajar("1m", "5d")
            if df.empty:
                print("Yahoo sin datos en esta vuelta", file=sys.stderr, flush=True)
            else:
                doc = live_doc(df)
                if publicar(doc, primero):
                    primero = False
                    n += 1
                    print(f"{datetime.datetime.now(datetime.timezone.utc):%H:%M:%S}Z último {doc['last']} (vela {datetime.datetime.fromtimestamp(doc['t'], datetime.timezone.utc):%H:%M}Z)", flush=True)
        except Exception as e:  # una vuelta fallida no debe tumbar el trabajo
            print(f"Vuelta fallida: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        if time.time() + INT > fin:
            break
        time.sleep(max(1, INT - (time.time() - t0)))
    print(f"{n} publicaciones")
    if n == 0:
        sys.exit("Ninguna publicación en toda la ejecución")


main()
