"""Prototipo: la misma historia contada por fechas. Cada hito se dibuja en una línea de tiempo
y, al seleccionarlo, se trazan los caminos hacia los pasos y temas de seguridad que afectó."""
import html
import json
import re
from pathlib import Path

import zip2
from detalle import INFO, SECHITOS, SUPA
from fuentes import FUENTES

HERE = Path(__file__).parent
e = html.escape
MESES = dict(ene=1, feb=2, mar=3, abr=4, may=5, jun=6, jul=7, ago=8, sep=9, oct=10, nov=11, dic=12)

# Hitos que afectaron a más de un paso o tema, además del suyo.
EXTRA_TARGETS = {
    "Function calling": [("a", 3)],
    "Model Context Protocol (MCP)": [("a", 7), ("s", "idn"), ("s", "mcp")],
    "Claude 3.5 Sonnet dispara los benchmarks": [("a", 4)],
    "ChatGPT": [("s", "inj")],
    "GPT-4": [("a", 3)],
    "Prompt caching": [("a", 8)],
    "Paper de LoRA": [("a", 10)],
    "QLoRA": [("a", 10)],
    "vLLM y PagedAttention": [("s", "dat")],
    "Llama 2 con licencia comercial": [("a", 12), ("a", 13)],
    "DeepSeek R1": [("a", 9), ("a", 11)],
    "Playwright MCP: un agente maneja el navegador": [("a", 6)],
    "GraphRAG": [("s", "rag")],
}


def fecha_t(f):
    f = f.replace("+", "").strip()
    f = re.split(r"[–-]", f)[0].strip() if not re.match(r"^[a-z]{3}–[a-z]{3}", f) else f
    m = re.match(r"^([a-z]{3}) (\d{4})$", f)
    if m:
        return int(m.group(2)) + (MESES[m.group(1)] - 1) / 12
    y = re.search(r"\d{4}", f)
    return int(y.group(0)) + 0.5


def uso_real(when):
    m = re.search(r"uso real (\d{4})", when)
    return int(m.group(1)) if m else 2015


# Recolectar hitos con sus destinos
raw = []
for i, v in INFO.items():
    if i > len(zip2.STEPS):
        continue
    for f, t in v["hitos"]:
        raw.append((f, t, [("a", i)]))
for sid, hs in SECHITOS.items():
    at = next(x["at"] for x in zip2.SEC if x["id"] == sid)
    for f, t in hs:
        raw.append((f, t, [("s", sid), ("a2", at)]))
for f, t in SUPA[5]["hitos"]:
    raw.append((f, t, [("a", 5)]))

merged = {}
for f, t, tg in raw:
    url = (FUENTES.get(t) or [""])[0]
    key = (fecha_t(f), url or t)
    if key in merged:
        for x in tg:
            if x not in merged[key]["tg"]:
                merged[key]["tg"].append(x)
        continue
    merged[key] = dict(f=f, t=t, url=url, tg=list(tg), tt=fecha_t(f))
for h in merged.values():
    for x in EXTRA_TARGETS.get(h["t"], []):
        if x not in h["tg"]:
            h["tg"].append(x)
H = sorted(merged.values(), key=lambda h: (h["tt"], h["t"]))

# Geometría
W, HGT = 1400, 600
YA, YT, YS = 92, 300, 514
X0, XN = 90, 1330
N = len(zip2.STEPS)
ax = [round(X0 + k * (XN - X0) / (N - 1), 1) for k in range(N)]
SEC = zip2.SEC
sx = {x["id"]: round(X0 + 40 + k * (XN - X0 - 80) / (len(SEC) - 1), 1) for k, x in enumerate(SEC)}


def tx(t):
    if t < 2019.5:
        return 70 + (max(t, 2004.5) - 2004.5) / 15 * 190
    return 260 + (min(t, 2026.5) - 2019.5) / 7 * 1080


slots = {}
for h in H:
    x = round(tx(h["tt"]), 1)
    k = round(x / 7)
    n = slots.get(k, 0)
    slots[k] = n + 1
    h["x"] = x
    h["y"] = YT - 11 * n

svg = []
# Ejes y rieles
svg.append(f'<path class="rail" d="M{X0 - 60},{YA} H{XN + 40}"/>')
svg.append(f'<path class="rail" d="M{X0 - 60},{YS} H{XN + 40}"/>')
svg.append(f'<path class="axis" d="M60,{YT} H{1350}"/>')
svg.append(f'<text class="rlbl" x="{X0 - 60}" y="{YA - 50}">AVANCE</text>')
svg.append(f'<text class="rlbl" x="{X0 - 60}" y="{YS + 50}">SEGURIDAD</text>')
svg.append(f'<text class="rlbl" x="60" y="{YT - 34}">TIEMPO</text>')
for y in [2005, 2010, 2015] + list(range(2020, 2027)):
    x = tx(y)
    svg.append(f'<path class="tick" d="M{x},{YT} V{YT + 8}"/><text class="year" x="{x}" y="{YT + 26}" text-anchor="middle">{y}</text>')
svg.append(f'<path class="gap" d="M{tx(2019.5)},{YT - 10} l-4,20 M{tx(2019.5) + 6},{YT - 10} l-4,20"/>')
svg.append(f'<rect class="era" x="{tx(2019.5) + 8}" y="{YT - 120}" width="{tx(2026.5) - tx(2019.5) - 8}" height="155" rx="8"/>')
svg.append('<g id="paths"></g>')
svg.append(f'<path id="playhead" class="playhead" d="M0,{YA - 30} V{YS + 30}"/>')


def box(cls, key, x, y, label, sub):
    lines = zip2.wrap(label, 13)
    ty = y - 7 * (len(lines) - 1) + 4
    return (f'<g class="node {cls}" id="n-{key}"><rect class="bx" x="{x - 44}" y="{y - 21}" width="88" height="42" rx="8"/>'
            f'<text class="bt" x="{x}" y="{ty}" text-anchor="middle">{zip2.tspans(lines, x, 14)}</text>'
            f'<text class="bs" x="{x}" y="{y + (36 if cls == "an" else -30)}" text-anchor="middle">{e(sub)}</text></g>')


for i, st in enumerate(zip2.STEPS, 1):
    svg.append(f'<text class="snum" x="{ax[i - 1]}" y="{YA - 28}" text-anchor="middle">{i}</text>')
    svg.append(box("an", f"a{i}", ax[i - 1], YA, st["n"], "uso real " + str(uso_real(st["when"]))))
for x in SEC:
    svg.append(box(f"sn st-{x['st']}", f"s{x['id']}", sx[x["id"]], YS, x["n"], zip2.ST[x["st"]].lower()))
for j, h in enumerate(H):
    kinds = {k for k, _ in h["tg"]}
    cls = "sec" if "s" in kinds and "a" not in kinds else "adv"
    svg.append(f'<circle class="hd {cls}" data-j="{j}" cx="{h["x"]}" cy="{h["y"]}" r="5"><title>{e(h["f"])} · {e(h["t"])}</title></circle>')

NODES = {f"a{i}": dict(x=ax[i - 1], y=YA, name=st["t"], short=st["n"], neck=st["neck"], real=uso_real(st["when"]), k="a")
         for i, st in enumerate(zip2.STEPS, 1)}
NODES.update({f"s{x['id']}": dict(x=sx[x["id"]], y=YS, name=x["n"], st=x["st"], stl=zip2.ST[x["st"]], k="s") for x in SEC})
DATA = dict(h=[dict(f=h["f"], t=h["t"], url=h["url"], tt=h["tt"], x=h["x"], y=h["y"],
                    tg=[("a" if k == "a2" else k) + str(v) for k, v in h["tg"]], sec=[k == "a2" for k, _ in h["tg"]]) for h in H],
            nodes=NODES, ya=YA, ys=YS)

css = (HERE / "master.css").read_text()
page = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mapa cronológico · prototipo</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600;650;700&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>
{css}
  html,body{{height:100%;margin:0}}
  body{{display:flex;flex-direction:column}}
  .bar{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 24px;border-bottom:1px solid var(--line)}}
  .bar .ttl{{font-family:var(--display);font-weight:600;font-size:1.05rem}}
  .bar .ttl span{{font-family:var(--sans);font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600;margin-right:10px}}
  .nav{{display:flex;align-items:center;gap:8px}}
  .nav button{{font:600 .9rem var(--sans);color:var(--accent);background:var(--accent-soft);border:1px solid var(--line-2);border-radius:8px;padding:5px 12px;cursor:pointer}}
  .nav button:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
  .pos{{font-family:var(--mono);font-size:.8rem;color:var(--muted);width:10em;text-align:center}}
  .wrapd{{background:var(--panel);border-bottom:1px solid var(--line);padding:6px 24px}}
  svg.map{{display:block;width:100%;max-width:1500px;margin:0 auto;height:auto}}
  .rail{{fill:none;stroke:var(--line-2);stroke-width:2.5}}
  .axis{{fill:none;stroke:var(--faint);stroke-width:1.5}}
  .tick{{stroke:var(--faint)}}
  .year{{font:600 11px var(--mono);fill:var(--muted)}}
  .gap{{stroke:var(--faint);stroke-width:1.5;fill:none}}
  .era{{fill:var(--accent-soft);opacity:.5}}
  .rlbl{{font:700 11px var(--sans);letter-spacing:.14em;fill:var(--accent)}}
  .snum{{font:600 12px var(--display);fill:var(--faint)}}
  .node .bx{{fill:var(--bg);stroke:var(--line-2);stroke-width:1.2;transition:fill .4s,stroke .4s}}
  .node .bt{{font:600 10.4px var(--sans);fill:var(--faint);transition:fill .4s}}
  .node .bs{{font:500 9.5px var(--mono);fill:var(--faint);opacity:0;transition:opacity .4s}}
  .node.ap .bt{{fill:var(--ink)}}
  .node.ap .bx{{stroke:var(--accent)}}
  .node.ap .bs{{opacity:1}}
  .node.an.re .bx{{fill:var(--accent-soft);stroke:var(--accent);stroke-width:2}}
  .node.sn.ap .bx{{stroke:var(--sc);stroke-width:2;fill:var(--panel-2)}}
  .st-ok{{--sc:var(--ok)}} .st-med{{--sc:var(--med)}} .st-crit{{--sc:var(--crit)}}
  .node.hit .bx{{stroke-width:3}}
  .hd{{fill:var(--bg);stroke:var(--accent);stroke-width:1.6;cursor:pointer;transition:fill .3s,r .3s}}
  .hd.sec{{stroke:var(--med)}}
  .hd.past{{fill:var(--accent)}} .hd.sec.past{{fill:var(--med)}}
  .hd.future{{opacity:.35}}
  .hd.cur{{r:9;stroke-width:3;fill:var(--bg)}}
  .playhead{{stroke:var(--crit);stroke-width:1.5;stroke-dasharray:4 4;transition:transform .5s cubic-bezier(.16,1,.3,1)}}
  .pth{{fill:none;stroke-width:2.2;stroke-linecap:round}}
  .pth.a{{stroke:var(--accent)}} .pth.s{{stroke:var(--med)}} .pth.dim{{stroke-dasharray:5 5;opacity:.6}}
  .pth.draw{{animation:draw .7s cubic-bezier(.16,1,.3,1) both}}
  @keyframes draw{{from{{stroke-dashoffset:var(--L)}}}}
  .panel{{flex:1;display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:40px;padding:18px 24px;max-width:1500px;width:100%;margin:0 auto;box-sizing:border-box}}
  .date{{font-family:var(--mono);font-size:1rem;color:var(--crit);font-weight:600}}
  .panel h2{{font-family:var(--display);font-weight:600;font-size:2.2rem;line-height:1.1;margin:4px 0 10px}}
  .panel h2 a{{font-size:1rem;text-decoration:none;color:var(--accent);vertical-align:middle}}
  .lbl{{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:var(--accent);margin:14px 0 6px}}
  .chips{{display:flex;flex-wrap:wrap;gap:8px}}
  .chip{{border:1px solid var(--line-2);border-radius:8px;padding:6px 10px;font-size:.95rem;background:var(--bg)}}
  .chip b{{font-family:var(--display);color:var(--accent);margin-right:6px}}
  .chip.s{{border-left:4px solid var(--sc)}}
  .chip.dim{{opacity:.7;border-style:dashed}}
  .stats{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}
  .stat{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px}}
  .stat .n{{font-family:var(--display);font-size:1.8rem;font-weight:600}}
  .stat .l{{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}}
  .neck{{margin-top:14px;padding:12px 14px;background:var(--crit-bg);border:1px solid var(--crit-line);border-radius:10px}}
  .neck .l{{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:var(--crit)}}
  .neck .v{{font-family:var(--display);font-size:1.4rem;font-weight:600;color:var(--crit)}}
  .note{{font-size:.85rem;color:var(--muted);margin-top:10px}}
</style>
</head>
<body>
<div class="bar">
  <div class="ttl"><span>Prototipo</span>Mapa cronológico · la misma historia, por fechas</div>
  <div class="nav">
    <button type="button" id="play">▶ reproducir</button>
    <button type="button" id="prev" aria-label="Hito anterior">◀</button>
    <span class="pos" id="pos"></span>
    <button type="button" id="next" aria-label="Hito siguiente">▶</button>
  </div>
</div>
<div class="wrapd"><svg class="map" viewBox="0 0 {W} {HGT}" role="img" aria-label="Línea de tiempo de hitos conectada a los pasos y temas de seguridad">{''.join(svg)}</svg></div>
<div class="panel" id="panel"></div>
<script>
(function () {{
  var D = {json.dumps(DATA, ensure_ascii=False)};
  var H = D.h, C = 0, TIMER = 0, NS = "http://www.w3.org/2000/svg";
  function esc(s) {{ return String(s).replace(/[&<>"]/g, function (c) {{ return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]; }}); }}
  function el(t, a) {{ var n = document.createElementNS(NS, t); for (var k in a) n.setAttribute(k, a[k]); return n; }}
  var MES = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];
  function render() {{
    var h = H[C], t = h.tt;
    document.querySelectorAll(".hd").forEach(function (c) {{
      var j = +c.getAttribute("data-j");
      c.classList.toggle("past", j < C); c.classList.toggle("cur", j === C); c.classList.toggle("future", j > C);
    }});
    document.getElementById("playhead").style.transform = "translateX(" + h.x + "px)";
    var seen = {{}};
    for (var j = 0; j <= C; j++) H[j].tg.forEach(function (k) {{ seen[k] = 1; }});
    var nReal = 0, nAp = 0, top = 0;
    Object.keys(D.nodes).forEach(function (k) {{
      var n = D.nodes[k], g = document.getElementById("n-" + k);
      var ap = !!seen[k], re = n.k === "a" && t >= n.real;
      g.classList.toggle("ap", ap); g.classList.toggle("re", re); g.classList.toggle("hit", h.tg.indexOf(k) >= 0);
      if (n.k === "a") {{ if (ap) nAp++; if (re) {{ nReal++; top = Math.max(top, +k.slice(1)); }} }}
    }});
    var P = document.getElementById("paths");
    while (P.firstChild) P.removeChild(P.firstChild);
    h.tg.forEach(function (k, q) {{
      var n = D.nodes[k], up = n.k === "a", y2 = up ? n.y + 21 : n.y - 21, my = (h.y + y2) / 2;
      var p = el("path", {{ d: "M" + h.x + "," + h.y + " C" + h.x + "," + my + " " + n.x + "," + my + " " + n.x + "," + y2,
        "class": "pth " + n.k + (h.sec[q] ? " dim" : "") }});
      P.appendChild(p);
      var L = p.getTotalLength();
      if (!h.sec[q]) {{ p.style.strokeDasharray = L; p.style.setProperty("--L", L); p.classList.add("draw"); }}
    }});
    var chips = h.tg.map(function (k, q) {{
      var n = D.nodes[k];
      return n.k === "a" ? '<span class="chip' + (h.sec[q] ? ' dim' : '') + '"><b>' + k.slice(1) + '</b>' + esc(n.name) + '</span>'
                         : '<span class="chip s st-' + n.st + '">' + esc(n.name) + ' · ' + esc(n.stl.toLowerCase()) + '</span>';
    }}).join("");
    var neck = top ? D.nodes["a" + top].neck : "todo es manual";
    var gap = h.tg.filter(function (k) {{ return k.charAt(0) === "a"; }}).map(function (k) {{
      var n = D.nodes[k]; return n.real - Math.floor(t) > 0 ? "«" + n.short + "» todavía tarda " + (n.real - Math.floor(t)) + " año(s) en usarse en serio." : "";
    }}).filter(Boolean)[0] || "";
    document.getElementById("panel").innerHTML =
      '<div><div class="date">' + esc(h.f) + '</div><h2>' + esc(h.t) + (h.url ? ' <a href="' + esc(h.url) + '" target="_blank" rel="noopener" aria-label="Fuente">↗</a>' : '') + '</h2>' +
        '<div class="lbl">Afectó a</div><div class="chips">' + chips + '</div>' + (gap ? '<p class="note">' + esc(gap) + '</p>' : '') + '</div>' +
      '<div><div class="stats"><div class="stat"><div class="n">' + nAp + '/13</div><div class="l">pasos que ya existen</div></div>' +
        '<div class="stat"><div class="n">' + nReal + '/13</div><div class="l">en uso real</div></div>' +
        '<div class="stat"><div class="n">' + (C + 1) + '/' + H.length + '</div><div class="l">hitos</div></div></div>' +
        '<div class="neck"><div class="l">En esta fecha, el cuello está en</div><div class="v">' + esc(neck) + '</div></div></div>';
    document.getElementById("pos").textContent = esc(h.f);
  }}
  function go(k) {{ C = Math.max(0, Math.min(H.length - 1, k)); render(); }}
  function stop() {{ clearInterval(TIMER); TIMER = 0; document.getElementById("play").textContent = "▶ reproducir"; }}
  document.getElementById("prev").onclick = function () {{ stop(); go(C - 1); }};
  document.getElementById("next").onclick = function () {{ stop(); go(C + 1); }};
  document.getElementById("play").onclick = function () {{
    if (TIMER) return stop();
    if (C === H.length - 1) go(0);
    this.textContent = "❚❚ pausa";
    TIMER = setInterval(function () {{ if (C >= H.length - 1) stop(); else go(C + 1); }}, 1300);
  }};
  document.querySelectorAll(".hd").forEach(function (c) {{ c.addEventListener("click", function () {{ stop(); go(+c.getAttribute("data-j")); }}); }});
  document.addEventListener("keydown", function (ev) {{
    if (ev.key === "ArrowRight") {{ stop(); go(C + 1); }} else if (ev.key === "ArrowLeft") {{ stop(); go(C - 1); }}
    else if (ev.key === " ") {{ ev.preventDefault(); document.getElementById("play").click(); }}
    else if (ev.key === "Home") {{ stop(); go(0); }} else if (ev.key === "End") {{ stop(); go(H.length - 1); }}
  }});
  render();
}})();
</script>
</body>
</html>
"""
if __name__ == "__main__":
    (HERE / "cronologico.html").write_text(page)
    print("hitos:", len(H), "multi-destino:", sum(1 for h in H if len(h["tg"]) > 1))
