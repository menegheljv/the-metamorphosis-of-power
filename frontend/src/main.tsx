import { StrictMode, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import "./styles.css";

type Row = { region: string; period: string; value: number; participacao: number; acesso_digital: number; transparencia: number };
const fallback: Row[] = [
  ["Aurora","2024-01-01",62,76,74],["Aurora","2024-07-01",68,79,77],["Brisa","2024-01-01",55,68,63],["Brisa","2024-07-01",59,72,68],["Cerrado","2024-01-01",71,81,82],["Cerrado","2024-07-01",73,84,85],["Dourado","2024-01-01",48,61,58],["Dourado","2024-07-01",54,66,64],["Estrela","2024-01-01",64,73,70],["Estrela","2024-07-01",69,78,75],
].map(([region, period, participacao, acesso_digital, transparencia]) => ({ region: String(region), period: String(period), value: Number(participacao), participacao: Number(participacao), acesso_digital: Number(acesso_digital), transparencia: Number(transparencia) }));
const labels: Record<string, string> = { participacao: "Participação cívica", acesso_digital: "Acesso digital", transparencia: "Transparência" };
function App() {
  const [indicator, setIndicator] = useState("participacao");
  const [region, setRegion] = useState("Todas");
  const [rows, setRows] = useState<Row[]>(fallback);
  useEffect(() => { fetch(`${import.meta.env.VITE_API_URL || "http://localhost:3001"}/api/observations?indicator=${indicator}`).then(r => r.ok ? r.json() : Promise.reject()).then(x => setRows(x.data)).catch(() => setRows(fallback.map(r => ({ ...r, value: r[indicator as keyof Row] as number })))); }, [indicator]);
  const regions = ["Todas", ...Array.from(new Set(rows.map(r => r.region)))];
  const filtered = rows.filter(r => region === "Todas" || r.region === region);
  const latest = filtered.filter(r => r.period === "2024-07-01");
  const average = latest.length ? latest.reduce((sum, r) => sum + r.value, 0) / latest.length : 0;
  const chart = filtered.map(r => ({ ...r, label: `${r.region} · ${r.period.slice(0, 7)}` }));
  return <main><header><div className="eyebrow">OBSERVATÓRIO · DEMO</div><h1>Public Data <span>Intelligence</span></h1><p className="subtitle">Explore sinais sintéticos para praticar análise pública responsável.</p></header>
    <section className="notice">⚗️ <strong>Ambiente demonstrativo</strong><span>Todos os valores são fictícios e não representam eleições, pessoas ou governos reais.</span></section>
    <div className="controls"><label>Indicador<select value={indicator} onChange={e => setIndicator(e.target.value)}>{Object.entries(labels).map(([key, name]) => <option key={key} value={key}>{name}</option>)}</select></label><label>Região<select value={region} onChange={e => setRegion(e.target.value)}>{regions.map(r => <option key={r}>{r}</option>)}</select></label></div>
    <section className="cards"><article><small>MÉDIA · JUL 2024</small><strong>{average.toFixed(1)}<em> pontos</em></strong><p>{labels[indicator]}</p></article><article><small>REGIÕES OBSERVADAS</small><strong>{latest.length}</strong><p>com dados no período</p></article><article><small>JANELA TEMPORAL</small><strong>2</strong><p>períodos sintéticos</p></article></section>
    <section className="panel"><div className="panel-title"><div><h2>Evolução por região</h2><p>Valores do indicador selecionado</p></div><span className="badge">● ATUALIZADO · JUL 2024</span></div><div className="chart"><ResponsiveContainer width="100%" height={320}><LineChart data={chart}><CartesianGrid strokeDasharray="3 3" stroke="#e5e9f0" /><XAxis dataKey="label" tick={{ fontSize: 11 }} /><YAxis domain={[0, 100]} tick={{ fontSize: 11 }} /><Tooltip /><Line type="monotone" dataKey="value" stroke="#3874ff" strokeWidth={3} dot={{ r: 4, fill: "#3874ff" }} /></LineChart></ResponsiveContainer></div></section>
    <footer>Fonte: dataset sintético local · Projeto educacional de inteligência de dados públicos</footer>
  </main>;
}
createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
