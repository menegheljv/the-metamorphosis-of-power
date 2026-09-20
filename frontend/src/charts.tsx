import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  LabelList,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type {
  CartesianSpec,
  ChartSpec,
  GridSpec,
  HeatmapSpec,
  MultiplesSpec,
  PanelsSpec,
  ScatterSpec,
  Side,
  SlopeSpec,
  TimelineSpec,
  Unit,
} from "./types";
import { useI18n } from "./i18n";
import { COLORS, FONT, GRID, INK, heatColor, prefersReducedMotion } from "./theme";

const tick = { fontSize: 11, fill: INK, fontFamily: FONT };
const labelStyle = { fontSize: 11, fill: INK, fontFamily: FONT, fontWeight: 600 };

/* ------------------------------------------------------------------ */
/* Pecas compartilhadas                                                */
/* ------------------------------------------------------------------ */

interface LegendItem { key: string; label: string; color: string }

/** Telas estreitas (celular): eixos menores, rotulos inclinados, SVGs proprios em vez de encolhidos. */
function useNarrow(max = 640) {
  const query = `(max-width: ${max}px)`;
  const [narrow, setNarrow] = useState(() => typeof window !== "undefined" && window.matchMedia(query).matches);
  useEffect(() => {
    const mq = window.matchMedia(query);
    const on = () => setNarrow(mq.matches);
    on();
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, [query]);
  return narrow;
}

function LegendChips({ items, hidden, toggle }: { items: LegendItem[]; hidden?: Set<string>; toggle?: (key: string) => void }) {
  const { t } = useI18n();
  if (!items.length) return null;
  return (
    <div className="legend" role="group" aria-label={t.legendLabel}>
      {items.map((item) => {
        const off = hidden?.has(item.key);
        const inner = (<><i style={{ background: item.color }} />{item.label}</>);
        return toggle ? (
          <button key={item.key} type="button" className={`legend-chip${off ? " off" : ""}`} aria-pressed={!off} onClick={() => toggle(item.key)}>{inner}</button>
        ) : (
          <span key={item.key} className="legend-chip static">{inner}</span>
        );
      })}
    </div>
  );
}

function useToggleSet() {
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const toggle = (key: string) =>
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  return { hidden, toggle };
}

function Tip({ title, lines, note }: { title?: ReactNode; lines: { color?: string; text: ReactNode }[]; note?: ReactNode }) {
  return (
    <div className="chart-tooltip" role="status">
      {title !== undefined && <strong>{title}</strong>}
      {lines.map((line, i) => (
        <span key={i}>{line.color && <i style={{ background: line.color }} />}{line.text}</span>
      ))}
      {note && <em>{note}</em>}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Cartesiano: linhas, barras, barras empilhadas e eixo duplo          */
/* ------------------------------------------------------------------ */

function CartesianChart({ spec }: { spec: CartesianSpec }) {
  const { hidden, toggle } = useToggleSet();
  const { t, fmt, fmtAxis } = useI18n();
  const narrow = useNarrow();
  const reduce = prefersReducedMotion();
  const hasRight = spec.layers.some((l) => l.axis === "right");
  const rightUnit: Unit = spec.rightUnit ?? spec.unit;
  const unitOf = (key: string): Unit => (spec.layers.find((l) => l.key === key)?.axis === "right" ? rightUnit : spec.unit);
  const bars = spec.layers.filter((l) => l.type === "bar");
  const lines = spec.layers.filter((l) => l.type === "line");
  const singleColored = spec.layers.length === 1 && spec.layers[0].colorBySide;
  const stacked = bars.some((b) => b.stackId);
  const showBarLabels = spec.rows.length <= (narrow ? 5 : 8) && !hasRight && !stacked && bars.length > 0 && lines.length === 0;
  const maxLen = Math.max(...spec.rows.map((r) => String(r.x).length));
  const tilt = spec.tiltX || (spec.rows.length > 3 && maxLen > (narrow ? 8 : 12));
  const interval = spec.denseX ? Math.ceil(spec.rows.length / (narrow ? 5 : 9)) : 0;
  const yW = narrow ? 44 : hasRight ? 60 : 64;

  const legendItems: LegendItem[] = singleColored
    ? [
        ...(spec.rows.some((r) => r.side === "adversario") ? [{ key: "adv", label: t.before, color: COLORS.adversario }] : []),
        ...(spec.rows.some((r) => r.side === "grupo") ? [{ key: "grp", label: t.after, color: COLORS.grupo }] : []),
        ...(spec.rows.some((r) => r.side === "neutro") ? [{ key: "ref", label: t.reference, color: COLORS.neutro }] : []),
      ]
    : spec.layers.map((l) => ({ key: l.key, label: l.label, color: COLORS[l.color] }));

  const sideFill = (row: (typeof spec.rows)[number], fallback: Side) => COLORS[(row.side as Side) ?? fallback] ?? COLORS[fallback];

  const CartesianTip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    const row = payload[0].payload;
    return (
      <Tip
        title={label}
        lines={payload.map((p: any) => {
          const layer = spec.layers.find((l) => l.key === p.dataKey);
          const color = layer?.colorBySide ? sideFill(row, layer.color) : p.color ?? p.stroke;
          return { color, text: <>{p.name}: <b>{fmt(unitOf(String(p.dataKey)), p.value)}</b></> };
        })}
        note={row.note}
      />
    );
  };

  return (
    <>
      <div className="chart-box" style={{ height: tilt ? (narrow ? 360 : 380) : narrow ? 300 : 340 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={spec.rows} margin={{ top: 22, right: hasRight ? 4 : narrow ? 8 : 16, left: 0, bottom: tilt ? 4 : 8 }} barCategoryGap={spec.denseX ? 0 : "22%"} barGap={4}>
            <CartesianGrid stroke={GRID} vertical={false} />
            <XAxis
              dataKey="x"
              tick={{ ...tick, fontSize: narrow ? 10 : 11 }}
              tickLine={false}
              axisLine={{ stroke: GRID }}
              interval={interval}
              angle={tilt ? -35 : 0}
              textAnchor={tilt ? "end" : "middle"}
              height={tilt ? (narrow ? 84 : 78) : 30}
              tickMargin={6}
            />
            <YAxis
              yAxisId="left"
              tick={{ ...tick, fontSize: narrow ? 10 : 11 }}
              tickLine={false}
              axisLine={false}
              width={yW}
              domain={spec.yDomain ?? [0, "auto"]}
              allowDecimals={false}
              tickFormatter={(v: number) => fmtAxis(spec.unit, v)}
            />
            {hasRight && (
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ ...tick, fontSize: narrow ? 10 : 11 }}
                tickLine={false}
                axisLine={false}
                width={narrow ? 40 : 54}
                domain={spec.rightDomain ?? [0, "auto"]}
                allowDecimals={false}
                tickFormatter={(v: number) => fmtAxis(rightUnit, v)}
              />
            )}
            <Tooltip content={<CartesianTip />} cursor={bars.length ? { fill: "rgba(23,23,26,0.04)" } : { stroke: "rgba(23,23,26,0.22)", strokeWidth: 1 }} />
            {bars.map((l) => (
              <Bar
                key={l.key}
                yAxisId={l.axis === "right" ? "right" : "left"}
                dataKey={l.key}
                name={l.label}
                fill={COLORS[l.color]}
                stackId={l.stackId}
                hide={hidden.has(l.key)}
                radius={l.stackId ? 0 : [4, 4, 0, 0]}
                maxBarSize={spec.denseX ? 10 : 64}
                isAnimationActive={!reduce}
                animationDuration={700}
              >
                {l.colorBySide && spec.rows.map((row, i) => <Cell key={i} fill={sideFill(row, l.color)} />)}
                {showBarLabels && <LabelList dataKey={l.key} position="top" formatter={(v: any) => fmt(unitOf(l.key), Number(v))} style={labelStyle} />}
              </Bar>
            ))}
            {lines.map((l) => (
              <Line
                key={l.key}
                yAxisId={l.axis === "right" ? "right" : "left"}
                type="monotone"
                dataKey={l.key}
                name={l.label}
                stroke={COLORS[l.color]}
                strokeWidth={l.dotsOnly ? 0 : 2.75}
                dot={{ r: l.dotsOnly ? 6 : 4.5, stroke: "#ffffff", strokeWidth: 1.5, fill: COLORS[l.color] }}
                activeDot={{ r: l.dotsOnly ? 8.5 : 7.5, stroke: "#ffffff", strokeWidth: 2 }}
                connectNulls
                hide={hidden.has(l.key)}
                isAnimationActive={!reduce}
                animationDuration={800}
              >
                {lines.length === 1 && spec.rows.length <= 7 && (
                  <LabelList dataKey={l.key} position="top" offset={10} formatter={(v: any) => fmt(unitOf(l.key), Number(v))} style={labelStyle} />
                )}
              </Line>
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <LegendChips items={legendItems} hidden={hidden} toggle={singleColored ? undefined : toggle} />
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Multiplos pequenos: um grafico por distrito                         */
/* ------------------------------------------------------------------ */

function MultiplesChart({ spec }: { spec: MultiplesSpec }) {
  const { hidden, toggle } = useToggleSet();
  const { t, fmt, fmtAxis } = useI18n();
  const narrow = useNarrow();
  const reduce = prefersReducedMotion();

  const legendItems = spec.layers.map((l) => ({ key: l.key, label: l.label, color: COLORS[l.color] }));
  const top = spec.layers[0]; // a linha do grupo recebe os rotulos

  const PanelTip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    const row = payload[0].payload;
    return (
      <Tip
        title={label}
        lines={[
          ...payload.map((p: any) => ({ color: p.color, text: <>{p.name}: <b>{fmt(spec.unit, p.value)}</b></> })),
          { text: <>{t.total}: <b>{fmt(spec.unit, Number(row.total))}</b></> },
        ]}
        note={row.note}
      />
    );
  };

  return (
    <>
      <div className="multiples">
        {spec.panels.map((panel, pi) => (
          <div key={panel.title} className="multiple">
            <h4 className="panel-title">{panel.title}</h4>
            <div style={{ height: pi === 0 ? (narrow ? 250 : 320) : narrow ? 230 : 270 }}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={panel.rows} margin={{ top: 22, right: narrow ? 14 : 22, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke={GRID} vertical={false} />
                  <XAxis dataKey="x" tick={{ ...tick, fontSize: narrow ? 10 : 11 }} tickLine={false} axisLine={{ stroke: GRID }} interval={0} tickFormatter={(v: string) => (narrow ? `’${String(v).slice(2)}` : String(v))} />
                  <YAxis tick={{ ...tick, fontSize: narrow ? 10 : 11 }} tickLine={false} axisLine={false} width={narrow ? 40 : 48} allowDecimals={false} domain={[0, "auto"]} tickFormatter={(v: number) => fmtAxis(spec.unit, v)} />
                  <Tooltip content={<PanelTip />} cursor={{ stroke: "rgba(23,23,26,0.22)", strokeWidth: 1 }} />
                  {spec.layers.map((l) => (
                    <Line
                      key={l.key}
                      type="monotone"
                      dataKey={l.key}
                      name={l.label}
                      stroke={COLORS[l.color]}
                      strokeWidth={2.5}
                      dot={{ r: 3.5, stroke: "#ffffff", strokeWidth: 1.5, fill: COLORS[l.color] }}
                      activeDot={{ r: 6, stroke: "#ffffff", strokeWidth: 2 }}
                      connectNulls
                      hide={hidden.has(l.key)}
                      isAnimationActive={!reduce}
                      animationDuration={700}
                    >
                      {l.key === top.key && (
                        <LabelList
                          dataKey={l.key}
                          content={(p: any) => {
                            const row: any = panel.rows[p.index];
                            const last = panel.rows.length - 1;
                            const above = Number(row?.[top.key]) >= Number(row?.[spec.layers[1]?.key]) || Number(p.y) > 118; // perto do eixo X, o rotulo sobe
                            const anchor = p.index === 0 ? "start" : p.index === last ? "end" : "middle";
                            return (
                              <text x={Number(p.x)} y={Number(p.y) + (above ? -9 : 17)} textAnchor={anchor} style={{ ...labelStyle, fontSize: narrow ? 10 : 11 }}>
                                {fmt(spec.unit, Number(p.value))}
                              </text>
                            );
                          }}
                        />
                      )}
                    </Line>
                  ))}
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>
      <p className="scale-note">{t.ownScale}</p>
      <LegendChips items={legendItems} hidden={hidden} toggle={toggle} />
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Paineis de barras horizontais (candidatos, vereadores)              */
/* ------------------------------------------------------------------ */

function PanelsChart({ spec }: { spec: PanelsSpec }) {
  const { t, fmt } = useI18n();
  const narrow = useNarrow();
  const reduce = prefersReducedMotion();
  const max = Math.max(...spec.panels.flatMap((p) => p.rows.map((r) => r.value)), 1);
  const sides = Array.from(new Set(spec.panels.flatMap((p) => p.rows.map((r) => r.side))));
  const legend: LegendItem[] = (["grupo", "adversario", "terceiro"] as Side[])
    .filter((s) => sides.includes(s))
    .map((s) => ({ key: s, label: t.side[s], color: COLORS[s] }));

  const PanelTip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;
    const row = payload[0].payload;
    return <Tip title={row.label} lines={[{ color: COLORS[row.side as Side], text: <>{t.side[row.side as Side]}: <b>{fmt(spec.unit, row.value)}</b></> }]} note={row.note} />;
  };

  return (
    <>
      <div className="panels" style={{ gridTemplateColumns: `repeat(${spec.panels.length}, minmax(0, 1fr))` }}>
        {spec.panels.map((panel, idx) => {
          const labelW = Math.min(narrow ? 128 : 172, Math.max(...panel.rows.map((r) => r.label.length)) * 6.3 + 14);
          return (
            <div key={idx} className="panel">
              {panel.title && <h4 className="panel-title">{panel.title}</h4>}
              <div style={{ height: panel.rows.length * 40 + 24 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={panel.rows} layout="vertical" margin={{ top: 4, right: narrow ? 62 : 82, left: 0, bottom: 0 }} barCategoryGap={10}>
                    <CartesianGrid horizontal={false} stroke={GRID} />
                    <XAxis type="number" domain={[0, max]} hide />
                    <YAxis type="category" dataKey="label" width={labelW} tick={{ ...tick, fontSize: narrow ? 10.5 : 11 }} tickLine={false} axisLine={false} interval={0} />
                    <Tooltip content={<PanelTip />} cursor={{ fill: "rgba(23,23,26,0.05)" }} />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={22} isAnimationActive={!reduce} animationDuration={700}>
                      {panel.rows.map((r, i) => <Cell key={i} fill={COLORS[r.side]} />)}
                      <LabelList dataKey="value" content={(props: any) => <text x={Number(props.x) + Number(props.width) + 8} y={Number(props.y) + Number(props.height) / 2} dy={4} style={labelStyle}>{fmt(spec.unit, Number(props.value))}</text>} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        })}
      </div>
      <LegendChips items={legend} />
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Mapa de calor (distrito x ano), vermelho -> verde                   */
/* ------------------------------------------------------------------ */

function HeatmapChart({ spec }: { spec: HeatmapSpec }) {
  const { t, fmt } = useI18n();
  return (
    <div className="heat-wrap">
      <div className="table-scroll">
        <table className="heat">
          <thead>
            <tr><th scope="col" className="corner">{t.district}</th>{spec.columns.map((c) => <th key={c} scope="col">{c}</th>)}</tr>
          </thead>
          <tbody>
            {spec.rows.map((row) => (
              <tr key={row.label}>
                <th scope="row">{row.label}</th>
                {row.values.map((v, i) => {
                  const color = v === null ? null : heatColor(v);
                  return (
                    <td key={i} tabIndex={0} style={color ? { background: color.bg, color: color.fg } : undefined}
                      title={`${row.label}, ${spec.columns[i]}: ${v === null ? t.noData : fmt("pct", v)}`}>
                      {v === null ? t.na : fmt("pct", v)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="heat-scale" aria-hidden="true"><span>0%</span><div className="heat-bar" /><span>100%</span></div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Slope: cada secao de 2020 para 2024                                 */
/* ------------------------------------------------------------------ */

function SlopeChart({ spec }: { spec: SlopeSpec }) {
  const { t, fmt } = useI18n();
  const narrow = useNarrow();
  const [active, setActive] = useState<number | null>(null);
  const W = narrow ? 300 : 760, H = narrow ? 400 : 470, padT = 40, padB = 26;
  const xa = narrow ? 76 : 190, xb = narrow ? 226 : 570;
  const vals = spec.rows.flatMap((r) => [r.a, r.b]).filter((v): v is number => v !== null);
  const lo = Math.floor(Math.min(...vals) / 10) * 10;
  const hi = Math.ceil(Math.max(...vals) / 10) * 10;
  const y = (v: number) => padT + ((hi - v) / (hi - lo)) * (H - padT - padB);
  const ticks: number[] = [];
  for (let k = lo; k <= hi; k += 10) ticks.push(k);
  const current = spec.rows.find((r) => r.secao === active);
  const both = spec.rows.filter((r) => r.a !== null && r.b !== null);
  const rose = both.filter((r) => (r.b as number) >= (r.a as number)).length;

  return (
    <>
      <svg className="slope" viewBox={`0 0 ${W} ${H}`} role="group" aria-label={t.slopeAria}>
        {ticks.map((k) => (
          <g key={k}>
            <line x1={xa - 20} x2={xb + 20} y1={y(k)} y2={y(k)} stroke={GRID} />
            <text x={xa - 28} y={y(k) + 4} textAnchor="end" style={tick}>{k}%</text>
          </g>
        ))}
        <text x={xa} y={20} textAnchor="middle" className="slope-head">{spec.aLabel}</text>
        <text x={xb} y={20} textAnchor="middle" className="slope-head">{spec.bLabel}</text>
        {spec.rows.map((r) => {
          const on = active === r.secao;
          const dim = active !== null && !on;
          const color = r.a === null ? COLORS.neutro : (r.b as number) >= r.a ? COLORS.grupo : COLORS.adversario;
          return (
            <g key={r.secao} tabIndex={0} role="img" aria-label={`${t.precinct} ${r.secao}: ${fmt("pct", r.a)} ${t.in2020}, ${fmt("pct", r.b)} ${t.in2024}`}
              onMouseEnter={() => setActive(r.secao)} onMouseLeave={() => setActive(null)} onFocus={() => setActive(r.secao)} onBlur={() => setActive(null)}
              onClick={() => setActive(r.secao)} style={{ outline: "none", cursor: "pointer" }}>
              {r.a !== null && r.b !== null && (
                <>
                  <line x1={xa} y1={y(r.a)} x2={xb} y2={y(r.b)} stroke="transparent" strokeWidth={14} />
                  <line x1={xa} y1={y(r.a)} x2={xb} y2={y(r.b)} stroke={color} strokeWidth={on ? 3.4 : 1.7} opacity={dim ? 0.13 : on ? 1 : 0.6} className="slope-line" />
                  <circle cx={xa} cy={y(r.a)} r={on ? 5 : 3} fill={color} opacity={dim ? 0.15 : 1} />
                </>
              )}
              {r.b !== null && <circle cx={xb} cy={y(r.b)} r={on ? 5 : 3} fill={color} opacity={dim ? 0.15 : 1} />}
            </g>
          );
        })}
      </svg>
      <p className="hover-readout" aria-live="polite">
        {current ? (
          <><b>{t.precinct} {current.secao}</b>{current.local && <> · {current.local}</>}: {current.a === null ? t.newPrecinct : fmt("pct", current.a)} → <b>{fmt("pct", current.b)}</b></>
        ) : t.slopeHint(rose, both.length)}
      </p>
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Grade das 42 secoes                                                 */
/* ------------------------------------------------------------------ */

const TILE_COLOR: Record<GridSpec["tiles"][number]["cat"], string> = { virou: COLORS.grupo, ja: "#157a4d", nova: COLORS.neutro };

function GridChart({ spec }: { spec: GridSpec }) {
  const { t, fmt } = useI18n();
  const [active, setActive] = useState<number | null>(null);
  const current = spec.tiles.find((x) => x.secao === active);
  const cats = (Object.keys(TILE_COLOR) as (keyof typeof TILE_COLOR)[]).map((k) => ({ key: k, n: spec.tiles.filter((x) => x.cat === k).length }));
  return (
    <>
      <div className="tile-grid" role="group" aria-label={t.gridAria}>
        {spec.tiles.map((x) => (
          <button key={x.secao} type="button" className={`tile${active === x.secao ? " on" : ""}`} style={{ background: TILE_COLOR[x.cat] }}
            onMouseEnter={() => setActive(x.secao)} onFocus={() => setActive(x.secao)} onClick={() => setActive(x.secao)}
            onMouseLeave={() => setActive(null)} onBlur={() => setActive(null)}
            aria-label={`${t.precinct} ${x.secao}, ${t.tile[x.cat]}${x.local ? `, ${x.local}` : ""}`}>
            {x.secao}
          </button>
        ))}
      </div>
      <p className="hover-readout" aria-live="polite">
        {current ? (
          <><b>{t.precinct} {current.secao}</b>{current.local && <> · {current.local}</>}: {current.a === null ? t.newPrecinct : `${fmt("pct", current.a)} ${t.in2020}`} → <b>{fmt("pct", current.b)}</b> {t.in2024}</>
        ) : t.gridHint}
      </p>
      <LegendChips items={cats.map((c) => ({ key: c.key, label: `${t.tile[c.key]} (${c.n})`, color: TILE_COLOR[c.key] }))} />
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Dispersao: prefeito x vereador por secao                            */
/* ------------------------------------------------------------------ */

function ScatterView({ spec }: { spec: ScatterSpec }) {
  const { hidden, toggle } = useToggleSet();
  const { t, fmt } = useI18n();
  const narrow = useNarrow();
  const reduce = prefersReducedMotion();
  const all = spec.series.flatMap((s) => s.points.flatMap((p) => [p.x, p.y]));
  const lo = Math.max(0, Math.floor(Math.min(...all) / 5) * 5 - 5);
  const hi = Math.min(100, Math.ceil(Math.max(...all) / 5) * 5 + 5);

  const ScatterTip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;
    const p = payload[0].payload;
    const s = payload[0];
    return (
      <Tip title={`${t.precinct} ${p.secao} · ${s.name}`}
        lines={[{ color: s.fill, text: <>{t.mayor}: <b>{fmt("pct", p.x)}</b></> }, { text: <>{t.council}: <b>{fmt("pct", p.y)}</b></> },
          { text: <>{t.difference}: <b>{fmt("pct", Math.abs(p.x - p.y))}</b></> }]} />
    );
  };

  return (
    <>
      <div className="chart-box" style={{ height: narrow ? 340 : 420 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 12, right: narrow ? 10 : 20, bottom: 30, left: 4 }}>
            <CartesianGrid stroke={GRID} />
            <XAxis type="number" dataKey="x" name={t.mayor} domain={[lo, hi]} tick={tick} tickLine={false} tickFormatter={(v: number) => `${v}%`}
              label={{ value: t.xAxisMayor, position: "insideBottom", offset: -16, style: { ...tick, fontWeight: 600 } }} />
            <YAxis type="number" dataKey="y" name={t.council} domain={[lo, hi]} tick={tick} tickLine={false} axisLine={false} width={narrow ? 40 : 48} tickFormatter={(v: number) => `${v}%`}
              label={{ value: t.yAxisCouncil, angle: -90, position: "insideLeft", offset: narrow ? 4 : 10, style: { ...tick, fontWeight: 600, textAnchor: "middle" } }} />
            <ZAxis range={[54, 54]} />
            <ReferenceLine segment={[{ x: lo, y: lo }, { x: hi, y: hi }]} stroke="rgba(23,23,26,0.35)" strokeDasharray="6 5"
              label={{ value: t.sameShare, position: "insideTopLeft", fill: "rgba(23,23,26,0.5)", fontSize: 10.5, fontFamily: FONT }} />
            <Tooltip content={<ScatterTip />} cursor={{ stroke: "rgba(23,23,26,0.22)", strokeWidth: 1 }} />
            {spec.series.map((s) => (
              <Scatter key={s.key} name={s.label} data={s.points} fill={COLORS[s.color]} fillOpacity={0.72} stroke="#ffffff" hide={hidden.has(s.key)} isAnimationActive={!reduce} />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <LegendChips items={spec.series.map((s) => ({ key: s.key, label: s.label, color: COLORS[s.color] }))} hidden={hidden} toggle={toggle} />
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Linha do tempo das pesquisas registradas                            */
/* ------------------------------------------------------------------ */

function TimelineChart({ spec }: { spec: TimelineSpec }) {
  const { t, dateLong, dateShort } = useI18n();
  const narrow = useNarrow();
  const [active, setActive] = useState<number | null>(null);
  const W = narrow ? 300 : 780, H = narrow ? 190 : 214, pad = narrow ? 16 : 34, baseY = narrow ? 104 : 128;
  const t0 = Date.parse("2024-04-01");
  const t1 = Date.parse("2024-10-14");
  const x = (iso: string) => pad + ((Date.parse(iso) - t0) / (t1 - t0)) * (W - pad * 2);
  const months = [3, 4, 5, 6, 7, 8, 9].map((m) => ({ m, iso: `2024-${String(m + 1).padStart(2, "0")}-01` }));
  return (
    <>
      <svg className="timeline" viewBox={`0 0 ${W} ${H}`} role="group" aria-label={t.timelineAria}>
        <line x1={pad} x2={W - pad} y1={baseY} y2={baseY} stroke={GRID} strokeWidth={2} />
        {months.map(({ m, iso }) => (
          <g key={m}>
            <line x1={x(iso)} x2={x(iso)} y1={baseY - 5} y2={baseY + 5} stroke="rgba(23,23,26,0.3)" />
            <text x={x(iso)} y={baseY + 24} textAnchor="middle" style={{ ...tick, fontSize: narrow ? 10 : 11 }}>{t.months[m]}</text>
          </g>
        ))}
        <line x1={x(spec.election)} x2={x(spec.election)} y1={16} y2={baseY + 6} stroke={COLORS.adversario} strokeWidth={2} strokeDasharray="4 3" />
        <text x={narrow ? x(spec.election) - 4 : x(spec.election)} y={baseY + 46} textAnchor={narrow ? "end" : "middle"} style={{ ...tick, fill: COLORS.adversario, fontWeight: 700, fontSize: narrow ? 10 : 11 }}>
          {t.election} · {dateShort(spec.election)}
        </text>
        {spec.polls.map((p, i) => {
          const cy = baseY - 22 - (i % 3) * (narrow ? 22 : 30);
          const on = active === i;
          return (
            <g key={p.registro} tabIndex={0} onMouseEnter={() => setActive(i)} onMouseLeave={() => setActive(null)} onFocus={() => setActive(i)} onBlur={() => setActive(null)} onClick={() => setActive(i)}
              style={{ outline: "none", cursor: "pointer" }} role="img" aria-label={`${dateLong(p.data)}: ${p.instituto}, ${p.registro}`}>
              <line x1={x(p.data)} x2={x(p.data)} y1={cy} y2={baseY} stroke={COLORS.info} strokeWidth={on ? 2 : 1} opacity={0.5} />
              <circle cx={x(p.data)} cy={cy} r={on ? 9 : narrow ? 5.5 : 6.5} fill={COLORS.info} stroke="#ffffff" strokeWidth={2} />
              {!narrow && <text x={x(p.data)} y={cy - 13} textAnchor="middle" style={{ ...labelStyle, fontSize: 10.5 }}>{dateShort(p.data)}</text>}
            </g>
          );
        })}
      </svg>
      <ol className="poll-list">
        {spec.polls.map((p, i) => (
          <li key={p.registro} className={active === i ? "on" : ""} onMouseEnter={() => setActive(i)} onMouseLeave={() => setActive(null)} onClick={() => setActive(i)}>
            <span className="poll-date">{dateLong(p.data)}</span>
            <span className="poll-inst">{p.instituto}</span>
            <code>{p.registro}</code>
          </li>
        ))}
      </ol>
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Despacho + montagem sob demanda                                      */
/* ------------------------------------------------------------------ */

export function ChartBody({ spec }: { spec: ChartSpec }) {
  switch (spec.kind) {
    case "cartesian": return <CartesianChart spec={spec} />;
    case "panels": return <PanelsChart spec={spec} />;
    case "multiples": return <MultiplesChart spec={spec} />;
    case "heatmap": return <HeatmapChart spec={spec} />;
    case "slope": return <SlopeChart spec={spec} />;
    case "grid": return <GridChart spec={spec} />;
    case "scatter": return <ScatterView spec={spec} />;
    case "timeline": return <TimelineChart spec={spec} />;
  }
}

/** So monta o grafico quando ele se aproxima da tela (27 graficos, animacao ao entrar). `eager` monta tudo (PDF). */
export function LazyMount({ children, minHeight = 320, eager = false }: { children: ReactNode; minHeight?: number; eager?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const [seen, setSeen] = useState(eager);
  useEffect(() => {
    const el = ref.current;
    if (!el || seen) return;
    if (!("IntersectionObserver" in window)) { setSeen(true); return; }
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) { setSeen(true); io.disconnect(); }
    }, { rootMargin: "500px 0px" });
    io.observe(el);
    return () => io.disconnect();
  }, [seen]);
  const style = useMemo(() => (seen ? undefined : { minHeight }), [seen, minHeight]);
  return <div ref={ref} style={style}>{seen ? children : null}</div>;
}
