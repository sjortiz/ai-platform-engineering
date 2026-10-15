"""Prototipo: genera cremallera-grafo.html, la presentación con el minimapa como grafo.

Basado en zip3.py: minimapa con la serpiente como índice,
una slide por posición (avance y, si aplica, su seguridad) y el mapa completo al final."""
import html
import json
import math
import random
from pathlib import Path

from detalle import SECX, ADVX, EXTRA, SECHITOS, SECEX, GLOS, SUPA, SUPS
from fuentes import FUENTES
import zip2  # datos, detalle y el SVG del mapa completo (zip2 escribe su propia versión; la pisamos abajo)

HERE = Path(__file__).parent
e = html.escape
N = len(zip2.STEPS)
SEC_AT = sorted({s["at"] for s in zip2.SEC})

# Posiciones de la serpiente: avance de cada paso y, si el paso trae seguridad, una parada abajo.
POS = [dict(k="portada")]
for i in range(1, N + 1):
    if i in GLOS:
        POS.append(dict(k="glos", i=i))
    POS.append(dict(k="avance", i=i))
    if i in SEC_AT:
        tops = [x["id"] for x in zip2.SEC if x["at"] == i]
        for n, t in enumerate(tops):
            POS.append(dict(k="seg", i=i, t=t, n=n, c=len(tops)))
POS.append(dict(k="hoy", i=N + 1))
POS.append(dict(k="mapa", i=N + 2))

# Minimapa como tablero de Snake: cada parada es comida repartida por el tablero. Los pasos son la
# comida grande, la seguridad la mediana y el apoyo (vocabulario, extras, preguntas) la chica.
# La posición sale de una relajación con semilla fija y después se ajusta a la cuadrícula.
G = 16
MW, MH = 1408, 208
MX0, MXN, XHOY = 100, 1180, 1316
STEPW = (MXN - MX0) / (N - 1)
RND = random.Random(11)
RAD = dict(portada=10, avance=14, hoy=24, seg=9, glos=7, xa=5, xs=5)
NODES, EDGES = {}, []


def node(nid, k, x, y):
    NODES[nid] = dict(k=k, xy=[x, y])


def edge(a, b, k):
    EDGES.append((a, b, k))


node("start", "portada", 34, 92)
# Cada paso queda a una o dos filas del anterior: se ve disperso, pero → es casi un tramo recto.
y = 88
for i in range(1, N + 1):
    y = min(104, max(56, y + RND.choice((-32, -16, 16, 32))))
    node(f"a{i}", "avance", MX0 + (i - 1) * STEPW + RND.uniform(-14, 14), y)
node("hoy", "hoy", XHOY, 100)
NODES["start"]["xy"][1] = NODES["a1"]["xy"][1]
NODES["hoy"]["xy"][1] = NODES[f"a{N}"]["xy"][1]
nxt = lambda i: f"a{i + 1}" if i < N else "hoy"
for i in GLOS:
    (x0, y0), (x1, y1) = NODES[f"a{i - 1}"]["xy"], NODES[f"a{i}"]["xy"]
    node(f"g{i}", "glos", (x0 + x1) / 2, (y0 + y1) / 2)
edge("start", "a1", "main")
SUPOF = {}
# Como mucho cuatro vecinos por nodo, uno por flecha: ← paso anterior, → siguiente (el vocabulario
# queda en el camino), ↑ extra y ↓ la rama de seguridad, que termina en sus preguntas.
for i in range(1, N + 1):
    ai, after = f"a{i}", nxt(i)
    gl = f"g{i + 1}" if i + 1 in GLOS else None
    if gl:
        edge(ai, gl, "main")
        edge(gl, after, "main")
    else:
        edge(ai, after, "main")
    tops = [x["id"] for x in zip2.SEC if x["at"] == i]
    x, y = NODES[ai]["xy"]
    prev = ai
    for n, t in enumerate(tops):
        node(f"s{t}", "seg", x + STEPW * .5 * n, y + 50)
        edge(prev, f"s{t}", "sec")
        prev = f"s{t}"
    if i in SUPA:
        node(f"xa{i}", "xa", x, y - 34)
        edge(ai, f"xa{i}", "sup")
        SUPOF[f"xa{i}"] = ai
    if i in SUPS:
        sx, sy = NODES[prev]["xy"]
        node(f"xs{i}", "xs", sx, sy + 30)
        edge(prev, f"xs{i}", "sup")
        SUPOF[f"xs{i}"] = prev

ids = list(NODES)
HOME = {n: list(NODES[n]["xy"]) for n in ids}
for _ in range(400):
    mv = {n: [0.0, 0.0] for n in ids}
    for n in ids:
        if NODES[n]["k"] in ("avance", "seg"):
            mv[n][1] += (HOME[n][1] - NODES[n]["xy"][1]) * .2
    for u in range(len(ids)):
        for v in range(u + 1, len(ids)):
            a, b = ids[u], ids[v]
            (xa, ya), (xb, yb) = NODES[a]["xy"], NODES[b]["xy"]
            dx, dy = xb - xa, yb - ya
            d = math.hypot(dx, dy) or .01
            want = RAD[NODES[a]["k"]] + RAD[NODES[b]["k"]] + 16
            if d < want:
                f = (want - d) / 2 / d
                mv[a][0] -= dx * f; mv[a][1] -= dy * f
                mv[b][0] += dx * f; mv[b][1] += dy * f
    for sat, par in SUPOF.items():
        (xp, yp), (xs, ys) = NODES[par]["xy"], NODES[sat]["xy"]
        d = math.hypot(xs - xp, ys - yp) or .01
        f = (32 - d) / d * .5
        mv[sat][0] += (xs - xp) * f; mv[sat][1] += (ys - yp) * f
    for n in ids:
        k, xy = NODES[n]["k"], NODES[n]["xy"]
        if k in ("portada", "hoy"):
            xy[1] = NODES["a1" if k == "portada" else f"a{N}"]["xy"][1]
            continue
        if k == "avance":  # los pasos quedan fijos en su fila: es lo que hace que → sea casi recto
            continue
        xy[0] += mv[n][0] * .5
        xy[1] += mv[n][1] * .5
        r = RAD[k] + 4
        xy[0] = min(MW - r, max(r, xy[0]))
        xy[1] = min(MH - r, max(r, xy[1]))
# Cada parada al centro de una celda libre.
used = set()
for n in sorted(ids, key=lambda n: -RAD[NODES[n]["k"]]):
    x, y = NODES[n]["xy"]
    cx, cy = round((x - G / 2) / G), round((y - G / 2) / G)
    cands = sorted(((cx + dx, cy + dy) for dx in range(-6, 7) for dy in range(-4, 5)
                    if 1 <= cy + dy <= MH // G - 2 and (cx + dx, cy + dy) not in used), key=lambda c: abs(c[0] - cx) + abs(c[1] - cy))
    c = cands[0]
    used.update((c[0] + dx, c[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    NODES[n]["xy"] = [c[0] * G + G // 2, c[1] * G + G // 2]

def pos_node(p):
    return {"portada": "start", "hoy": "hoy", "mapa": "hoy", "glos": f"g{p.get('i')}",
            "seg": f"s{p.get('t')}"}.get(p["k"], f"a{p.get('i')}")


for p in POS:
    p["node"] = pos_node(p)
    p["xy"] = NODES[p["node"]]["xy"]
ADJ = {}
for a, b, _ in EDGES:
    ADJ.setdefault(a, []).append(b)
    ADJ.setdefault(b, []).append(a)

mini = [f'<defs><pattern id="tablero" width="{2 * G}" height="{2 * G}" patternUnits="userSpaceOnUse">'
        f'<rect class="tb1" width="{2 * G}" height="{2 * G}"/><rect class="tb2" width="{G}" height="{G}"/>'
        f'<rect class="tb2" x="{G}" y="{G}" width="{G}" height="{G}"/></pattern></defs>'
        f'<rect class="tablero" width="{MW}" height="{MH}" rx="8" fill="url(#tablero)"/>']
for i in SUPA:
    x, y = NODES[f"xa{i}"]["xy"]
    big = " big" if SUPA[i].get("t") else ""
    mini.append(f'<g class="msup{big}" data-sup="a" data-i="{i}" tabindex="0" role="button" aria-label="Extra del paso {i}">'
                f'<rect class="hit" x="{x - 12}" y="{y - 12}" width="24" height="24"/>'
                f'<rect class="sq" x="{x - 5}" y="{y - 5}" width="10" height="10" rx="1.5"/></g>')
for i in SUPS:
    x, y = NODES[f"xs{i}"]["xy"]
    mini.append(f'<g class="msup" data-sup="s" data-i="{i}" tabindex="0" role="button" aria-label="Preguntas de seguridad del paso {i}">'
                f'<rect class="hit" x="{x - 12}" y="{y - 12}" width="24" height="24"/>'
                f'<rect class="sq" x="{x - 5}" y="{y - 5}" width="10" height="10" rx="1.5"/></g>')
for idx, p in enumerate(POS):
    if p["k"] in ("portada", "mapa"):
        continue
    x, y = p["xy"]
    if p["k"] == "hoy":
        mini.append(f'<g class="mdot hoy" data-p="{idx}" tabindex="0" role="button" aria-label="Hoy">'
                    f'<rect x="{x - 24}" y="{y - 13}" width="48" height="26" rx="3"/><text x="{x}" y="{y + 4}" text-anchor="middle">Hoy</text></g>')
        continue
    if p["k"] == "glos":
        mini.append(f'<g class="mdot glos" data-p="{idx}" tabindex="0" role="button" aria-label="Vocabulario">'
                    f'<rect class="hit" x="{x - 14}" y="{y - 14}" width="28" height="28"/>'
                    f'<rect class="gd" x="{x - 6}" y="{y - 6}" width="12" height="12" rx="1.5"/></g>')
        continue
    label = f'Paso {p["i"]}' + (" · seguridad" if p["k"] == "seg" else "")
    if p["k"] == "avance":
        mini.append(f'<g class="mdot avance" data-p="{idx}" tabindex="0" role="button" aria-label="{label}">'
                    f'<rect class="hit" x="{x - 18}" y="{y - 18}" width="36" height="36"/>'
                    f'<rect class="blk" x="{x - 13}" y="{y - 13}" width="26" height="26" rx="3"/><text class="mnum" x="{x}" y="{y + 4}" text-anchor="middle">{p["i"]}</text></g>')
    else:
        mini.append(f'<g class="mdot seg" data-p="{idx}" tabindex="0" role="button" aria-label="{label}">'
                    f'<rect class="hit" x="{x - 14}" y="{y - 14}" width="28" height="28"/><rect class="blk" x="{x - 8}" y="{y - 8}" width="16" height="16" rx="2"/></g>')

mini.append('<g id="msnake"></g><g id="mkeys" aria-hidden="true"></g>')
MINI_SVG = f'<svg class="mini" viewBox="0 0 {MW} {MH}" role="navigation" aria-label="Índice de la charla">{"".join(mini)}</svg>'
GROUPS = [
    ("Entregar y escribir", "pasos 1–2", [1, 2]),
    ("Más cambios, más rápido", "pasos 3–5", [3, 4, 5]),
    ("Operar y pedir", "pasos 6–7", [6, 7]),
    ("Contexto y costo", "pasos 8–10", [8, 9, 10]),
    ("Modelos propios", "pasos 11–13", [11, 12, 13]),
]
TAGST = {"ok": "int", "med": "ext", "crit": "pub"}


def arch_map():
    cols = []
    for title, sub, steps in GROUPS:
        parts = [f'<p class="colhead">{e(title)}<small>{e(sub)}</small></p>']
        first = True
        for i in steps:
            st = zip2.STEPS[i - 1]
            tools = ", ".join(ADVX[i]["tools"][:3])
            if not first:
                parts.append('<div class="conn"></div>')
            first = False
            parts.append(f'<div class="node"><span class="tag aws">Paso {i}</span><div class="t">{e(st["n"])}</div><div class="s">{e(tools)}</div></div>')
            for x in zip2.SEC:
                if x["at"] != i or not x.get("rail", True):
                    continue
                stools = ", ".join(SECX[x["id"]]["tools"][:3])
                parts.append('<div class="conn dash"></div>')
                parts.append(f'<div class="node secn st-{x["st"]}"><span class="tag {TAGST[x["st"]]}">{zip2.ST[x["st"]]}</span>'
                             f'<div class="t">{e(x["n"])}</div><div class="s">{e(stools)}</div></div>')
        parts.append('<div class="conn join"></div>')
        cols.append(f'<div class="col">{"".join(parts)}</div>')
    common = ('<div class="common"><div class="bus"></div><div class="conn"></div>'
              '<div class="node hoyn"><div class="t">Hoy · el cuello es la atención humana</div>'
              '<div class="s">Lo mueve la seguridad: clasificadores de permisos, trazabilidad e identidad de agentes</div></div></div>')
    legend = ('<div class="legend"><span><i class="sw"></i>avance</span><span><i class="sw sok"></i>seguridad resuelta</span>'
              '<span><i class="sw smed"></i>parcial</span><span><i class="sw scrit"></i>abierta</span></div>')
    return f'{legend}<div class="diagram amap-wrap"><div class="amap">{"".join(cols)}{common}</div></div>'


ARCH_MAP = arch_map()

FULL_SVG = (f'<svg class="zip-svg" viewBox="0 0 {zip2.W} {zip2.H}" role="img" aria-label="Mapa completo: avances arriba, seguridad abajo, se juntan en Hoy">'
            f'{zip2.defs}{"".join(zip2.svg)}</svg>')

DATA = dict(pos=[dict(k=p["k"], i=p.get("i"), t=p.get("t"), n=p.get("n", 0), c=p.get("c", 1), xy=p["xy"], node=p["node"]) for p in POS],
            detail={str(k): v for k, v in zip2.DETAIL.items()},
            names={str(i): s["n"] for i, s in enumerate(zip2.STEPS, 1)},
            secnames={str(i): [s["n"] for s in zip2.SEC if s["at"] == i] for i in SEC_AT},
            secx=SECX,
            advx={str(k): v for k, v in ADVX.items()},
            extra={str(k): v for k, v in EXTRA.items()},
            sechitos=SECHITOS,
            secex=SECEX,
            glos={str(k): v for k, v in GLOS.items()},
            supa={str(k): v for k, v in SUPA.items()},
            sups={str(k): v for k, v in SUPS.items()},
            fuentes=FUENTES,
            nodes={k: v["xy"] for k, v in NODES.items()}, adj=ADJ, grid=[G, MW // G, MH // G])

css = (HERE / "master.css").read_text()

page = f"""<title>AI Platform Engineering</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600;650;700&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>
{css}
  /* Presentación: barra con título y controles, minimapa-índice, y una slide que ocupa el resto de la pantalla. */
  html{{font-size:17.6px}}
  html,body{{height:100%}}
  body{{font-size:16.5px}}
  body{{display:flex;flex-direction:column;min-height:100%}}
  .bar,.minibox,.stage{{padding-left:max(16px, env(safe-area-inset-left, 0px));padding-right:max(16px, env(safe-area-inset-right, 0px))}}
  .bar{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding-block:10px;border-bottom:1px solid var(--line)}}
  .bar .ttl{{font-family:var(--display);font-weight:600;font-size:1.05rem}}
  .bar .ttl span{{font-family:var(--sans);font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600;margin-right:10px}}
  .nav{{display:flex;align-items:center;gap:8px}}
  .nav button{{font:600 .9rem var(--sans);color:var(--accent);background:var(--accent-soft);border:1px solid var(--line-2);border-radius:8px;padding:5px 12px;cursor:pointer}}
  .nav button:hover{{border-color:var(--accent)}}
  .nav button:focus-visible,.mdot:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
  .nav button:disabled{{opacity:.35;cursor:default}}
  .pos{{font-family:var(--mono);font-size:.8rem;color:var(--muted);width:16.5em;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
  .score{{width:6.5em}}
  .minibox{{background:var(--panel);border-bottom:1px solid var(--line);padding-block:4px}}
  .mini{{display:block;width:100%;max-width:1240px;max-height:104px;margin:0 auto;height:auto}}
  .mrail{{fill:none;stroke:var(--line-2);stroke-width:2.5;stroke-linecap:round}}
  .mode{{display:inline-flex;margin-left:14px;border:1px solid var(--line-2);border-radius:8px;overflow:hidden;vertical-align:middle}}
  .bar .mode a,.bar .mode span{{font:600 .78rem var(--sans);padding:4px 10px;text-decoration:none;color:var(--accent);letter-spacing:0;text-transform:none;margin:0}}
  .bar .mode span{{background:var(--accent);color:var(--bg)}}
  .mode a:hover{{background:var(--accent-soft)}}
  .mode a:focus-visible{{outline:2px solid var(--accent);outline-offset:-2px}}
  .mrail.sup{{stroke:var(--line);stroke-width:1.5;stroke-dasharray:3 5}}
  .mlab{{font:600 9.5px var(--sans);letter-spacing:.06em;fill:var(--faint)}}
  .msup{{cursor:pointer}}
  .msup:focus{{outline:none}}
  .msup .hit{{fill:transparent}}
  .msup .sq{{fill:var(--bg);stroke:var(--faint);stroke-width:1.4}}
  .msup.big .sq{{stroke:var(--accent);stroke-width:2}}
  .msup.avail .sq{{fill:var(--crit-bg);stroke:var(--crit);stroke-width:1.8}}
  .msup.cur .sq{{fill:var(--accent);stroke:var(--accent)}}
  .msup:focus-visible .sq{{stroke:var(--ink);stroke-width:2.4}}
  .supbtn{{font:600 .82rem var(--sans) !important;color:var(--crit) !important;background:var(--crit-bg) !important;border-color:var(--crit-line) !important}}
  .food,.msup.avail .sq{{transform-box:fill-box;transform-origin:center;animation:pulse 1.1s ease-in-out infinite}}
  @keyframes pulse{{50%{{transform:scale(1.4)}}}}
  .score{{font-family:var(--mono);font-weight:600;font-size:.85rem;color:var(--ok);background:var(--ok-bg);border:1px solid var(--ok-line);
    border-radius:8px;padding:5px 10px;min-width:5.5em;text-align:center;font-variant-numeric:tabular-nums}}
  .score.bump{{animation:bump .35s ease}}
  @keyframes bump{{50%{{transform:scale(1.18)}}}}
  .pop{{font:700 15px var(--mono);fill:var(--ok);paint-order:stroke;stroke:var(--panel);stroke-width:4px;
    transform-box:fill-box;animation:popup .9s ease-out forwards}}
  @keyframes popup{{to{{transform:translateY(-22px);opacity:0}}}}
  .mdot{{cursor:pointer}}
  .mdot:focus{{outline:none}}
  .mdot .hit{{fill:transparent}}
  .mdot circle{{fill:var(--bg);stroke:var(--accent);stroke-width:2}}
  .mdot.seg circle{{stroke:var(--med)}}
  .mdot.done circle,.mdot.glos.done .gd{{opacity:0;transition:opacity .2s}}
  .mdot.seg.done circle{{fill:var(--med)}}
  .mdot.hoy rect{{fill:var(--bg);stroke:var(--accent);stroke-width:2}}
  .mdot.hoy text{{font:600 12px var(--display);fill:var(--accent)}}
  .mdot.hoy.done rect{{fill:var(--accent)}} .mdot.hoy.done text{{fill:var(--bg)}}
  .mnum{{font:600 11px var(--display);fill:var(--muted)}}
  .mdot.cur .mnum{{fill:var(--accent)}}
  .snake-geo{{fill:none;stroke:none}}
  .snake-body{{fill:none;stroke:var(--ok);stroke-width:7;stroke-linecap:round;stroke-linejoin:round}}
  .tongue{{stroke:var(--crit);stroke-width:1.6;fill:none;stroke-linecap:round;opacity:0;animation:tongue 4.5s infinite}}
  @keyframes tongue{{0%,86%,100%{{opacity:0}}88%,92%{{opacity:1}}}}
  .hd-in{{transform-box:fill-box;transform-origin:center}}
  .hd-in.chomp{{animation:chomp .32s ease}}
  @keyframes chomp{{40%{{transform:scale(1.35,0.75)}}}}
  .spark{{fill:var(--crit);transform-box:fill-box;animation:spark .6s ease-out forwards}}
  .spark.s-seg{{fill:var(--med)}} .spark.s-glos{{fill:var(--accent)}} .spark.s-extra{{fill:var(--ok)}}
  @keyframes spark{{to{{transform:translate(var(--dx),var(--dy));opacity:0}}}}
  .food.f-seg{{fill:var(--med)}} .food.f-glos{{fill:var(--accent)}} .food.f-hoy,.food.f-mapa{{fill:var(--ok)}}
  .msup.eaten .sq{{fill:var(--line-2);stroke:var(--line-2)}}
  .toasts{{position:fixed;right:max(16px, env(safe-area-inset-right, 0px));bottom:calc(16px + env(safe-area-inset-bottom, 0px));display:grid;gap:8px;z-index:5}}
  .toast{{background:var(--bg);border:1px solid var(--line-2);border-left:4px solid var(--med);border-radius:10px;padding:10px 14px;min-width:240px;
    box-shadow:0 8px 24px rgba(0,0,0,.12);animation:tin .35s cubic-bezier(.16,1,.3,1)}}
  .toast.out{{animation:tout .4s ease-in forwards}}
  @keyframes tin{{from{{opacity:0;transform:translateY(12px)}}}}
  @keyframes tout{{to{{opacity:0;transform:translateY(8px)}}}}
  .toast .tk{{font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;font-weight:700;color:var(--med)}}
  .toast .tt{{font-family:var(--display);font-weight:600;font-size:1.15rem}}
  .toast .td{{font-size:.85rem;color:var(--muted)}}
  .board{{display:flex;flex-wrap:wrap;align-items:center;gap:10px 28px;padding:10px 14px;margin-bottom:10px;background:var(--ok-bg);border:1px solid var(--ok-line);border-radius:10px}}
  .board .bk{{display:block;font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;font-weight:700;color:var(--muted)}}
  .board b{{font-family:var(--display);font-size:1.5rem;font-variant-numeric:tabular-nums}}
  .board .bl{{display:flex;flex-wrap:wrap;gap:6px;flex:1;min-width:280px}}
  .badge2{{font-size:.76rem;font-weight:600;border:1px dashed var(--line-2);color:var(--faint);border-radius:20px;padding:3px 9px}}
  .badge2.got{{border:1px solid var(--med);color:var(--med);background:var(--med-bg)}}
  .again{{font:600 .85rem var(--sans);color:var(--ok);background:var(--bg);border:1px solid var(--ok-line);border-radius:8px;padding:6px 12px;cursor:pointer}}
  .again:focus-visible{{outline:2px solid var(--ok);outline-offset:2px}}
  .snake-head{{fill:var(--ok)}} .snake-eye{{fill:var(--bg)}} .food{{fill:var(--crit)}}
  .stage > .supslide,.stage > .glosslide,.stage > .sslide,.stage > .cover,.stage > .hoyslide,.stage > .mapslide{{animation:slidein .5s cubic-bezier(.16,1,.3,1) both}}
  @keyframes slidein{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
  .food{{transition:opacity .25s}}
  .mdot circle,.mdot rect{{transition:fill .3s}}
  .stage{{transition:opacity .22s ease}}
  .stage.fading{{opacity:0}}
  .stage{{flex:1;display:flex;flex-direction:column;justify-content:flex-start;padding-block:14px 16px;max-width:1280px;width:100%;margin:0 auto}}

  /* Portada */
  .cover{{margin-block:auto}}
  .cover h1{{font-family:var(--display);font-weight:600;font-size:clamp(2.4rem,6vw,4.2rem);line-height:1.05;margin:0 0 10px}}
  .cover .csub{{font-family:var(--display);font-weight:500;font-size:clamp(1.6rem,3.6vw,2.6rem);color:var(--crit);margin:0 0 22px;line-height:1.1}}
  .cover p{{font-size:1.35rem;color:var(--muted);max-width:44ch;margin:0 0 26px}}
  .cover .k{{font-size:.8rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:14px}}
  .cover .go{{font-family:var(--mono);font-size:.9rem;color:var(--faint)}}

  /* Slide de paso: dos bandas, como los rieles */
  .band{{display:grid;grid-template-columns:260px minmax(0,1fr);gap:26px;align-items:start}}
  .card{{border:2px solid var(--line-2);border-radius:14px;padding:16px 18px;background:var(--bg)}}
  .card .rl{{font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;font-weight:700;color:var(--accent);margin-bottom:6px}}
  .card h2{{font-family:var(--display);font-weight:600;font-size:1.8rem;line-height:1.1;margin:0 0 8px}}
  .card .num{{font-family:var(--display);color:var(--accent);font-size:1rem;font-weight:600}}
  .card .when{{font-family:var(--mono);font-size:.8rem;color:var(--muted)}}
  .card.adv{{border-color:var(--accent)}}
  .card.sec{{background:var(--panel-2)}}
  .card.sec h2{{font-size:1.5rem}}
  .card.sec .rl{{color:var(--med)}}
  .bcontent{{min-width:0}}
  .lead{{font-size:1.15rem;line-height:1.5;margin:0 0 12px;max-width:none}}
  .tools{{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 14px}}
  .tool{{font-size:.85rem;font-weight:600;background:var(--panel-2);border:1px solid var(--line-2);border-radius:6px;padding:3px 9px}}
  .cols{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}}
  .lbl{{font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:var(--accent);margin:0 0 8px}}
  .ej,.err{{border-radius:10px;padding:10px 14px;margin-bottom:10px}}
  .ej{{background:var(--accent-soft);border:1px solid var(--line-2)}}
  .err{{background:var(--med-bg);border:1px solid var(--med-line)}}
  .err .lbl{{color:var(--med)}}
  .ej p,.err p{{margin:0;font-size:.98rem;line-height:1.4;max-width:none}}
  .take ul{{list-style:none;padding:0;margin:0 0 12px;display:grid;gap:8px}}
  .take li{{font-size:1.05rem;font-weight:600;line-height:1.3;padding-left:24px;position:relative}}
  .take li::before{{content:"✓";position:absolute;left:0;color:var(--ok);font-weight:700}}
  .take ul.plain li{{font-size:.9rem;font-weight:400;color:var(--muted)}}
  .take ul.plain li::before{{content:"·";color:var(--faint)}}
  .snip{{font-family:var(--mono);font-size:.78rem;line-height:1.5;background:var(--inset);border:1px solid var(--line);border-radius:8px;
    padding:10px 12px;margin:0 0 10px;white-space:pre-wrap;overflow-wrap:anywhere;color:var(--ink)}}
  .medir{{font-size:.88rem;color:var(--muted);margin:0 0 10px;max-width:none}}
  .hitos.inc{{margin-top:12px;border-left-color:var(--line)}}
  .hitos.inc li{{font-size:.8rem;grid-template-columns:4.8em minmax(0,1fr)}}
  .hitos.inc .hd{{font-size:.72rem}}
  .take{{margin-top:12px}}
  .hitos{{list-style:none;margin:0;display:grid;gap:6px;border-left:2px solid var(--line-2);padding-left:12px}}
  .hitos li{{font-size:.92rem;display:grid;grid-template-columns:5.6em minmax(0,1fr);gap:8px}}
  .hd{{font-family:var(--mono);font-size:.78rem;color:var(--accent);padding-top:2px}}
  .neck{{margin-top:12px;padding:10px 14px;background:var(--crit-bg);border:1px solid var(--crit-line);border-radius:10px}}
  .neck .lbl{{color:var(--crit);margin-bottom:2px}}
  .neck .nk{{font-family:var(--display);font-size:1.25rem;font-weight:600;color:var(--crit)}}
  .neck p{{font-size:.88rem;margin:4px 0 0}}
  .secitems{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}}
  .segi{{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:10px 14px}}
  .segi .h{{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:4px;font-weight:650}}
  .segi p{{margin:0;font-size:.95rem;max-width:none}}
  .segi .ve{{font-size:.98rem;margin:0 0 8px;padding-left:10px;border-left:3px solid var(--line-2)}}
  .how{{display:grid;grid-template-columns:auto minmax(0,1fr);gap:4px 10px;font-size:.9rem;margin-bottom:8px}}
  .hk{{font-size:.66rem;text-transform:uppercase;letter-spacing:.08em;font-weight:700;color:var(--accent);padding-top:3px;white-space:nowrap}}
  .relx{{font-size:.72rem;font-weight:600;color:var(--ok);margin-left:auto}}
  .tools.sm{{margin:0}} .tools.sm .tool{{font-size:.78rem;padding:2px 8px}}
  .segnote{{font-size:1.05rem;margin:0 0 10px;max-width:none}}
  .b-ok{{background:var(--ok-bg);color:var(--ok);border:1px solid var(--ok-line)}}
  .quiet{{color:var(--faint);font-size:1rem;margin:0}}

  /* Hoy y mapa */
  .hoyslide h2{{font-family:var(--display);font-weight:600;font-size:2.6rem;margin:0 0 10px}}
  .hoyslide .lead{{font-size:1.3rem;max-width:56ch}}
  .bigquote{{font-family:var(--display);font-size:1.7rem;line-height:1.3;max-width:40ch;margin:22px 0 0}}
  .mapslide h2{{font-family:var(--display);font-weight:600;font-size:2.3rem;margin:0 0 8px;padding-bottom:10px;border-bottom:2px solid var(--ink)}}
  .mapslide .diagram{{padding:12px 14px}}
  .amap-wrap{{overflow-x:auto}}
  .amap{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:0 16px;min-width:1000px}}
  .amap .col{{display:flex;flex-direction:column;justify-content:flex-end;min-width:0}}
  .amap .node{{padding:7px 11px}}
  .amap .node .t{{font-size:.95rem;padding-right:70px;line-height:1.25}}
  .amap .node .s{{font-size:.74rem;line-height:1.3}}
  .amap .conn{{height:10px}}
  .amap .conn.dash{{background:repeating-linear-gradient(to bottom,var(--line-2) 0 4px,transparent 4px 8px)}}
  .amap .conn.join::after{{display:none}}
  .amap .secn{{background:var(--panel-2);border-left:4px solid var(--sc)}}
  .amap .secn.st-ok{{--sc:var(--ok)}} .amap .secn.st-med{{--sc:var(--med)}} .amap .secn.st-crit{{--sc:var(--crit)}}
  .amap .common{{grid-column:1 / -1;display:flex;flex-direction:column;align-items:center}}
  .amap .common .bus{{align-self:stretch;height:2px;background:var(--line-2);margin:0 10%}}
  .amap .hoyn{{width:min(560px,100%);border:2px solid var(--accent);background:var(--accent-soft);text-align:center}}
  .amap .hoyn .t{{padding-right:0;font-family:var(--display);font-size:1.3rem}}
  .amap .hoyn .s{{font-size:.9rem}}
  .legend .sw.sok{{border-left:4px solid var(--ok)}} .legend .sw.smed{{border-left:4px solid var(--med)}} .legend .sw.scrit{{border-left:4px solid var(--crit)}}
  .mapslide .bigquote{{font-size:1.15rem;margin-top:6px}}
  .zip-svg{{display:block;width:100%;height:auto}}
  .rail{{fill:none;stroke:var(--line-2);stroke-width:2.5;stroke-linecap:round}}
  .mk-r{{fill:var(--line-2)}} .mk-c{{fill:var(--faint)}} .mk-u{{fill:var(--accent)}}
  .rlbl{{font:700 11px var(--sans);letter-spacing:.14em;fill:var(--accent)}}
  .snum{{font:600 12px var(--display);fill:var(--accent)}}
  .bx{{fill:var(--bg);stroke:var(--line-2);stroke-width:1.2}}
  .bt{{font:600 10.6px var(--sans);fill:var(--ink)}}
  .sec .bx{{fill:var(--panel-2)}}
  .conn{{fill:none;stroke:var(--faint);stroke-width:1.5}}
  .conn.up{{stroke:var(--accent);stroke-width:1.7}}
  .hoybx{{fill:var(--accent);stroke:var(--accent)}}
  .hoyt{{font:600 15px var(--display);fill:var(--bg)}}
  .stitle{{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;padding-bottom:10px;border-bottom:2px solid var(--ink)}}
  .stitle .num,.sechead .num{{font-family:var(--display);font-weight:600;color:var(--accent);font-size:1.1rem;white-space:nowrap}}
  .stitle h2{{font-family:var(--display);font-weight:600;font-size:2.3rem;line-height:1.1;margin:0}}
  .stitle .when{{margin-left:auto;font-family:var(--mono);font-size:.85rem;color:var(--muted)}}
  .sgrid{{display:grid;grid-template-columns:minmax(0,1fr) 255px;gap:32px;padding-top:14px}}
  .smain{{min-width:0}}
  .smain .lead{{font-size:1.12rem;line-height:1.5;margin:0 0 4px;max-width:none}}
  .mcols{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 36px}}
  .sub{{font-family:var(--display);font-weight:600;font-size:1.02rem;color:var(--ink);display:flex;align-items:center;gap:10px;margin:11px 0 4px}}
  .sub::after{{content:"";flex:1;height:1px;background:var(--line-2)}}
  .sub.warn{{color:var(--med)}} .sub.crit{{color:var(--crit)}}
  .txt{{margin:0;font-size:.97rem;line-height:1.45;max-width:none}}
  .txt.muted{{color:var(--muted)}}
  .nk{{color:var(--crit)}}
  ul.take{{margin:0;padding-left:20px;display:grid;gap:4px;font-size:.97rem}}
  ul.take li::marker{{color:var(--ok)}}
  dl.how{{display:grid;grid-template-columns:auto minmax(0,1fr);gap:4px 12px;margin:0;font-size:.95rem}}
  dl.how dt{{font-weight:600;white-space:nowrap}}
  dl.how dd{{margin:0}}
  .snip{{font-family:var(--mono);font-size:.76rem;line-height:1.5;background:var(--inset);border:1px solid var(--line);border-radius:6px;
    padding:9px 12px;margin:0;white-space:pre-wrap;overflow-wrap:anywhere;color:var(--ink)}}
  aside.tl{{border-left:1px solid var(--line-2);padding-left:18px}}
  aside.tl .sub:first-child{{margin-top:0}}
  aside.tl .txt{{font-size:.9rem}}
  aside.tl ol{{list-style:none;margin:6px 0 0;padding:0;display:grid;gap:6px}}
  aside.tl li{{display:grid;gap:1px;position:relative;font-size:.88rem;line-height:1.32}}
  aside.tl li::before{{content:"";position:absolute;left:-23px;top:5px;width:9px;height:9px;border-radius:50%;background:var(--accent)}}
  a.src{{font-size:.85rem;font-weight:700;color:var(--accent);text-decoration:none;padding:0 2px}}
  a.src:hover{{color:var(--ink)}}
  aside.tl .hd{{font-family:var(--mono);font-size:.76rem;color:var(--accent)}}
  .sechead{{display:flex;align-items:baseline;gap:14px;margin-top:12px;padding-top:10px;border-top:2px solid var(--med)}}
  .sechead .num{{color:var(--med)}}
  .sechead h3{{font-family:var(--display);font-weight:600;font-size:1.35rem;margin:0}}
  .relx{{font-family:var(--sans);font-size:.75rem;font-weight:600;color:var(--ok)}}
  .seegrid{{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.15fr);gap:16px;align-items:start}}
  .xfile,.xdiag{{margin:0;border:1px solid var(--line-2);border-radius:6px;overflow:hidden;background:var(--bg)}}
  .xfile figcaption,.xdiag figcaption{{font-family:var(--mono);font-size:.72rem;color:var(--muted);background:var(--panel-2);
    border-bottom:1px solid var(--line);padding:5px 10px}}
  .tri svg{{display:block;width:100%;max-width:400px;margin:6px auto 0}}
  .tri .tfc{{fill:var(--med-bg);fill-opacity:.55;stroke:var(--med);stroke-width:1.5}}
  .tri .tfk{{fill:var(--crit)}}
  .tri .tfn{{font:600 14px var(--sans);fill:var(--ink)}}
  .tri .tfx{{font:11px var(--mono);fill:var(--muted)}}
  .tri .tfm{{font:700 12px var(--sans);fill:var(--bg)}}
  .tri .tfnote{{margin:0;padding:4px 12px 9px;font-size:.92rem;font-weight:600;color:var(--crit);text-align:center}}
  .xfile pre{{margin:0;padding:9px 12px;font-family:var(--mono);font-size:.74rem;line-height:1.45;white-space:pre-wrap;overflow-wrap:anywhere;color:var(--ink)}}
  .flow-h{{display:flex;flex-wrap:wrap;align-items:center;gap:6px 6px;padding:12px}}
  .flow-h .fn{{border:1px solid var(--line-2);border-radius:7px;padding:5px 9px;font-size:.84rem;font-weight:600;background:var(--panel)}}
  .flow-h .arr{{color:var(--faint);font-weight:700}}
  .asec .sub{{font-size:1.12rem;margin:13px 0 5px}}
  .asec .txt,.asec ul.take,.asec dl.how{{font-size:1rem}}
  .asec .snip{{font-size:.8rem}}
  .mdot.glos .gd{{fill:var(--bg);stroke:var(--accent);stroke-width:1.8}}
  .mdot.glos.done .gd{{fill:var(--accent)}}
  dl.glos{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 48px;margin:6px 0 0}}
  dl.glos > div{{padding:11px 0;border-bottom:1px solid var(--line)}}
  dl.glos dt{{font-family:var(--display);font-weight:600;font-size:1.25rem;margin:0 0 3px}}
  dl.glos dd{{margin:0;font-size:1.02rem;line-height:1.45;color:var(--ink)}}
  .supslide .stitle{{border-bottom-color:var(--accent)}}
  .supslide.secsup .stitle{{border-bottom-color:var(--med)}}
  .supslide.secsup .stitle .num{{color:var(--med)}}
  .faq .sub{{font-size:1.25rem;margin:16px 0 6px}}
  .faq .txt{{font-size:1.08rem;line-height:1.5}}
  .secslide .stitle{{border-bottom-color:var(--med)}}
  .secslide .stitle .num{{color:var(--med)}}
  .secslide .lead{{font-size:1.08rem;line-height:1.45;margin:0;max-width:none}}
  .tlg + .tlg{{margin-top:14px}}
  .tlname{{font-weight:650;font-size:.9rem;margin:0 0 6px}}
  .secslide aside.tl li::before{{background:var(--med)}}
  .secslide aside.tl .hd{{color:var(--med)}}
  .ssec{{margin-top:10px}}
  .ssec .sub{{font-size:1.3rem;margin:12px 0 6px}}
  .ssec .sub .badge{{font-family:var(--sans);font-size:.72rem}}
  .ssgrid{{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.1fr);gap:0 40px;align-items:start}}
  .ssec .txt{{font-size:1.02rem;line-height:1.5;margin-bottom:8px}}
  .ssec dl.how{{font-size:1rem;gap:6px 14px}}
  .mlbl.gap{{margin-top:12px}}
  .mlbl.warn{{color:var(--med)}}
  .ssec ul.take{{font-size:.97rem;margin-bottom:4px}}
  .mlbl{{font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:var(--accent);margin:0 0 4px}}
  @media (max-width:860px){{
    dl.glos{{grid-template-columns:minmax(0,1fr)}}
    .seegrid{{grid-template-columns:minmax(0,1fr)}}
    .ssgrid{{grid-template-columns:minmax(0,1fr)}}
    .sgrid,.mcols{{grid-template-columns:minmax(0,1fr)}}
    .band{{grid-template-columns:minmax(0,1fr)}}
    .secwrap .link{{margin-left:24px}}
    .cols{{grid-template-columns:minmax(0,1fr)}}
  }}
  .mini{{max-height:150px}}
  .tablero{{stroke:var(--line-2)}} .tb1{{fill:var(--bg)}} .tb2{{fill:var(--panel-2);opacity:.55}}
  .medge{{fill:none;stroke-linejoin:miter;stroke-opacity:0;stroke-width:2;stroke-dasharray:2 5;transition:stroke-opacity .3s}}
  .medge.main{{stroke:var(--accent)}} .medge.sec{{stroke:var(--med)}} .medge.sup{{stroke:var(--accent)}}
  .medge.lit{{stroke-opacity:.75}}
  .snake-body{{stroke-linecap:square;stroke-linejoin:miter;stroke-width:9;stroke-dasharray:12 2}}
  .mini .mdot.done .blk,.mini .mdot.glos.done .gd{{opacity:1}}
  .mini .mdot .blk{{fill:var(--bg);stroke:var(--accent);stroke-width:2.2}}
  .mini .mdot.seg .blk{{stroke:var(--med)}}
  .mini .mdot.avance .mnum{{font:600 13px var(--display);fill:var(--accent)}}
  .mini .mdot.avance.done .blk{{fill:var(--accent)}}
  .mini .mdot.avance.done .mnum{{fill:var(--bg)}}
  .mini .mdot.seg.done .blk{{fill:var(--med)}}
  .mini .mdot.cur .blk{{stroke:var(--ink);stroke-width:3}}
  .msup .sq{{opacity:.3;transition:opacity .3s}}
  .mprev{{fill:none;stroke:var(--accent);stroke-width:2;stroke-dasharray:2 5;stroke-linecap:round;opacity:.7}}
  .mkey rect{{fill:var(--ink);opacity:.85}} .mkey text{{font:700 11px var(--sans);fill:var(--bg)}}
  .msup.avail .sq,.msup.cur .sq,.msup.eaten .sq{{opacity:1}}
  @media (prefers-reduced-motion:reduce){{*{{transition:none !important}}}}
</style>
<div class="bar">
  <div class="ttl"><span>BarCamp</span>AI Platform Engineering — El blocker eres tú<nav class="mode" aria-label="Vista"><a href="./">Por pasos</a><a href="por-anos.html">Por años</a><span aria-current="page">Grafo</span></nav></div>
  <div class="nav">
    <button type="button" id="b-sup" class="supbtn" hidden></button>
    <button type="button" id="b-prev" aria-label="Anterior">◀</button>
    <span class="pos" id="pos"></span>
    <button type="button" id="b-next" aria-label="Siguiente">▶</button>
    <span class="score" id="score" aria-live="polite">0 pts</span>
  </div>
</div>
<div class="minibox">{MINI_SVG}</div>
<main class="stage" id="stage" aria-live="polite"></main>
<div class="toasts" id="toasts" aria-live="polite"></div>
<template id="d-inj">{zip2.trifecta_svg()}</template>
<template id="t-map">
  <div class="mapslide">
    <h2>El mapa completo</h2>
    {ARCH_MAP}
    <p class="bigquote">“El próximo salto de velocidad no lo va a dar un modelo mejor. Lo va a dar poder confiar en lo que hacen los agentes.”</p>
  </div>
</template>
<script>
(function () {{
  var D = {json.dumps(DATA, ensure_ascii=False)};
  var POS = D.pos, LAST = POS.length - 1, P = 0;
  var NS = "http://www.w3.org/2000/svg";
  function el(t, a) {{ var n = document.createElementNS(NS, t); for (var k in a) n.setAttribute(k, a[k]); return n; }}
  function esc(s) {{ return String(s).replace(/[&<>"]/g, function (c) {{ return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]; }}); }}
  function li(a) {{ return a.map(function (x) {{ return "<li>" + esc(x) + "</li>"; }}).join(""); }}
  var REL = {{ abre: "abre", resuelve: "resuelve", pieza: "misma pieza", habilita: "habilitado por", falta: "falta" }};

  // Serpiente: un solo trazo con toda la ruta; se revela hasta la posición actual y la cabeza recorre el trazo.
  var REDUCED = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var SG = document.getElementById("msnake"), BODY, HEAD, FOOD, LENS = [], TOTAL = 0, CUR = 0, RAF = 0;
  // Serpiente con rastro: cada movimiento agrega un tramo desde la cabeza; los desvíos quedan en el camino.
  var SUP = null, WIG, FX, HEADIN, SAMP = [], STEPS = 3, TRD = "", STACK = [], RETRACT = null, PLAN = null, DIRECT = false;
  function route(a, b) {{
    if (a === b || DIRECT) return [b];
    var prev = {{}}, q = [a];
    prev[a] = a;
    while (q.length) {{
      var n = q.shift();
      if (n === b) break;
      (D.adj[n] || []).forEach(function (m) {{ if (!(m in prev)) {{ prev[m] = n; q.push(m); }} }});
    }}
    var out = [b];
    while (out[0] !== a) out.unshift(prev[out[0]]);
    return out.slice(1);
  }}
  function sample(path, total) {{
    var out = [];
    for (var s = 0; s <= total; s += STEPS) {{
      var a = path.getPointAtLength(s), b = path.getPointAtLength(Math.min(total, s + 1));
      var dx = b.x - a.x, dy = b.y - a.y, n = Math.hypot(dx, dy) || 1;
      out.push([a.x, a.y, -dy / n, dx / n]);
    }}
    return out;
  }}
  function setTrail(d) {{ TRD = d; BODY.setAttribute("d", d); TOTAL = BODY.getTotalLength(); SAMP = sample(BODY, TOTAL); }}
  // Cada tramo se busca en la cuadrícula: esquiva el cuerpo y la otra comida, arranca hacia la
  // flecha presionada (o sigue de frente) y gira lo menos posible.
  var GS = D.grid[0], GW = D.grid[1], GH = D.grid[2], NEXTDIR = null, LASTEND = null;
  function cellOf(xy) {{ return [Math.round((xy[0] - GS / 2) / GS), Math.round((xy[1] - GS / 2) / GS)]; }}
  function center(c) {{ return [c[0] * GS + GS / 2, c[1] * GS + GS / 2]; }}
  function heading() {{
    if (TOTAL < 2) return [1, 0];
    var a = BODY.getPointAtLength(TOTAL - 2), b = BODY.getPointAtLength(TOTAL);
    return Math.abs(b.x - a.x) >= Math.abs(b.y - a.y) ? [b.x >= a.x ? 1 : -1, 0] : [0, b.y >= a.y ? 1 : -1];
  }}
  // Celdas ocupadas: el cuerpo (no se puede cruzar) y la comida que no es el destino; los pasos
  // ocupan 3×3 celdas. Las celdas vecinas a ambos cuestan más, para que la serpiente deje aire.
  function obstacles(from, target, food) {{
    // Como en Snake, la cola avanza con la cabeza: cada celda del cuerpo guarda en qué paso queda
    // libre. El tramo que crece al comer (GROW) queda ocupado todo el movimiento.
    var hard = {{}}, soft = {{}}, body = {{}}, L = bodyLen(), GROW = 24, tail = TOTAL - L;
    function mark(x, y, r, v) {{ for (var dx = -r; dx <= r; dx++) for (var dy = -r; dy <= r; dy++) {{ var k = (x + dx) + "," + (y + dy); if (v) hard[k] = 1; else soft[k] = 1; }} }}
    for (var s = Math.max(0, tail - GROW); s < TOTAL - GS / 2; s += GS / 4) {{
      var p = BODY.getPointAtLength(s), c = cellOf([p.x, p.y]), k = c[0] + "," + c[1];
      body[k] = Math.max(body[k] || 0, s < tail ? 1e9 : Math.ceil((s - tail) / GS) + 1);
      mark(c[0], c[1], 1, 0);
    }}
    var tc = cellOf(D.nodes[target]);
    mark(tc[0], tc[1], 0, 1);
    if (food) Object.keys(D.nodes).forEach(function (n) {{
      if (n === target) return;
      var c = cellOf(D.nodes[n]), big = n.charAt(0) === "a" || n === "hoy";
      mark(c[0], c[1], big ? 1 : 0, 1); mark(c[0], c[1], big ? 2 : 1, 0);
    }});
    return {{ hard: hard, soft: soft, body: body }};
  }}
  // Búsqueda por celdas (cada celda una sola vez, así la ruta nunca se cruza) con costo extra por
  // girar y por pasar pegado a algo. La primera dirección favorecida es la flecha presionada.
  // La serpiente no entra al centro del nodo (puede estar ocupado por su cuerpo si ya pasó por ahí):
  // se detiene en una celda pegada a él, como si lo mordiera.
  function gridPath(from, to, dir, ob) {{
    var D4 = [[1, 0], [0, 1], [-1, 0], [0, -1]], d0 = 0, goals = {{}}, tk = null;
    D4.forEach(function (d, k) {{
      if (d[0] === dir[0] && d[1] === dir[1]) d0 = k;
      var gk = (to[0] + d[0]) + "," + (to[1] + d[1]);
      goals[gk] = d[0] === -dir[0] && d[1] === -dir[1] ? 1 : 4;
    }});
    var done = {{}}, prev = {{}}, open = [[0, from[0], from[1], d0, null, 0]];
    while (open.length) {{
      open.sort(function (a, b) {{ return a[0] - b[0]; }});
      var cur = open.shift(), key = cur[1] + "," + cur[2];
      if (done[key]) continue;
      done[key] = cur[3] + 1; prev[key] = cur[4];
      if (goals[key] && cur[4] !== null) {{ tk = key; break; }}
      var step = cur[5] + 1;
      D4.forEach(function (d, k) {{
        if ((k + 2) % 4 === cur[3]) return;
        var x = cur[1] + d[0], y = cur[2] + d[1], nk = x + "," + y;
        if (x < 0 || y < 0 || x >= GW || y >= GH || done[nk]) return;
        if (!goals[nk] && ob.hard[nk]) return;
        if (ob.body && ob.body[nk] && step <= ob.body[nk]) return;  // la cola todavía no salió de esa celda
        open.push([cur[0] + 1 + (k === cur[3] ? 0 : 3) + (ob.soft[nk] && !goals[nk] ? 1.5 : 0) + (goals[nk] ? goals[nk] - 1 : 0), x, y, k, key, step]);
      }});
    }}
    if (!tk) return null;
    var out = [];
    for (var k = tk; k; k = prev[k]) {{ var q = k.split(","); out.unshift([+q[0], +q[1]]); }}
    return out;
  }}
  function hopPath(fromXY, n, dir, fromId) {{
    var a = cellOf(fromXY), b = cellOf(D.nodes[n]);
    var cells = gridPath(a, b, dir, obstacles(fromId, n, true)) || gridPath(a, b, dir, obstacles(fromId, n, false)) ||
      gridPath(a, b, dir, {{ hard: {{}}, soft: {{}} }}) || [a, b];
    LASTEND = center(cells[cells.length - 1]);
    var d = "", pts = cells.map(center);
    for (var i = 1; i < pts.length; i++) {{
      var last = i === pts.length - 1, p0 = pts[i - 1], p1 = pts[i], p2 = pts[i + 1];
      if (last || (p1[0] - p0[0]) !== (p2[0] - p1[0]) || (p1[1] - p0[1]) !== (p2[1] - p1[1])) d += " L" + p1[0] + "," + p1[1];
    }}
    return d;
  }}
  function extendTo(id, key) {{
    var path = route(STACK[STACK.length - 1].id, id), dir = NEXTDIR;
    NEXTDIR = null; DIRECT = false;
    path.forEach(function (n, k) {{
      var top = STACK[STACK.length - 1], s = hopPath(top.xy, n, k === 0 && dir ? dir : heading(), top.id);
      if (s) setTrail(TRD + s);
      STACK.push({{ key: k === path.length - 1 ? key : "v", id: n, xy: LASTEND, len: TOTAL, d: TRD }});
    }});
  }}
  function curNode() {{ return SUP ? "x" + SUP + POS[P].i : POS[P].node; }}
  // Todo desvío (seguridad, extras, preguntas) tiene un atajo al siguiente punto de la línea base.
  function shortcut(cn) {{
    if (!SUP && /^([ag][0-9]|start$|hoy$)/.test(cn)) return null;
    for (var j = P + 1; j < POS.length; j++) if (/^(avance|glos|hoy)$/.test(POS[j].k)) return POS[j].node;
    return null;
  }}
  // Flechas como en Snake: cada una lleva al vecino que está en esa dirección.
  var DIRS = {{ ArrowRight: [1, 0, "→"], ArrowLeft: [-1, 0, "←"], ArrowUp: [0, -1, "↑"], ArrowDown: [0, 1, "↓"] }};
  // Reparte las flechas entre los vecinos para que todos tengan una, lo más alineada posible.
  function options() {{
    var cn = curNode(), h = D.nodes[cn], sc = shortcut(cn), ns = (D.adj[cn] || []).slice(0, sc ? 3 : 4), keys = Object.keys(DIRS), best = null, bestS = -1e9;
    // En un desvío, → es "siguiente": la próxima parada (seguridad 2 de 2) o el atajo a la línea base.
    var nx = sc && !SUP && POS[P + 1] && POS[P + 1].node, fwd = sc && (ns.indexOf(nx) >= 0 ? nx : sc);
    function score(n, k) {{
      if (n === fwd) return k === "ArrowRight" ? 100 : -100;
      var xy = D.nodes[n], dx = xy[0] - h[0], dy = xy[1] - h[1];
      return (dx * DIRS[k][0] + dy * DIRS[k][1]) / (Math.hypot(dx, dy) || 1);
    }}
    if (sc && ns.indexOf(sc) < 0) ns.push(sc);
    (function perm(i, used, acc, sc) {{
      if (i === ns.length) {{ if (sc > bestS) {{ bestS = sc; best = acc.slice(); }} return; }}
      keys.forEach(function (k) {{ if (!used[k]) {{ used[k] = 1; acc.push(k); perm(i + 1, used, acc, sc + score(ns[i], k)); acc.pop(); used[k] = 0; }} }});
    }})(0, {{}}, [], 0);
    var out = {{}};
    (best || []).forEach(function (k, i) {{ out[k] = ns[i]; }});
    return out;
  }}
  function moveTo(n) {{
    if (n.charAt(0) === "x") {{ enterSup(n.charAt(1)); return; }}
    DIRECT = n === shortcut(curNode());
    if (SUP && n === POS[P].node) {{
      settle(); SUP = null;
      extendTo(POS[P].node, "p" + P); PLAN = {{ len: TOTAL }};
      render(); return;
    }}
    for (var j = 0; j < POS.length; j++) if (POS[j].node === n) {{ go(j); return; }}
  }}
  function drawKeys() {{
    var g = document.getElementById("mkeys"), o = options(), h = STACK[STACK.length - 1].xy;
    while (g.firstChild) g.removeChild(g.firstChild);
    Object.keys(o).forEach(function (k) {{
      g.appendChild(el("path", {{ "class": "mprev", d: "M" + h[0] + "," + h[1] + hopPath(h, o[k], DIRS[k], STACK[STACK.length - 1].id) }}));
    }});
    Object.keys(o).forEach(function (k) {{
      var xy = D.nodes[o[k]], v = DIRS[k], x = xy[0] + v[0] * 22 + (v[0] ? 0 : 20), y = xy[1] + v[1] * 22 + (v[1] ? 0 : -14);
      var t = el("g", {{ "class": "mkey" }});
      t.appendChild(el("rect", {{ x: x - 8, y: y - 8, width: 16, height: 16, rx: 3 }}));
      var tx = el("text", {{ x: x, y: y + 4, "text-anchor": "middle" }});
      tx.textContent = v[2]; t.appendChild(tx); g.appendChild(t);
    }});
  }}
  function truncate(idx) {{ STACK = STACK.slice(0, idx + 1); setTrail(STACK[idx].d); }}
  function resetTrail() {{
    var xy = POS[0].xy;
    STACK = [{{ key: "p0", id: POS[0].node, xy: xy, len: 0, d: "M" + xy[0] + "," + xy[1] }}];
    setTrail(STACK[0].d);
  }}
  function settle() {{
    if (!RETRACT) return;
    cancelAnimationFrame(RAF); setLen(RETRACT.len); truncate(RETRACT.idx); RETRACT = null;
  }}
  function initSnake() {{
    BODY = el("path", {{ d: "M0,0", "class": "snake-geo" }});
    WIG = el("path", {{ d: "M0,0", "class": "snake-body" }});
    FOOD = el("rect", {{ width: 12, height: 12, rx: 2.5, "class": "food" }});
    FX = el("g", {{}});
    HEAD = el("g", {{}});
    var inner = el("g", {{ "class": "hd-in" }});
    inner.appendChild(el("path", {{ d: "M8,0 L15,0 M15,0 L18,-2.5 M15,0 L18,2.5", "class": "tongue" }}));
    inner.appendChild(el("rect", {{ x: -9, y: -9, width: 18, height: 18, rx: 4.5, "class": "snake-head" }}));
    inner.appendChild(el("rect", {{ x: 1.5, y: -5, width: 3.5, height: 3.5, "class": "snake-eye" }}));
    inner.appendChild(el("rect", {{ x: 1.5, y: 1.5, width: 3.5, height: 3.5, "class": "snake-eye" }}));
    HEAD.appendChild(inner); HEADIN = inner;
    SG.appendChild(BODY); SG.appendChild(FOOD); SG.appendChild(WIG); SG.appendChild(HEAD); SG.appendChild(FX);
    resetTrail();
  }}
  // Como en Snake: el cuerpo tiene un largo que crece con lo que come y la cola sigue a la cabeza.
  function bodyLen() {{ return Math.min(340, 70 + 12 * Object.keys(EATEN).length); }}
  function wave(samp, upto, t, amp) {{
    var n = Math.min(samp.length - 1, Math.floor(upto / STEPS)), d = "";
    var i0 = Math.max(0, Math.floor((upto - bodyLen()) / STEPS));
    for (var i = i0; i <= n; i++) {{
      var s = i * STEPS, q = samp[i];
      var A = amp * Math.min(1, s / 24) * Math.min(1, Math.max(0, (upto - s) / 16));
      var o = A * Math.sin(s / 13 - t);
      d += (i > i0 ? " L" : "M") + (q[0] + q[2] * o).toFixed(1) + "," + (q[1] + q[3] * o).toFixed(1);
    }}
    return d || "M0,0";
  }}
  function drawBody(now) {{ WIG.setAttribute("d", CUR > 1 ? wave(SAMP, CUR, now / 170, 0) : "M0,0"); }}
  function tick(now) {{ drawBody(now); if (!REDUCED) requestAnimationFrame(tick); }}
  function burst(xy, cls) {{
    if (REDUCED) return;
    for (var k = 0; k < 9; k++) {{
      var ang = k / 9 * Math.PI * 2, r = 14 + Math.random() * 10;
      var c = el("circle", {{ cx: xy[0], cy: xy[1], r: 2.4, "class": "spark " + (cls || "") }});
      c.style.setProperty("--dx", (Math.cos(ang) * r).toFixed(1) + "px");
      c.style.setProperty("--dy", (Math.sin(ang) * r).toFixed(1) + "px");
      FX.appendChild(c);
      (function (c) {{ setTimeout(function () {{ if (c.parentNode) c.parentNode.removeChild(c); }}, 650); }})(c);
    }}
    HEADIN.classList.remove("chomp"); void HEADIN.getBBox(); HEADIN.classList.add("chomp");
  }}
  function setLen(len) {{
    CUR = len;
    var pt = BODY.getPointAtLength(len);
    var a = len > 3 ? BODY.getPointAtLength(len - 3) : pt, b = len > 3 ? pt : BODY.getPointAtLength(Math.min(TOTAL, len + 3));
    var ang = Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI;
    HEAD.setAttribute("transform", "translate(" + pt.x + "," + pt.y + ") rotate(" + ang + ")");
    if (REDUCED) drawBody(0);
  }}
  function placeFood() {{
    if (P >= LAST) {{ FOOD.style.opacity = 0; return; }}
    var f = POS[P + 1].xy, h = STACK[STACK.length - 1].xy;
    if (f[0] === h[0] && f[1] === h[1]) {{ FOOD.style.opacity = 0; return; }}
    FOOD.setAttribute("x", f[0] - 6); FOOD.setAttribute("y", f[1] - 6);
    FOOD.setAttribute("class", "food f-" + POS[P + 1].k);
    FOOD.style.opacity = 1;
  }}
  function animateLen(to, onArrive, onDone) {{
    var from = CUR;
    cancelAnimationFrame(RAF);
    if (REDUCED || Math.abs(to - from) < 0.5) {{ setLen(to); if (onArrive) onArrive(); if (onDone) onDone(); return; }}
    FOOD.style.opacity = 0;
    var dur = Math.min(1500, Math.max(600, Math.abs(to - from) * 2.6)), t0 = null;
    function frame(now) {{
      if (t0 === null) t0 = now;
      var t = Math.min(1, (now - t0) / dur);
      setLen(from + (to - from) * ease(t));
      if (onArrive && t >= 0.35) {{ var cb = onArrive; onArrive = null; cb(); }}
      if (t < 1) RAF = requestAnimationFrame(frame); else if (onDone) onDone();
    }}
    RAF = requestAnimationFrame(frame);
  }}
  function supAvail(kind) {{
    var p = POS[P];
    if (kind === "a") return p.k === "avance" && !!D.supa[String(p.i)];
    return p.k === "seg" && p.n === p.c - 1 && !!D.sups[String(p.i)];
  }}
  function markSup() {{
    var p = POS[P];
    document.querySelectorAll(".msup").forEach(function (m) {{
      var k = m.getAttribute("data-sup"), i = +m.getAttribute("data-i");
      m.classList.toggle("cur", SUP === k && p.i === i);
      m.classList.toggle("avail", !SUP && p.i === i && supAvail(k));
    }});
    var b = document.getElementById("b-sup");
    if (SUP === "a") {{ b.hidden = false; b.textContent = "↓ volver"; }}
    else if (SUP === "s") {{ b.hidden = false; b.textContent = "↑ volver"; }}
    else if (supAvail("a")) {{ b.hidden = false; b.textContent = D.supa[String(p.i)].t ? "↑ extra: " + D.supa[String(p.i)].t : "↑ preguntas"; }}
    else if (supAvail("s")) {{ b.hidden = false; b.textContent = "↓ preguntas"; }}
    else b.hidden = true;
    var cn = curNode();
    document.querySelectorAll(".medge").forEach(function (e) {{
      e.classList.toggle("lit", e.getAttribute("data-a") === cn || e.getAttribute("data-b") === cn);
    }});
    drawKeys();
  }}
  var SCORE = 0, EATEN = {{}}, PTS = {{ avance: 10, seg: 10, glos: 5, hoy: 10, mapa: 10, extra: 20 }};
  function pop(xy, n) {{
    var t = el("text", {{ x: xy[0] + 10, y: xy[1] - 10, "class": "pop" }});
    t.textContent = "+" + n; SG.appendChild(t);
    setTimeout(function () {{ if (t.parentNode) t.parentNode.removeChild(t); }}, 950);
    var sc = document.getElementById("score");
    sc.textContent = SCORE + " pts"; sc.classList.remove("bump"); void sc.offsetWidth; sc.classList.add("bump");
  }}
  // Solo se come la parada a la que se llega: saltarse nodos deja comida en el mapa.
  function eatAt(k) {{
    if (k < 1 || EATEN["p" + k]) return;
    EATEN["p" + k] = 1;
    var gained = PTS[POS[k].k] || 10;
    SCORE += gained; pop(POS[k].xy, gained); burst(POS[k].xy, "s-" + POS[k].k); markDots(); checkAch();
  }}
  function markDots() {{
    document.querySelectorAll(".mdot").forEach(function (m) {{
      var k = +m.getAttribute("data-p");
      m.classList.toggle("done", !!EATEN["p" + k]);
      m.classList.toggle("cur", k === P && !SUP);
    }});
  }}
  function eatExtra(kind, i, xy) {{
    var key = kind + i;
    if (EATEN[key]) return;
    EATEN[key] = 1; SCORE += PTS.extra; pop(xy, PTS.extra); burst(xy, "s-extra"); checkAch();
    document.querySelectorAll('.msup[data-sup="' + kind + '"][data-i="' + i + '"]').forEach(function (m) {{ m.classList.add("eaten"); }});
  }}
  function nEaten(prefix) {{ return Object.keys(EATEN).filter(function (k) {{ return k.charAt(0) === prefix; }}).length; }}
  var NA = Object.keys(D.supa).length, NSQ = Object.keys(D.sups).length, NP = POS.length - 1;
  var ACH = [
    ["primer", "Primer bocado", "Te comiste la primera parada.", function () {{ return EATEN.p1; }}],
    ["poliglota", "Políglota", "Pasaste por los tres vocabularios.", function () {{ return POS.every(function (q, j) {{ return q.k !== "glos" || EATEN["p" + j]; }}); }}],
    ["curioso", "Curioso", "Exploraste 3 extras.", function () {{ return nEaten("a") + nEaten("s") >= 3; }}],
    ["qa", "QA no ha muerto", "Abriste «Calidad aumentada por IA».", function () {{ return EATEN.a5; }}],
    ["paranoico", "Paranoico profesional", "Todas las preguntas de seguridad.", function () {{ return nEaten("s") === NSQ; }}],
    ["blocker", "El blocker eres tú", "Llegaste a Hoy.", function () {{ return POS.some(function (q, j) {{ return q.k === "hoy" && EATEN["p" + j]; }}); }}],
    ["completo", "Completista", "Te comiste todo el mapa y todos los extras.", function () {{ return nEaten("p") === NP && nEaten("a") === NA && nEaten("s") === NSQ; }}],
  ];
  var GOT = {{}};
  function checkAch() {{
    ACH.forEach(function (a) {{ if (!GOT[a[0]] && a[3]()) {{ GOT[a[0]] = 1; toast(a[1], a[2]); }} }});
    updateBoard();
  }}
  function toast(title, desc) {{
    var box = document.getElementById("toasts"), t = document.createElement("div");
    t.className = "toast"; t.innerHTML = '<div class="tk">Logro desbloqueado</div><div class="tt">' + esc(title) + '</div><div class="td">' + esc(desc) + '</div>';
    box.appendChild(t);
    setTimeout(function () {{ t.classList.add("out"); }}, 3200);
    setTimeout(function () {{ if (t.parentNode) t.parentNode.removeChild(t); }}, 3700);
  }}
  function best() {{ try {{ return +localStorage.getItem("ape-best") || 0; }} catch (e) {{ return 0; }} }}
  function updateBoard() {{
    var b = document.getElementById("board");
    if (!b) return;
    var rec = best();
    if (SCORE > rec) {{ try {{ localStorage.setItem("ape-best", SCORE); }} catch (e) {{}} rec = SCORE; }}
    b.querySelector(".bs").textContent = SCORE;
    b.querySelector(".bx").textContent = (nEaten("a") + nEaten("s")) + " de " + (NA + NSQ);
    b.querySelector(".br").textContent = rec;
    b.querySelector(".bl").innerHTML = ACH.map(function (a) {{
      return '<span class="badge2' + (GOT[a[0]] ? ' got' : '') + '" title="' + esc(a[2]) + '">' + esc(a[1]) + '</span>';
    }}).join("");
  }}
  function restart() {{
    SCORE = 0; EATEN = {{}}; GOT = {{}};
    document.getElementById("score").textContent = "0 pts";
    document.querySelectorAll(".msup.eaten").forEach(function (m) {{ m.classList.remove("eaten"); }});
    go(0);
  }}
  function ease(t) {{ return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }}
  function moveSnake(first, onArrive) {{
    markDots();
    if (first) {{ setLen(0); placeFood(); return; }}
    animateLen((PLAN || {{ len: TOTAL }}).len, onArrive, function () {{
      if (RETRACT) {{ truncate(RETRACT.idx); RETRACT = null; }}
      placeFood(); eatAt(P);
    }});
  }}

  function hl(h) {{
    var u = D.fuentes[h[1]] || [];
    var a = u.map(function (x, k) {{
      return '<a class="src" href="' + esc(x) + '" target="_blank" rel="noopener" title="' + esc(x) + '" aria-label="Fuente' + (u.length > 1 ? ' ' + (k + 1) : '') + '">↗</a>';
    }}).join(" ");
    return '<li><span class="hd">' + esc(h[0]) + '</span><span>' + esc(h[1]) + (a ? ' ' + a : '') + '</span></li>';
  }}
  function sub(t, cls) {{ return '<h4 class="sub' + (cls ? " " + cls : "") + '">' + t + '</h4>'; }}
  function howBlock(x, who) {{
    return '<dl class="how"><dt>Con Claude</dt><dd>' + esc(x.claude) + '</dd>' +
      '<dt>' + who + '</dt><dd>' + esc(x.equipo || x.agente) + '</dd>' +
      ((x.tools || []).length ? '<dt>Herramientas</dt><dd>' + esc(x.tools.join(", ")) + '</dd>' : '') + '</dl>';
  }}
  function extraHTML(i) {{ return exHTML(D.extra[String(i)]); }}
  function exHTML(x) {{
    if (!x) return "";
    if (x.kind === "diagram") {{
      return '<figure class="xdiag"><figcaption>' + esc(x.name) + '</figcaption><div class="flow-h">' +
        x.nodes.map(function (n, k) {{ return (k ? '<span class="arr">→</span>' : '') + '<span class="fn">' + esc(n) + '</span>'; }}).join("") + '</div></figure>';
    }}
    return '<figure class="xfile"><figcaption>' + esc(x.name) + '</figcaption><pre>' + esc(x.body) + '</pre></figure>';
  }}
  function advBand(i, d, secHTML) {{
    var x = D.advx[String(i)] || {{}};
    var hitos = d.hitos.map(hl).join("");
    return '<div class="sslide">' +
      '<header class="stitle"><span class="num">Paso ' + i + '</span><h2>' + esc(d.t) + '</h2><span class="when">' + esc(d.when) + '</span></header>' +
      '<div class="sgrid"><div class="smain">' +
        '<p class="lead">' + esc(d.lead) + '</p>' +
        '<div class="asec">' + sub("En la práctica") + '<p class="txt">' + esc(d.ej) + '</p></div>' +
        '<div class="asec">' + sub("Cómo se ve") + '<div class="seegrid"><pre class="snip">' + esc(x.ve || "") + '</pre>' + extraHTML(i) + '</div></div>' +
        '<div class="asec">' + sub("Cómo aplicarlo") + howBlock(x, "En tu equipo") + '</div>' +
        '<div class="asec">' + sub("Llévate esto") + '<ul class="take">' + li(d.lleva) + '</ul></div>' +
        '<div class="asec">' + sub("Error común", "warn") + '<p class="txt">' + esc(d.err) + '</p></div>' +
        (secHTML || '') + '</div>' +
        '<aside class="tl">' + (hitos ? sub("Hitos") + '<ol>' + hitos + '</ol>' : '') +
          sub("Cómo saber si funciona") + '<p class="txt muted">' + esc(d.medir.join(" ")) + '</p>' +
          sub("El cuello salta a", "crit") + '<p class="txt"><b class="nk">' + esc(d.neck) + '.</b> ' + esc(d.why) + '</p>' +
        '</aside>' +
      '</div></div>';
  }}
  function tplHTML(id) {{
    var t = document.getElementById(id);
    return t ? t.innerHTML : "";
  }}
  function secSlide(p, d) {{
    var i = p.i, step = D.detail[String(i)];
    var mine = d.sec.filter(function (s) {{ return s.id === p.t || (s.rel === "habilita" && p.n === 0); }});
    var sections = mine.map(function (s) {{
      var x = D.secx[s.id] || {{}};
      var head = esc(s.n) + ' <span class="badge b-' + s.st + '">' + s.stl + '</span>' +
        (s.rel === "habilita" ? ' <span class="relx">habilita este paso · explicado en el paso 3</span>' : '');
      if (s.rel === "habilita") return '<div class="ssec">' + sub(head) + '<p class="txt">' + esc(s.d) + '</p></div>';
      return '<div class="ssec">' + sub(head) +
        '<div class="ssgrid"><div><div class="mlbl">Cómo se ve</div><p class="txt">' + esc(x.ve || s.d) + '</p>' + exHTML(D.secex[s.id]) + tplHTML("d-" + s.id) + '</div>' +
        '<div>' + (x.claude ? howBlock(x, "En tu agente") : '') +
          (x.lleva ? '<div class="mlbl gap">Llévate esto</div><ul class="take">' + li(x.lleva) + '</ul>' : '') +
          (x.err ? '<div class="mlbl gap warn">Error común</div><p class="txt">' + esc(x.err) + '</p>' : '') +
          (x.medir ? '<div class="mlbl gap">Cómo saber si funciona</div><p class="txt muted">' + esc(x.medir) + '</p>' : '') +
        '</div></div></div>';
    }}).join("");
    var aside = mine.filter(function (s) {{ return s.rel !== "habilita" && D.sechitos[s.id]; }}).map(function (s) {{
      return '<div class="tlg"><div class="tlname">' + esc(s.n) + '</div><ol>' +
        D.sechitos[s.id].map(hl).join("") +
        '</ol></div>';
    }}).join("");
    return '<div class="sslide secslide">' +
      '<header class="stitle"><span class="num">Paso ' + i + ' · Seguridad' + (p.c > 1 ? ' · ' + (p.n + 1) + ' de ' + p.c : '') + '</span><h2>' +
        esc((D.secx[p.t] && d.sec.filter(function (s) {{ return s.id === p.t; }})[0] || {{}}).n || "") + '</h2>' +
        '<span class="when">llega con: ' + esc(step.t) + '</span></header>' +
      '<div class="sgrid"><div class="smain"><p class="lead">' + esc(d.seg) + '</p>' + sections + '</div>' +
      '<aside class="tl">' + sub("Hitos") + aside + '</aside></div></div>';
  }}
  function faqHTML(list) {{
    return '<div class="faq">' + list.map(function (q) {{ return sub(esc(q[0])) + '<p class="txt">' + esc(q[1]) + '</p>'; }}).join("") + '</div>';
  }}
  function supSlide(kind, i) {{
    var step = D.detail[String(i)];
    if (kind === "s") {{
      return '<div class="sslide supslide secsup"><header class="stitle"><span class="num">Paso ' + i + ' · Seguridad · Preguntas</span><h2>' +
        esc((D.secnames[i] || []).join(" · ")) + '</h2><span class="when">↑ para volver</span></header>' + faqHTML(D.sups[String(i)]) + '</div>';
    }}
    var x = D.supa[String(i)];
    if (!x.t) {{
      return '<div class="sslide supslide"><header class="stitle"><span class="num">Paso ' + i + ' · Preguntas</span><h2>' + esc(step.t) +
        '</h2><span class="when">↓ para volver</span></header>' + faqHTML(x.faq) + '</div>';
    }}
    var hitos = x.hitos.map(hl).join("");
    return '<div class="sslide supslide"><header class="stitle"><span class="num">Paso ' + i + ' · Extra</span><h2>' + esc(x.t) +
      '</h2><span class="when">↓ para volver</span></header>' +
      '<div class="sgrid"><div class="smain"><p class="lead">' + esc(x.lead) + '</p>' +
        '<div class="asec">' + sub("Cómo se ve") + '<div class="seegrid"><pre class="snip">' + esc(x.ve) + '</pre>' + exHTML(x.ex) + '</div></div>' +
        '<div class="asec">' + sub("Cómo aplicarlo") + howBlock(x.how, "En tu equipo") + '</div>' +
        '<div class="asec">' + sub("Llévate esto") + '<ul class="take">' + li(x.lleva) + '</ul></div>' +
        '<div class="asec">' + sub("Error común", "warn") + '<p class="txt">' + esc(x.err) + '</p></div>' +
      '</div><aside class="tl">' + sub("Hitos") + '<ol>' + hitos + '</ol>' + sub("Preguntas") +
        x.faq.map(function (q) {{ return '<p class="txt"><b>' + esc(q[0]) + '</b> ' + esc(q[1]) + '</p>'; }}).join('<br>') +
      '</aside></div></div>';
  }}
  function showStage(html) {{
    var st = document.getElementById("stage");
    clearTimeout(SWAP);
    if (FIRST || REDUCED) {{ st.innerHTML = html; st.classList.remove("fading"); return; }}
    st.classList.add("fading");
    SWAP = setTimeout(function () {{ st.innerHTML = html; st.classList.remove("fading"); updateBoard(); }}, 220);
  }}
  function enterSup(kind) {{
    if (SUP || !supAvail(kind)) return;
    settle();
    SUP = kind;
    var p = POS[P], key = kind + p.i;
    var xy = D.nodes["x" + key];
    if (STACK[STACK.length - 1].key !== key) extendTo("x" + key, key);
    var ii = p.i;
    animateLen(TOTAL, null, function () {{ eatAt(P); eatExtra(kind, ii, xy); placeFood(); }});
    showStage(supSlide(kind, p.i));
    document.getElementById("pos").textContent = "Paso " + p.i + (kind === "a" ? (D.supa[String(p.i)].t ? " · extra" : " · preguntas") : " · seguridad · preguntas");
    markSup();
  }}
  function leaveSup() {{
    if (!SUP) return;
    SUP = null;
    render(true);
  }}
  var SHOWN = null, SWAP = 0;
  function slideHTML(p) {{
    if (p.k === "portada") {{
      return '<div class="cover"><div class="k">BarCamp</div><h1>AI Platform Engineering</h1><h2 class="csub">El blocker eres tú</h2>' +
        '<p>Cada vez que automatizamos un paso, el cuello de botella salta al siguiente. Y cada avance trae su problema de seguridad.</p>' +
        '<div class="go">▶ o flecha derecha para empezar</div></div>';
    }}
    if (p.k === "mapa") return '<div class="board" id="board"><div><span class="bk">Puntaje</span><b class="bs">0</b></div>' +
      '<div><span class="bk">Extras explorados</span><b class="bx">0</b></div><div><span class="bk">Récord en este navegador</span><b class="br">0</b></div>' +
      '<div class="bl"></div><button type="button" class="again" id="b-again">Jugar de nuevo</button></div>' + document.getElementById("t-map").innerHTML;
    if (p.k === "glos") {{
      var g = D.glos[String(p.i)];
      return '<div class="sslide glosslide"><header class="stitle"><span class="num">Antes de seguir</span><h2>' + esc(g.t) + '</h2>' +
        '<span class="when">vocabulario para los pasos que siguen</span></header><dl class="glos">' +
        g.items.map(function (t) {{ return '<div><dt>' + esc(t[0]) + '</dt><dd>' + esc(t[1]) + '</dd></div>'; }}).join("") + '</dl></div>';
    }}
    var d = D.detail[String(p.i)];
    if (p.k === "hoy") {{
      var falta = d.sec.map(function (s) {{
        return '<div class="segi"><div class="h"><span class="badge b-' + s.st + '">' + s.stl + '</span>' + esc(s.n) + '</div><p>' + esc(s.d) + '</p></div>';
      }}).join("");
      return '<div class="hoyslide"><div class="lbl">Hoy · las dos líneas se juntan</div><h2>El cuello → atención humana</h2>' +
        '<p class="lead">' + esc(d.lead) + '</p>' +
        '<div class="cols" style="margin-top:16px"><div class="take"><div class="lbl">Llévate esto</div><ul>' + li(d.lleva) + '</ul></div>' +
        '<div style="grid-column:span 2"><div class="lbl">Lo que falta, desde la pista de seguridad</div><div class="secitems">' + falta + '</div></div></div>' +
        '<div class="seegrid" style="margin-top:14px"><div class="err"><div class="lbl">Error común</div><p>' + esc(d.err) + '</p></div>' + extraHTML(p.i) + '</div></div>';
    }}
    return p.k === "seg" ? secSlide(p, d) : advBand(p.i, d, "");
  }}
  function render(back) {{
    var p = POS[P], arrive = null;
    showStage(slideHTML(p));
    SHOWN = {{ k: p.k, i: p.i }};
    var label = p.k === "portada" ? "Portada" : p.k === "mapa" ? "Mapa completo" : p.k === "hoy" ? "Hoy" : p.k === "glos" ? "Vocabulario" :
      "Paso " + p.i + " de " + (D.pos.filter(function (q) {{ return q.k === "avance"; }}).length) + (p.k === "seg" ? " · seguridad" + (p.c > 1 ? " " + (p.n + 1) + "/" + p.c : "") : "");
    document.getElementById("pos").textContent = label;
    document.getElementById("b-prev").disabled = P === 0;
    document.getElementById("b-next").disabled = P === LAST;
    if (!back) moveSnake(FIRST, arrive);
    FIRST = false;
    markSup();
  }}
  function go(k) {{
    k = Math.min(LAST, Math.max(0, k));
    settle();
    SUP = null; PLAN = null;
    // Como en Snake, nunca hay reversa: también para volver, la cabeza avanza hasta el nodo.
    // Solo la portada reinicia la serpiente.
    if (k === 0 && P !== 0) {{ resetTrail(); setLen(0); PLAN = {{ len: 0 }}; }}
    else if (k !== P) {{ extendTo(POS[k].node, "p" + k); PLAN = {{ len: TOTAL }}; }}
    else PLAN = {{ len: CUR }};
    P = k; render();
  }}
  document.getElementById("b-prev").addEventListener("click", function () {{ go(P - 1); }});
  document.getElementById("b-next").addEventListener("click", function () {{ go(P + 1); }});
  document.querySelectorAll(".mdot").forEach(function (m) {{
    function pick() {{ go(+m.getAttribute("data-p")); }}
    m.addEventListener("click", pick);
    m.addEventListener("keydown", function (ev) {{ if (ev.key === "Enter" || ev.key === " ") {{ ev.preventDefault(); pick(); }} }});
  }});
  document.addEventListener("keydown", function (ev) {{
    if (ev.target && ev.target.closest && ev.target.closest(".mdot,.msup")) return;
    if (DIRS[ev.key]) {{ ev.preventDefault(); var o = options()[ev.key]; if (o) {{ NEXTDIR = DIRS[ev.key]; moveTo(o); }} }}
    else if (ev.key === "PageDown" || ev.key === " ") {{ ev.preventDefault(); go(P + 1); }}
    else if (ev.key === "PageUp") {{ ev.preventDefault(); go(P - 1); }}
    else if (ev.key === "Home") {{ go(0); }} else if (ev.key === "End") {{ go(LAST); }}
  }});
  document.getElementById("b-sup").addEventListener("click", function () {{
    if (SUP) leaveSup(); else if (supAvail("a")) enterSup("a"); else enterSup("s");
  }});
  document.querySelectorAll(".msup").forEach(function (m) {{
    function pick() {{
      var k = m.getAttribute("data-sup"), i = +m.getAttribute("data-i");
      if (SUP === k && POS[P].i === i) {{ leaveSup(); return; }}
      var target = -1;
      POS.forEach(function (q, j) {{ if (q.i === i && q.k === (k === "a" ? "avance" : "seg") && (target < 0 || k === "s")) target = j; }});
      if (target < 0) return;
      if (target !== P || SUP) go(target);
      setTimeout(function () {{ enterSup(k); }}, target !== P ? 900 : 0);
    }}
    m.addEventListener("click", pick);
    m.addEventListener("keydown", function (ev) {{ if (ev.key === "Enter" || ev.key === " ") {{ ev.preventDefault(); ev.stopPropagation(); pick(); }} }});
  }});
  document.getElementById("stage").addEventListener("click", function (ev) {{
    if (ev.target && ev.target.id === "b-again") restart();
  }});
  var FIRST = true;
  initSnake();
  requestAnimationFrame(tick);
  render();
}})();
</script>
"""

(HERE / "cremallera-grafo.html").write_text('<meta charset="utf-8">\n' + page)  # el prototipo se abre suelto, sin build.py
print(len(page), "posiciones:", len(POS))
