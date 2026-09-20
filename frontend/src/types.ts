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
  /** false = nao mostra a serie como item da legenda (ex.: segunda serie de "outros candidatos"). */
  legend?: boolean;
}

/** Candidato a prefeito de uma eleicao (legenda e tooltip). */
export interface CandInfo {
  n: string;
  p: string;
  side: Side;
  pct?: number;
  win?: boolean;
}

interface Base {
  slug: string;
  figure: string;
  title: string;
  subtitle: string;
  cap: string;
  caption: string;
  alt: string;
  /** Todos os candidatos a prefeito de cada eleicao (chave = ano), na ordem de votos. */
  cands?: Record<string, CandInfo[]>;
}

export interface CartesianSpec extends Base {
  kind: "cartesian";
  layers: Layer[];
  rows: Row[];
  unit: Unit;
  yDomain?: [number, number];
  yTicks?: number[];
  /** Linha horizontal de referencia (ex.: margem zero). */
  refY?: number;
  rightUnit?: Unit;
  rightDomain?: [number, number];
  denseX?: boolean;
  tiltX?: boolean;
  /** Chave da linha exibida em segunda linha sob o rotulo do eixo X (ex.: o partido sob o ano). */
  subKey?: string;
  /** Nomes da legenda por cor quando o grafico pinta cada barra pelo lado (ex.: Derrota / Vitoria). */
  sideLegend?: Partial<Record<Side, string>>;
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

export interface MultiplesSpec extends Base {
  kind: "multiples";
  layers: Layer[];
  unit: Unit;
  panels: { title: string; rows: Row[] }[];
}

export interface DistrictMapSpec extends Base {
  kind: "districtmap";
  viewBox: string;
  years: number[];
  /** Rotulos dos botoes (por padrao, o proprio numero). */
  labels?: Record<string, string>;
  defaultYear?: number;
  /** Quais botoes aparecem no PDF (padrao: 2020 e 2024). */
  printYears?: number[];
  /** Valores sao so percentuais (cenarios): esconde a contagem de votos. */
  pctOnly?: boolean;
  strings?: { hint?: string; aria?: string; suffix?: string; tableTitle?: string };
  districts: { name: string; path: string; lx: number; ly: number; values: Record<string, [number, number]>; /** votos de cada candidato (mesma ordem de `cands`) por ano */ cv?: Record<string, number[]> }[];
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
  rows: { secao: number; local: string; a: number | null; b: number | null }[];
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

export type ChartSpec = CartesianSpec | PanelsSpec | MultiplesSpec | DistrictMapSpec | HeatmapSpec | SlopeSpec | GridSpec | ScatterSpec | TimelineSpec;
