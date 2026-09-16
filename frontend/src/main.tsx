import { StrictMode, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  CartesianGrid,
  Brush,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TooltipProps } from "recharts";
import "./styles.css";

type Indicator = "participacao" | "acesso_digital" | "transparencia";
type Row = {
  region: string;
  period: string;
  value: number;
  participacao: number;
  acesso_digital: number;
  transparencia: number;
};

const fallback: Row[] = [
  ["Aurora", "2024-01-01", 62, 76, 74],
  ["Aurora", "2024-07-01", 68, 79, 77],
  ["Brisa", "2024-01-01", 55, 68, 63],
  ["Brisa", "2024-07-01", 59, 72, 68],
  ["Cerrado", "2024-01-01", 71, 81, 82],
  ["Cerrado", "2024-07-01", 73, 84, 85],
  ["Dourado", "2024-01-01", 48, 61, 58],
  ["Dourado", "2024-07-01", 54, 66, 64],
  ["Estrela", "2024-01-01", 64, 73, 70],
  ["Estrela", "2024-07-01", 69, 78, 75],
].map(([region, period, participacao, acesso_digital, transparencia]) => ({
  region: String(region),
  period: String(period),
  value: Number(participacao),
  participacao: Number(participacao),
  acesso_digital: Number(acesso_digital),
  transparencia: Number(transparencia),
}));

const labels: Record<Indicator, string> = {
  participacao: "Participação cívica",
  acesso_digital: "Acesso digital",
  transparencia: "Transparência",
};

function ChartTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  const point = payload[0];
  return (
    <div className="chart-tooltip" role="status">
      <strong>{label}</strong>
      <span>{point.value} pontos</span>
    </div>
  );
}

function App() {
  const [indicator, setIndicator] = useState<Indicator>("participacao");
  const [region, setRegion] = useState("Todas");
  const [rows, setRows] = useState<Row[]>(fallback);
  const [source, setSource] = useState("fallback local");

  useEffect(() => {
    const api = import.meta.env.VITE_API_URL || "http://localhost:3001";
    fetch(`${api}/api/observations?indicator=${indicator}`)
      .then((response) => (response.ok ? response.json() : Promise.reject()))
      .then((payload: { data: Row[] }) => {
        setRows(payload.data);
        setSource("API");
      })
      .catch(() => {
        setRows(
          fallback.map((row) => ({
            ...row,
            value: row[indicator],
          })),
        );
        setSource("fallback local");
      });
  }, [indicator]);

  const regions = ["Todas", ...Array.from(new Set(rows.map((row) => row.region)))];
  const filtered = rows.filter((row) => region === "Todas" || row.region === region);
  const latest = filtered.filter((row) => row.period === "2024-07-01");
  const average = latest.length
    ? latest.reduce((sum, row) => sum + row.value, 0) / latest.length
    : 0;
  const chart = filtered.map((row) => ({
    ...row,
    label: `${row.region} · ${row.period.slice(0, 7)}`,
  }));
  const change = useMemo(() => {
    if (!latest.length) return 0;
    const first = filtered.filter((row) => row.period === "2024-01-01");
    const firstAverage = first.reduce((sum, row) => sum + row.value, 0) / first.length;
    return average - firstAverage;
  }, [average, filtered, latest.length]);

  return (
    <main>
      <nav className="topbar" aria-label="Navegação principal">
        <a className="brand" href="./">
          PDI <span>·</span> observatório
        </a>
        <div className="nav-links">
          <a href="#explorar">Explorar dados</a>
          <a href="study/">Estudo completo</a>
          <a className="nav-cta" href="study/">Baixar estudo em PDF</a>
        </div>
      </nav>

      <header className="hero">
        <div className="eyebrow">PUBLIC DATA INTELLIGENCE · 2004—2024</div>
        <h1>A metamorfose do poder, <span>vista pelos dados.</span></h1>
        <p className="hero-copy">
          Um estudo aberto sobre Alfredo Chaves, ES, e uma camada exploratória
          para entender como dados eleitorais e públicos podem contar histórias
          com transparência.
        </p>
        <div className="hero-actions">
          <a className="primary-button" href="study/">Baixar estudo em PDF <span>↗</span></a>
          <a className="text-link" href="#explorar">Explorar o observatório ↓</a>
        </div>
        <div className="hero-meta">
          <span><strong>6</strong> pleitos analisados</span>
          <span><strong>42</strong> seções em 2024</span>
          <span><strong>TSE + IBGE</strong> dados públicos</span>
        </div>
      </header>

      <section className="notice" aria-label="Aviso sobre os dados">
        <span className="notice-icon" aria-hidden="true">i</span>
        <div><strong>Leitura responsável</strong><span> O estudo editorial usa dados oficiais; o explorador abaixo usa indicadores sintéticos para demonstração.</span></div>
      </section>

      <section className="metric-grid" aria-label="Métricas principais do estudo">
        <article className="metric-card featured"><span>VIRADA ELEITORAL</span><strong>1 → 42</strong><p>seções vencidas pela candidatura, de 2020 para 2024</p></article>
        <article className="metric-card"><span>VOTAÇÃO VÁLIDA</span><strong>37,8% → 56,4%</strong><p>participação do candidato no primeiro turno</p></article>
        <article className="metric-card"><span>REPRESENTAÇÃO</span><strong>3/9 → 5/9</strong><p>cadeiras da chapa na Câmara Municipal</p></article>
      </section>

      <section id="explorar" className="explorer">
        <div className="section-heading">
          <div><div className="eyebrow">CAMADA EXPLORATÓRIA</div><h2>Explore os sinais</h2><p>Filtre a amostra didática e veja como uma API de dados pode alimentar uma narrativa pública.</p></div>
          <span className="status" aria-live="polite"><i /> {source}</span>
        </div>
        <div className="controls" aria-label="Filtros do explorador">
          <label>Indicador<select value={indicator} onChange={(event) => setIndicator(event.target.value as Indicator)}>{Object.entries(labels).map(([key, name]) => <option key={key} value={key}>{name}</option>)}</select></label>
          <label>Região<select value={region} onChange={(event) => setRegion(event.target.value)}>{regions.map((item) => <option key={item}>{item}</option>)}</select></label>
        </div>
        <div className="explorer-grid">
          <div className="chart-panel"><div className="panel-heading"><div><h3>{labels[indicator]}</h3><p id="chart-help">Passe o mouse para destacar pontos. Use a faixa inferior para ampliar o período.</p></div><strong className={change >= 0 ? "positive" : "negative"}>{change >= 0 ? "+" : ""}{change.toFixed(1)} p.p.</strong></div><div className="chart" tabIndex={0} role="img" aria-label={`Gráfico interativo de ${labels[indicator]} por região e período`} aria-describedby="chart-help"><ResponsiveContainer width="100%" height={350}><LineChart data={chart}><CartesianGrid strokeDasharray="3 3" stroke="#e5e9f0" /><XAxis dataKey="label" tick={{ fontSize: 11 }} /><YAxis domain={[0, 100]} tick={{ fontSize: 11 }} /><Tooltip content={<ChartTooltip />} cursor={{ stroke: "#ef7654", strokeWidth: 1.5, strokeDasharray: "4 4" }} /><Brush dataKey="label" height={24} stroke="#ef7654" travellerWidth={12} /><Line type="monotone" dataKey="value" stroke="#ef7654" strokeWidth={3} dot={{ r: 4, fill: "#ef7654", strokeWidth: 2, stroke: "#fff" }} activeDot={{ r: 8, fill: "#ef7654", stroke: "#fff", strokeWidth: 3 }} animationDuration={700} animationEasing="ease-out" /></LineChart></ResponsiveContainer></div></div>
          <aside className="summary-panel"><span className="panel-label">RECORTE ATUAL</span><strong>{average.toFixed(1)}</strong><p>média no período de julho de 2024</p><div className="summary-rule" /><span className="panel-label">OBSERVAÇÕES</span><strong>{latest.length}</strong><p>regiões no filtro selecionado</p><a className="outline-button" href="study/">Ler o estudo completo ↗</a></aside>
        </div>
      </section>

      <footer><span>PUBLIC DATA INTELLIGENCE</span><span>Projeto aberto para estudar dados públicos com responsabilidade.</span><a href="study/">Estudo editorial</a></footer>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
