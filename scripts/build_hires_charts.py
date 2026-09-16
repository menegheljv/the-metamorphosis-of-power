# -*- coding: utf-8 -*-
"""
Re-runs every chart-generating script under scripts/_hires_hook.py, so
each one ALSO emits a 300 DPI PNG into output/hires/, alongside its
normal 160 DPI output/*.b64 (used by the website, untouched by this).

Run this whenever a chart script changes, before scripts/build_charts_pdf.py.

Usage: python3 scripts/build_hires_charts.py
"""
import os
import runpy
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

CHART_SCRIPTS = [
    "campanha_digital", "coerencia_voto", "comparecimento_historico",
    "distritos_analysis", "historical_arc", "ibge_cruzamento",
    "ibge_demografico", "viz", "viz2", "viz3", "viz4", "viz5", "viz6",
]

import _hires_hook  # noqa: E402  (patches Figure.savefig + open() on import)

for name in CHART_SCRIPTS:
    print(f"=== {name} ===")
    runpy.run_path(os.path.join(SCRIPTS, f"{name}.py"), run_name="__main__")

print("\nDone. See output/hires/")
