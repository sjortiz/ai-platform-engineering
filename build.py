"""Genera index.html a partir de src/: python3 build.py"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
subprocess.run([sys.executable, "zip3.py"], cwd=ROOT / "src", check=True, stdout=subprocess.DEVNULL)
page = (ROOT / "src" / "cremallera.html").read_text()
cut = page.index("</style>") + len("</style>")
head = page[:cut].replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
body = page[cut:]
doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="AI Platform Engineering — El blocker eres tú. Cada vez que automatizamos un paso, el cuello de botella se mueve.">
<style>:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
{head}
</head>
<body>
{body}
</body>
</html>
"""
(ROOT / "index.html").write_text(doc)
print("index.html", len(doc))
