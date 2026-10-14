"""Traduce una página ya generada con una tabla es→en (i18n/en.json).

Traduce tres tipos de segmento, sin tocar la lógica de src/:
- texto HTML (corridas de texto con etiquetas en línea),
- atributos visibles (aria-label, title, alt, content),
- literales de string en <script>, incluido el JSON de datos.
Los literales comparados con === / !== son identificadores y no se traducen.
"""
import json
import re

INLINE = {"b", "strong", "em", "i", "code", "a", "span", "br", "small", "kbd", "abbr", "sup", "sub", "mark", "u", "s", "q"}
ATTRS = ("aria-label", "title", "alt", "content")
TAG = re.compile(r"<(/?)([a-zA-Z][\w:-]*)([^>]*)>|<!--.*?-->", re.S)
ATTR = re.compile(r'\b(' + "|".join(ATTRS) + r')="([^"]*)"')
WORD = re.compile(r"[A-Za-zÁÉÍÓÚÑáéíóúñü]{2}")


def _wordy(s):
    if re.fullmatch(r"[a-z][\w.:#-]*|[\w-]+=[\w,= .-]+", s):  # identificadores, eventos, selectores, viewport
        return False
    return bool(WORD.search(re.sub(r"<[^>]+>|&\w+;", "", s)))


def _js_strings(js):
    """Devuelve (inicio, fin, comilla, valor) de cada literal, saltando comentarios y regex."""
    out, i, n, prev = [], 0, len(js), ""
    while i < n:
        c = js[i]
        if c in "'\"`":
            j, buf = i + 1, []
            while j < n and js[j] != c:
                if js[j] == "\\":
                    buf.append(js[j:j + 2])
                    j += 2
                else:
                    buf.append(js[j])
                    j += 1
            raw = "".join(buf)
            if c != "`":
                try:
                    val = json.loads('"' + raw.replace("\\'", "'").replace('"', '\\"').replace('\\\\"', '\\"') + '"') if c == "'" else json.loads(c + raw + c)
                except ValueError:
                    val = None
                if val is not None:
                    out.append((i, j + 1, c, val))
            i, prev = j + 1, "x"
        elif js.startswith("//", i):
            i = js.find("\n", i)
            i = n if i < 0 else i
        elif js.startswith("/*", i):
            i = js.index("*/", i) + 2
        elif c == "/" and prev in "(,=:[!&|?{};":
            j = i + 1
            while j < n and js[j] != "/":
                j += 2 if js[j] == "\\" else 1
                if j < n and js[j - 1] == "[":
                    while j < n and js[j] != "]":
                        j += 2 if js[j] == "\\" else 1
            i, prev = j + 1, "x"
        else:
            if not c.isspace():
                prev = c if not (c.isalnum() or c in "_$") else "x"
            i += 1
    return out


def _ids(js, lits):
    """Literales usados como identificadores: comparados con ===/!==/==/!= o usados como valor de case."""
    ids = set()
    for a, b, _, v in lits:
        before, after = js[max(0, a - 5):a].rstrip(), js[b:b + 5].lstrip()
        if re.search(r"[!=]==?$", before) or re.match(r"[!=]==?", after) or before.endswith("case"):
            ids.add(v)
    return ids


def segments(page):
    """Yields (tipo, texto) de cada segmento traducible de la página."""
    for kind, _, _, val in _walk(page):
        yield kind, val


def _walk(page):
    """Yields (tipo, inicio, fin, valor) en orden; valor es el texto ya decodificado.

    Un atributo dentro de una corrida de texto viaja con la corrida."""
    end = 0
    for seg in sorted(_raw(page), key=lambda x: (x[1], -x[2])):
        if seg[1] >= end:
            yield seg
            end = seg[2]


def _raw(page):
    pos = 0
    for m in re.finditer(r"<(script|style)\b[^>]*>(.*?)</\1>", page, re.S):
        yield from _html(page, pos, m.start(2))
        if m.group(1) == "script":
            js, base = m.group(2), m.start(2)
            lits = _js_strings(js)
            ids = _ids(js, lits)
            for a, b, q, v in lits:
                if v not in ids and _wordy(v):
                    yield "js:" + q, base + a, base + b, v
        pos = m.end(2)
    yield from _html(page, pos, len(page))


def _html(page, a, b):
    chunk, run, run_start, last = page[a:b], [], None, 0

    def flush(end):
        if run_start is None:
            return
        raw = chunk[run_start:end]
        lead, core, trail = re.match(r"(\s*)(.*?)(\s*)$", raw, re.S).groups()
        if core and _wordy(core):
            yield "html", a + run_start + len(lead), a + end - len(trail), core

    for m in TAG.finditer(chunk):
        if m.start() > last and run_start is None:
            run_start = last
        name = (m.group(2) or "").lower()
        for am in ATTR.finditer(m.group(3) or ""):
            if _wordy(am.group(2)):
                s = a + m.start(3) + am.start(2)
                yield "attr", s, s + len(am.group(2)), am.group(2)
        if name in INLINE:
            if run_start is None:
                run_start = m.start()
        else:
            yield from flush(m.start())
            run_start = None
        last = m.end()
    if last < len(chunk):
        if run_start is None:
            run_start = last
    yield from flush(len(chunk))


def translate(page, table):
    """Devuelve (página traducida, segmentos sin traducción)."""
    out, pos, missing = [], 0, []
    for kind, a, b, val in _walk(page):
        en = table.get(val)
        if en is None:
            missing.append(val)
            continue
        if kind.startswith("js:"):
            q = kind[3:]
            enc = json.dumps(en, ensure_ascii=False)
            if q == "'":
                enc = "'" + enc[1:-1].replace('\\"', '"').replace("'", "\\'") + "'"
            # "</" dentro de <script> cerraría el bloque
            enc = enc.replace("</script", "<\\/script")
        else:
            enc = en
        out.append(page[pos:a])
        out.append(enc)
        pos = b
    out.append(page[pos:])
    return "".join(out), missing
