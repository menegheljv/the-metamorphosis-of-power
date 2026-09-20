import { createContext, useContext, useMemo } from "react";
import type { Side, Unit } from "./types";

export type Lang = "pt" | "en";
export const LangContext = createContext<Lang>("pt");

const dict = {
  pt: {
    locale: "pt-BR",
    side: { grupo: "Grupo", adversario: "Adversário", terceiro: "Terceiro colocado", neutro: "Referência", info: "", muted: "" } as Record<Side, string>,
    legendLabel: "Legenda do gráfico",
    before: "2020, antes da virada",
    after: "2024, depois da virada",
    reference: "Referência (população e eleitorado)",
    precinct: "Seção",
    mayor: "Prefeito",
    council: "Vereador",
    difference: "Diferença",
    total: "Total",
    year: "anos",
    newPrecinct: "seção nova",
    in2020: "em 2020",
    in2024: "em 2024",
    xAxisMayor: "% do grupo para prefeito",
    yAxisCouncil: "% do grupo para vereador",
    sameShare: "mesmo % nos dois cargos",
    slopeAria: "Gráfico de inclinação por seção",
    gridAria: "Seções eleitorais",
    gridHint: "Toque ou passe o mouse em uma seção para ver o local de votação e a votação de cada eleição.",
    slopeHint: (rose: number, both: number) =>
      `Toque ou passe o mouse sobre uma linha para ver a seção. ${rose} de ${both} seções com voto em 2020 subiram para o candidato do grupo; os pontos cinza são as seções novas.`,
    tile: { virou: "Derrota em 2020, vitória em 2024", ja: "Já vencida em 2020", nova: "Seção nova (criada após 2020)" },
    district: "Distrito",
    noData: "sem dado",
    na: "s/d",
    election: "Eleição",
    timelineAria: "Linha do tempo das pesquisas registradas",
    months: ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
    ownScale: "escala própria",
    electionButtons: "Escolha a eleição",
    mapAria: "Mapa dos distritos de Alfredo Chaves",
    mapHint: "Toque ou passe o mouse em um distrito para ver os votos. Escolha a eleição nos botões acima.",
    ofValid: "dos votos válidos para prefeito",
    votesOf: (g: number, t: number) => `${g} votos do candidato do grupo em ${t} votos válidos`,
    scaleLow: "grupo abaixo",
    scaleHigh: "grupo acima",
    tableTitle: "Todas as eleições, por distrito",
  },
  en: {
    locale: "en-US",
    side: { grupo: "Group", adversario: "Opponent", terceiro: "Third place", neutro: "Reference", info: "", muted: "" } as Record<Side, string>,
    legendLabel: "Chart legend",
    before: "2020, before the turnaround",
    after: "2024, after the turnaround",
    reference: "Reference (population and electorate)",
    precinct: "Precinct",
    mayor: "Mayor",
    council: "Council",
    difference: "Difference",
    total: "Total",
    year: "years",
    newPrecinct: "new precinct",
    in2020: "in 2020",
    in2024: "in 2024",
    xAxisMayor: "% for the group, mayoral race",
    yAxisCouncil: "% for the group, council race",
    sameShare: "same % in both races",
    slopeAria: "Slope chart by precinct",
    gridAria: "Voting precincts",
    gridHint: "Tap or hover over a precinct to see its polling place and its vote in each election.",
    slopeHint: (rose: number, both: number) =>
      `Tap or hover over a line to see the precinct. ${rose} of ${both} precincts with votes in 2020 moved up for the group's candidate; gray dots are new precincts.`,
    tile: { virou: "Lost in 2020, won in 2024", ja: "Already won in 2020", nova: "New precinct (created after 2020)" },
    district: "District",
    noData: "no data",
    na: "n/a",
    election: "Election",
    timelineAria: "Timeline of registered polls",
    months: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    ownScale: "own scale",
    electionButtons: "Choose the election",
    mapAria: "Map of the districts of Alfredo Chaves",
    mapHint: "Tap or hover over a district to see the votes. Choose the election with the buttons above.",
    ofValid: "of the valid votes for mayor",
    votesOf: (g: number, t: number) => `${g} votes for the group's candidate out of ${t} valid votes`,
    scaleLow: "group behind",
    scaleHigh: "group ahead",
    tableTitle: "All elections, by district",
  },
};

export type Dict = (typeof dict)["pt"];

export function useI18n() {
  const lang = useContext(LangContext);
  return useMemo(() => {
    const t = dict[lang];
    const n0 = new Intl.NumberFormat(t.locale, { maximumFractionDigits: 0 });
    const n1 = new Intl.NumberFormat(t.locale, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
    const n2 = new Intl.NumberFormat(t.locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    const fmt = (unit: Unit, v: number | null | undefined): string => {
      if (v === null || v === undefined || Number.isNaN(v)) return "—";
      switch (unit) {
        case "pct": return `${n1.format(v)}%`;
        case "brl": return `R$ ${n0.format(v)}`;
        case "brl2": return `R$ ${n2.format(v)}`;
        case "yr": return `${n0.format(v)} ${t.year}`;
        default: return n0.format(v);
      }
    };

    /** Rotulo curto para eixos (R$ 150 mil / R$ 150k, 12 mil / 12k). */
    const fmtAxis = (unit: Unit, v: number): string => {
      if (unit === "pct") return `${n0.format(v)}%`;
      if (unit === "yr") return n0.format(v);
      const prefix = unit === "brl" || unit === "brl2" ? "R$ " : "";
      const thousand = lang === "en" ? "k" : " mil";
      if (Math.abs(v) >= 1_000_000) return `${prefix}${n1.format(v / 1_000_000)} ${lang === "en" ? "M" : "mi"}`;
      if (Math.abs(v) >= 1000) return `${prefix}${n0.format(v / 1000)}${thousand}`;
      return `${prefix}${n0.format(v)}`;
    };

    /** dd/mm/aaaa (pt) ou mm/dd/yyyy (en) a partir de AAAA-MM-DD. */
    const dateLong = (iso: string) => {
      const [y, m, d] = iso.split("-");
      return lang === "en" ? `${m}/${d}/${y}` : `${d}/${m}/${y}`;
    };
    const dateShort = (iso: string) => {
      const [, m, d] = iso.split("-");
      return lang === "en" ? `${m}/${d}` : `${d}/${m}`;
    };

    return { lang, t, fmt, fmtAxis, dateLong, dateShort };
  }, [lang]);
}
