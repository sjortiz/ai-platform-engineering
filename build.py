"""Genera index.html a partir de src/: python3 build.py"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def build(script, src_html, out):
    subprocess.run([sys.executable, script], cwd=ROOT / "src", check=True, stdout=subprocess.DEVNULL)
    page = (ROOT / "src" / src_html).read_text()
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
    (ROOT / out).write_text(doc)
    print(out, len(doc))


build("zip3.py", "cremallera.html", "index.html")
build("zip3_anos.py", "cremallera-anos.html", "por-anos.html")
