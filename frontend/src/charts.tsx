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
  PanelsSpec,
  ScatterSpec,
  Side,
  SlopeSpec,
  TimelineSpec,
  Unit,
} from "./types";
import { COLORS, FONT, GRID, INK, SIDE_LABEL, fmt, fmtAxis, heatColor, prefersReducedMotion } from "./theme";

const tick = { fontSize: 11, fill: INK, fontFamily: FONT };
const labelStyle = { fontSize: 11, fill: INK, fontFamily: FONT, fontWeight: 600 };

/* ------------------------------------------------------------------ */
/* Pecas compartilhadas                                                */
/* ------------------------------------------------------------------ */

interface LegendItem { key: string; label: string; color: string }

function LegendChips({ items, hidden, toggle }: { items: LegendItem[]; hidden?: Set<string>; toggle?: (key: string) => void }) {
  if (!items.length) return null;
  return (
    <div className="legend" role="group" aria-label="Legenda do gráfico">
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
  const reduce = prefersReducedMotion();
  const hasRight = spec.layers.some((l) => l.axis === "right");
  const rightUnit: Unit = spec.rightUnit ?? spec.unit;
  const unitOf = (key: string): Unit => (spec.layers.find((l) => l.key === key)?.axis === "right" ? rightUnit : spec.unit);
  const bars = spec.layers.filter((l) => l.type === "bar");
  const lines = spec.layers.filter((l) => l.type === "line");
  const singleColored = spec.layers.length === 1 && spec.layers[0].colorBySide;
  const stacked = bars.some((b) => b.stackId);
  const showBarLabels = spec.rows.length <= 8 && !hasRight && !stacked && bars.length > 0 && lines.length === 0;
  const maxLen = Math.max(...spec.rows.map((r) => String(r.x).length));
  const tilt = spec.tiltX || (spec.rows.length > 3 && maxLen > 12);
  const interval = spec.denseX ? Math.ceil(spec.rows.length / 9) : 0;

  const legendItems: LegendItem[] = singleColored
    ? [
        ...(spec.rows.some((r) => r.side === "adversario") ? [{ key: "adv", label: "2020, antes da virada", color: COLORS.adversario }] : []),
        ...(spec.rows.some((r) => r.side === "grupo") ? [{ key: "grp", label: "2024, depois da virada", color: COLORS.grupo }] : []),
        ...(spec.rows.some((r) => r.side === "neutro") ? [{ key: "ref", label: "Referência (população e eleitorado)", color: COLORS.neutro }] : []),
      ]
    : spec.layers.map((l) => ({ key: l.key, label: l.label, color: COLORS[l.color] }));
  const legendToggle = singleColored ? undefined : toggle;

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
      <div className="chart-box" style={{ height: tilt ? 380 : 340 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={spec.rows} margin={{ top: 22, right: hasRight ? 6 : 16, left: 0, bottom: tilt ? 4 : 8 }} barCategoryGap={spec.denseX ? 0 : "22%"} barGap={4}>
            <CartesianGrid stroke={GRID} vertical={false} />
            <XAxis
              dataKey="x"
              tick={tick}
              tickLine={false}
              axisLine={{ stroke: GRID }}
              interval={interval}
              angle={tilt ? -32 : 0}
              textAnchor={tilt ? "end" : "middle"}
              height={tilt ? 78 : 30}
              tickMargin={6}
            />
            <YAxis
              yAxisId="left"
              tick={tick}
              tickLine={false}
              axisLine={false}
              width={hasRight ? 60 : 64}
              domain={spec.yDomain ?? [0, "auto"]}
              allowDecimals={false}
              tickFormatter={(v: number) => fmtAxis(spec.unit, v)}
            />
            {hasRight && (
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={tick}
                tickLine={false}
                axisLine={false}
                width={54}
                domain={spec.rightDomain ?? [0, "auto"]}
                allowDecimals={false}
                tickFormatter={(v: number) => fmtAxis(rightUnit, v)}
              />
            )}
            <Tooltip content={<CartesianTip />} cursor={{ fill: "rgba(23,23,26,0.05)", stroke: "rgba(31,157,99,0.45)", strokeDasharray: "4 4" }} />
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
      <LegendChips items={legendItems} hidden={hidden} toggle={legendToggle} />
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Paineis de barras horizontais (candidatos, vereadores)              */
/* ------------------------------------------------------------------ */

function PanelsChart({ spec }: { spec: PanelsSpec }) {
  const reduce = prefersReducedMotion();
  const max = Math.max(...spec.panels.flatMap((p) => p.rows.map((r) => r.value)), 1);
  const sides = Array.from(new Set(spec.panels.flatMap((p) => p.rows.map((r) => r.side))));
  const legend: LegendItem[] = (["grupo", "adversario", "terceiro"] as Side[])
    .filter((s) => sides.includes(s))
    .map((s) => ({ key: s, label: SIDE_LABEL[s] ?? s, color: COLORS[s] }));

  const PanelTip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;
    const row = payload[0].payload;
    return (
      <Tip
        title={row.label}
        lines={[{ color: COLORS[row.side as Side], text: <>{SIDE_LABEL[row.side as Side]}: <b>{fmt(spec.unit, row.value)}</b></> }]}
        note={row.note}
      />
    );
  };

  return (
    <>
      <div className="panels" style={{ gridTemplateColumns: `repeat(${spec.panels.length}, minmax(0, 1fr))` }}>
        {spec.panels.map((panel, idx) => {
          const labelW = Math.min(172, Math.max(...panel.rows.map((r) => r.label.length)) * 6.3 + 14);
          return (
            <div key={idx} className="panel">
              {panel.title && <h4 className="panel-title">{panel.title}</h4>}
              <div style={{ height: panel.rows.length * 40 + 24 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={panel.rows} layout="vertical" margin={{ top: 4, right: 82, left: 0, bottom: 0 }} barCategoryGap={10}>
                    <CartesianGrid horizontal={false} stroke={GRID} />
                    <XAxis type="number" domain={[0, max]} hide />
                    <YAxis type="category" dataKey="label" width={labelW} tick={tick} tickLine={false} axisLine={false} interval={0} />
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
  return (
    <div className="heat-wrap">
      <div className="table-scroll">
        <table className="heat">
          <thead>
            <tr><th scope="col" className="corner">Distrito</th>{spec.columns.map((c) => <th key={c} scope="col">{c}</th>)}</tr>
          </thead>
          <tbody>
            {spec.rows.map((row) => (
              <tr key={row.label}>
                <th scope="row">{row.label}</th>
                {row.values.map((v, i) => {
                  const color = v === null ? null : heatColor(v);
                  return (
                    <td
                      key={i}
                      tabIndex={0}
                      style={color ? { background: color.bg, color: color.fg } : undefined}
                      title={`${row.label}, ${spec.columns[i]}: ${v === null ? "sem dado" : fmt("pct", v)}`}
                    >
                      {v === null ? "s/d" : fmt("pct", v)}
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
  const [active, setActive] = useState<number | null>(null);
  const W = 760, H = 470, padT = 40, padB = 26, xa = 190, xb = 570;
  const vals = spec.rows.flatMap((r) => [r.a, r.b]).filter((v): v is number => v !== null);
  const lo = Math.floor(Math.min(...vals) / 10) * 10;
  const hi = Math.ceil(Math.max(...vals) / 10) * 10;
  const y = (v: number) => padT + ((hi - v) / (hi - lo)) * (H - padT - padB);
  const ticks: number[] = [];
  for (let t = lo; t <= hi; t += 10) ticks.push(t);
  const current = spec.rows.find((r) => r.secao === active);
  const rose = spec.rows.filter((r) => r.a !== null && r.b !== null && (r.b as number) >= (r.a as number)).length;
  const withBoth = spec.rows.filter((r) => r.a !== null && r.b !== null).length;

  return (
    <>
      <svg className="slope" viewBox={`0 0 ${W} ${H}`} role="group" aria-label="Gráfico de inclinação por seção">
        {ticks.map((t) => (
          <g key={t}>
            <line x1={xa - 20} x2={xb + 20} y1={y(t)} y2={y(t)} stroke={GRID} />
            <text x={xa - 30} y={y(t) + 4} textAnchor="end" style={{ ...tick }}>{t}%</text>
          </g>
        ))}
        <text x={xa} y={20} textAnchor="middle" className="slope-head">{spec.aLabel}</text>
        <text x={xb} y={20} textAnchor="middle" className="slope-head">{spec.bLabel}</text>
        {spec.rows.map((r) => {
          const on = active === r.secao;
          const dim = active !== null && !on;
          const color = r.a === null ? COLORS.neutro : (r.b as number) >= r.a ? COLORS.grupo : COLORS.adversario;
          return (
            <g
              key={r.secao}
              tabIndex={0}
              role="img"
              aria-label={`Seção ${r.secao}: ${fmt("pct", r.a)} em 2020, ${fmt("pct", r.b)} em 2024`}
              onMouseEnter={() => setActive(r.secao)}
              onMouseLeave={() => setActive(null)}
              onFocus={() => setActive(r.secao)}
              onBlur={() => setActive(null)}
              style={{ outline: "none", cursor: "pointer" }}
            >
              {r.a !== null && r.b !== null && (
                <>
                  <line x1={xa} y1={y(r.a)} x2={xb} y2={y(r.b)} stroke="transparent" strokeWidth={12} />
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
          <><b>Seção {current.secao}</b>{current.local && <> · {current.local}</>}: {current.a === null ? "seção nova" : fmt("pct", current.a)} → <b>{fmt("pct", current.b)}</b></>
        ) : (
          <>Passe o mouse sobre uma linha para ver a seção. <b>{rose} de {withBoth}</b> seções com voto em 2020 subiram para o candidato do grupo; os pontos cinza são as seções novas.</>
        )}
      </p>
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Grade das 42 secoes                                                 */
/* ------------------------------------------------------------------ */

const TILE_META: Record<GridSpec["tiles"][number]["cat"], { label: string; color: string }> = {
  virou: { label: "Derrota em 2020, vitória em 2024", color: COLORS.grupo },
  ja: { label: "Já vencida em 2020", color: "#157a4d" },
  nova: { label: "Seção nova (criada após 2020)", color: COLORS.neutro },
};

function GridChart({ spec }: { spec: GridSpec }) {
  const [active, setActive] = useState<number | null>(null);
  const current = spec.tiles.find((t) => t.secao === active);
  const counts = (Object.keys(TILE_META) as (keyof typeof TILE_META)[]).map((k) => ({ key: k, n: spec.tiles.filter((t) => t.cat === k).length }));
  return (
    <>
      <div className="tile-grid" role="group" aria-label="Seções eleitorais">
        {spec.tiles.map((t) => (
          <button
            key={t.secao}
            type="button"
            className={`tile${active === t.secao ? " on" : ""}`}
            style={{ background: TILE_META[t.cat].color }}
            onMouseEnter={() => setActive(t.secao)}
            onFocus={() => setActive(t.secao)}
            onMouseLeave={() => setActive(null)}
            onBlur={() => setActive(null)}
            aria-label={`Seção ${t.secao}, ${TILE_META[t.cat].label}${t.local ? `, ${t.local}` : ""}`}
          >
            {t.secao}
          </button>
        ))}
      </div>
      <p className="hover-readout" aria-live="polite">
        {current ? (
          <><b>Seção {current.secao}</b>{current.local && <> · {current.local}</>}: {current.a === null ? "seção nova" : `${fmt("pct", current.a)} em 2020`} → <b>{fmt("pct", current.b)}</b> em 2024</>
        ) : (
          <>Passe o mouse ou use a tecla Tab para ver o local de votação e a votação de cada seção.</>
        )}
      </p>
      <LegendChips items={counts.map((c) => ({ key: c.key, label: `${TILE_META[c.key].label} (${c.n})`, color: TILE_META[c.key].color }))} />
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Dispersao: prefeito x vereador por secao                            */
/* ------------------------------------------------------------------ */

function ScatterView({ spec }: { spec: ScatterSpec }) {
  const { hidden, toggle } = useToggleSet();
  const reduce = prefersReducedMotion();
  const all = spec.series.flatMap((s) => s.points.flatMap((p) => [p.x, p.y]));
  const lo = Math.max(0, Math.floor(Math.min(...all) / 5) * 5 - 5);
  const hi = Math.min(100, Math.ceil(Math.max(...all) / 5) * 5 + 5);

  const ScatterTip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;
    const p = payload[0].payload;
    const s = payload[0];
    return (
      <Tip
        title={`Seção ${p.secao} · ${s.name}`}
        lines={[
          { color: s.fill, text: <>Prefeito: <b>{fmt("pct", p.x)}</b></> },
          { text: <>Vereador: <b>{fmt("pct", p.y)}</b></> },
          { text: <>Diferença: <b>{fmt("pct", Math.abs(p.x - p.y))}</b></> },
        ]}
      />
    );
  };

  return (
    <>
      <div className="chart-box" style={{ height: 420 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 12, right: 20, bottom: 30, left: 4 }}>
            <CartesianGrid stroke={GRID} />
            <XAxis type="number" dataKey="x" name="Prefeito" domain={[lo, hi]} tick={tick} tickLine={false} tickFormatter={(v: number) => `${v}%`}
              label={{ value: "% do grupo para prefeito", position: "insideBottom", offset: -16, style: { ...tick, fontWeight: 600 } }} />
            <YAxis type="number" dataKey="y" name="Vereador" domain={[lo, hi]} tick={tick} tickLine={false} axisLine={false} width={48} tickFormatter={(v: number) => `${v}%`}
              label={{ value: "% do grupo para vereador", angle: -90, position: "insideLeft", offset: 10, style: { ...tick, fontWeight: 600, textAnchor: "middle" } }} />
            <ZAxis range={[54, 54]} />
            <ReferenceLine segment={[{ x: lo, y: lo }, { x: hi, y: hi }]} stroke="rgba(23,23,26,0.35)" strokeDasharray="6 5"
              label={{ value: "mesmo % nos dois cargos", position: "insideTopLeft", fill: "rgba(23,23,26,0.5)", fontSize: 10.5, fontFamily: FONT }} />
            <Tooltip content={<ScatterTip />} cursor={{ strokeDasharray: "3 3", stroke: "rgba(23,23,26,0.3)" }} />
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

const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const dmy = (iso: string) => iso.split("-").reverse().join("/");
const dm = (iso: string) => iso.slice(5).split("-").reverse().join("/");

function TimelineChart({ spec }: { spec: TimelineSpec }) {
  const [active, setActive] = useState<number | null>(null);
  const W = 780, H = 214, pad = 34, baseY = 128;
  const t0 = Date.parse("2024-04-01");
  const t1 = Date.parse("2024-10-14");
  const x = (iso: string) => pad + ((Date.parse(iso) - t0) / (t1 - t0)) * (W - pad * 2);
  const months = [3, 4, 5, 6, 7, 8, 9].map((m) => ({ m, iso: `2024-${String(m + 1).padStart(2, "0")}-01` }));
  return (
    <>
      <svg className="timeline" viewBox={`0 0 ${W} ${H}`} role="group" aria-label="Linha do tempo das pesquisas registradas">
        <line x1={pad} x2={W - pad} y1={baseY} y2={baseY} stroke={GRID} strokeWidth={2} />
        {months.map(({ m, iso }) => (
          <g key={m}>
            <line x1={x(iso)} x2={x(iso)} y1={baseY - 5} y2={baseY + 5} stroke="rgba(23,23,26,0.3)" />
            <text x={x(iso)} y={baseY + 24} textAnchor="middle" style={tick}>{MESES[m]}</text>
          </g>
        ))}
        <line x1={x(spec.election)} x2={x(spec.election)} y1={16} y2={baseY + 6} stroke={COLORS.adversario} strokeWidth={2} strokeDasharray="4 3" />
        <text x={x(spec.election)} y={baseY + 46} textAnchor="middle" style={{ ...tick, fill: COLORS.adversario, fontWeight: 700 }}>Eleição · {dm(spec.election)}</text>
        {spec.polls.map((p, i) => {
          const sameDay = spec.polls.filter((q, j) => j < i && q.data === p.data).length;
          const cy = baseY - 22 - (i % 3) * 30 - sameDay * 0;
          const on = active === i;
          return (
            <g key={p.registro} tabIndex={0} onMouseEnter={() => setActive(i)} onMouseLeave={() => setActive(null)} onFocus={() => setActive(i)} onBlur={() => setActive(null)}
              style={{ outline: "none", cursor: "pointer" }} role="img" aria-label={`${dmy(p.data)}: ${p.instituto}, registro ${p.registro}`}>
              <line x1={x(p.data)} x2={x(p.data)} y1={cy} y2={baseY} stroke={COLORS.info} strokeWidth={on ? 2 : 1} opacity={0.5} />
              <circle cx={x(p.data)} cy={cy} r={on ? 9 : 6.5} fill={COLORS.info} stroke="#ffffff" strokeWidth={2} />
              <text x={x(p.data)} y={cy - 13} textAnchor="middle" style={{ ...labelStyle, fontSize: 10.5 }}>{dm(p.data)}</text>
            </g>
          );
        })}
      </svg>
      <ol className="poll-list">
        {spec.polls.map((p, i) => (
          <li key={p.registro} className={active === i ? "on" : ""} onMouseEnter={() => setActive(i)} onMouseLeave={() => setActive(null)}>
            <span className="poll-date">{dmy(p.data)}</span>
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
    case "heatmap": return <HeatmapChart spec={spec} />;
    case "slope": return <SlopeChart spec={spec} />;
    case "grid": return <GridChart spec={spec} />;
    case "scatter": return <ScatterView spec={spec} />;
    case "timeline": return <TimelineChart spec={spec} />;
  }
}

/** So monta o grafico quando ele se aproxima da tela: 26 graficos, animacao ao entrar. */
export function LazyMount({ children, minHeight = 320 }: { children: ReactNode; minHeight?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (!("IntersectionObserver" in window)) { setSeen(true); return; }
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) { setSeen(true); io.disconnect(); }
    }, { rootMargin: "400px 0px" });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  const style = useMemo(() => (seen ? undefined : { minHeight }), [seen, minHeight]);
  return <div ref={ref} style={style}>{seen ? children : null}</div>;
}
