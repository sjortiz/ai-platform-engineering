"""Genera cremallera.html como presentación: minimapa con la serpiente como índice,
una slide por posición (avance y, si aplica, su seguridad) y el mapa completo al final."""
import html
import json
from pathlib import Path

from detalle import SECX, ADVX, EXTRA, SECHITOS, SECEX, GLOS, SUPA, SUPS
from fuentes import FUENTES
import cronologico2 as P2
import zip2  # datos, detalle y el SVG del mapa completo (zip2 escribe su propia versión; la pisamos abajo)

HERE = Path(__file__).parent
e = html.escape
N = len(zip2.STEPS)
SEC_AT = sorted({s["at"] for s in zip2.SEC})

# Posiciones de la serpiente: avance de cada paso y, si el paso trae seguridad, una parada abajo.
POS = [dict(k="portada", cc=0)]
for ci in range(len(P2.CAPS)):
    POS.append(dict(k="cap", c=ci, cc=ci))
    items = [("a", i) for i, c in P2.step_cap.items() if c == ci] + [("s", x["id"]) for x in zip2.SEC if P2.sec_cap.get(x["id"]) == ci]
    items.sort(key=lambda it: P2.pos[f"{it[0]}{it[1]}"])
    for kind, v in items:
        if kind == "a":
            if v in GLOS:
                POS.append(dict(k="glos", i=v, cc=ci))
            POS.append(dict(k="avance", i=v, cc=ci))
        else:
            sx = next(x for x in zip2.SEC if x["id"] == v)
            tops = [x["id"] for x in zip2.SEC if x["at"] == sx["at"]]
            POS.append(dict(k="seg", i=sx["at"], t=v, n=tops.index(v), c=len(tops), cc=ci))
POS.append(dict(k="hoy", i=N + 1, cc=len(P2.CAPS) - 1))
POS.append(dict(k="mapa", i=N + 2, cc=len(P2.CAPS) - 1))

# Minimapa
MW, MH = 1400, 180
MX0, MXN, MXHOY = 70, 1190, 1336
TLY = 16
MYA, MYT, MYB, MYZ = 44, 84, 128, 166
MYH = (MYT + MYB) // 2


NCAP = len(P2.CAPS)
# Separación por par de paradas vecinas: más espacio si quedan en la misma fila o cambian de capítulo.
SEQ = [q for q in POS if q["k"] not in ("portada", "hoy", "mapa")]
row = lambda q: "s" if q["k"] == "seg" else "a"
gaps = [(1.0 if row(a) == row(b) else .55) + (.35 if b["k"] == "cap" else 0) for a, b in zip(SEQ, SEQ[1:])]
unit = (MXN - MX0 + 30) / (sum(gaps) + 1)
x = MX0 - 15 + unit / 2
for k, q in enumerate(SEQ):
    x += unit * gaps[k - 1] if k else 0
    q["sx"] = round(x, 1)
CAPX = [MX0 - 20] + [round(q["sx"] - unit * .55, 1) for q in SEQ if q["k"] == "cap"][1:] + [MXN + 20]

def coord(p):
    if p["k"] == "portada":
        return [MX0 - 46, MYT]
    if p["k"] in ("hoy", "mapa"):
        return [MXHOY - 16, MYH]
    return [p["sx"], MYB if p["k"] == "seg" else MYT]


for p in POS:
    p["xy"] = coord(p)

mini = [
    f'<path class="mrail" d="M{MX0 - 46},{MYT} H{MXN + 40} C{MXN + 90},{MYT} {MXHOY - 60},{MYH} {MXHOY - 16},{MYH}"/>',
    f'<path class="mrail" d="M{MX0 - 46},{MYB} H{MXN + 40} C{MXN + 90},{MYB} {MXHOY - 60},{MYH} {MXHOY - 16},{MYH}"/>',
    f'<path class="mrail sup" d="M{MX0 - 46},{MYA} H{MXN + 20}"/>',
    f'<path class="mrail sup" d="M{MX0 - 46},{MYZ} H{MXN + 20}"/>',
    f'<text class="mlab" x="{MX0 - 46}" y="{MYA - 5}">extras ↑</text>',
    f'<text class="mlab" x="{MX0 - 46}" y="{MYZ + 12}">preguntas de seguridad ↓</text>',
]
STEPX = {q["i"]: q["xy"][0] for q in POS if q["k"] == "avance"}
SUPADX = SUPSDX = round((CAPX[-1] - CAPX[0]) / (len(POS) + 4) * .45, 1)
for ci in range(NCAP):
    mini.append(f'<g class="tlcap" data-cc="{ci}"><path class="tltick" d="M{CAPX[ci]},{TLY - 6} V{TLY + 6}"/>'
                f'<text class="tllab" x="{(CAPX[ci] + CAPX[ci + 1]) / 2}" y="{TLY - 4}" text-anchor="middle">{e(P2.CAPS[ci]["k"])}</text>'
                f'<path class="tlseg" d="M{CAPX[ci] + 4},{TLY} H{CAPX[ci + 1] - 4}"/></g>')
mini.insert(0, f'<path class="tlline" d="M{CAPX[0]},{TLY} H{CAPX[-1]}"/>')
for i in SUPA:
    x = round(STEPX[i] + SUPADX, 1)
    big = " big" if SUPA[i].get("t") else ""
    mini.append(f'<g class="msup{big}" data-sup="a" data-i="{i}" tabindex="0" role="button" aria-label="Extra del paso {i}">'
                f'<rect class="hit" x="{x - 12}" y="{MYA - 12}" width="24" height="24"/>'
                f'<rect class="sq" x="{x - 5}" y="{MYA - 5}" width="10" height="10" rx="2"/></g>')
for i in SUPS:
    x = round([q for q in POS if q["k"] == "seg" and q["i"] == i][-1]["xy"][0] + SUPSDX, 1)
    mini.append(f'<g class="msup" data-sup="s" data-i="{i}" tabindex="0" role="button" aria-label="Preguntas de seguridad del paso {i}">'
                f'<rect class="hit" x="{x - 12}" y="{MYZ - 12}" width="24" height="24"/>'
                f'<rect class="sq" x="{x - 5}" y="{MYZ - 5}" width="10" height="10" rx="2"/></g>')
for idx, p in enumerate(POS):
    if p["k"] in ("portada", "mapa"):
        continue
    x, y = p["xy"]
    if p["k"] == "hoy":
        mini.append(f'<g class="mdot hoy" data-p="{idx}" tabindex="0" role="button" aria-label="Hoy">'
                    f'<rect x="{x - 4}" y="{y - 11}" width="44" height="22" rx="11"/><text x="{x + 18}" y="{y + 4}" text-anchor="middle">Hoy</text></g>')
        continue
    if p["k"] == "cap":
        mini.append(f'<g class="mdot capd" data-p="{idx}" tabindex="0" role="button" aria-label="Capítulo {e(P2.CAPS[p["c"]]["k"])}">'
                    f'<rect class="hit" x="{x - 14}" y="{y - 14}" width="28" height="28"/>'
                    f'<rect class="gd" x="{x - 6}" y="{y - 6}" width="12" height="12" rx="2"/></g>')
        continue
    if p["k"] == "glos":
        mini.append(f'<g class="mdot glos" data-p="{idx}" tabindex="0" role="button" aria-label="Vocabulario">'
                    f'<rect class="hit" x="{x - 14}" y="{y - 14}" width="28" height="28"/>'
                    f'<rect class="gd" x="{x - 5}" y="{y - 5}" width="10" height="10" transform="rotate(45 {x} {y})"/></g>')
        continue
    label = f'Paso {p["i"]}' + (" · seguridad" if p["k"] == "seg" else "")
    num = f'<text class="mnum" x="{x}" y="{MYT - 14}" text-anchor="middle">{p["i"]}</text>' if p["k"] == "avance" else ""
    mini.append(f'<g class="mdot {p["k"]}" data-p="{idx}" tabindex="0" role="button" aria-label="{label}">'
                f'<rect class="hit" x="{x - 18}" y="{y - 30 if p["k"] == "avance" else y - 14}" width="36" height="{44 if p["k"] == "avance" else 30}"/>'
                f'{num}<circle cx="{x}" cy="{y}" r="6.5"/></g>')

mini.append('<g id="msnake"></g>')
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

DATA = dict(pos=[dict(k=p["k"], i=p.get("i"), t=p.get("t"), n=p.get("n", 0), c=p.get("c", 1), cc=p["cc"], xy=p["xy"]) for p in POS],
            caps=[dict(k=c["k"], titulo=c["titulo"], lead=c["lead"], neck=c["neck"], why=c["why"]) for c in P2.CAPS],
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
            mya=MYA, myz=MYZ, supadx=SUPADX, supsdx=SUPSDX)

css = (HERE / "master.css").read_text()

page = f"""<title>AI Platform Engineering</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600;650;700&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>
{css}
  /* Presentación: barra con título y controles, minimapa-índice, y una slide que ocupa el resto de la pantalla. */
  html{{font-size:17.6px}}
  html,body{{height:100%}}
  /* La barra y el minimapa no se encogen cuando la slide es larga, y la barra de scroll no cambia el ancho. */
  html{{scrollbar-gutter:stable}}
  .bar,.minibox{{flex:none}}
  .stage[data-page="1"] [data-pg]:not([data-pg="1"]),.stage[data-page="2"] [data-pg]:not([data-pg="2"]),
  .stage[data-page="3"] [data-pg]:not([data-pg="3"]){{display:none !important}}
  .stage[data-page] .stitle .num::after,.stage[data-page] .hoyslide > .lbl::after{{letter-spacing:.1em}}
  .stage[data-np="2"][data-page="1"] .stitle .num::after,.stage[data-np="2"][data-page="1"] .hoyslide > .lbl::after{{content:"  ● ○"}}
  .stage[data-np="2"][data-page="2"] .stitle .num::after,.stage[data-np="2"][data-page="2"] .hoyslide > .lbl::after{{content:"  ○ ●"}}
  .stage[data-np="3"][data-page="1"] .stitle .num::after{{content:"  ● ○ ○"}}
  .stage[data-np="3"][data-page="2"] .stitle .num::after{{content:"  ○ ● ○"}}
  .stage[data-np="3"][data-page="3"] .stitle .num::after{{content:"  ○ ○ ●"}}
  .stage:not([data-page="1"]) .secslide .sgrid{{grid-template-columns:minmax(0,1fr)}}
  .xbig{{display:flex;justify-content:center;padding-top:6px}}
  .xbig .xdiag{{width:min(100%,640px)}}
  /* El botón de apoyo ocupa siempre el mismo ancho (aunque esté oculto): la barra no cambia de alto según la parada. */
  .bar .supbtn{{width:15em;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
  .bar .supbtn[hidden]{{display:inline-block !important;visibility:hidden}}
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
  .mini{{display:block;width:100%;max-width:1240px;max-height:110px;margin:0 auto;height:auto}}
  .mrail{{fill:none;stroke:var(--line-2);stroke-width:2.5;stroke-linecap:round}}
  .tlline{{stroke:var(--line-2);stroke-width:1.5}}
  .tltick{{stroke:var(--faint);stroke-width:1.5}}
  .tlseg{{stroke:transparent;stroke-width:4;stroke-linecap:round;transition:stroke .4s}}
  .tlcap.done .tlseg{{stroke:var(--line-2)}}
  .tlcap.cur .tlseg{{stroke:var(--crit)}}
  .tllab{{font:600 11px var(--display);fill:var(--faint)}}
  .tlcap.cur .tllab{{fill:var(--crit)}} .tlcap.done .tllab{{fill:var(--muted)}}
  .mdot.capd .gd{{fill:var(--bg);stroke:var(--crit);stroke-width:1.8}}
  .mdot.capd.done .gd{{opacity:0}}
  .capslide .stitle{{border-bottom-color:var(--crit)}}
  .capslide .stitle .num{{color:var(--crit)}}
  .caplead{{font-size:1.35rem;line-height:1.5;margin:18px 0 0;max-width:62ch}}
  .capneck{{margin-top:20px;padding:16px 18px;background:var(--crit-bg);border:1px solid var(--crit-line);border-radius:10px;max-width:62ch}}
  .capneck .l{{font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:var(--crit)}}
  .capneck .v{{font-family:var(--display);font-size:2rem;font-weight:600;color:var(--crit);line-height:1.15;margin:2px 0 4px}}
  .capneck p{{margin:0;font-size:1rem;max-width:none}}
  .capslide .chips{{display:flex;flex-wrap:wrap;gap:8px}}
  .capslide .chip{{border:1px solid var(--line-2);border-radius:8px;padding:5px 10px;font:inherit;font-size:.98rem;color:inherit;background:var(--bg);cursor:pointer}}
  .capslide .chip:hover{{border-color:var(--accent);background:var(--accent-soft)}}
  .capslide .chip:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
  .capslide .chip::after{{content:" →";color:var(--accent)}}
  .capslide .chip b{{font-family:var(--display);color:var(--accent);margin-right:6px}}
  .capslide .chip.s{{border-left:4px solid var(--med)}}
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
  .stage > .capslide,.stage > .supslide,.stage > .glosslide,.stage > .sslide,.stage > .cover,.stage > .hoyslide,.stage > .mapslide{{animation:slidein .5s cubic-bezier(.16,1,.3,1) both}}
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
  @media (prefers-reduced-motion:reduce){{*{{transition:none !important}}}}
  /* Móvil: título fuera de la barra (está en la portada), controles abajo al alcance del pulgar, minimapa desplazable. */
  @media (max-width:700px){{
    html{{font-size:16px}}
    .bar{{padding-block:8px}}
    .bar .ttl{{font-size:0;display:flex;align-items:center;flex-wrap:wrap;gap:8px}}
    .bar .ttl > span{{font-size:.68rem;margin-right:0}}
    .bar .mode{{margin-left:0}}
    .bar .mode a,.bar .mode span{{padding:7px 11px}}
    .nav{{position:fixed;left:0;right:0;bottom:0;z-index:30;justify-content:center;gap:8px;background:var(--bg);border-top:1px solid var(--line);
      box-shadow:0 -2px 12px rgb(0 0 0 / .08);padding:8px max(12px, env(safe-area-inset-right, 0px)) calc(8px + env(safe-area-inset-bottom, 0px)) max(12px, env(safe-area-inset-left, 0px))}}
    .nav button{{min-width:46px;min-height:44px;font-size:1rem}}
    .pos{{flex:1;width:auto;min-width:0;font-size:.72rem}}
    .score{{display:none}}
    .bar .supbtn{{width:auto;max-width:34vw;font-size:.8rem !important}}
    .bar .supbtn[hidden]{{display:none !important}}
    .minibox{{overflow-x:auto;overscroll-behavior-x:contain;scrollbar-width:none}}
    .minibox::-webkit-scrollbar{{display:none}}
    .mini{{width:860px;max-width:none;max-height:none}}
    .stage{{padding-bottom:calc(84px + env(safe-area-inset-bottom, 0px))}}
    .stitle h2,.mapslide h2{{font-size:1.65rem}}
    .stitle .when{{margin-left:0}}
    .hoyslide h2{{font-size:1.9rem}}
    .hoyslide .lead,.cover p{{font-size:1.12rem}}
    .bigquote{{font-size:1.3rem}}
    aside.tl{{border-left:0;padding-left:16px;border-top:1px solid var(--line-2);padding-top:10px}}
    aside.tl li::before{{left:-16px}}
    dl.how{{grid-template-columns:minmax(0,1fr)}}
    dl.how dt{{white-space:normal}}
    .faq .sub{{font-size:1.1rem}}
    .toasts{{left:12px;right:12px;bottom:calc(84px + env(safe-area-inset-bottom, 0px))}}
    .toast{{min-width:0}}
  }}
</style>
<div class="bar">
  <div class="ttl"><span>BarCamp</span>AI Platform Engineering — El blocker eres tú<nav class="mode" aria-label="Vista"><span aria-current="page">Por años</span><a href="espacio.html">Espacio</a></nav></div>
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
  var SUP = null, WIG, FX, HEADIN, SAMP = [], STEPS = 3, TRD = "", STACK = [], RETRACT = null, PLAN = null;
  function segD(a, b) {{
    if (a[0] === b[0] && a[1] === b[1]) return "";
    if (a[1] === b[1]) return " L" + b[0] + "," + b[1];
    var dx = Math.max(12, b[0] - a[0]) * .55;
    return " C" + (a[0] + dx) + "," + a[1] + " " + (b[0] - dx) + "," + b[1] + " " + b[0] + "," + b[1];
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
  function extend(xy, key) {{
    var s = segD(STACK[STACK.length - 1].xy, xy);
    if (s) setTrail(TRD + s);
    STACK.push({{ key: key, xy: xy, len: TOTAL, d: TRD }});
  }}
  function truncate(idx) {{ STACK = STACK.slice(0, idx + 1); setTrail(STACK[idx].d); }}
  function resetTrail() {{
    var xy = POS[0].xy;
    STACK = [{{ key: "p0", xy: xy, len: 0, d: "M" + xy[0] + "," + xy[1] }}];
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
  function wave(samp, upto, t, amp) {{
    var n = Math.min(samp.length - 1, Math.floor(upto / STEPS)), d = "";
    for (var i = 0; i <= n; i++) {{
      var s = i * STEPS, q = samp[i];
      var A = amp * Math.min(1, s / 24) * Math.min(1, Math.max(0, (upto - s) / 16));
      var o = A * Math.sin(s / 13 - t);
      d += (i ? " L" : "M") + (q[0] + q[2] * o).toFixed(1) + "," + (q[1] + q[3] * o).toFixed(1);
    }}
    return d || "M0,0";
  }}
  function drawBody(now) {{ WIG.setAttribute("d", CUR > 1 ? wave(SAMP, CUR, now / 170, REDUCED ? 0 : 1.2) : "M0,0"); }}
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
    b.title = b.textContent;
  }}
  var SCORE = 0, EATEN = {{}}, PTS = {{ avance: 10, seg: 10, glos: 5, hoy: 10, mapa: 10, extra: 20 }};
  function pop(xy, n) {{
    var t = el("text", {{ x: xy[0] + 10, y: xy[1] - 10, "class": "pop" }});
    t.textContent = "+" + n; SG.appendChild(t);
    setTimeout(function () {{ if (t.parentNode) t.parentNode.removeChild(t); }}, 950);
    var sc = document.getElementById("score");
    sc.textContent = SCORE + " pts"; sc.classList.remove("bump"); void sc.offsetWidth; sc.classList.add("bump");
  }}
  function eatUpTo(k) {{
    var gained = 0;
    for (var j = 1; j <= k; j++) {{
      if (EATEN["p" + j]) continue;
      EATEN["p" + j] = 1; gained += PTS[POS[j].k] || 10;
    }}
    if (gained) {{ SCORE += gained; pop(POS[k].xy, gained); burst(POS[k].xy, "s-" + POS[k].k); checkAch(); }}
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
    document.querySelectorAll(".mdot").forEach(function (m) {{
      var k = +m.getAttribute("data-p");
      m.classList.toggle("done", k <= P);
      m.classList.toggle("cur", k === P);
    }});
    if (first) {{ setLen(0); placeFood(); return; }}
    animateLen((PLAN || {{ len: TOTAL }}).len, onArrive, function () {{
      if (RETRACT) {{ truncate(RETRACT.idx); RETRACT = null; }}
      placeFood(); eatUpTo(P);
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
        '<div data-pg="1"><p class="lead">' + esc(d.lead) + '</p>' +
        '<div class="asec">' + sub("En la práctica") + '<p class="txt">' + esc(d.ej) + '</p></div>' +
        '<div class="asec">' + sub("Cómo se ve") + '<div class="seegrid"><pre class="snip">' + esc(x.ve || "") + '</pre>' + extraHTML(i) + '</div></div></div>' +
        '<div data-pg="2"><div class="asec">' + sub("Cómo aplicarlo") + howBlock(x, "En tu equipo") + '</div>' +
        '<div class="asec">' + sub("Llévate esto") + '<ul class="take">' + li(d.lleva) + '</ul></div>' +
        '<div class="asec">' + sub("Error común", "warn") + '<p class="txt">' + esc(d.err) + '</p></div></div>' +
        (secHTML || '') + '</div>' +
        '<aside class="tl"><div data-pg="1">' + (hitos ? sub("Hitos") + '<ol>' + hitos + '</ol>' : '') + '</div>' +
          '<div data-pg="2">' + sub("Cómo saber si funciona") + '<p class="txt muted">' + esc(d.medir.join(" ")) + '</p>' +
          sub("El cuello salta a", "crit") + '<p class="txt"><b class="nk">' + esc(d.neck) + '.</b> ' + esc(d.why) + '</p></div>' +
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
      if (s.rel === "habilita") return '<div class="ssec" data-pg="1">' + sub(head) + '<p class="txt">' + esc(s.d) + '</p></div>';
      var ex = exHTML(D.secex[s.id]), dg = tplHTML("d-" + s.id), last = dg ? "3" : "2";
      return '<div class="ssec">' + sub(head) +
        '<div class="ssgrid" data-pg="1"><div><div class="mlbl">Cómo se ve</div><p class="txt">' + esc(x.ve || s.d) + '</p></div><div>' + ex + '</div></div>' +
        (dg ? '<div class="xbig" data-pg="2">' + dg + '</div>' : '') +
        '<div class="ssgrid" data-pg="' + last + '"><div>' + (x.claude ? howBlock(x, "En tu agente") : '') +
          (x.lleva ? '<div class="mlbl gap">Llévate esto</div><ul class="take">' + li(x.lleva) + '</ul>' : '') + '</div>' +
        '<div>' + (x.err ? '<div class="mlbl warn">Error común</div><p class="txt">' + esc(x.err) + '</p>' : '') +
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
      '<div class="sgrid"><div class="smain"><p class="lead" data-pg="1">' + esc(d.seg) + '</p>' + sections + '</div>' +
      '<aside class="tl" data-pg="1">' + sub("Hitos") + aside + '</aside></div></div>';
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
      '<div class="sgrid"><div class="smain"><div data-pg="1"><p class="lead">' + esc(x.lead) + '</p>' +
        '<div class="asec">' + sub("Cómo se ve") + '<div class="seegrid"><pre class="snip">' + esc(x.ve) + '</pre>' + exHTML(x.ex) + '</div></div></div>' +
        '<div data-pg="2"><div class="asec">' + sub("Cómo aplicarlo") + howBlock(x.how, "En tu equipo") + '</div>' +
        '<div class="asec">' + sub("Llévate esto") + '<ul class="take">' + li(x.lleva) + '</ul></div>' +
        '<div class="asec">' + sub("Error común", "warn") + '<p class="txt">' + esc(x.err) + '</p></div></div>' +
      '</div><aside class="tl"><div data-pg="1">' + sub("Hitos") + '<ol>' + hitos + '</ol></div><div data-pg="2">' + sub("Preguntas") +
        x.faq.map(function (q) {{ return '<p class="txt"><b>' + esc(q[0]) + '</b> ' + esc(q[1]) + '</p>'; }}).join('<br>') +
      '</div></aside></div></div>';
  }}
  // Páginas: las slides largas traen bloques data-pg="1" y data-pg="2"; se ve una página a la vez.
  var PG = 0, NPG = 1, LANDLAST = false;
  function pageClass(st) {{
    if (NPG > 1) {{ st.setAttribute("data-page", PG + 1); st.setAttribute("data-np", NPG); }}
    else {{ st.removeAttribute("data-page"); st.removeAttribute("data-np"); }}
  }}
  function showStage(html) {{
    var st = document.getElementById("stage");
    clearTimeout(SWAP);
    NPG = html.indexOf('data-pg="3"') >= 0 ? 3 : html.indexOf('data-pg="2"') >= 0 ? 2 : 1;
    PG = LANDLAST ? NPG - 1 : 0; LANDLAST = false;
    if (FIRST || REDUCED) {{ st.innerHTML = html; pageClass(st); fitStage(); st.classList.remove("fading"); return; }}
    st.classList.add("fading");
    SWAP = setTimeout(function () {{ st.innerHTML = html; pageClass(st); fitStage(); st.classList.remove("fading"); updateBoard(); }}, 220);
  }}
  // Si una página igual no cabe en la pantalla (proyector de 720 px, el mapa completo), se achica lo justo.
  function fitStage() {{
    var kids = [].slice.call(document.getElementById("stage").children);
    if (!kids.length) return;
    kids.forEach(function (k) {{ k.style.zoom = ""; }});
    if (window.innerWidth <= 700) return;
    var top = kids[0].getBoundingClientRect().top, bottom = top;
    kids.forEach(function (k) {{
      [k].concat([].slice.call(k.querySelectorAll("*"))).forEach(function (e) {{ var r = e.getBoundingClientRect(); if (r.height) bottom = Math.max(bottom, r.bottom); }});
    }});
    var avail = window.innerHeight - top - 12, need = bottom - top;
    if (need > avail && need > 0) kids.forEach(function (k) {{ k.style.zoom = Math.max(.5, avail / need).toFixed(3); }});
  }}
  window.addEventListener("resize", fitStage);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitStage);
  function turnPage(k) {{
    var st = document.getElementById("stage");
    PG = k;
    if (typeof drawKeys === "function") drawKeys();
    if (REDUCED) {{ pageClass(st); fitStage(); return; }}
    clearTimeout(SWAP);
    st.classList.add("fading");
    SWAP = setTimeout(function () {{ pageClass(st); fitStage(); st.scrollTop = 0; st.classList.remove("fading"); }}, 180);
  }}
  // Siguiente / anterior: primero recorre las páginas de la slide y después cambia de parada.
  function nextPage() {{ if (PG < NPG - 1) {{ turnPage(PG + 1); return true; }} return false; }}
  function prevPage() {{ if (PG > 0) {{ turnPage(PG - 1); return true; }} return false; }}
  function enterSup(kind) {{
    if (SUP || !supAvail(kind)) return;
    settle();
    SUP = kind;
    var p = POS[P], key = kind + p.i;
    var xy = [Math.round((p.xy[0] + (kind === "a" ? D.supadx : D.supsdx)) * 10) / 10, kind === "a" ? D.mya : D.myz];
    if (STACK[STACK.length - 1].key !== key) extend(xy, key);
    var ii = p.i;
    animateLen(TOTAL, null, function () {{ eatUpTo(P); eatExtra(kind, ii, xy); placeFood(); }});
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
    if (p.k === "cap") {{
      var cp = D.caps[p.c];
      var en = D.pos.map(function (q, j) {{
        if (q.cc !== p.c || (q.k !== "avance" && q.k !== "seg")) return "";
        return q.k === "avance" ? '<button type="button" class="chip" data-go="' + j + '"><b>' + q.i + '</b>' + esc(D.detail[String(q.i)].t) + '</button>'
          : '<button type="button" class="chip s" data-go="' + j + '">' + esc(D.secx[q.t] ? (D.detail[String(q.i)].sec.filter(function (x) {{ return x.id === q.t; }})[0] || {{}}).n || q.t : q.t) + '</button>';
      }}).join("");
      return '<div class="sslide capslide"><header class="stitle"><span class="num">Capítulo ' + (p.c + 1) + ' de ' + D.caps.length + '</span><h2>' + esc(cp.k) + ' · ' + esc(cp.titulo) + '</h2></header>' +
        '<p class="caplead">' + esc(cp.lead) + '</p>' +
        '<div class="capneck"><div class="l">Al final de este periodo, el cuello de botella queda en</div><div class="v">' + esc(cp.neck) + '</div><p>' + esc(cp.why) + '</p></div>' +
        '<h4 class="sub">Lo que llega en este periodo</h4><div class="chips">' + en + '</div></div>';
    }}
    if (p.k === "glos") {{
      var g = D.glos[String(p.i)];
      return '<div class="sslide glosslide"><header class="stitle"><span class="num">Antes de seguir</span><h2>' + esc(g.t) + '</h2>' +
        '<span class="when">vocabulario para los pasos que siguen</span></header><dl class="glos">' +
        g.items.map(function (t, k) {{
          var pg = g.items.length > 4 ? (k < Math.ceil(g.items.length / 2) ? 1 : 2) : 1;
          return '<div data-pg="' + pg + '"><dt>' + esc(t[0]) + '</dt><dd>' + esc(t[1]) + '</dd></div>';
        }}).join("") + '</dl></div>';
    }}
    var d = D.detail[String(p.i)];
    if (p.k === "hoy") {{
      var falta = d.sec.map(function (s) {{
        return '<div class="segi"><div class="h"><span class="badge b-' + s.st + '">' + s.stl + '</span>' + esc(s.n) + '</div><p>' + esc(s.d) + '</p></div>';
      }}).join("");
      return '<div class="hoyslide"><div class="lbl">Hoy · las dos líneas se juntan</div><h2>El cuello → atención humana</h2>' +
        '<div data-pg="1"><p class="lead">' + esc(d.lead) + '</p>' +
        '<div class="seegrid" style="margin-top:16px"><div class="take"><div class="lbl">Llévate esto</div><ul>' + li(d.lleva) + '</ul></div>' +
        '<div class="err"><div class="lbl">Error común</div><p>' + esc(d.err) + '</p></div></div></div>' +
        '<div data-pg="2"><div class="lbl">Lo que falta, desde la pista de seguridad</div><div class="secitems">' + falta + '</div>' +
        '<div style="margin-top:14px">' + extraHTML(p.i) + '</div></div></div>';
    }}
    return p.k === "seg" ? secSlide(p, d) : advBand(p.i, d, "");
  }}
  function render(back) {{
    var p = POS[P], arrive = null;
    showStage(slideHTML(p));
    SHOWN = {{ k: p.k, i: p.i }};
    var label = p.k === "portada" ? "Portada" : p.k === "mapa" ? "Mapa completo" : p.k === "hoy" ? "Hoy" : p.k === "glos" ? "Vocabulario" : p.k === "cap" ? D.caps[p.cc].k :
      "Paso " + p.i + " de " + (D.pos.filter(function (q) {{ return q.k === "avance"; }}).length) + (p.k === "seg" ? " · seguridad" + (p.c > 1 ? " " + (p.n + 1) + "/" + p.c : "") : "");
    document.getElementById("pos").textContent = label;
    document.getElementById("b-prev").disabled = P === 0;
    document.getElementById("b-next").disabled = P === LAST;
    if (!back) moveSnake(FIRST, arrive);
    FIRST = false;
    markSup();
    document.querySelectorAll(".tlcap").forEach(function (g) {{ var c = +g.getAttribute("data-cc"); g.classList.toggle("cur", c === p.cc); g.classList.toggle("done", c < p.cc); }});
  }}
  function go(k) {{
    k = Math.min(LAST, Math.max(0, k));
    settle();
    SUP = null; PLAN = null;
    if (k > P) {{
      for (var j = P + 1; j <= k; j++) extend(POS[j].xy, "p" + j);
      PLAN = {{ len: TOTAL }};
    }} else if (k < P) {{
      var idx = -1;
      for (var q = STACK.length - 1; q >= 0; q--) if (STACK[q].key === "p" + k) {{ idx = q; break; }}
      if (idx >= 0) {{ RETRACT = {{ len: STACK[idx].len, idx: idx }}; PLAN = {{ len: STACK[idx].len }}; }}
      else {{ resetTrail(); for (var j2 = 1; j2 <= k; j2++) extend(POS[j2].xy, "p" + j2); setLen(TOTAL); PLAN = {{ len: TOTAL }}; }}
    }} else PLAN = {{ len: CUR }};
    P = k; render();
  }}
  document.getElementById("b-prev").addEventListener("click", function () {{ if (!prevPage()) {{ LANDLAST = P > 0; go(P - 1); }} }});
  document.getElementById("b-next").addEventListener("click", function () {{ if (!nextPage()) go(P + 1); }});
  // Móvil: deslizar sobre la slide = ▶ / ◀ (menos sobre contenido que se desplaza de lado).
  var TX = null;
  document.getElementById("stage").addEventListener("touchstart", function (ev) {{
    TX = ev.touches.length === 1 ? [ev.touches[0].clientX, ev.touches[0].clientY] : null;
  }}, {{ passive: true }});
  document.getElementById("stage").addEventListener("touchend", function (ev) {{
    if (!TX) return;
    var t = ev.changedTouches[0], dx = t.clientX - TX[0], dy = t.clientY - TX[1];
    TX = null;
    if (Math.abs(dx) < 60 || Math.abs(dx) < 1.5 * Math.abs(dy)) return;
    if (ev.target.closest && ev.target.closest(".amap-wrap,pre,.snip")) return;
    document.getElementById(dx < 0 ? "b-next" : "b-prev").click();
  }});
  // Móvil: el minimapa es más ancho que la pantalla y se desplaza para seguir la parada actual.
  var MB = document.querySelector(".minibox"), MBQ = 0;
  new MutationObserver(function () {{
    if (MBQ || MB.scrollWidth <= MB.clientWidth) return;
    MBQ = requestAnimationFrame(function () {{
      MBQ = 0;
      var c = MB.querySelector(".mdot.cur, .msup.cur");
      if (!c) return;
      var r = c.getBoundingClientRect(), b = MB.getBoundingClientRect();
      MB.scrollTo({{ left: MB.scrollLeft + r.left + r.width / 2 - b.left - b.width / 2, behavior: REDUCED ? "auto" : "smooth" }});
    }});
  }}).observe(MB, {{ subtree: true, attributes: true, attributeFilter: ["class"] }});
  document.querySelectorAll(".mdot").forEach(function (m) {{
    function pick() {{ go(+m.getAttribute("data-p")); }}
    m.addEventListener("click", pick);
    m.addEventListener("keydown", function (ev) {{ if (ev.key === "Enter" || ev.key === " ") {{ ev.preventDefault(); pick(); }} }});
  }});
  document.addEventListener("keydown", function (ev) {{
    if (ev.target && ev.target.closest && ev.target.closest(".mdot,.msup,[data-go]")) return;
    if (ev.key === "ArrowRight" || ev.key === "PageDown" || ev.key === " ") {{ ev.preventDefault(); if (!nextPage()) go(P + 1); }}
    else if (ev.key === "ArrowLeft" || ev.key === "PageUp") {{ ev.preventDefault(); if (!prevPage()) {{ LANDLAST = P > 0; go(P - 1); }} }}
    else if (ev.key === "Home") {{ go(0); }} else if (ev.key === "End") {{ go(LAST); }}
    else if (ev.key === "ArrowUp") {{ ev.preventDefault(); if (SUP === "s") leaveSup(); else enterSup("a"); }}
    else if (ev.key === "ArrowDown") {{ ev.preventDefault(); if (SUP === "a") leaveSup(); else enterSup("s"); }}
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
    var c = ev.target && ev.target.closest && ev.target.closest("[data-go]");
    if (c) go(+c.getAttribute("data-go"));
  }});
  var FIRST = true;
  initSnake();
  requestAnimationFrame(tick);
  render();
}})();
</script>
"""

(HERE / "cremallera-anos.html").write_text(page)
print(len(page), "posiciones:", len(POS))
