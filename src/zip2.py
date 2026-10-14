"""Genera cremallera.html: dos rieles (avance y seguridad) que se juntan en "Hoy", estilo mapa maestro."""
import html
import json
from detalle import INFO, LLEVA, EJEMPLO, ERROR
from pathlib import Path

HERE = Path(__file__).parent
e = html.escape

# Línea principal: nombre corto (riel), cuello corto, y el detalle para el panel.
STEPS = [
    dict(n="Manual y CI/CD", neck="escribir código", t="Manual → CI/CD → monitoreo",
         when="antes de 2020", d="Ticket, branch, PR, review, deploy, QA y PROD. Primero a mano, después con pipelines y monitoreo en producción."),
    dict(n="Chat y autocompletado", neck="escribir código", t="Autocompletado y chat",
         when="aparece 2021 · uso real 2023", d="Copilot y ChatGPT. Se escribe más rápido, aparece el vibe coding y la respuesta es la ingeniería de siempre: tests, ambientes y revisión."),
    dict(n="Agentes de código", neck="revisión de PRs", t="Agentes de código",
         when="aparece 2023 · uso real 2025", d="Agentes en el IDE y la CLI con archivos de reglas. Se hacen 5 cambios en el tiempo de 1 y la revisión humana no da abasto."),
    dict(n="Revisión con IA", neck="QA y ambientes", t="Agentes de revisión de código",
         when="aparece 2023 · uso real 2024", d="Revisan cada PR antes que una persona."),
    dict(n="Ambiente por PR", neck="incidentes en PROD", t="Pruebas y ambiente por PR",
         when="uso real 2025", d="Tests generados y un ambiente efímero por PR. Más cambios llegan a producción, y con ellos más incidentes."),
    dict(n="Agentes de incidentes", neck="qué construir", t="Agentes de incidentes",
         when="aparece 2024 · uso real 2025", d="Se activan con un deploy o una alerta, leen logs y métricas por MCP y dejan un análisis de causa raíz para que una persona decida."),
    dict(n="Agentes de requerimientos", neck="contexto de negocio", t="Agentes de requerimientos",
         when="uso real 2025–2026", d="Producto pide funcionalidades sin contexto técnico. El agente necesita conocer el negocio mejor que quien le pide."),
    dict(n="RAG y KAG", neck="costo", t="RAG → GraphRAG y KAG → búsqueda agéntica",
         when="aparece 2020 · uso real 2023–2025", d="Entrenar un modelo propio era imposible, así que se le da contexto al modelo: primero RAG simple, después grafos y búsqueda agéntica."),
    dict(n="Routing de modelos", neck="tareas simples a precio frontier", t="Control de costos",
         when="uso real 2024–2025", d="Batch, prompt caching, elegir Haiku, Sonnet u Opus según la tarea, y un gateway con presupuesto por equipo."),
    dict(n="SLM por tarea", neck="hacer bien tu tarea", t="Modelos pequeños por tarea (SLM)",
         when="aparece 2023 · uso real 2024–2025", d="Modelos de 1 a 8B para clasificar, extraer y enrutar, destilados de un modelo frontier."),
    dict(n="LoRA", neck="dónde correrlos", t="LoRA sobre modelos abiertos",
         when="aparece 2021 · uso real 2024", d="Especializar un modelo pequeño con tus datos sin entrenar desde cero. QLoRA y los modelos abiertos lo volvieron viable."),
    dict(n="vLLM self-hosting", neck="GPU y operación", t="Self-hosting de varios modelos",
         when="aparece 2023 · uso real 2024–2025", d="vLLM sirviendo varios adapters LoRA, cuantización y modelos MoE. Los modelos abiertos se acercan al frontier."),
    dict(n="IA local", neck="confianza y operación", t="IA local",
         when="aparece 2023 · uso real 2025", d="llama.cpp, Ollama, MLX y Hermes con tool calling: modelos y agentes en la laptop o en el edge, sin costo por token y sin que los datos salgan."),
]

# Pista de seguridad: en qué paso aparece (at), estado y relación con el avance de ese paso.
SEC = [
    dict(id="inj", at=2, rail=False, n="Prompt injection", st="crit", rel="abre", d="No hay defensa completa. Lo práctico es no juntar datos no confiables, datos privados y una salida al exterior."),
    dict(id="cls", at=2, n="Guardrails", st="med", rel="abre", falta=True, d="Clasificadores de entrada y salida: paran ataques conocidos, no los nuevos."),
    dict(id="har", at=3, n="Harness y sandbox", st="ok", rel="abre", d="Permisos de herramientas, sandbox y hooks: qué puede usar el agente y dónde."),
    dict(id="trz", at=6, n="Trazabilidad", st="med", rel="abre", falta=True, d="Langfuse, LangSmith y OpenTelemetry muestran qué hizo cada agente: tool calls, permisos y resultados. Falta el porqué y quién lo delegó."),
    dict(id="idn", at=7, n="Identidad de agentes", st="crit", rel="abre", falta=True, d="Permisos delegados, mínimo privilegio y revocación para agentes."),
    dict(id="mcp", at=7, rail=False, n="MCP y memoria", st="crit", rel="abre", d="Servidores MCP de terceros y memoria envenenada como vía de ataque."),
    dict(id="rag", at=8, n="Acceso en RAG", st="crit", rel="abre", d="Los documentos indexados traen instrucciones escondidas, y los permisos por usuario son difíciles de respetar al buscar."),
    dict(id="gw", at=9, n="AI gateway", st="ok", rel="pieza", d="El mismo gateway de costos es el punto de control: clasificadores y enmascarado de datos personales."),
    dict(id="dat", at=12, rail=False, n="Datos al proveedor", st="ok", rel="resuelve", d="Con self-hosting los datos se quedan en tu infraestructura."),
    dict(id="sup", at=12, n="Safetensors", st="med", rel="abre", d="Safetensors evita que un modelo ejecute código; la procedencia y las puertas traseras siguen sin resolver."),
]
CROSS = [dict(src="har", to=6, label="habilita")]

ST = {"ok": "Resuelto", "med": "Parcial", "crit": "Abierto"}

# Geometría del SVG
W, H = 1400, 360
X0, XN, XHOY = 96, 1166, 1330
YT, YB = 110, 280
YHOY = (YT + YB) // 2
N = len(STEPS)
xs = [round(X0 + i * (XN - X0) / (N - 1), 1) for i in range(N)]


def wrap(text, width=15):
    lines, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def tspans(lines, x, dy):
    return "".join(f'<tspan x="{x}" dy="{0 if i == 0 else dy}">{e(l)}</tspan>' for i, l in enumerate(lines))


svg = []
BW, BH = 86, 40
RAIL = [x for x in SEC if x.get("rail", True)]
for x in RAIL:
    x["x"] = xs[x["at"] - 1]

svg.append(f'<path class="rail" d="M{X0 - 52},{YT} H{XN + 60} C{XN + 110},{YT} {XHOY - 70},{YHOY} {XHOY - 18},{YHOY}" marker-end="url(#m-r)"/>')
svg.append(f'<path class="rail" d="M{X0 - 52},{YB} H{XN + 60} C{XN + 110},{YB} {XHOY - 70},{YHOY} {XHOY - 18},{YHOY}" marker-end="url(#m-r)"/>')
svg.append(f'<text class="rlbl" x="{X0 - 52}" y="{YT - 84}">AVANCE</text>')
svg.append(f'<text class="rlbl" x="{X0 - 52}" y="{YB + 48}">SEGURIDAD</text>')

# Conexiones: hacia abajo desde el avance, y hacia arriba cuando un tema de seguridad habilita un avance posterior
for x in RAIL:
    cx = x["x"]
    svg.append(f'<path class="conn" data-i="{x["at"]}" d="M{cx},{YT + BH / 2} V{YB - BH / 2 - 3}" marker-end="url(#m-c)"/>')
for c in CROSS:
    src = next(x for x in RAIL if x["id"] == c["src"])
    x1, x2 = src["x"] + BW / 2 - 14, xs[c["to"] - 1] - BW / 2 + 14
    ym = YHOY
    svg.append(f'<path class="conn up" data-i="{c["to"]}" d="M{x1},{YB - BH / 2} V{ym} H{x2} V{YT + BH / 2 + 3}" marker-end="url(#m-u)"/>')

def box(cls, i, x, y, label, sel):
    lines = wrap(label, 13)
    ty = y - 7 * (len(lines) - 1) + 4
    return (f'<g class="{cls}" data-i="{i}" data-sel="{sel}" tabindex="0" role="button" aria-label="{e(label)}">'
            f'<rect class="bx" x="{x - BW / 2}" y="{y - BH / 2}" width="{BW}" height="{BH}" rx="8"/>'
            f'<text class="bt" x="{x}" y="{ty}" text-anchor="middle">{tspans(lines, x, 14)}</text></g>')

for i, st in enumerate(STEPS, 1):
    svg.append(f'<text class="snum" data-i="{i}" x="{xs[i - 1]}" y="{YT - BH / 2 - 8}" text-anchor="middle">{i}</text>')
    svg.append(box("step", i, xs[i - 1], YT, st["n"], i))
for x in RAIL:
    svg.append(box("sec", x["at"], x["x"], YB, x["n"], x["at"]))

svg.append(f'''<g class="step hoy" data-i="{N + 1}" data-sel="{N + 1}" tabindex="0" role="button" aria-label="Hoy">
  <rect class="bx hoybx" x="{XHOY - 44}" y="{YHOY - 22}" width="88" height="44" rx="22"/>
  <text class="hoyt" x="{XHOY}" y="{YHOY + 5}" text-anchor="middle">Hoy</text>
</g>''')
svg.append('<g id="snake"></g>')

defs = """<defs>
  <marker id="m-c" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk-c"/></marker>
  <marker id="m-u" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk-u"/></marker>
  <marker id="m-r" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk-r"/></marker>
</defs>"""

DETAIL = {}
for i in range(1, N + 2):
    st = STEPS[i - 1] if i <= N else dict(t="Hoy", when="", neck="atención humana")
    info = INFO[i]
    sec = [dict(id=x["id"], n=x["n"], st=x["st"], stl=ST[x["st"]], rel=x["rel"], d=x["d"]) for x in SEC if x["at"] == i]
    if i == N + 1:
        sec = [dict(id=x["id"], n=x["n"], st=x["st"], stl=ST[x["st"]], rel="falta", d=x["d"]) for x in SEC if x.get("falta")]
    DETAIL[i] = dict(t=st["t"], when=st["when"], neck=st["neck"], tools=info["tools"][:4], lleva=LLEVA[i],
                     ej=EJEMPLO[i], err=ERROR[i], lead=info["lead"], hitos=info["hitos"], medir=info["medir"], seg=info["seg"], why=info["neck_why"], sec=sec)
for c in CROSS:
    src = next(x for x in SEC if x["id"] == c["src"])
    DETAIL[c["to"]]["sec"].insert(0, dict(id=src["id"], n=src["n"], st=src["st"], stl=ST[src["st"]], rel="habilita", d="Es lo que permite que estos agentes toquen producción en solo lectura."))

page = f"""<title>El cuello se mueve</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600;650;700&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>
{(HERE / 'master.css').read_text()}
  /* Cremallera: dos rieles horizontales que se juntan en Hoy; el detalle del paso va debajo. */
  .wrap{{max-width:1240px;padding-left:max(16px, env(safe-area-inset-left, 0px));padding-right:max(16px, env(safe-area-inset-right, 0px))}}
  .zip-scroll{{overflow-x:auto;padding:14px 10px}}
  .zip-svg{{display:block;width:100%;min-width:980px;height:auto}}
  .rail{{fill:none;stroke:var(--line-2);stroke-width:2.5;stroke-linecap:round}}
  .mk-r{{fill:var(--line-2)}} .mk-c{{fill:var(--faint)}} .mk-u{{fill:var(--accent)}}
  .rlbl{{font:700 11px var(--sans);letter-spacing:.14em;fill:var(--accent)}}
  .snum{{font:600 12px var(--display);fill:var(--accent)}}
  .bx{{fill:var(--bg);stroke:var(--line-2);stroke-width:1.2}}
  .bt{{font:600 10.6px var(--sans);fill:var(--ink)}}
  .sec .bx{{fill:var(--panel-2)}}
  .step,.sec{{cursor:pointer}}
  .step:focus,.sec:focus{{outline:none}}
  .step:hover .bx,.sec:hover .bx,.step:focus-visible .bx,.sec:focus-visible .bx{{stroke:var(--accent)}}
  .conn{{fill:none;stroke:var(--faint);stroke-width:1.5}}
  .conn.up{{stroke:var(--accent);stroke-width:1.7}}
  .hoybx{{fill:var(--accent);stroke:var(--accent)}}
  .hoyt{{font:600 15px var(--display);fill:var(--bg)}}
  [data-i]{{transition:opacity .25s}}
  .step.dim .bt,.sec.dim .bt{{opacity:.2}}
  .step.dim .bx,.sec.dim .bx{{stroke-opacity:.3}}
  .snum.dim,.conn.dim,.hoy.dim,.clbl.dim{{opacity:.15}}
  .cur .bx{{stroke:var(--accent);stroke-width:2.2}}
  .snake-body{{fill:none;stroke:var(--ok);stroke-width:9;stroke-linecap:round;opacity:.85}}
  .snake-head{{fill:var(--ok)}} .snake-eye{{fill:var(--bg)}} .food{{fill:var(--crit)}}
  .legend .ln{{display:inline-block;width:26px;height:2px;vertical-align:middle}}
  .legend .ln.abre{{background:repeating-linear-gradient(to right,var(--crit) 0 5px,transparent 5px 9px)}}
  .legend .ln.ok{{background:var(--ok)}}
  .legend .ln.pieza{{height:6px;border-top:2px solid var(--accent);border-bottom:2px solid var(--accent)}}
  .legend .dt{{display:inline-block;width:11px;height:11px;border-radius:50%}}
  .legend .dt.ring{{border:1.5px dashed var(--accent);width:16px;height:16px}}
  .ctrl{{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;margin:0 0 10px}}
  .ctrl button{{font:600 .82rem var(--sans);color:var(--accent);background:var(--accent-soft);border:1px solid var(--line-2);
    border-radius:8px;padding:6px 12px;cursor:pointer}}
  .ctrl button:hover{{border-color:var(--accent)}}
  .ctrl button:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
  .pos{{font-family:var(--mono);font-size:.8rem;color:var(--muted);min-width:7.5em;text-align:center}}
  .hint{{font-size:.8rem;color:var(--faint)}}
  .detail{{margin-top:10px;background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:18px 22px}}
  .detail .empty{{margin:0;color:var(--faint);font-size:1rem}}
  .s-head{{display:grid;grid-template-columns:minmax(0,.85fr) minmax(0,1.6fr);gap:28px;align-items:start;padding-bottom:16px;border-bottom:1px solid var(--line)}}
  .s-k{{font-family:var(--display);font-weight:600;color:var(--accent);font-size:1.05rem}}
  .s-title h3{{font-family:var(--display);font-weight:600;font-size:2rem;line-height:1.1;margin:4px 0 8px}}
  .s-when{{font-family:var(--mono);font-size:.85rem;color:var(--muted)}}
  .s-lead p{{font-size:1.05rem;line-height:1.45;margin:0;max-width:none}}
  .tools{{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}}
  .tool{{font-size:.85rem;font-weight:600;background:var(--panel-2);border:1px solid var(--line-2);border-radius:6px;padding:3px 9px}}
  .presenting .zip-svg{{max-height:230px;min-width:0;margin:0 auto}}
  .presenting .zip-scroll{{padding:6px 10px}}
  .s-strip{{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);gap:14px;padding-top:16px}}
  .ej,.err{{border-radius:10px;padding:12px 16px}}
  .ej{{background:var(--accent-soft);border:1px solid var(--line-2)}}
  .ej p{{font-size:1rem;line-height:1.4;margin:0;max-width:none}}
  .err{{background:var(--med-bg);border:1px solid var(--med-line)}}
  .err .s-lbl{{color:var(--med);margin-bottom:6px}}
  .err p{{font-size:.98rem;line-height:1.4;margin:0;max-width:none}}
  .ej .s-lbl{{margin-bottom:6px}}
  .s-cols{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:28px;padding-top:14px}}
  .s-lbl{{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:var(--accent);margin:0 0 10px}}
  .s-gap{{margin-top:14px}}
  .hitos{{list-style:none;margin:0;display:grid;gap:7px;border-left:2px solid var(--line-2);padding-left:12px}}
  .hitos li{{font-size:.95rem;display:grid;grid-template-columns:5.8em minmax(0,1fr);gap:8px}}
  .hd{{font-family:var(--mono);font-size:.8rem;color:var(--accent);padding-top:2px}}
  .s-take ul{{list-style:none;padding:0;margin:0;display:grid;gap:9px}}
  .s-take li{{font-size:1.05rem;font-weight:600;line-height:1.3;padding-left:24px;position:relative}}
  .s-take li::before{{content:"✓";position:absolute;left:0;color:var(--ok);font-weight:700}}
  .s-take ul.plain li{{font-size:.92rem;font-weight:400;color:var(--muted)}}
  .s-take ul.plain li::before{{content:"·";color:var(--faint)}}
  .segn{{font-size:.92rem;margin:0 0 10px}}
  .segi{{margin-bottom:10px}}
  .segi p{{font-size:.86rem;color:var(--muted);margin:4px 0 0}}
  .segl{{display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:.95rem}}
  .s-neck{{margin-top:14px;padding:12px 14px;background:var(--crit-bg);border:1px solid var(--crit-line);border-radius:10px}}
  .s-neck .s-lbl{{color:var(--crit);margin-bottom:4px}}
  .nk{{font-family:var(--display);font-size:1.3rem;font-weight:600;color:var(--crit);line-height:1.2}}
  .s-neck p{{font-size:.88rem;margin:6px 0 0}}
  @media (max-width:820px){{.s-head,.s-cols,.s-strip{{grid-template-columns:minmax(0,1fr)}}}}
  .b-ok{{background:var(--ok-bg);color:var(--ok);border:1px solid var(--ok-line)}}
  .quote{{font-family:var(--display);font-size:1.3rem;line-height:1.35;max-width:46ch;margin:18px 0 0}}
  @media (prefers-reduced-motion:reduce){{[data-i]{{transition:none}}}}
</style>
<div class="wrap">
<header class="masthead">
  <p class="kicker">BarCamp · borrador del diagrama</p>
  <h1>El cuello de botella se mueve</h1>
  <div class="meta"><span><b>Fecha</b> 2026-10-14</span><span><b>Autora</b> Shailyn Ortiz</span><span><b>Estado</b> borrador, fechas por verificar</span></div>
</header>

<section>
  <div class="sec-head"><span class="sec-num">01</span><h2>La línea de tiempo</h2></div>
  <div class="ctrl" id="ctrl-anchor">
    <button type="button" id="b-mode">Presentar</button>
    <button type="button" id="b-prev" aria-label="Paso anterior" hidden>◀</button>
    <span class="pos" id="pos" hidden></span>
    <button type="button" id="b-next" aria-label="Paso siguiente" hidden>▶</button>
    <span class="hint" id="hint">Toca un paso para ver el detalle, o presenta: la serpiente avanza y se come el cuello de botella de cada paso.</span>
  </div>
  <div class="diagram zip-scroll">
    <svg class="zip-svg" id="zsvg" viewBox="0 0 {W} {H}" role="img" aria-label="Línea de avances arriba y pista de seguridad abajo, que se juntan en Hoy">
      {defs}
      {''.join(svg)}
    </svg>
  </div>
  <div class="detail" id="detail" aria-live="polite"></div>
  <p class="quote">“El próximo salto de velocidad no lo va a dar un modelo mejor. Lo va a dar poder confiar en lo que hacen los agentes.”</p>
</section>

<footer>
  <div class="disc">Los pasos van en el orden en que cada uno se volvió el cuello de botella, no por fecha de lanzamiento. Las fechas son de año y salieron de memoria; hay que verificarlas con fuentes antes de la charla. “Aparece” es la primera publicación o lanzamiento; “uso real” es cuando se volvió práctico en producción.</div>
</footer>
</div>
<script>
(function () {{
  var DETAIL = {json.dumps(DETAIL, ensure_ascii=False)};
  var XS = {json.dumps(xs + [XHOY])};
  var YT = {YT}, X0 = {X0 - 52}, LAST = {N + 1};
  var STEP = 0, SEL = 0;
  var NS = "http://www.w3.org/2000/svg";
  function el(tag, a) {{ var n = document.createElementNS(NS, tag); for (var k in a) n.setAttribute(k, a[k]); return n; }}
  function esc(s) {{ return String(s).replace(/[&<>"]/g, function (c) {{ return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]; }}); }}
  var REL = {{ abre: "abre", resuelve: "resuelve", pieza: "misma pieza", habilita: "habilitado por", falta: "falta" }};
  function li(a) {{ return a.map(function (x) {{ return "<li>" + esc(x) + "</li>"; }}).join(""); }}
  function detail(i) {{
    var box = document.getElementById("detail");
    if (!i) {{ box.innerHTML = '<p class="empty">Toca un paso, o presenta con ▶.</p>'; return; }}
    var d = DETAIL[i];
    var tools = d.tools.map(function (t) {{ return '<span class="tool">' + esc(t) + '</span>'; }}).join("");
    var sec = d.sec.map(function (s) {{
      return '<div class="segl"><span class="badge b-' + s.st + '">' + s.stl + '</span><b>' + esc(s.n) + '</b></div>';
    }}).join("");
    var hitos = d.hitos.map(function (h) {{ return '<li><span class="hd">' + esc(h[0]) + '</span>' + esc(h[1]) + '</li>'; }}).join("");
    var secn = d.sec.map(function (s) {{ return '<li><b>' + esc(s.n) + ' (' + REL[s.rel] + ', ' + s.stl.toLowerCase() + ').</b> ' + esc(s.d) + '</li>'; }}).join("");
    var secl = d.sec.map(function (s) {{
      return '<div class="segi"><div class="segl"><span class="badge b-' + s.st + '">' + s.stl + '</span><b>' + esc(s.n) + '</b></div><p>' + esc(s.d) + '</p></div>';
    }}).join("");
    box.innerHTML =
      '<div class="s-head">' +
        '<div class="s-title"><div class="s-k">' + (i === LAST ? "Hoy" : "Paso " + i) + '</div><h3>' + esc(d.t) + '</h3>' +
          (d.when ? '<div class="s-when">' + esc(d.when) + '</div>' : '') + '</div>' +
        '<div class="s-lead"><p>' + esc(d.lead) + '</p>' + (tools ? '<div class="tools">' + tools + '</div>' : '') + '</div>' +
      '</div>' +
      '<div class="s-strip">' +
        '<div class="ej"><div class="s-lbl">En la práctica</div><p>' + esc(d.ej) + '</p></div>' +
        '<div class="err"><div class="s-lbl">Error común</div><p>' + esc(d.err) + '</p></div>' +
      '</div>' +
      '<div class="s-cols">' +
        (hitos ? '<div><div class="s-lbl">Hitos</div><ul class="hitos">' + hitos + '</ul></div>' : '') +
        '<div class="s-take"><div class="s-lbl">Llévate esto</div><ul>' + li(d.lleva) + '</ul>' +
          '<div class="s-lbl s-gap">Cómo saber si funciona</div><ul class="plain">' + li(d.medir) + '</ul></div>' +
        '<div>' + (secl || d.seg ? '<div class="s-lbl">Seguridad</div>' + (d.seg && !secl ? '<p class="segn">' + esc(d.seg) + '</p>' : '') + secl : '') +
          '<div class="s-neck"><div class="s-lbl">' + (d.why ? 'El cuello salta a' : 'El cuello') + '</div><div class="nk">' + esc(d.neck) + '</div>' +
          (d.why ? '<p>' + esc(d.why) + '</p>' : '') + '</div>' +
        '</div>' +
      '</div>';
  }}
  function paint() {{
    document.querySelectorAll("#zsvg [data-i]").forEach(function (g) {{
      var i = +g.getAttribute("data-i");
      g.classList.toggle("dim", !!STEP && i > STEP);
      g.classList.toggle("cur", (STEP || SEL) === i);
    }});
    var sn = document.getElementById("snake");
    while (sn.firstChild) sn.removeChild(sn.firstChild);
    if (STEP) {{
      var hx = XS[STEP - 1], y = YT;
      if (STEP === LAST) {{ y = {YHOY}; }}
      sn.appendChild(el("path", {{ d: "M" + X0 + "," + (YT - 50) + " H" + (hx - 10), "class": "snake-body" }}));
      sn.appendChild(el("rect", {{ x: hx - 10, y: y - 60, width: 20, height: 20, rx: 5, "class": "snake-head" }}));
      sn.appendChild(el("rect", {{ x: hx + 2, y: y - 56, width: 4, height: 4, "class": "snake-eye" }}));
      sn.appendChild(el("rect", {{ x: hx + 2, y: y - 48, width: 4, height: 4, "class": "snake-eye" }}));
      if (STEP < LAST) {{
        var fx = XS[STEP], fy = STEP + 1 === LAST ? {YHOY} : YT;
        sn.appendChild(el("rect", {{ x: fx - 7, y: fy - 57, width: 14, height: 14, rx: 3, "class": "food" }}));
      }}
    }}
    detail(STEP || SEL);
    var on = !!STEP;
    document.body.classList.toggle("presenting", on);
    document.getElementById("b-mode").textContent = on ? "Ver todo" : "Presentar";
    ["b-prev", "pos", "b-next"].forEach(function (id) {{ document.getElementById(id).hidden = !on; }});
    document.getElementById("hint").hidden = on;
    document.getElementById("pos").textContent = on ? (STEP === LAST ? "Hoy" : "Paso " + STEP + " de " + (LAST - 1)) : "";
  }}
  function go(d) {{ STEP = Math.min(LAST, Math.max(1, STEP + d)); paint(); }}
  document.getElementById("b-mode").addEventListener("click", function () {{ STEP = STEP ? 0 : 1; SEL = 0; paint();
    if (STEP) document.getElementById("ctrl-anchor").scrollIntoView({{ behavior: "smooth", block: "start" }}); }});
  document.getElementById("b-prev").addEventListener("click", function () {{ go(-1); }});
  document.getElementById("b-next").addEventListener("click", function () {{ go(1); }});
  document.querySelectorAll("#zsvg [data-sel]").forEach(function (g) {{
    function pick() {{ var i = +g.getAttribute("data-sel"); if (STEP) STEP = i; else SEL = (SEL === i ? 0 : i); paint(); }}
    g.addEventListener("click", pick);
    g.addEventListener("keydown", function (ev) {{ if (ev.key === "Enter" || ev.key === " ") {{ ev.preventDefault(); pick(); }} }});
  }});
  document.addEventListener("keydown", function (ev) {{
    if (!STEP) return;
    if (ev.key === "ArrowRight" || ev.key === "PageDown") {{ ev.preventDefault(); go(1); }}
    else if (ev.key === "ArrowLeft" || ev.key === "PageUp") {{ ev.preventDefault(); go(-1); }}
    else if (ev.key === "Escape") {{ STEP = 0; paint(); }}
  }});
  paint();
}})();
</script>
"""

(HERE / "cremallera.html").write_text(page)
print(len(page))
