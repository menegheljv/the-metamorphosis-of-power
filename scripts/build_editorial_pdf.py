"""Build the printable editorial study as a paginated PDF.

The source remains output/case_study.html, so factual content is not copied
or rewritten here. Chart data URIs are upgraded to the matching 300 DPI PNGs
from output/hires/ when available. Requires: weasyprint.

Usage:
  python scripts/build_hires_charts.py
  python scripts/build_editorial_pdf.py
"""
from __future__ import annotations

import base64
import re
import subprocess
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "output"
SOURCE = OUT / "case_study.html"
TARGET = OUT / "metamorfose-do-poder-2004-2024.pdf"


def chart_data_uri_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for source in OUT.glob("chart_*.b64"):
        hires = OUT / "hires" / f"{source.stem}.png"
        if not hires.exists():
            continue
        original = source.read_text(encoding="utf-8").strip()
        encoded = base64.b64encode(hires.read_bytes()).decode("ascii")
        mapping[original] = f"data:image/png;base64,{encoded}"
    return mapping


def upgrade_chart_images(fragment: str) -> tuple[str, int]:
    mapping = chart_data_uri_map()
    replaced = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal replaced
        replacement = mapping.get(match.group(1))
        if replacement is None:
            return match.group(0)
        replaced += 1
        return f'src="{replacement}"'

    return re.sub(r'src="data:image/png;base64,([^"]+)"', replace, fragment), replaced


source = SOURCE.read_text(encoding="utf-8")
style_match = re.search(r"<style>(.*?)</style>", source, flags=re.S)
fragment_match = re.search(r'(<div class="wrap">.*)', source, flags=re.S)
if not fragment_match:
    raise SystemExit("Could not find the editorial study wrapper.")

fragment, upgraded = upgrade_chart_images(fragment_match.group(1))
original_style = style_match.group(1) if style_match else ""

editorial_css = r"""
@page {
  size: A4;
  margin: 19mm 17mm 20mm;
  @top-left {
    content: "A METAMORFOSE DO PODER";
    color: #587064;
    font: 600 8pt "DejaVu Sans", sans-serif;
    letter-spacing: .08em;
  }
  @top-right {
    content: "ALFREDO CHAVES · 2004—2024";
    color: #8a968e;
    font: 8pt "DejaVu Sans", sans-serif;
  }
  @bottom-center {
    content: "Public Data Intelligence  ·  Página " counter(page) " de " counter(pages);
    color: #8a968e;
    font: 8pt "DejaVu Sans", sans-serif;
  }
}
@page:first {
  margin: 0;
  @top-left { content: none; }
  @top-right { content: none; }
  @bottom-center { content: none; }
}
body { background: #fff !important; color: #17231f; }
.pdf-cover {
  height: 257mm;
  padding: 34mm 25mm 25mm;
  background: #17231f;
  color: #fff;
  page-break-after: always;
  position: relative;
}
.pdf-cover .kicker { color: #ef7654; justify-content: flex-start; margin: 0 0 24mm; }
.pdf-cover h1 { color: #fff; font: 400 42pt/1.06 "DejaVu Sans", sans-serif; letter-spacing: -.03em; text-transform: none; white-space: normal; text-align: left; max-width: 155mm; margin: 0 0 9mm; }
.pdf-cover h1 span { display: block; color: #ef7654; font-size: .72em; margin-top: 8mm; }
.pdf-cover .subtitle { color: #d7e0d9; font: 15pt/1.45 "DejaVu Sans", sans-serif; max-width: 130mm; }
.pdf-cover .cover-rule { width: 34mm; height: 2px; background: #ef7654; margin: 18mm 0 7mm; }
.pdf-cover .cover-meta { position: absolute; left: 25mm; right: 25mm; bottom: 25mm; padding-top: 6mm; border-top: 1px solid #486057; color: #b9c8bc; font: 9pt/1.5 "DejaVu Sans", sans-serif; }
.pdf-cover .cover-meta strong { color: #fff; }
.pdf-note { margin: 0 0 12mm; padding: 5mm 6mm; background: #edf4ec; border-left: 3px solid #ef7654; color: #42584b; font: 9.5pt/1.5 "DejaVu Sans", sans-serif; }
.pdf-note strong { color: #17231f; }
.pdf-content { padding-top: 3mm; }
.pdf-content .wrap { max-width: none !important; padding: 0 !important; }
.pdf-content .masthead { padding-top: 0 !important; }
.pdf-content .print-actions, .pdf-content .lang-switch { display: none !important; }
.pdf-content h2 { break-after: avoid; }
.pdf-content section { break-inside: auto; }
.pdf-content figure, .pdf-content table, .pdf-content .card, .pdf-content .stat { break-inside: avoid; }
.pdf-content figure.chart-block { break-inside: avoid; margin: 8mm 0; }
.pdf-content figure.chart-block img { max-height: 105mm; object-fit: contain; }
.pdf-content img { max-width: 100%; }
.pdf-content a { color: inherit; text-decoration: none; }
"""

cover = """
<section class="pdf-cover">
  <div class="kicker">Estudo de caso · análise de dados eleitorais</div>
  <h1>A metamorfose do poder em Alfredo Chaves:<span>não vivemos mais como nossos pais</span></h1>
  <p class="subtitle">Uma reconstrução editorial da virada política municipal entre 2004 e 2024, baseada em dados públicos do TSE e do IBGE.</p>
  <div class="cover-rule"></div>
  <p class="subtitle" style="font-size:10pt">Relatório para leitura em tela e impressão · versão gerada a partir do estudo publicado</p>
  <div class="cover-meta"><strong>Autor:</strong> João Victor Meneghel<br><strong>Município:</strong> Alfredo Chaves — ES<br><strong>Nota:</strong> os gráficos desta edição são imagens estáticas em alta resolução para garantir compatibilidade de impressão.</div>
</section>
"""

html = f"""<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>A metamorfose do poder — relatório</title>
<style>{original_style}</style><style>{editorial_css}</style></head>
<body>{cover}<div class="pdf-note"><strong>Como ler este PDF.</strong> Esta edição é estática e adequada para impressão; a interface web principal mantém os gráficos interativos, com filtros, tooltip e zoom.</div><div class="pdf-content">{fragment}</div></body>
</html>"""

try:
    from weasyprint import HTML
except (ImportError, OSError):
    chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    edge = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
    browser = chrome if chrome.exists() else edge
    if not browser.exists():
        raise SystemExit("Install WeasyPrint or Chromium/Edge to generate the PDF.")
    with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as handle:
        handle.write(html)
        source_path = Path(handle.name)
    subprocess.run(
        [str(browser), "--headless", "--disable-gpu", "--no-sandbox",
         f"--print-to-pdf={TARGET}", str(source_path)],
        check=True,
    )
    source_path.unlink(missing_ok=True)
else:
    HTML(string=html, base_url=str(BASE)).write_pdf(TARGET)
print(f"Written: {TARGET}")
print(f"High-resolution chart images upgraded: {upgraded}")
print(f"Size (MB): {TARGET.stat().st_size / 1024 / 1024:.2f}")
