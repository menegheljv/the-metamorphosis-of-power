import express from "express";
import cors from "cors";

export type Observation = { region: string; period: string; participacao: number; acesso_digital: number; transparencia: number };
export const observations: Observation[] = [
  ["Aurora","2024-01-01",62,76,74],["Aurora","2024-07-01",68,79,77],
  ["Brisa","2024-01-01",55,68,63],["Brisa","2024-07-01",59,72,68],
  ["Cerrado","2024-01-01",71,81,82],["Cerrado","2024-07-01",73,84,85],
  ["Dourado","2024-01-01",48,61,58],["Dourado","2024-07-01",54,66,64],
  ["Estrela","2024-01-01",64,73,70],["Estrela","2024-07-01",69,78,75],
].map(([region, period, participacao, acesso_digital, transparencia]) => ({ region: String(region), period: String(period), participacao: Number(participacao), acesso_digital: Number(acesso_digital), transparencia: Number(transparencia) }));

export const app = express();
app.use(cors());
app.use(express.json());
app.get("/api/health", (_req, res) => res.json({ status: "ok" }));
app.get("/api/observations", (req, res) => {
  const region = typeof req.query.region === "string" ? req.query.region : undefined;
  const indicator = typeof req.query.indicator === "string" ? req.query.indicator : "participacao";
  if (!["participacao", "acesso_digital", "transparencia"].includes(indicator)) return res.status(400).json({ error: "Indicador inválido" });
  const rows = observations.filter(row => !region || row.region === region).map(row => ({ ...row, value: row[indicator as keyof Observation] }));
  res.json({ data: rows, indicator, synthetic: true });
});
