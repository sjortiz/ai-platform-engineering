"""Genera index.html, por-anos.html y en/ a partir de src/: python3 build.py"""
import json
import subprocess
import sys
from pathlib import Path

import i18n

ROOT = Path(__file__).parent
EN = json.loads((ROOT / "i18n" / "en.json").read_text())


def lang_nav(lang, out):
    """Selector ES | EN; cada enlace apunta a la misma vista en el otro idioma."""
    es, en = (out, f"en/{out}") if lang == "es" else (f"../{out}", out)
    es, en = (p.replace("index.html", "") or "./" for p in (es, en))
    cur = '<span aria-current="page" lang="{0}">{1}</span>'
    link = '<a href="{0}" lang="{1}" hreflang="{1}">{2}</a>'
    items = [cur.format("es", "ES") if lang == "es" else link.format(es, "es", "ES"),
             cur.format("en", "EN") if lang == "en" else link.format(en, "en", "EN")]
    return f'<nav class="mode" aria-label="{"Idioma" if lang == "es" else "Language"}">{"".join(items)}</nav>'


def build(script, src_html, out):
    subprocess.run([sys.executable, script], cwd=ROOT / "src", check=True, stdout=subprocess.DEVNULL)
    page = (ROOT / "src" / src_html).read_text().removeprefix('<meta charset="utf-8">\n')
    cut = page.index("</style>") + len("</style>")
    head = page[:cut].replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    body = page[cut:]
    doc = f"""<!doctype html>
    <html lang="es">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect x='4' y='4' width='24' height='24' rx='7' fill='%230f766e'/%3E%3Crect x='17' y='10' width='4' height='4' fill='white'/%3E%3Crect x='17' y='18' width='4' height='4' fill='white'/%3E%3C/svg%3E">
    <meta name="description" content="AI Platform Engineering — El blocker eres tú. Cada vez que automatizamos un paso, el cuello de botella se mueve.">
    <style>:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
    {head}
    </head>
    <body>
    {body}
    </body>
    </html>
    """
    en, missing = i18n.translate(doc, EN)
    en = en.replace('<html lang="es">', '<html lang="en">', 1)
    for lang, html, path in (("es", doc, ROOT / out), ("en", en, ROOT / "en" / out)):
        nav = html.index("</nav>", html.index('<nav class="mode"')) + len("</nav>")
        html = html[:nav] + lang_nav(lang, out) + html[nav:]
        path.parent.mkdir(exist_ok=True)
        path.write_text(html)
        print(path.relative_to(ROOT), len(html))
    return missing


missing = set(build("zip3.py", "cremallera.html", "index.html"))
missing |= set(build("zip3_anos.py", "cremallera-anos.html", "por-anos.html"))
missing |= set(build("zip3_grafo.py", "cremallera-grafo.html", "grafo.html"))
if missing:
    print(f"\n{len(missing)} textos sin traducción en i18n/en.json (quedan en español en en/):", file=sys.stderr)
    for m in sorted(missing)[:40]:
        print("  " + m[:100].replace("\n", "\\n"), file=sys.stderr)
