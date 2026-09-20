# -*- coding: utf-8 -*-
"""Monta o site publicado no GitHub Pages (pasta site/).

Pagina unica e interativa: o proprio estudo, com cada figura montada no navegador pelo
bundle de graficos (frontend/dist/assets/study-charts.js).

  /                  estudo em portugues
  /en/               estudo em ingles
  /*.pdf, /en/*.pdf  PDFs estaticos (gerados por scripts/build_pdf.py, com o mesmo visual)
  /study/...         redirecionamentos dos enderecos antigos

Antes:  python scripts/build_artifact.py && python scripts/build_artifact_en.py
        (cd frontend && npm ci && npm run build)
Uso:    python scripts/build_pages_site.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "output"
DIST = BASE / "frontend" / "dist"
SITE = BASE / "site"

PAGES = {
    "pt": {
        "src": OUT / "case_study.html", "dest": "index.html", "lang": "pt-BR", "prefix": "./",
        "switch": ("en/", "Read in English"), "pdf": "a-metamorfose-do-poder-em-alfredo-chaves.pdf",
        "description": "A metamorfose do poder em Alfredo Chaves (ES): estudo de caso sobre as eleições municipais de 2004 a 2024, "
                       "com gráficos interativos, a partir de dados abertos do TSE e do IBGE.",
    },
    "en": {
        "src": OUT / "case_study_en.html", "dest": "en/index.html", "lang": "en", "prefix": "../",
        "switch": ("../", "Ler em Português"), "pdf": "the-metamorphosis-of-power-in-alfredo-chaves.pdf",
        "description": "The metamorphosis of power in Alfredo Chaves, ES, Brazil: a case study on the 2004-2024 municipal elections, "
                       "with interactive charts, built from TSE and IBGE open data.",
    },
}


def wrap(html: str, cfg: dict) -> str:
    """O estudo e um fragmento (title + style + div.wrap): completa doctype, head, botao de idioma e bundle."""
    cut = html.index("</style>") + len("</style>")
    head, body = html[:cut], html[cut:]
    prefix = cfg["prefix"]
    href, label = cfg["switch"]
    body = body.replace('<div class="wrap">', f'<div class="wrap">\n  <a class="lang-switch" href="{href}">{label}</a>', 1)
    return (
        "<!DOCTYPE html>\n"
        f'<html lang="{cfg["lang"]}">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="color-scheme" content="light">\n'
        '<meta name="theme-color" content="#faf9f7">\n'
        f'<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">\n'
        f'<link rel="icon" href="{prefix}favicon.ico" sizes="any">\n'
        f'<link rel="apple-touch-icon" href="{prefix}apple-touch-icon.png">\n'
        f'<meta name="description" content="{cfg["description"]}">\n'
        '<meta property="og:type" content="article">\n'
        f'<meta property="og:description" content="{cfg["description"]}">\n'
        f"{head}\n"
        f'<link rel="stylesheet" href="{prefix}assets/study-charts.css">\n'
        "</head>\n<body>"
        f"{body}\n"
        f'<script type="module" src="{prefix}assets/study-charts.js"></script>\n'
        "</body>\n</html>\n"
    )


def redirect(to: str) -> str:
    return (f'<!DOCTYPE html>\n<html><head><meta charset="UTF-8"><title>Redirecionando…</title>'
            f'<meta http-equiv="refresh" content="0; url={to}"><link rel="canonical" href="{to}">'
            f'<script>location.replace("{to}" + location.hash);</script></head>'
            f'<body><a href="{to}">{to}</a></body></html>\n')


def main() -> None:
    if not (DIST / "assets" / "study-charts.js").exists():
        raise SystemExit("Faltou o build dos graficos: cd frontend && npm ci && npm run build")
    shutil.rmtree(SITE, ignore_errors=True)
    (SITE / "en").mkdir(parents=True)
    shutil.copytree(DIST / "assets", SITE / "assets")
    for icon in ("favicon.svg", "favicon.ico", "apple-touch-icon.png", "icon-192.png"):  # frontend/public (scripts/build_favicon.py)
        shutil.copy2(DIST / icon, SITE / icon)
    (SITE / ".nojekyll").write_text("", encoding="utf-8")

    for cfg in PAGES.values():
        (SITE / cfg["dest"]).write_text(wrap(cfg["src"].read_text(encoding="utf-8"), cfg), encoding="utf-8")
        pdf = OUT / cfg["pdf"]
        target_dir = (SITE / cfg["dest"]).parent
        if pdf.exists():
            shutil.copy2(pdf, target_dir / cfg["pdf"])
        else:
            print(f"AVISO: {pdf.name} nao existe (rode scripts/build_pdf.py)")

    # enderecos antigos (/study/ e /study/en/) continuam funcionando
    (SITE / "study" / "en").mkdir(parents=True)
    (SITE / "study" / "index.html").write_text(redirect("../"), encoding="utf-8")
    (SITE / "study" / "en" / "index.html").write_text(redirect("../../en/"), encoding="utf-8")
    total = sum(f.stat().st_size for f in SITE.rglob("*") if f.is_file())
    print(f"Site montado em {SITE} ({total / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
