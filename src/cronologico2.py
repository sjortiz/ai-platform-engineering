"""Prototipo 2: los rieles son el tiempo. Capítulos por año; la serpiente avanza por capítulo y
el panel cuenta dónde quedó el cuello de botella. Los hitos de cada capítulo se recorren con ↑ ↓."""
import html
import json
from pathlib import Path

import cronologico as C  # reutiliza hitos fusionados, destinos y fechas
import zip2

HERE = Path(__file__).parent
e = html.escape

CAPS = [
    dict(k="Antes de 2020", t0=2004.5, t1=2020, titulo="Entregar se volvió fácil",
         lead="CI/CD, contenedores y monitoreo resuelven el camino a producción: lo que se mergea llega solo a cada ambiente y una alerta avisa si algo falla.",
         neck="escribir código", why="Entregar ya es rápido. Lo lento es escribir el código."),
    dict(k="2020–2022", t0=2020, t1=2023, titulo="Aparece todo, no se usa nada",
         lead="En tres años salen GPT-3, el paper de RAG, LoRA, Copilot, ReAct y ChatGPT. Casi nada está listo para producción, pero ya tiene nombre hasta el primer problema de seguridad: el prompt injection.",
         neck="escribir código", why="La IA todavía es autocompletado y curiosidad. El código se sigue escribiendo a mano."),
    dict(k="2023", t0=2023, t1=2024, titulo="La IA entra al día a día",
         lead="Chat y autocompletado pasan a ser herramientas de todos los días. LangChain, los embeddings baratos y las bases vectoriales arman el primer RAG, y nacen vLLM, QLoRA y Llama 2. En seguridad aparecen los guardrails y el OWASP Top 10 para LLMs.",
         neck="escribir código, más rápido", why="Se escribe más rápido, pero una persona sigue escribiendo cada línea."),
    dict(k="2024", t0=2024, t1=2025, titulo="Llegan los volúmenes, y la factura",
         lead="Claude 3.5 Sonnet dispara la calidad del código generado y llegan los revisores con IA. Más llamadas con más contexto disparan el costo: aparecen el routing de modelos, el prompt caching, los modelos pequeños, LoRA viable y el self-hosting. A fin de año sale MCP.",
         neck="costo y revisión de PRs", why="Hay más código que revisar y cada llamada carga más contexto."),
    dict(k="2025", t0=2025, t1=2026, titulo="Los agentes trabajan solos",
         lead="Claude Code y Codex ejecutan tareas completas; los agentes responden a deploys e incidentes, escriben pruebas y corren en la laptop. La seguridad se vuelve de agentes: harness y sandbox, trazabilidad e identidad.",
         neck="contexto de negocio", why="El agente hace el trabajo, pero no conoce las reglas del negocio ni las decisiones anteriores."),
    dict(k="Hoy", t0=2026, t1=2027, titulo="El blocker eres tú",
         lead="Producto pide funcionalidades a agentes que entienden el negocio. Lo que queda es decidir y aprobar, y eso solo se mueve si podemos confiar en lo que hacen los agentes.",
         neck="atención humana", why="Aprobar y decidir. Lo mueven los clasificadores de permisos, la trazabilidad y la identidad de agentes."),
]


def cap_of_t(t):
    for i, c in enumerate(CAPS):
        if t < c["t1"]:
            return i
    return len(CAPS) - 1


def cap_of_year(y):
    return cap_of_t(y + 0.5)


STEPS = zip2.STEPS
step_cap = {i: cap_of_year(C.uso_real(s["when"])) for i, s in enumerate(STEPS, 1)}
step_cap[7] = 5  # uso real 2025–2026: va con Hoy
sec_first = {}
for h in C.H:
    for k, v in h["tg"]:
        if k == "s":
            sec_first[v] = min(sec_first.get(v, 9e9), h["tt"])
sec_cap = {sid: cap_of_t(t) for sid, t in sec_first.items()}

# Anchos de capítulo según lo que contienen
SLOT, MINW, X0 = 100, 140, 40
widths = []
for ci in range(len(CAPS)):
    na = sum(1 for c in step_cap.values() if c == ci)
    ns = sum(1 for c in sec_cap.values() if c == ci)
    widths.append(max(MINW, SLOT * max(na, ns) + 30))
cx = [X0]
for w in widths:
    cx.append(cx[-1] + w)
W, HGT = cx[-1] + X0, 520
YA, YS = 118, 402
YDA, YDS = YA + 44, YS - 44

pos = {}
for ci in range(len(CAPS)):
    a = sorted(i for i, c in step_cap.items() if c == ci)
    s = [x["id"] for x in zip2.SEC if sec_cap.get(x["id"]) == ci]
    for lst, key in ((a, "a"), (s, "s")):
        for n, v in enumerate(lst):
            pos[f"{key}{v}"] = round(cx[ci] + (widths[ci]) * (n + 1) / (len(lst) + 1), 1)

# Hitos: posición dentro de su capítulo, sobre el riel de su tipo
slots = {}
HH = []
for h in C.H:
    ci = cap_of_t(h["tt"])
    c = CAPS[ci]
    top = any(k == "a" for k, _ in h["tg"]) and not any(k == "s" for k, _ in h["tg"])
    x = cx[ci] + 16 + (min(h["tt"], c["t1"] - 0.01) - c["t0"]) / (c["t1"] - c["t0"]) * (widths[ci] - 32)
    b = (round(x / 10), top)
    n = slots.get(b, 0)
    slots[b] = n + 1
    y = (YDA + 11 * n) if top else (YDS - 11 * n)
    HH.append(dict(f=h["f"], t=h["t"], url=h["url"], c=ci, x=round(x, 1), y=y, top=top,
                   tg=[("a" if k in ("a", "a2") else "s") + str(v) for k, v in h["tg"]],
                   sec=[k == "a2" for k, _ in h["tg"]]))

svg = []
for ci, c in enumerate(CAPS):
    svg.append(f'<rect class="cap" data-c="{ci}" x="{cx[ci] + 3}" y="{YA - 70}" width="{widths[ci] - 6}" height="{YS - YA + 120}" rx="10"/>')
    svg.append(f'<text class="ck" data-c="{ci}" x="{cx[ci] + widths[ci] / 2}" y="{YA - 48}" text-anchor="middle">{e(c["k"])}</text>')
    if ci:
        svg.append(f'<path class="sep" d="M{cx[ci]},{YA - 70} V{YS + 50}"/>')
svg.append(f'<path class="rail" d="M{X0},{YA} H{cx[-1]}"/>')
svg.append(f'<path class="rail" d="M{X0},{YS} H{cx[-1]}"/>')
svg.append(f'<text class="rlbl" x="{X0 + 6}" y="{YA + 30}">AVANCE</text>')
svg.append(f'<text class="rlbl" x="{X0 + 6}" y="{YS - 22}">SEGURIDAD</text>')
svg.append('<g id="paths"></g>')


def box(cls, key, x, y, label, sub):
    lines = zip2.wrap(label, 13)
    ty = y - 7 * (len(lines) - 1) + 4
    return (f'<g class="node {cls}" id="n-{key}"><rect class="bx" x="{x - 44}" y="{y - 21}" width="88" height="42" rx="8"/>'
            f'<text class="bt" x="{x}" y="{ty}" text-anchor="middle">{zip2.tspans(lines, x, 14)}</text>'
            f'<text class="bs" x="{x}" y="{y - 28}" text-anchor="middle">{e(sub)}</text></g>')


for i, st in enumerate(STEPS, 1):
    svg.append(box("an", f"a{i}", pos[f"a{i}"], YA, st["n"], f"paso {i}"))
for x in zip2.SEC:
    svg.append(box(f"sn st-{x['st']}", f"s{x['id']}", pos[f"s{x['id']}"], YS, x["n"], zip2.ST[x["st"]].lower()))
for j, h in enumerate(HH):
    svg.append(f'<circle class="hd {"top" if h["top"] else "bot"}" data-j="{j}" data-c="{h["c"]}" cx="{h["x"]}" cy="{h["y"]}" r="4.6"/>')
svg.append('<g id="snake"></g>')

NODES = {f"a{i}": dict(x=pos[f"a{i}"], y=YA, name=st["t"], short=st["n"], c=step_cap[i], k="a") for i, st in enumerate(STEPS, 1)}
NODES.update({f"s{x['id']}": dict(x=pos[f"s{x['id']}"], y=YS, name=x["n"], st=x["st"], stl=zip2.ST[x["st"]], c=sec_cap[x["id"]], k="s") for x in zip2.SEC})
DATA = dict(caps=[dict(k=c["k"], titulo=c["titulo"], lead=c["lead"], neck=c["neck"], why=c["why"], x0=cx[i], x1=cx[i + 1]) for i, c in enumerate(CAPS)],
            h=HH, nodes=NODES, ya=YA, ys=YS, x0=X0)

css = (HERE / "master.css").read_text()
page = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mapa cronológico 2 · prototipo</title>
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
  .pos{{font-family:var(--mono);font-size:.8rem;color:var(--muted);width:12em;text-align:center}}
  .hint{{font-size:.78rem;color:var(--faint)}}
  .wrapd{{background:var(--panel);border-bottom:1px solid var(--line);padding:4px 16px}}
  svg.map{{display:block;width:100%;height:auto}}
  .cap{{fill:transparent;transition:fill .5s}}
  .cap.cur{{fill:var(--accent-soft)}}
  .ck{{font:600 15px var(--display);fill:var(--faint);transition:fill .4s}}
  .ck.done{{fill:var(--muted)}} .ck.cur{{fill:var(--accent)}}
  .sep{{stroke:var(--line-2);stroke-dasharray:3 5}}
  .rail{{fill:none;stroke:var(--line-2);stroke-width:2.5}}
  .rlbl{{font:700 10px var(--sans);letter-spacing:.14em;fill:var(--accent)}}
  .node .bx{{fill:var(--bg);stroke:var(--line-2);stroke-width:1.2;transition:fill .4s,stroke .4s,opacity .4s}}
  .node .bt{{font:600 10.4px var(--sans);fill:var(--ink);transition:opacity .4s}}
  .node .bs{{font:500 9.5px var(--mono);fill:var(--faint)}}
  .node.fut .bx,.node.fut .bt,.node.fut .bs{{opacity:.28}}
  .node.wait .bx{{stroke:var(--accent);stroke-dasharray:4 3}}
  .node.an.real .bx{{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1.8}}
  .node.an.new .bx{{fill:var(--accent);}} .node.an.new .bt{{fill:var(--bg)}}
  .node.sn.real .bx{{stroke:var(--sc);stroke-width:2;fill:var(--panel-2)}}
  .node.sn.new .bx{{fill:var(--sc)}} .node.sn.new .bt{{fill:var(--bg)}}
  .node.hit .bx{{stroke:var(--crit);stroke-width:3}}
  .st-ok{{--sc:var(--ok)}} .st-med{{--sc:var(--med)}} .st-crit{{--sc:var(--crit)}}
  .hd{{fill:var(--bg);stroke:var(--accent);stroke-width:1.5;cursor:pointer;transition:opacity .4s}}
  .hd.bot{{stroke:var(--med)}}
  .hd.past{{fill:var(--accent)}} .hd.bot.past{{fill:var(--med)}}
  .hd.fut{{opacity:.25}}
  .hd.sel{{stroke:var(--crit);stroke-width:3;r:7}}
  .pth{{fill:none;stroke-linecap:round}}
  .pth.faint{{stroke:var(--line-2);stroke-width:1.2}}
  .pth.sel{{stroke:var(--crit);stroke-width:2.4}}
  .pth.sel.draw{{animation:draw .6s cubic-bezier(.16,1,.3,1) both}}
  @keyframes draw{{from{{stroke-dashoffset:var(--L)}}}}
  .snake{{fill:none;stroke:var(--ok);stroke-width:8;stroke-linecap:round}}
  .snake-head{{fill:var(--ok)}} .snake-eye{{fill:var(--bg)}} .food{{fill:var(--crit)}}
  .panel{{flex:1;display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:36px;padding:16px 24px;box-sizing:border-box;width:100%;max-width:1800px;margin:0 auto}}
  .kick{{font-family:var(--mono);font-size:.95rem;color:var(--accent);font-weight:600}}
  .panel h2{{font-family:var(--display);font-weight:600;font-size:2.3rem;line-height:1.1;margin:4px 0 10px}}
  .lead{{font-size:1.1rem;line-height:1.5;margin:0 0 6px;max-width:none}}
  .lbl{{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:var(--accent);margin:12px 0 6px}}
  .chips{{display:flex;flex-wrap:wrap;gap:6px}}
  .chip{{border:1px solid var(--line-2);border-radius:8px;padding:4px 9px;font-size:.92rem;background:var(--bg)}}
  .chip b{{font-family:var(--display);color:var(--accent);margin-right:5px}}
  .chip.s{{border-left:4px solid var(--sc)}}
  .chip.wait{{border-style:dashed}}
  .neck{{padding:14px 16px;background:var(--crit-bg);border:1px solid var(--crit-line);border-radius:10px}}
  .neck .l{{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:var(--crit)}}
  .neck .v{{font-family:var(--display);font-size:1.7rem;font-weight:600;color:var(--crit);line-height:1.15;margin:2px 0 4px}}
  .neck p{{margin:0;font-size:.95rem;max-width:none}}
  .sel{{margin-top:14px;border-top:1px solid var(--line);padding-top:10px}}
  .sel .d{{font-family:var(--mono);font-size:.85rem;color:var(--crit)}}
  .sel .t{{font-family:var(--display);font-weight:600;font-size:1.3rem;margin:2px 0 6px}}
  .sel .t a{{text-decoration:none;color:var(--accent);font-size:1rem}}
  .sel .m{{font-size:.88rem;color:var(--muted)}}
</style>
</head>
<body>
<div class="bar">
  <div class="ttl"><span>Prototipo 2</span>La misma historia, por años</div>
  <div class="nav">
    <span class="hint">← → capítulo · ↑ ↓ hito</span>
    <button type="button" id="prev" aria-label="Capítulo anterior">◀</button>
    <span class="pos" id="pos"></span>
    <button type="button" id="next" aria-label="Capítulo siguiente">▶</button>
  </div>
</div>
<div class="wrapd"><svg class="map" id="map" viewBox="0 0 {W} {HGT}" role="img" aria-label="Rieles de avance y seguridad en el tiempo">{''.join(svg)}</svg></div>
<div class="panel" id="panel"></div>
<script>
(function () {{
  var D = {json.dumps(DATA, ensure_ascii=False)};
  var CP = 0, SEL = -1, HEADX = D.x0, RAF = 0, NS = "http://www.w3.org/2000/svg";
  var REDUCED = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function esc(s) {{ return String(s).replace(/[&<>"]/g, function (c) {{ return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]; }}); }}
  function el(t, a) {{ var n = document.createElementNS(NS, t); for (var k in a) n.setAttribute(k, a[k]); return n; }}
  function inCap() {{ var out = []; D.h.forEach(function (h, j) {{ if (h.c === CP) out.push(j); }}); return out; }}
  var SN = document.getElementById("snake"), BODY = el("path", {{ "class": "snake" }}), FOOD = el("rect", {{ width: 12, height: 12, rx: 3, "class": "food" }}), HEAD = el("g", {{}});
  HEAD.appendChild(el("rect", {{ x: -10, y: -10, width: 20, height: 20, rx: 5, "class": "snake-head" }}));
  HEAD.appendChild(el("rect", {{ x: 2, y: -6, width: 4, height: 4, "class": "snake-eye" }}));
  HEAD.appendChild(el("rect", {{ x: 2, y: 2, width: 4, height: 4, "class": "snake-eye" }}));
  SN.appendChild(BODY); SN.appendChild(FOOD); SN.appendChild(HEAD);
  function setHead(x) {{
    HEADX = x;
    var y = D.ya;
    BODY.setAttribute("d", "M" + D.x0 + "," + y + " H" + x);
    HEAD.setAttribute("transform", "translate(" + x + "," + y + ")");
  }}
  function moveHead(to) {{
    cancelAnimationFrame(RAF);
    var from = HEADX;
    FOOD.style.opacity = 0;
    if (REDUCED) {{ setHead(to); placeFood(); return; }}
    var dur = Math.min(1400, Math.max(500, Math.abs(to - from) * 1.6)), t0 = null;
    function f(now) {{
      if (t0 === null) t0 = now;
      var t = Math.min(1, (now - t0) / dur), k = t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
      setHead(from + (to - from) * k);
      if (t < 1) RAF = requestAnimationFrame(f); else placeFood();
    }}
    RAF = requestAnimationFrame(f);
  }}
  function placeFood() {{
    if (CP >= D.caps.length - 1) {{ FOOD.style.opacity = 0; return; }}
    FOOD.setAttribute("x", D.caps[CP + 1].x1 - 22); FOOD.setAttribute("y", D.ya - 6); FOOD.style.opacity = 1;
  }}
  function drawPaths() {{
    var P = document.getElementById("paths");
    while (P.firstChild) P.removeChild(P.firstChild);
    (SEL >= 0 ? [SEL] : []).forEach(function (j) {{
      var h = D.h[j];
      h.tg.forEach(function (k, q) {{
        var n = D.nodes[k], y2 = n.k === "a" ? n.y + 21 : n.y - 21, my = (h.y + y2) / 2;
        var p = el("path", {{ d: "M" + h.x + "," + h.y + " C" + h.x + "," + my + " " + n.x + "," + my + " " + n.x + "," + y2,
          "class": "pth " + (j === SEL ? "sel" : "faint") }});
        P.appendChild(p);
        if (j === SEL && !REDUCED) {{ var L = p.getTotalLength(); p.style.strokeDasharray = L; p.style.setProperty("--L", L); p.classList.add("draw"); }}
      }});
    }});
  }}
  function chip(k) {{
    var n = D.nodes[k];
    return n.k === "a" ? '<span class="chip' + (n.c > CP ? ' wait' : '') + '"><b>' + k.slice(1) + '</b>' + esc(n.short) + '</span>'
                       : '<span class="chip s st-' + n.st + '">' + esc(n.name) + ' · ' + esc(n.stl.toLowerCase()) + '</span>';
  }}
  function render(moved) {{
    var c = D.caps[CP];
    document.querySelectorAll(".cap,.ck").forEach(function (r) {{
      var ci = +r.getAttribute("data-c"); r.classList.toggle("cur", ci === CP); r.classList.toggle("done", ci < CP);
    }});
    var seenNow = {{}};
    D.h.forEach(function (h) {{ if (h.c <= CP) h.tg.forEach(function (k) {{ seenNow[k] = 1; }}); }});
    var hit = SEL >= 0 ? D.h[SEL].tg : [];
    Object.keys(D.nodes).forEach(function (k) {{
      var n = D.nodes[k], g = document.getElementById("n-" + k);
      g.classList.toggle("real", n.c <= CP); g.classList.toggle("new", n.c === CP);
      g.classList.toggle("wait", n.c > CP && !!seenNow[k]); g.classList.toggle("fut", n.c > CP && !seenNow[k]);
      g.classList.toggle("hit", hit.indexOf(k) >= 0);
    }});
    document.querySelectorAll(".hd").forEach(function (d) {{
      var j = +d.getAttribute("data-j"), hc = D.h[j].c;
      d.classList.toggle("past", hc <= CP); d.classList.toggle("fut", hc > CP); d.classList.toggle("sel", j === SEL);
    }});
    drawPaths();
    if (moved) moveHead(c.x1 - 12);
    var nuevos = [], espera = [], seg = [];
    Object.keys(D.nodes).forEach(function (k) {{
      var n = D.nodes[k];
      if (n.k === "a" && n.c === CP) nuevos.push(k);
      if (n.k === "s" && n.c === CP) seg.push(k);
    }});
    inCap().forEach(function (j) {{ D.h[j].tg.forEach(function (k) {{ var n = D.nodes[k]; if (n.k === "a" && n.c > CP && espera.indexOf(k) < 0) espera.push(k); }}); }});
    var sel = "";
    if (SEL >= 0) {{
      var h = D.h[SEL];
      sel = '<div class="sel"><div class="d">' + esc(h.f) + ' · hito ' + (inCap().indexOf(SEL) + 1) + ' de ' + inCap().length + '</div>' +
        '<div class="t">' + esc(h.t) + (h.url ? ' <a href="' + esc(h.url) + '" target="_blank" rel="noopener" aria-label="Fuente">↗</a>' : '') + '</div>' +
        '<div class="chips">' + h.tg.map(chip).join("") + '</div></div>';
    }} else {{
      sel = '<div class="sel"><div class="m">' + inCap().length + ' hitos en este periodo. Usa ↑ ↓ para recorrerlos.</div></div>';
    }}
    document.getElementById("panel").innerHTML =
      '<div><div class="kick">' + esc(c.k) + '</div><h2>' + esc(c.titulo) + '</h2><p class="lead">' + esc(c.lead) + '</p>' +
        (nuevos.length ? '<div class="lbl">Se vuelve de uso real</div><div class="chips">' + nuevos.map(chip).join("") + '</div>' : '') +
        (espera.length ? '<div class="lbl">Aparece ahora, se usa después</div><div class="chips">' + espera.map(chip).join("") + '</div>' : '') +
        (seg.length ? '<div class="lbl">Seguridad que aparece</div><div class="chips">' + seg.map(chip).join("") + '</div>' : '') + '</div>' +
      '<div><div class="neck"><div class="l">El cuello de botella queda en</div><div class="v">' + esc(c.neck) + '</div><p>' + esc(c.why) + '</p></div>' + sel + '</div>';
    document.getElementById("pos").textContent = c.k + " · " + (CP + 1) + "/" + D.caps.length;
  }}
  function goCap(k) {{ k = Math.max(0, Math.min(D.caps.length - 1, k)); var m = k !== CP; CP = k; SEL = -1; render(m); }}
  function goSel(d) {{
    var list = inCap(); if (!list.length) return;
    var i = list.indexOf(SEL); i = i < 0 ? (d > 0 ? 0 : list.length - 1) : Math.max(-1, Math.min(list.length - 1, i + d));
    SEL = i < 0 ? -1 : list[i]; render(false);
  }}
  document.getElementById("prev").onclick = function () {{ goCap(CP - 1); }};
  document.getElementById("next").onclick = function () {{ goCap(CP + 1); }};
  document.querySelectorAll(".hd").forEach(function (d) {{
    d.addEventListener("click", function () {{ var j = +d.getAttribute("data-j"); goCap(D.h[j].c); SEL = j; render(false); }});
  }});
  document.addEventListener("keydown", function (ev) {{
    if (ev.key === "ArrowRight") {{ ev.preventDefault(); goCap(CP + 1); }}
    else if (ev.key === "ArrowLeft") {{ ev.preventDefault(); goCap(CP - 1); }}
    else if (ev.key === "ArrowDown") {{ ev.preventDefault(); goSel(1); }}
    else if (ev.key === "ArrowUp") {{ ev.preventDefault(); goSel(-1); }}
  }});
  setHead(D.caps[0].x1 - 12); placeFood(); render(false);
}})();
</script>
</body>
</html>
"""
if __name__ == "__main__":
    (HERE / "cronologico2.html").write_text(page)
    print("capítulos:", [(c["k"], w) for c, w in zip(CAPS, widths)], "W:", W)
    print("pasos por capítulo:", {ci: sorted(i for i, c in step_cap.items() if c == ci) for ci in range(len(CAPS))})
    print("seguridad por capítulo:", {ci: [s for s, c in sec_cap.items() if c == ci] for ci in range(len(CAPS))})
