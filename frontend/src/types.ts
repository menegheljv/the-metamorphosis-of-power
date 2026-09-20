/** Cores semanticas do estudo: verde = o grupo, vermelho = adversario, azul = terceiro colocado. */
export type Side = "grupo" | "adversario" | "terceiro" | "neutro" | "info" | "muted";
export type Unit = "pct" | "int" | "brl" | "brl2" | "yr";
export type Row = Record<string, string | number | null>;

export interface Layer {
  type: "bar" | "line";
  key: string;
  label: string;
  color: Side;
  axis?: "left" | "right";
  stackId?: string;
  /** Pinta cada barra pela chave `side` da linha (ex.: 2020 vermelho, 2024 verde). */
  colorBySide?: boolean;
  /** Linha sem tracado (so os pontos), para categorias que nao formam serie temporal. */
  dotsOnly?: boolean;
}

interface Base {
  slug: string;
  figure: string;
  section: string;
  title: string;
  subtitle: string;
  source: string;
  cap: string;
  caption: string;
  alt: string;
}

export interface CartesianSpec extends Base {
  kind: "cartesian";
  layers: Layer[];
  rows: Row[];
  unit: Unit;
  yDomain?: [number, number];
  rightUnit?: Unit;
  rightDomain?: [number, number];
  denseX?: boolean;
  tiltX?: boolean;
}

export interface PanelRow {
  label: string;
  value: number;
  side: Side;
  note?: string;
}

export interface PanelsSpec extends Base {
  kind: "panels";
  unit: Unit;
  panels: { title?: string; rows: PanelRow[] }[];
}

export interface HeatmapSpec extends Base {
  kind: "heatmap";
  columns: string[];
  rows: { label: string; values: (number | null)[] }[];
}

export interface SlopeSpec extends Base {
  kind: "slope";
  aLabel: string;
  bLabel: string;
  rows: { secao: number; local: string; a: number | null; b: number | null; flip: boolean }[];
}

export interface GridSpec extends Base {
  kind: "grid";
  tiles: { secao: number; cat: "virou" | "ja" | "nova"; local: string; a: number | null; b: number | null }[];
}

export interface ScatterSpec extends Base {
  kind: "scatter";
  series: { key: string; label: string; color: Side; points: { x: number; y: number; secao: number }[] }[];
}

export interface TimelineSpec extends Base {
  kind: "timeline";
  election: string;
  polls: { registro: string; instituto: string; data: string }[];
}

export type ChartSpec = CartesianSpec | PanelsSpec | HeatmapSpec | SlopeSpec | GridSpec | ScatterSpec | TimelineSpec;

export interface SectionSpec {
  id: string;
  study: string;
  eyebrow: string;
  title: string;
  short: string;
}

export interface MetaSpec {
  dek: string;
  ribbon: { before: string; after: string; label: string }[];
}
