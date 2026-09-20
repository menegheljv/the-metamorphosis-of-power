import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ChartBody, LazyMount } from "./charts";
import { studyCharts, studyMeta, studySections } from "./studyData";
import type { ChartSpec, SectionSpec } from "./types";
import "./styles.css";

const PDF = "study/metamorfose-do-poder-2004-2024.pdf";
const REPO = "https://github.com/menegheljv/the-metamorphosis-of-power-2004-2024";

const minHeightFor = (kind: ChartSpec["kind"]) => (kind === "heatmap" ? 260 : kind === "timeline" ? 380 : 340);

function Figure({ spec, section }: { spec: ChartSpec; section: SectionSpec }) {
  const titleId = `t-${spec.slug}`;
  const descId = `d-${spec.slug}`;
  return (
    <figure className="exhibit" id={`fig-${spec.slug}`}>
      <div className="exhibit-head">
        <span className="tag">{spec.figure}</span>
        <span className="cap">{spec.cap}</span>
      </div>
      <div className="exhibit-body" role="group" aria-labelledby={titleId} aria-describedby={descId}>
        <h3 className="chart-title" id={titleId}>{spec.title}</h3>
        <p className="chart-sub">{spec.subtitle}</p>
        <p id={descId} className="sr-only">{spec.alt}</p>
        <LazyMount minHeight={minHeightFor(spec.kind)}><ChartBody spec={spec} /></LazyMount>
      </div>
      {spec.caption && <figcaption>{spec.caption}</figcaption>}
      <div className="exhibit-foot">
        <span>Fonte: {spec.source}</span>
        <a href={`study/#${section.study}`}>Ver no estudo &#8599;</a>
      </div>
    </figure>
  );
}

function App() {
  return (
    <>
      <nav className="topbar" aria-label="Navegação principal">
        <a className="brand" href="./">A metamorfose <span>&middot;</span> dados</a>
        <div className="nav-links">
          {studySections.map((s) => <a key={s.id} href={`#${s.id}`} className="nav-sec">{s.short}</a>)}
          <a className="nav-cta" href="study/">Estudo completo</a>
        </div>
      </nav>

      <div className="wrap">
        <header className="masthead">
          <div className="kicker">Estudo de caso &middot; Análise de dados eleitorais</div>
          <h1 className="title">
            A metamorfose do poder em Alfredo&nbsp;Chaves:
            <span className="subtitle">não vivemos mais como nossos pais</span>
          </h1>
          <p className="dek">{studyMeta.dek}</p>
          <div className="meta-row">
            <span><strong>Autor:</strong> João Victor Meneghel</span>
            <span><strong>Município:</strong> Alfredo Chaves &ndash; ES</span>
            <span><strong>Eleições:</strong> Municipais 2004 a 2024 (seis pleitos)</span>
            <span><strong>Fonte:</strong> dadosabertos.tse.jus.br</span>
          </div>
          <div className="actions">
            <a className="btn primary" href={PDF}>Baixar estudo em PDF</a>
            <a className="btn" href="study/">Ler o estudo completo</a>
            <a className="btn ghost" href="study/en/">Read in English</a>
          </div>
          <div className="ribbon">
            {studyMeta.ribbon.map((stat) => (
              <div className="stat" key={stat.label}>
                <div className="n">{stat.before} <span className="after">{stat.after}</span></div>
                <div className="l">{stat.label}</div>
              </div>
            ))}
          </div>
        </header>

        <p className="hint">
          <strong>Os 26 gráficos do estudo, em dados vivos.</strong> Passe o mouse ou use a tecla Tab para ver os valores; clique na legenda para ocultar uma série.
        </p>

        {studySections.map((section) => {
          const charts = studyCharts.filter((c) => c.section === section.id);
          return (
            <section id={section.id} key={section.id}>
              <div className="eyebrow">{section.eyebrow}</div>
              <h2>{section.title}</h2>
              <p className="section-link"><a href={`study/#${section.study}`}>Ler a análise desta seção no estudo &#8599;</a></p>
              {charts.map((chart) => <Figure key={chart.slug} spec={chart} section={section} />)}
            </section>
          );
        })}

        <footer className="site-footer">
          <div className="foot-brand">A metamorfose do poder em Alfredo Chaves</div>
          <p>
            Dados públicos e oficiais do TSE e do IBGE, tratados em Python, SQL e R. Os gráficos desta página são gerados no navegador a partir
            dos mesmos números do estudo editorial; o PDF mantém as imagens estáticas para impressão.
          </p>
          <div className="foot-links">
            <a href="study/">Estudo completo</a>
            <a href="study/en/">English</a>
            <a href={PDF}>PDF</a>
            <a href={REPO}>Código no GitHub &#8599;</a>
          </div>
          <div className="foot-author">João Victor Meneghel</div>
        </footer>
      </div>
    </>
  );
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
