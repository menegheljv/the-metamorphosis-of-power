# -*- coding: utf-8 -*-
"""Gera os PDFs estaticos do estudo a partir da propria pagina interativa, em formato academico.

O site montado em site/ e aberto no Chrome (headless) com ?print: todos os graficos sao montados de
imediato, sem animacao, e o navegador imprime a pagina para PDF. Assim o PDF usa exatamente o visual
dos graficos interativos (mesmas cores, fonte e rotulos).

Alem do estudo, este script acrescenta ao PDF (a pagina web nao muda):
  - capa no estilo do Check Step Flow (azul-marinho, dourado, "CHECK" em sans + "step flow" em serifa);
  - resumo, palavras-chave e "como citar";
  - sumario com numero de pagina, e lista de figuras e tabelas;
  - numeracao de paginas no rodape e margens de trabalho academico.
Os numeros de pagina do sumario vem de uma primeira impressao (PyMuPDF localiza cada titulo) e sao
gravados numa segunda impressao, que e a final.

Antes:  python scripts/build_artifact.py && python scripts/build_artifact_en.py
        (cd frontend && npm run build) && python scripts/build_pages_site.py
Uso:    python scripts/build_pdf.py            # PT e EN
Saida:  output/a-metamorfose-do-poder-em-alfredo-chaves.pdf
        output/the-metamorphosis-of-power-in-alfredo-chaves.pdf
Requer: Chrome ou Edge instalado (CHROME_PATH sobrescreve a busca) e  pip install pymupdf
"""
from __future__ import annotations

import functools
import html as htmllib
import http.server
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path

import pymupdf

BASE = Path(__file__).resolve().parents[1]
SITE = BASE / "site"
OUT = BASE / "output"
FAVICON = (BASE / "frontend" / "public" / "favicon.svg").read_text(encoding="utf-8")

CANDIDATES = [
    os.environ.get("CHROME_PATH", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
]

URL = "https://menegheljv.github.io/the-metamorphosis-of-power/"

LANGS = {
    "pt": {
        "page": SITE / "index.html", "temp": "_print_pt.html", "url_path": "/_print_pt.html?print",
        "pdf": OUT / "a-metamorfose-do-poder-em-alfredo-chaves.pdf", "template": OUT / "template.html",
        "kicker": "ESTUDO DE CASO · ANÁLISE DE DADOS ELEITORAIS",
        "title_a": "A METAMORFOSE<br>DO PODER", "title_b": "em Alfredo Chaves",
        "subtitle": "não vivemos mais como nossos pais",
        "meta": [("Autor", "João Victor Meneghel"), ("Município", "Alfredo Chaves, ES"),
                 ("Eleições", "Municipais, 2004 a 2024"), ("Dados", "TSE e IBGE (dados abertos)")],
        "foot": "A metamorfose do poder em Alfredo Chaves",
        "abstract_h": "RESUMO", "keywords_h": "Palavras-chave", "cite_h": "COMO CITAR",
        "abstract": ("Estudo de caso sobre seis eleições municipais em Alfredo Chaves (ES), de 2004 a 2024. Depois de cinco derrotas consecutivas na disputa "
                     "para prefeito, a candidatura do grupo analisado venceu em 2024 nas 42 seções eleitorais do município, contra 1 de 36 seções em 2020. "
                     "A análise usa dados abertos do TSE (votação por seção, candidaturas, prestação de contas, pesquisas registradas) cruzados com dados do "
                     "IBGE, em Python, SQL e R, e apresenta os resultados em gráficos interativos. A seção final reúne cenários para 2028, declarados como "
                     "hipóteses e não como previsão."),
        "keywords": "eleições municipais; Alfredo Chaves; dados abertos; TSE; análise de dados eleitorais; cenários eleitorais",
        "cite": ("MENEGHEL, João Victor. <strong>A metamorfose do poder em Alfredo Chaves</strong>: não vivemos mais como nossos pais. "
                 f"Estudo de caso. 2026. Disponível em: {URL}."),
        "toc_h": "SUMÁRIO", "lof_h": "LISTA DE FIGURAS E TABELAS", "page_word": "p.",
        "fig": "Figura", "tab": "Tabela", "tag_re": r"(FIGURA|TABELA)",
    },
    "en": {
        "page": SITE / "en" / "index.html", "temp": "_print_en.html", "url_path": "/en/_print_en.html?print",
        "pdf": OUT / "the-metamorphosis-of-power-in-alfredo-chaves.pdf", "template": OUT / "template_en.html",
        "kicker": "CASE STUDY · ELECTORAL DATA ANALYSIS",
        "title_a": "THE METAMORPHOSIS<br>OF POWER", "title_b": "in Alfredo Chaves",
        "subtitle": "we no longer live like our parents",
        "meta": [("Author", "João Victor Meneghel"), ("Municipality", "Alfredo Chaves, ES, Brazil"),
                 ("Elections", "Municipal, 2004 to 2024"), ("Data", "TSE and IBGE (open data)")],
        "foot": "The metamorphosis of power in Alfredo Chaves",
        "abstract_h": "ABSTRACT", "keywords_h": "Keywords", "cite_h": "HOW TO CITE",
        "abstract": ("A case study of six municipal elections in Alfredo Chaves, Espírito Santo (Brazil), from 2004 to 2024. After five consecutive losses in the "
                     "mayoral race, the analyzed group's candidacy won in 2024 in all 42 voting precincts in the municipality, against 1 of 36 precincts in 2020. "
                     "The analysis uses open data from the Superior Electoral Court (TSE: precinct-level results, candidacies, campaign finance filings, registered polls) "
                     "cross-referenced with IBGE data, in Python, SQL and R, and presents the results in interactive charts. The final section gathers scenarios for "
                     "2028, stated as assumptions rather than a forecast."),
        "keywords": "municipal elections; Alfredo Chaves; open data; TSE; electoral data analysis; electoral scenarios",
        "cite": ("Meneghel, J. V. (2026). <strong>The metamorphosis of power in Alfredo Chaves</strong>: We no longer live like our parents [Case study]. "
                 f"{URL}en/"),
        "toc_h": "CONTENTS", "lof_h": "LIST OF FIGURES AND TABLES", "page_word": "p.",
        "fig": "Figure", "tab": "Table", "tag_re": r"(FIGURE|TABLE)",
    },
}


def find_browser() -> str:
    for c in CANDIDATES:
        if c and (Path(c).exists() or shutil.which(c)):
            return c
    raise SystemExit("Chrome/Edge nao encontrado: defina CHROME_PATH")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def strip(fragment: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def outline(template: Path):
    """Secoes (numero, titulo) e figuras/tabelas (rotulo, legenda) do estudo, na ordem do documento."""
    t = template.read_text(encoding="utf-8")
    sections = []
    for m in re.finditer(r'<section id="([^"]+)">\s*<div class="eyebrow">(.*?)</div>\s*<h2>(.*?)</h2>', t, re.S):
        eyebrow = strip(m.group(2))
        num, _, label = eyebrow.partition("·")
        sections.append({"id": m.group(1), "num": num.strip(), "label": label.strip(), "h2": strip(m.group(3))})
    items = []
    for m in re.finditer(r'<span class="tag">([^<]*)</span><span class="cap">([^<]*)</span>', t):
        tag = strip(m.group(1))
        if tag.lower().startswith(("figura", "figure", "tabela", "table")):
            items.append({"tag": tag, "cap": strip(m.group(2))})
    return sections, items


def cover_css() -> str:
    return """
@media screen { .pdf-front { display: none !important; } }
@media print {
  @page { size: A4; margin: 22mm 17mm 25mm 22mm;
    @bottom-left { content: "__FOOT__"; font: 500 8.5pt "Bricolage Grotesque", sans-serif; color: #5b6473; vertical-align: top; padding-top: 6mm; }
    @bottom-right { content: counter(page); font: 600 9.5pt "Bricolage Grotesque", sans-serif; color: #1a2540; vertical-align: top; padding-top: 6mm; }
  }
  @page cover { size: A4; margin: 0; @bottom-left { content: none; } @bottom-right { content: none; } }
  nav.toc { display: none !important; }
  .pdf-front { display: block; }
  .pdf-cover {
    page: cover; box-sizing: border-box; width: 210mm; height: 296mm; padding: 32mm 22mm 24mm 24mm; position: relative; overflow: hidden;
    display: flex; flex-direction: column; color: #f2f5fb; break-after: page;
    background: radial-gradient(ellipse 70% 60% at 82% 8%, #1a3566, transparent 60%), linear-gradient(160deg, #05070f 20%, #0b1730 75%);
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
  }
  .pdf-cover .map { position: absolute; right: -14mm; top: 30mm; width: 120mm; opacity: 0.16; }
  .pdf-cover .map path { fill: none; stroke: #d7ab5a; stroke-width: 0.9; }
  .pdf-cover .kick { display: flex; align-items: center; gap: 10px; font: 600 9.5pt "Bricolage Grotesque", sans-serif; letter-spacing: 0.14em; color: #d7ab5a; }
  .pdf-cover .kick::before { content: ""; width: 26px; height: 1px; background: #d7ab5a; }
  .pdf-cover h1.wm { margin: 22mm 0 0; display: flex; flex-direction: column; gap: 2mm; line-height: 0.98; position: relative; }
  .pdf-cover .wm-a { font: 800 44pt/1.0 "Bricolage Grotesque", -apple-system, "Segoe UI", Arial, sans-serif; letter-spacing: 0.01em; color: #f2f5fb; }
  .pdf-cover .wm-b { font: 400 40pt/1.1 Georgia, "Iowan Old Style", "Palatino Linotype", "Times New Roman", serif; font-style: normal; color: #f2f5fb; }
  .pdf-cover .sub { margin: 10mm 0 0; font: 600 15pt/1.3 "Bricolage Grotesque", sans-serif; color: #d7ab5a; position: relative; }
  .pdf-cover .rule { width: 34mm; height: 1.4px; background: #d7ab5a; margin: 10mm 0 8mm; }
  .pdf-cover .dek { font: 400 11.5pt/1.55 "Bricolage Grotesque", sans-serif; color: #b6c2de; max-width: 132mm; text-align: justify; margin: 0; position: relative; }
  .pdf-cover .meta { margin-top: auto; display: grid; grid-template-columns: repeat(2, 1fr); gap: 5mm 10mm; border-top: 1px solid rgba(255,255,255,0.18); padding-top: 8mm; position: relative; }
  .pdf-cover .meta div { font: 400 10.5pt/1.35 "Bricolage Grotesque", sans-serif; color: #f2f5fb; }
  .pdf-cover .meta span { display: block; font: 600 8pt "Bricolage Grotesque", sans-serif; letter-spacing: 0.12em; text-transform: uppercase; color: #d7ab5a; margin-bottom: 1mm; }
  .pdf-cover .year { position: absolute; right: 22mm; bottom: 24mm; font: 400 11pt Georgia, serif; color: #d7ab5a; }

  .pdf-page { break-after: page; font-family: "Bricolage Grotesque", sans-serif; color: #111; }
  .pdf-page h2.pdf-h { font: 700 13pt/1.3 "Bricolage Grotesque", sans-serif; letter-spacing: 0.08em; text-align: center; text-transform: uppercase; margin: 0 0 9mm; color: #111; white-space: normal; }
  .pdf-page h3.pdf-h3 { font: 700 10.5pt "Bricolage Grotesque", sans-serif; margin: 8mm 0 2mm; color: #111; text-align: left; }
  .pdf-page p { font-size: 11.5pt; line-height: 1.6; color: #111; text-align: justify; }
  .pdf-page .kw { font-size: 11pt; color: #111; text-align: left; }
  .pdf-page .cite { border-left: 3px solid #d7ab5a; padding: 2mm 0 2mm 5mm; background: #faf7ef; text-align: left; }
  .pdf-list { list-style: none; margin: 0; padding: 0; }
  .pdf-list li { display: flex; align-items: baseline; gap: 6px; padding: 1.7mm 0; font-size: 11pt; line-height: 1.35; color: #111; break-inside: avoid; }
  .pdf-list .n { flex: none; width: 13mm; font-weight: 700; }
  .pdf-list .t { flex: none; max-width: 78%; }
  .pdf-list .d { flex: 1; border-bottom: 1.5px dotted #888; transform: translateY(-3px); min-width: 8mm; }
  .pdf-list .p { flex: none; width: 9mm; text-align: right; font-variant-numeric: tabular-nums; }
  .pdf-list.lof li { font-size: 9.5pt; padding: 1.1mm 0; }
  .pdf-list.lof .n { width: 24mm; font-weight: 600; }
  .pdf-list.lof .t { max-width: 80%; }
}
"""


def front_html(cfg: dict, sections, items, pages: dict | None) -> str:
    def pg(key):
        return str(pages.get(key, "00")) if pages else "00"

    toc = "".join(
        f'<li><span class="n">{s["num"]}</span><span class="t">{htmllib.escape(s["label"])}</span><span class="d"></span>'
        f'<span class="p">{pg("s:" + s["id"])}</span></li>' for s in sections)
    lof = "".join(
        f'<li><span class="n">{htmllib.escape(i["tag"])}</span><span class="t">{htmllib.escape(i["cap"])}</span><span class="d"></span>'
        f'<span class="p">{pg("i:" + i["tag"])}</span></li>' for i in items)
    meta = "".join(f"<div><span>{k}</span>{v}</div>" for k, v in cfg["meta"])
    path = re.search(r'd="([^"]+)"', FAVICON).group(1)
    return f"""<div class="pdf-front">
  <section class="pdf-cover">
    <svg class="map" viewBox="0 0 100 100"><path d="{path}"/></svg>
    <div class="kick">{cfg["kicker"]}</div>
    <h1 class="wm"><span class="wm-a">{cfg["title_a"]}</span><span class="wm-b">{cfg["title_b"]}</span></h1>
    <p class="sub">{cfg["subtitle"]}</p>
    <div class="rule"></div>
    <p class="dek">{cfg["abstract"].split(". ")[0]}. {cfg["abstract"].split(". ")[1]}.</p>
    <div class="meta">{meta}</div>
    <div class="year">2026</div>
  </section>
  <section class="pdf-page">
    <h2 class="pdf-h">{cfg["abstract_h"]}</h2>
    <p>{cfg["abstract"]}</p>
    <p class="kw"><strong>{cfg["keywords_h"]}:</strong> {cfg["keywords"]}.</p>
    <h3 class="pdf-h3">{cfg["cite_h"]}</h3>
    <p class="cite">{cfg["cite"]}</p>
  </section>
  <section class="pdf-page">
    <h2 class="pdf-h">{cfg["toc_h"]}</h2>
    <ul class="pdf-list">{toc}</ul>
  </section>
  <section class="pdf-page">
    <h2 class="pdf-h">{cfg["lof_h"]}</h2>
    <ul class="pdf-list lof">{lof}</ul>
  </section>
</div>"""


def build_page(cfg: dict, sections, items, pages) -> None:
    src = cfg["page"].read_text(encoding="utf-8")
    foot = cfg["foot"].replace('"', '\\"')
    style = '<style id="pdf-front">' + cover_css().replace("__FOOT__", foot) + "</style>\n"
    out = src.replace("</head>", style + "</head>", 1)
    out = out.replace('<div class="wrap">', '<div class="wrap">\n' + front_html(cfg, sections, items, pages), 1)
    (cfg["page"].parent / cfg["temp"]).write_text(out, encoding="utf-8")


def print_pdf(browser: str, port: int, cfg: dict, target: Path) -> None:
    tmp = target.with_suffix(".tmp.pdf")
    cmd = [
        browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--hide-scrollbars", "--window-size=720,1100", "--force-device-scale-factor=1",
        "--virtual-time-budget=40000", f"--print-to-pdf={tmp}", f"http://127.0.0.1:{port}{cfg['url_path']}",
    ]
    subprocess.run(cmd, check=True, timeout=240, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tmp.replace(target)


def locate(pdf: Path, cfg: dict, sections, items) -> dict:
    """Numero da pagina (1 = capa) em que cada secao e cada figura/tabela comeca."""
    doc = pymupdf.open(pdf)
    texts = ["".join(p.get_text().split()) for p in doc]
    kick = [i for i, t in enumerate(texts) if "".join(cfg["kicker"].split()) in t]
    body = kick[1] if len(kick) > 1 else 4
    found: dict[str, int] = {}
    # Secoes e figuras aparecem na ordem do documento: cada busca comeca onde a anterior terminou,
    # para nao confundir o titulo de uma secao com o cabecalho de tabela de mesmo texto (ex.: "Perfil dos candidatos").
    start = body
    for s in sections:
        label = "".join(s["label"].upper().split())
        with_num = "".join((s["num"] + "·" + s["label"]).upper().split())
        hit = next((i for i in range(start, len(texts)) if with_num in texts[i]), None)
        if hit is None:
            hit = next((i for i in range(start, len(texts)) if label in texts[i]), None)
        if hit is not None:
            found["s:" + s["id"]] = hit + 1
            start = hit
    start = body
    for it in items:
        tag = "".join(it["tag"].upper().split())
        pat = re.compile(re.escape(tag) + r"(?![\d.])")
        hit = next((i for i in range(start, len(texts)) if pat.search(texts[i])), None)
        if hit is not None:
            found["i:" + it["tag"]] = hit + 1
            start = hit
    missing = [s["label"] for s in sections if "s:" + s["id"] not in found] + [i["tag"] for i in items if "i:" + i["tag"] not in found]
    if missing:
        print("AVISO: nao localizados no PDF:", missing)
    return found


def main() -> None:
    if not (SITE / "index.html").exists():
        raise SystemExit("Rode antes: python scripts/build_pages_site.py")
    browser = find_browser()
    handler = functools.partial(Quiet, directory=str(SITE))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    try:
        for cfg in LANGS.values():
            sections, items = outline(cfg["template"])
            target = cfg["pdf"]
            pages = None
            for attempt in range(3):  # a 1a passagem mede; as seguintes gravam e conferem
                build_page(cfg, sections, items, pages)
                print_pdf(browser, port, cfg, target)
                measured = locate(target, cfg, sections, items)
                if pages == measured:
                    break
                pages = measured
            (cfg["page"].parent / cfg["temp"]).unlink(missing_ok=True)
            n = len(pymupdf.open(target))
            print(f"{target.name}: {target.stat().st_size / 1e6:.1f} MB, {n} paginas")
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
