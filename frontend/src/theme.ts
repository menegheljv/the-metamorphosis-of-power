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
