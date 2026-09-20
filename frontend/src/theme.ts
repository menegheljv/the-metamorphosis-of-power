import type { Side } from "./types";

/** Paleta do estudo (output/template.html): verde = grupo, vermelho = adversario, azul = terceiro colocado. */
export const COLORS: Record<Side, string> = {
  grupo: "#1f9d63",
  adversario: "#c8433a",
  terceiro: "#3d7fc4",
  info: "#2f6690",
  neutro: "#8f8f8f",
  muted: "#cdd3cd",
};

export const INK = "#333333";
export const GRID = "rgba(23,23,26,0.10)";
export const FONT = "'Bricolage Grotesque', system-ui, sans-serif";

/** Sem animacao para quem pede menos movimento e na versao para PDF (?print). */
export const prefersReducedMotion = () =>
  typeof window !== "undefined" &&
  (document.documentElement.classList.contains("print-mode") ||
    Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)").matches));

/** Escala do estudo: vermelho (<= 20%), creme (50%) e verde (>= 80%). Os valores reais dos distritos ficam
 *  entre 9% e 72%, entao esticar a escala deixa cada distrito com uma cor bem distinta. */
export const HEAT_LO = 20;
export const HEAT_HI = 80;

export function heatColor(v: number): { bg: string; fg: string } {
  const red = [200, 67, 58];
  const mid = [245, 239, 232];
  const green = [31, 157, 99];
  const t = Math.max(HEAT_LO, Math.min(HEAT_HI, v));
  const half = (HEAT_HI - HEAT_LO) / 2;
  const [from, to, k] = t <= 50 ? [red, mid, (t - HEAT_LO) / half] : [mid, green, (t - 50) / half];
  const rgb = from.map((c, i) => Math.round(c + (to[i] - c) * k));
  return { bg: `rgb(${rgb.join(",")})`, fg: Math.abs(t - 50) > half * 0.62 ? "#ffffff" : INK };
}
