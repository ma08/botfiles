import React from 'react';
import {Easing, useCurrentFrame} from 'remotion';
import {SceneFrame, Title} from '../components/SceneFrame';
import {colors, fonts, glow} from '../theme';
import {pathFrom, ramp} from '../lib/anim';
import {sceneById} from '../lib/timeline';
import {Check, M, Tag, lerp, wf} from './s04/kit';

const s = sceneById('s06_stepanov');
const inOut = Easing.inOut(Easing.cubic);

const B = {
  trick: wf(s, 'trick'),
  build: wf(s, 'build'),
  helper: wf(s, 'helper'),
  zero0: wf(s, 'zero', 0),
  every: wf(s, 'every'),
  not: wf(s, 'not'),
  zero2: wf(s, 'zero', 2),
  times: wf(s, 'times'),
  limited: wf(s, 'limited'),
  roots: wf(s, 'roots'),
  counted: wf(s, 'counted'),
  more: wf(s, 'more'),
  means: wf(s, 'means'),
  tighter: wf(s, 'tighter'),
  and: wf(s, 'and'),
  mult2: wf(s, 'multiplicity', 2),
  comes: wf(s, 'comes'),
  derivatives: wf(s, 'derivatives'),
};

// ---------------- schematic polynomial ----------------
const PX0 = 150;
const PX1 = 1300;
const AY = 590;
const AMPL = 175;
const ROOTS = [0.13, 0.31, 0.5, 0.67, 0.86];
const tX = (t: number) => PX0 + t * (PX1 - PX0);
const W = 0.07;
const N_S = 700;
const TS = Array.from({length: N_S}, (_, i) => i / (N_S - 1));
const BUDGET = 20;

/** Bounded stand-in for prod (t - a_i)^m: same sign pattern and order-m contact at each root, readable at any m. */
const rawCurve = (m: number) =>
  TS.map((t) => {
    let v = 1;
    for (const a of ROOTS) v *= Math.pow(Math.tanh((t - a) / W), m);
    const lift = 1 + 10 * Math.pow(Math.max(0, Math.abs(t - 0.5) - 0.36), 2);
    return v * lift;
  });
const CURVES = [1, 2, 3, 4].map((m) => {
  const raw = rawCurve(m);
  let mx = 0;
  TS.forEach((t, i) => {
    if (t >= ROOTS[0] && t <= ROOTS[4]) mx = Math.max(mx, Math.abs(raw[i]));
  });
  return raw.map((v) => v / mx);
});

const mAt = (f: number) => 1 + ramp(f, B.zero2, 12, inOut) + ramp(f, B.times, 12, inOut) + ramp(f, B.more, 14, inOut);
const curvePts = (m: number): [number, number][] => {
  const i = Math.min(2, Math.floor(m - 1));
  const t = m - 1 - i;
  const a = CURVES[i];
  const b = CURVES[i + 1];
  return TS.map((tt, k) => [tX(tt), AY - AMPL * lerp(a[k], b[k], t)]);
};

// ---------------- budget bar ----------------
const BAR_X = 1446;
const BAR_W = 50;
const BAR_TOP = 430;
const BAR_BOT = 858;
const SEG = (BAR_BOT - BAR_TOP) / BUDGET;

// zoom target (middle root)
const ZX = tX(ROOTS[2]);
const ZY = AY;

export const S06Stepanov: React.FC = () => {
  const f = useCurrentFrame();
  const m = mAt(f);
  const mShown = Math.round(m);
  const axisIn = ramp(f, B.trick - 14, 28, inOut);
  const draw = ramp(f, B.helper, 40, Easing.inOut(Easing.quad));
  const zoom = 1 + 0.9 * ramp(f, B.and, 26, inOut);
  const zoomT = ramp(f, B.and, 20);
  const rightDim = 1 - 0.75 * zoomT;
  const barIn = ramp(f, B.limited - 6, 16);
  const groupFill = (i: number) => ramp(f, B.counted + i * 8, 9, Easing.out(Easing.quad));
  const usedIn = ramp(f, B.counted + 44, 12);
  const readIn = ramp(f, B.counted + 46, 14);
  const capPulse = Math.max(0, 1 - Math.abs(f - (B.roots + 6)) / 10) + Math.max(0, 1 - Math.abs(f - (B.more + 16)) / 12);
  const boundNow = Math.floor(BUDGET / (f >= B.means ? 4 : 3));
  const tightPulse = Math.max(0, 1 - Math.abs(f - (B.tighter + 4)) / 10);
  const pts = curvePts(m);

  return (
    <SceneFrame index={6} kicker="Stepanov's trick">
      <Title size={78}>Stepanov's trick</Title>

      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        <defs>
          <clipPath id="s06-plot">
            <rect x={PX0 - 30} y={318} width={PX1 - PX0 + 60} height={548} />
          </clipPath>
        </defs>
        <g clipPath="url(#s06-plot)">
          <g transform={`translate(${ZX} ${ZY}) scale(${zoom}) translate(${-ZX} ${-ZY})`}>
            {/* axis */}
            <line
              x1={PX0 - 20}
              x2={lerp(PX0 - 20, PX1 + 20, axisIn)}
              y1={AY}
              y2={AY}
              stroke={colors.faint}
              strokeWidth={1.5}
              vectorEffect="non-scaling-stroke"
            />
            {/* flat tangent at the zoomed root (f' = 0) */}
            <line
              x1={ZX - 90}
              x2={ZX + 90}
              y1={AY}
              y2={AY}
              stroke={colors.good}
              strokeWidth={3}
              vectorEffect="non-scaling-stroke"
              opacity={ramp(f, B.comes - 2, 12)}
              style={{filter: glow(6, 'rgba(159,211,138,0.8)')}}
            />
            {/* helper polynomial */}
            <path
              d={pathFrom(pts, draw)}
              fill="none"
              stroke={colors.fg}
              strokeWidth={2.8}
              strokeLinejoin="round"
              vectorEffect="non-scaling-stroke"
            />
            {/* target points */}
            {ROOTS.map((a, i) => {
              const at = B.trick + 6 + i * 6;
              const t = ramp(f, at, 10);
              const pulseAt = B.zero0 + i * 6;
              const pulse = ramp(f, pulseAt, 18);
              const flashAt = B.counted + i * 8;
              const flash = Math.max(0, 1 - Math.abs(f - (flashAt + 4)) / 8);
              const filled = ramp(f, pulseAt, 6);
              const r = 9 / zoom;
              return (
                <g key={a} opacity={t}>
                  {pulse > 0 && pulse < 1 && (
                    <circle cx={tX(a)} cy={AY} r={(10 + 26 * pulse) / zoom} fill="none" stroke={colors.accent} strokeOpacity={1 - pulse} strokeWidth={2} vectorEffect="non-scaling-stroke" />
                  )}
                  <circle
                    cx={tX(a)}
                    cy={AY}
                    r={r * (1 + 0.5 * flash)}
                    fill={filled > 0 ? colors.accent : colors.bg}
                    fillOpacity={Math.max(filled, 0.0001)}
                    stroke={colors.accent}
                    strokeWidth={2.4}
                    vectorEffect="non-scaling-stroke"
                    style={{filter: glow(6 + 10 * flash)}}
                  />
                </g>
              );
            })}
          </g>
        </g>

        {/* ---------- degree budget bar ---------- */}
        <g opacity={barIn * rightDim}>
          <rect x={BAR_X} y={BAR_TOP} width={BAR_W} height={BAR_BOT - BAR_TOP} fill="none" stroke={colors.line} strokeWidth={1.5} rx={4} />
          {Array.from({length: BUDGET - 1}, (_, k) => (
            <line key={k} x1={BAR_X} x2={BAR_X + BAR_W} y1={BAR_BOT - (k + 1) * SEG} y2={BAR_BOT - (k + 1) * SEG} stroke={colors.line} strokeOpacity={0.6} />
          ))}
          {ROOTS.map((_, i) => {
            const g = groupFill(i);
            const y0 = BAR_BOT - i * m * SEG;
            const h = m * SEG * g;
            return (
              <rect
                key={i}
                x={BAR_X + 4}
                y={y0 - h + 1.5}
                width={BAR_W - 8}
                height={Math.max(0, h - 3)}
                rx={3}
                fill={colors.accent}
                opacity={i % 2 ? 0.55 : 0.95}
              />
            );
          })}
          <line
            x1={BAR_X - 14}
            x2={BAR_X + BAR_W + 14}
            y1={BAR_TOP}
            y2={BAR_TOP}
            stroke={colors.accent}
            strokeWidth={2.5 + 2 * Math.min(1, capPulse)}
            strokeDasharray="6 5"
            style={{filter: glow(4 + 8 * Math.min(1, capPulse))}}
          />
        </g>
      </svg>

      {/* curve name */}
      <div style={{position: 'absolute', left: PX1 + 22, top: Math.max(338, Math.min(AY - 50, pts[N_S - 1][1])) - 34, opacity: ramp(f, B.helper + 36, 12) * (1 - zoomT)}}>
        <M style={{fontSize: 40, color: colors.fg}}>f</M>
      </div>
      <div
        style={{
          position: 'absolute',
          left: (tX(ROOTS[0]) + tX(ROOTS[1])) / 2,
          top: AY + 30,
          transform: 'translateX(-50%)',
          fontFamily: fonts.mono,
          fontSize: 20,
          color: colors.muted,
          whiteSpace: 'nowrap',
          opacity: ramp(f, B.trick + 10, 12) * (1 - zoomT),
        }}
      >
        points to count
      </div>
      <Tag style={{left: PX1 - 132, top: 262}}>schematic</Tag>

      {/* ---------- right column ---------- */}
      <div style={{position: 'absolute', left: 1446, top: 268, opacity: ramp(f, B.not - 4, 14) * rightDim}}>
        <div style={{fontFamily: fonts.mono, fontSize: 18, letterSpacing: '0.08em', textTransform: 'uppercase', color: colors.muted}}>multiplicity</div>
        <div style={{fontFamily: fonts.body, fontSize: 30, color: colors.fg, marginTop: 6, whiteSpace: 'nowrap'}}>
          <M style={{fontSize: 56, color: colors.accent}}>m</M>
          <span style={{fontFamily: fonts.displayUpright, fontSize: 56, color: colors.accent, fontVariantNumeric: 'lining-nums'}}> = {mShown}</span>
        </div>
      </div>
      <div style={{position: 'absolute', left: BAR_X + BAR_W + 26, top: BAR_TOP - 14, opacity: barIn * rightDim, whiteSpace: 'nowrap'}}>
        <div style={{fontFamily: fonts.mono, fontSize: 18, color: colors.accent}}>degree budget: {BUDGET}</div>
        <div style={{fontFamily: fonts.mono, fontSize: 18, color: colors.fg, marginTop: 6, opacity: usedIn}}>
          used: 5 × {mShown} = {5 * mShown}
        </div>
      </div>
      <div style={{position: 'absolute', left: BAR_X + BAR_W + 26, top: 600, opacity: readIn * rightDim, whiteSpace: 'nowrap'}}>
        <div style={{fontFamily: fonts.mono, fontSize: 18, letterSpacing: '0.06em', color: colors.muted}}>
          POINTS ≤ {BUDGET} ÷ <M style={{fontSize: 22, letterSpacing: 0}}>m</M>
        </div>
        <div
          style={{
            fontFamily: fonts.display,
            fontStyle: 'italic',
            fontSize: 84,
            lineHeight: 1.05,
            color: colors.accent,
            transform: `scale(${1 + 0.1 * tightPulse})`,
            transformOrigin: 'left center',
            filter: tightPulse > 0 ? glow(14 * tightPulse) : undefined,
          }}
        >
          ≤ {boundNow}
        </div>
        <div style={{display: 'flex', gap: 10, marginTop: 10, fontFamily: fonts.mono, fontSize: 18}}>
          {[1, 2, 3, 4].map((k) => {
            const at = k < 4 ? B.counted + 46 + (k - 1) * 4 : B.means;
            const cur = k === (f >= B.means ? 4 : 3);
            return (
              <span
                key={k}
                style={{
                  opacity: ramp(f, at, 10),
                  color: cur ? colors.accent : colors.muted,
                  border: `1px solid ${cur ? colors.accent : colors.line}`,
                  borderRadius: 6,
                  padding: '3px 7px',
                }}
              >
                {k}: {Math.floor(BUDGET / k)}
              </span>
            );
          })}
        </div>
        <div style={{fontFamily: fonts.mono, fontSize: 17, color: colors.muted, marginTop: 8, opacity: ramp(f, B.counted + 50, 10)}}>
          bound for each m
        </div>
      </div>

      {/* ---------- derivatives ---------- */}
      <div style={{position: 'absolute', left: ZX + 150, top: AY + 34, opacity: zoomT, fontFamily: fonts.mono, fontSize: 36, color: colors.fg, lineHeight: 1.5}}>
        {(
          [
            ['f', '', B.mult2],
            ['f', '′', B.comes],
            ['f', '″', B.derivatives],
          ] as [string, string, number][]
        ).map(([fn, pr, at]) => (
          <div key={fn + pr} style={{display: 'grid', gridTemplateColumns: '150px 90px 40px', alignItems: 'center', opacity: ramp(f, at - 4, 10)}}>
            <span>
              {fn}
              <span style={{fontFamily: fonts.body, marginLeft: 1}}>{pr}</span>(a)
            </span>
            <span>= 0</span>
            <Check size={32} progress={ramp(f, at + 2, 10)} />
          </div>
        ))}
        <div style={{fontFamily: fonts.mono, fontSize: 21, color: colors.muted, marginTop: 6, opacity: ramp(f, B.derivatives + 12, 12)}}>
          so multiplicity ≥ 3 at a
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          left: ZX - 10,
          top: AY + 26,
          opacity: ramp(f, B.and + 18, 12),
        }}
      >
        <M style={{fontSize: 34, color: colors.accent}}>a</M>
      </div>
    </SceneFrame>
  );
};
