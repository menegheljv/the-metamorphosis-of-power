import type { Side, Unit } from "./types";

/** Paleta do estudo (output/template.html + scripts/viz*.py). */
export const COLORS: Record<Side, string> = {
  grupo: "#1f9d63",
  adversario: "#c8433a",
  terceiro: "#3d7fc4",
  info: "#2f6690",
  neutro: "#8f8f8f",
  muted: "#cdd3cd",
};

export const SIDE_LABEL: Partial<Record<Side, string>> = {
  grupo: "Grupo",
  adversario: "Adversário",
  terceiro: "Terceiro colocado",
  neutro: "Referência",
};

export const INK = "#333333";
export const TITLE_GRAY = "#4d4d4d";
export const GRID = "rgba(23,23,26,0.10)";
export const FONT = "'Bricolage Grotesque', system-ui, sans-serif";

const n0 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
const n1 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const n2 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function fmt(unit: Unit, v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  switch (unit) {
    case "pct": return `${n1.format(v)}%`;
    case "brl": return `R$ ${n0.format(v)}`;
    case "brl2": return `R$ ${n2.format(v)}`;
    case "yr": return `${n0.format(v)} anos`;
    default: return n0.format(v);
  }
}

/** Rotulo curto para eixos (R$ 150 mil, 12 mil). */
export function fmtAxis(unit: Unit, v: number): string {
  if (unit === "pct") return `${n0.format(v)}%`;
  if (unit === "yr") return n0.format(v);
  const prefix = unit === "brl" || unit === "brl2" ? "R$ " : "";
  if (Math.abs(v) >= 1_000_000) return `${prefix}${n1.format(v / 1_000_000)} mi`;
  if (Math.abs(v) >= 1000) return `${prefix}${n0.format(v / 1000)} mil`;
  return `${prefix}${n0.format(v)}`;
}

export const prefersReducedMotion = () =>
  typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

/** Interpola vermelho -> creme -> verde, centrado em 50% (mesma escala da Figura 6 do estudo). */
export function heatColor(v: number): { bg: string; fg: string } {
  const red = [200, 67, 58];
  const mid = [245, 239, 232];
  const green = [31, 157, 99];
  const t = Math.max(0, Math.min(100, v));
  const [from, to, k] = t <= 50 ? [red, mid, t / 50] : [mid, green, (t - 50) / 50];
  const rgb = from.map((c, i) => Math.round(c + (to[i] - c) * k));
  return { bg: `rgb(${rgb.join(",")})`, fg: t < 25 || t > 75 ? "#ffffff" : INK };
}
