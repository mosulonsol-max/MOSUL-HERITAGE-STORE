#!/usr/bin/env python3
"""Add a discovery link to the built Pages copy without changing source history."""
import sys
from pathlib import Path

site = Path(sys.argv[1])
index = site / "index.html"
html = index.read_text(encoding="utf-8")
if 'href="catalog.html"' not in html:
    marker = "</main>"
    if marker not in html:
        raise SystemExit("index.html has no main element; refusing to publish a broken page")
    section = '''<section aria-label="Artwork previews"><div class="actions"><a class="btn primary" href="catalog.html" data-en="Explore new artwork previews" data-ar="استعرض المعاينات الفنية الجديدة">Explore new artwork previews</a></div></section>
'''
    html = html.replace(marker, section + marker, 1)
    index.write_text(html, encoding="utf-8")
