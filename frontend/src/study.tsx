import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ChartBody, LazyMount } from "./charts";
import { LangContext, type Lang } from "./i18n";
import { studyChartsEn, studyChartsPt } from "./studyData";
import type { ChartSpec } from "./types";
import "./charts.css";

/**
 * Entrada unica: encontra cada <div data-chart="slug"> do estudo e monta ali o grafico
 * interativo. O idioma vem do <html lang>. Com ?print (usado para gerar o PDF) todos os
 * graficos sao montados de imediato e sem animacao.
 */
const lang: Lang = document.documentElement.lang.toLowerCase().startsWith("en") ? "en" : "pt";
const printMode = new URLSearchParams(window.location.search).has("print");
if (printMode) document.documentElement.classList.add("print-mode");

const specs = new Map<string, ChartSpec>((lang === "en" ? studyChartsEn : studyChartsPt).map((s) => [s.slug, s]));

const minHeightFor = (kind: ChartSpec["kind"]) =>
  kind === "heatmap" ? 260 : kind === "timeline" ? 380 : kind === "multiples" ? 700 : 320;

function ChartFigure({ spec }: { spec: ChartSpec }) {
  return (
    <>
      <div className="chart-title" role="heading" aria-level={4}>{spec.title}</div>
      <p className="chart-sub">{spec.subtitle}</p>
      {spec.alt && <p className="sr-only">{spec.alt}</p>}
      <LazyMount minHeight={minHeightFor(spec.kind)} eager={printMode}><ChartBody spec={spec} /></LazyMount>
    </>
  );
}

document.querySelectorAll<HTMLElement>("[data-chart]").forEach((el) => {
  const spec = specs.get(el.dataset.chart ?? "");
  if (!spec) return;
  el.textContent = "";
  createRoot(el).render(
    <StrictMode>
      <LangContext.Provider value={lang}><ChartFigure spec={spec} /></LangContext.Provider>
    </StrictMode>,
  );
});

if (printMode) window.setTimeout(() => document.documentElement.setAttribute("data-charts-ready", "1"), 1500);
