# -*- coding: utf-8 -*-
"""Gera os PDFs estaticos do estudo a partir da propria pagina interativa.

O site montado em site/ e aberto no Chrome (headless) com ?print: todos os graficos sao
montados de imediato, sem animacao, e o navegador imprime a pagina para PDF. Assim o PDF
usa exatamente o visual dos graficos interativos (mesmas cores, fonte e rotulos).

Antes:  python scripts/build_artifact.py && python scripts/build_artifact_en.py
        (cd frontend && npm run build) && python scripts/build_pages_site.py
Uso:    python scripts/build_pdf.py            # PT e EN
Saida:  output/metamorfose-do-poder-2004-2024.pdf
        output/the-metamorphosis-of-power-2004-2024.pdf
Requer o Chrome ou o Edge instalado (CHROME_PATH sobrescreve a busca).
"""
from __future__ import annotations

import functools
import http.server
import os
import shutil
import subprocess
import threading
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SITE = BASE / "site"
OUT = BASE / "output"

JOBS = [
    ("/?print", OUT / "metamorfose-do-poder-2004-2024.pdf"),
    ("/en/?print", OUT / "the-metamorphosis-of-power-2004-2024.pdf"),
]

CANDIDATES = [
    os.environ.get("CHROME_PATH", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
]


def find_browser() -> str:
    for c in CANDIDATES:
        if c and (Path(c).exists() or shutil.which(c)):
            return c
    raise SystemExit("Chrome/Edge nao encontrado: defina CHROME_PATH")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # noqa: D401
        pass


def main() -> None:
    if not (SITE / "index.html").exists():
        raise SystemExit("Rode antes: python scripts/build_pages_site.py")
    browser = find_browser()
    handler = functools.partial(Quiet, directory=str(SITE))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    try:
        for path, target in JOBS:
            tmp = target.with_suffix(".tmp.pdf")
            cmd = [
                browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                "--hide-scrollbars", "--window-size=720,1100", "--force-device-scale-factor=1",
                "--virtual-time-budget=30000", f"--print-to-pdf={tmp}",
                f"http://127.0.0.1:{port}{path}",
            ]
            subprocess.run(cmd, check=True, timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            tmp.replace(target)
            print(f"{target.name}: {target.stat().st_size / 1e6:.1f} MB")
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
