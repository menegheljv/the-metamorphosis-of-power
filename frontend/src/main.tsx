import { StrictMode, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Brush,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TooltipProps } from "recharts";
import { studyCharts, type StudyChart } from "./studyData";
import "./styles.css";

const palette = ["#1f9d63", "#2f6690", "#c8433a", "#c9781f"];

function ChartTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip" role="status">
      <strong>{label}</strong>
      {payload.map((point) => <span key={String(point.dataKey)}>{String(point.dataKey)}: {String(point.value)}</span>)}
    </div>
  );
}

function InteractiveStudyChart({ chart }: { chart: StudyChart }) {
  const keys = chart.rows.length
    ? Object.keys(chart.rows[0]).filter((key) => chart.rows.some((row) => typeof row[key] === "number")).slice(0, 3)
    : [];
  const labelKey = chart.rows.length ? Object.keys(chart.rows[0])[0] : "label";
  const data = chart.rows.map((row, index) => ({ ...row, label: String(row[labelKey] ?? index + 1) }));
  return (
    <article className="study-chart-card" id={`grafico-${chart.slug}`}>
      <div className="study-chart-heading">
        <div><span className="chart-index">{chart.slug.replace(/_/g, " ")}</span><h3>{chart.title}</h3><p>Fonte: {chart.source}</p></div>
        <span className="interactive-badge">interativo</span>
      </div>
      <div className="study-chart" tabIndex={0} role="img" aria-label={`Gráfico interativo: ${chart.title}`} aria-describedby={`desc-${chart.slug}`}>
        <p id={`desc-${chart.slug}`} className="sr-only">Use o mouse ou teclado para explorar os valores. A faixa inferior permite selecionar a janela visível.</p>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data} margin={{ top: 12, right: 14, left: 0, bottom: 16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(23,23,26,.12)" />
            <XAxis dataKey="label" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip content={<ChartTooltip />} cursor={{ stroke: "#1f9d63", strokeDasharray: "4 4" }} />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            <Brush dataKey="label" height={22} stroke="#1f9d63" travellerWidth={10} />
            {keys.map((key, index) => <Line key={key} type="monotone" dataKey={key} stroke={palette[index]} strokeWidth={2.5} dot={{ r: 3, stroke: "#fff", strokeWidth: 1 }} activeDot={{ r: 7 }} animationDuration={650} animationEasing="ease-out" />)}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </article>
  );
}

function App() {
  const [query, setQuery] = useState("");
  const visibleCharts = useMemo(() => studyCharts.filter((chart) => `${chart.title} ${chart.source}`.toLocaleLowerCase().includes(query.toLocaleLowerCase())), [query]);
  return (
    <main>
      <nav className="topbar" aria-label="Navegação principal">
        <a className="brand" href="./">A metamorfose <span>·</span> observatório</a>
        <div className="nav-links"><a href="#graficos">Todos os gráficos</a><a href="study/">Estudo editorial</a><a className="nav-cta" href="study/metamorfose-do-poder-2004-2024.pdf">Baixar PDF</a></div>
      </nav>
      <header className="hero">
        <div className="eyebrow">ESTUDO DE CASO · ANÁLISE DE DADOS ELEITORAIS</div>
        <h1>A metamorfose do poder em <span>Alfredo Chaves</span></h1>
        <p className="hero-copy">Vinte anos de dados públicos do TSE e do IBGE, agora exploráveis em uma interface interativa que preserva a identidade editorial e os números do estudo original.</p>
        <div className="hero-actions"><a className="primary-button" href="study/metamorfose-do-poder-2004-2024.pdf">Baixar estudo em PDF ↗</a><a className="text-link" href="#graficos">Explorar todos os gráficos ↓</a></div>
        <div className="hero-meta"><span><strong>25</strong> gráficos do estudo</span><span><strong>6</strong> eleições municipais</span><span><strong>TSE + IBGE</strong> fontes públicas</span></div>
      </header>
      <section className="notice" aria-label="Nota metodológica"><span className="notice-icon" aria-hidden="true">i</span><div><strong>Interface interativa</strong><span> Os gráficos abaixo são renderizados no navegador a partir dos CSVs do estudo; passe o mouse para tooltips e use o Brush para ampliar períodos. O PDF mantém imagens estáticas para impressão.</span></div></section>
      <section id="graficos" className="explorer">
        <div className="section-heading"><div><div className="eyebrow">EXPLORAÇÃO COMPLETA</div><h2>Todos os gráficos, em dados vivos</h2><p>Catálogo navegável com títulos, fontes e descrições preservados do pipeline publicado.</p></div><span className="status"><i /> {visibleCharts.length} de {studyCharts.length}</span></div>
        <label className="search-label">Filtrar gráficos<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ex.: eleitorado, campanha, distrito" /></label>
        <div className="chart-catalog">{visibleCharts.map((chart) => <InteractiveStudyChart key={chart.slug} chart={chart} />)}</div>
      </section>
      <footer><span>PUBLIC DATA INTELLIGENCE</span><span>Dados e metodologia no estudo editorial.</span><a href="study/">Abrir estudo completo ↗</a></footer>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
