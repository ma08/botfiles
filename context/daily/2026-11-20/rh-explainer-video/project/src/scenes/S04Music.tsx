import React from 'react';
import {Easing, useCurrentFrame} from 'remotion';
import {SceneFrame, Title} from '../components/SceneFrame';
import {colors, fonts, glow} from '../theme';
import {pathFrom, ramp, scale, stepPathFrom} from '../lib/anim';
import {lineStartFrame, sceneById} from '../lib/timeline';
import explicit from '../data/explicit.json';
import zerosJson from '../data/zeros.json';
import lastdigit from '../data/lastdigit.json';
import {Equiv, M, Tag, fmt, lerp, mathFont, wf, win} from './s04/kit';

const s = sceneById('s04_music');
const inOut = Easing.inOut(Easing.cubic);

// ---- narration beats (keyed to words) ----
const B = {
  zero: wf(s, 'zero', 0),
  adds: wf(s, 'adds'),
  wave: wf(s, 'wave', 0),
  together: wf(s, 'together'),
  rebuild: wf(s, 'rebuild'),
  staircase: wf(s, 'staircase'),
  line1: lineStartFrame(s, 1),
  farther: wf(s, 'farther'),
  right: wf(s, 'right'),
  louder: wf(s, 'louder'),
  grows: wf(s, 'grows'),
  line2: lineStartFrame(s, 2),
  noWave: wf(s, 'no'),
  error: wf(s, 'error'),
  square: wf(s, 'square'),
  line3: lineStartFrame(s, 3),
  generalized: wf(s, 'generalized'),
  patterns: wf(s, 'patterns'),
  primes7: wf(s, 'primes', 1),
  ending: wf(s, 'ending'),
  seven: wf(s, '7'),
};

const gam = zerosJson.gammas;
const d1 = (v: number) => v.toFixed(2);

// =====================================================================
// Beat A: three waves, then partial sums rebuilding psi(x)
// =====================================================================
const PX0 = 470;
const PX1 = 1760;
const X = scale(0, 40, PX0, PX1);
const Y = scale(0, 40, 860, 330);
const xs = explicit.x;
const psiPts = xs.map((x, i) => [X(x), Y(explicit.psi[i])] as [number, number]);
const LEVELS = ['1', '3', '10', '30', '100'] as const;
const LEVEL_N = LEVELS.map(Number);
const partials = LEVELS.map((k) => explicit.partials[k]);
const waveKeys = ['1', '2', '3'] as const;
const ROW_Y = [405, 545, 685];
const WAVE_K = 60; // px per unit for the individual waves (their own scale)

// morph schedule (1 -> 3 -> 10 -> 30 -> 100), landing on 30 around "staircase" and holding 100
const MORPH = [B.rebuild + 5, B.rebuild + 14, B.staircase - 7, B.staircase + 2];
const levelAt = (f: number) => MORPH.reduce((acc, m) => acc + ramp(f, m, 8, inOut), 0);

// mini critical line in the left column
const CLX = 205;
const CL_Y = scale(0, 240, 862, 470);

const BeatA: React.FC<{f: number}> = ({f}) => {
  const out = win(f, 0, 1, B.farther - 14, 12);
  if (out <= 0) return null;
  const merge = ramp(f, B.together, 16, inOut);
  const rowsOpacity = 1 - ramp(f, B.together + 2, 14);
  const plotIn = ramp(f, B.together + 4, 16);
  const L = levelAt(f);
  const li = Math.min(3, Math.floor(L));
  const lt = L - li;
  const curve = partials[li].map((v, i) => [X(xs[i]), Y(lerp(v, partials[Math.min(4, li + 1)][i], lt))] as [number, number]);
  const curveIn = ramp(f, B.rebuild, 8);
  const shownLevel = LEVELS[Math.round(L)];
  const nCont = lerp(LEVEL_N[li], LEVEL_N[Math.min(4, li + 1)], lt);
  const bump = MORPH.reduce((a, m) => a + Math.max(0, 1 - Math.abs(f - (m + 4)) / 5), 0);
  const zoom = 1 + 0.025 * ramp(f, B.rebuild, 80, inOut);
  const starts = [B.zero, B.adds, B.wave];

  return (
    <div style={{position: 'absolute', inset: 0, opacity: out}}>
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        {/* ---------- individual waves ---------- */}
        <g opacity={rowsOpacity}>
          {waveKeys.map((k, r) => {
            const t = ramp(f, starts[r], 28, Easing.inOut(Easing.quad));
            const ty = merge * (620 - ROW_Y[r]);
            const pts = explicit.waves[k].map((v, i) => [X(xs[i]), ROW_Y[r] + ty - WAVE_K * v] as [number, number]);
            const n = Math.max(2, Math.floor(pts.length * t));
            const tip = pts[n - 1];
            const rowIn = ramp(f, starts[r] - 4, 10);
            return (
              <g key={k} opacity={rowIn}>
                <line x1={PX0} x2={PX1} y1={ROW_Y[r] + ty} y2={ROW_Y[r] + ty} stroke={colors.line} strokeWidth={1} />
                <path d={pathFrom(pts, t)} fill="none" stroke={colors.fg} strokeOpacity={0.88} strokeWidth={2} />
                {t > 0 && t < 1 && <circle cx={tip[0]} cy={tip[1]} r={4} fill={colors.accent} style={{filter: glow(6)}} />}
              </g>
            );
          })}
        </g>
        {/* zero dots: sit beside their wave, then drop onto the mini critical line */}
        {waveKeys.map((k, r) => {
          const rowIn = ramp(f, starts[r] - 4, 10);
          const cx = lerp(200, CLX, merge);
          const cy = lerp(ROW_Y[r], CL_Y(gam[r]), merge);
          return (
            <circle key={k} cx={cx} cy={cy} r={lerp(8, 3.5, merge)} fill={colors.accent} opacity={rowIn} style={{filter: glow(lerp(10, 5, merge))}} />
          );
        })}

        {/* ---------- psi(x) plot ---------- */}
        <g opacity={plotIn} transform={`translate(${PX0 + 600} 600) scale(${zoom}) translate(${-(PX0 + 600)} -600)`}>
          {[10, 20, 30].map((v) => (
            <g key={v}>
              <line x1={PX0} x2={PX1} y1={Y(v)} y2={Y(v)} stroke={colors.line} strokeWidth={1} strokeDasharray="2 8" />
              <text x={PX0 - 14} y={Y(v) + 6} textAnchor="end" fontFamily={fonts.mono} fontSize={17} fill={colors.faint}>
                {v}
              </text>
            </g>
          ))}
          <line x1={PX0} x2={PX1} y1={Y(0)} y2={Y(0)} stroke={colors.faint} strokeWidth={1.5} />
          {[10, 20, 30, 40].map((v) => (
            <g key={v}>
              <line x1={X(v)} x2={X(v)} y1={Y(0)} y2={Y(0) + 8} stroke={colors.faint} />
              <text x={X(v)} y={Y(0) + 32} textAnchor="middle" fontFamily={fonts.mono} fontSize={18} fill={colors.muted}>
                {v}
              </text>
            </g>
          ))}
          <text x={PX1 + 14} y={Y(0) + 6} fontFamily={mathFont} fontStyle="italic" fontSize={28} fill={colors.muted}>
            x
          </text>
          {/* true staircase */}
          <path d={stepPathFrom(psiPts)} fill="none" stroke={colors.fg} strokeOpacity={0.42} strokeWidth={3} />
          {/* sum of waves from the first K zeros */}
          <path d={pathFrom(curve)} fill="none" stroke={colors.accent} strokeWidth={2.6} opacity={curveIn} style={{filter: glow(5)}} />
        </g>

        {/* mini critical line with the zeros used so far */}
        <g opacity={plotIn}>
          <line x1={CLX} x2={CLX} y1={CL_Y(0)} y2={CL_Y(240)} stroke={colors.accent} strokeOpacity={0.35} strokeWidth={1.5} />
          {gam.slice(3, 100).map((g, i) => {
            const k = i + 4;
            const o = Math.max(0, Math.min(1, nCont - (k - 1)));
            return o > 0 ? <circle key={k} cx={CLX} cy={CL_Y(g)} r={3} fill={colors.accent} opacity={o * curveIn} /> : null;
          })}
        </g>
      </svg>

      {/* zero labels beside the waves */}
      {waveKeys.map((k, r) => (
        <div
          key={k}
          style={{
            position: 'absolute',
            left: 226,
            top: ROW_Y[r] - 15,
            fontFamily: fonts.mono,
            fontSize: 22,
            color: colors.fg,
            opacity: ramp(f, starts[r] - 2, 10) * rowsOpacity,
          }}
        >
          1/2 + {d1(gam[r])}i
        </div>
      ))}

      {/* counter */}
      <div style={{position: 'absolute', left: 232, top: 470, opacity: curveIn}}>
        <div style={{fontFamily: fonts.mono, fontSize: 18, letterSpacing: '0.08em', color: colors.muted, textTransform: 'uppercase'}}>zeros used</div>
        <div
          style={{
            fontFamily: fonts.display,
            fontStyle: 'italic',
            fontSize: 96,
            lineHeight: 1,
            marginTop: 6,
            color: colors.accent,
            transform: `scale(${1 + 0.06 * Math.min(1, bump)})`,
            transformOrigin: 'left center',
          }}
        >
          {shownLevel}
        </div>
      </div>

      {/* psi honesty label */}
      <div style={{position: 'absolute', left: PX0, top: 262, opacity: ramp(f, B.rebuild + 4, 14), display: 'flex', alignItems: 'baseline', gap: 2}}>
        <M style={{fontSize: 34, color: colors.fg}}>ψ(x)</M>
        <span style={{fontFamily: fonts.mono, fontSize: 21, color: colors.muted}}>: primes and prime powers, weighted by log p</span>
      </div>
    </div>
  );
};

// =====================================================================
// Beats B + C: zero off the line (louder wave), then all on the line (error ~ sqrt x)
// =====================================================================
const SX0 = 170;
const SX1 = 450;
const SY0 = 300;
const SY1 = 850;
const reX = scale(0, 1, SX0, SX1);
const gY = scale(0, 45, SY1, SY0 + 10);
const WX0 = 560;
const WX1 = 1760;
const WY = 575;
const U1 = 6;
const uX = scale(0, U1, WX0, WX1);
const AMP = 65 / Math.exp(0.5 * U1); // single on-line wave reaches 65 px at the right edge
const OMEGA = 6;
const N_ZEROS = 6;
const aK = gam.slice(0, N_ZEROS).map((g) => gam[0] / g);
const wK = gam.slice(0, N_ZEROS).map((g) => (OMEGA * g) / gam[0]);
const vK = gam.slice(0, N_ZEROS).map((g) => (0.09 * g) / gam[0]);
const BETA_MAX = 0.72;
const U_SAMPLES = Array.from({length: 361}, (_, i) => (U1 * i) / 360);

const waveK = (k: number, u: number, f: number) => Math.cos(wK[k] * u - vK[k] * f);
// tightest constant that still contains the summed waves while they are on screen (so the band hugs the curve)
const SUM_MAX = (() => {
  let m = 0;
  for (let f = B.error; f <= B.line3; f++)
    for (const u of U_SAMPLES) {
      let v = 0;
      for (let k = 0; k < N_ZEROS; k++) v += aK[k] * waveK(k, u, f);
      m = Math.max(m, Math.abs(v));
    }
  return m * 1.04;
})();

const BeatBC: React.FC<{f: number}> = ({f}) => {
  const op = win(f, B.farther - 2, 14, B.line3 - 12, 10);
  if (op <= 0) return null;
  const betaDot = 0.5 + (BETA_MAX - 0.5) * (ramp(f, B.right - 6, 26, inOut) - ramp(f, B.line2, 26, inOut));
  const betaWave = 0.5 + (BETA_MAX - 0.5) * (ramp(f, B.louder - 22, 40, inOut) - ramp(f, B.line2 + 4, 30, inOut));
  const drawIn = ramp(f, B.farther, 26, Easing.inOut(Easing.quad));
  const othersIn = (k: number) => ramp(f, B.noWave - 6 + 7 * (k - 1), 12);
  const collapse = ramp(f, B.error, 22, inOut); // individual waves -> their sum
  const envBeta = win(f, B.farther + 6, 16, B.noWave - 8, 14);
  const sqrtEnv = ramp(f, B.error + 16, 30, inOut);

  const w1 = U_SAMPLES.map((u) => [uX(u), WY - AMP * Math.exp(betaWave * u) * waveK(0, u, f)] as [number, number]);
  const env = (sign: number) => U_SAMPLES.map((u) => [uX(u), WY - sign * AMP * Math.exp(betaWave * u)] as [number, number]);
  const sumPts = U_SAMPLES.map((u) => {
    let v = 0;
    for (let k = 0; k < N_ZEROS; k++) v += aK[k] * waveK(k, u, f);
    return [uX(u), WY - AMP * Math.exp(0.5 * u) * v] as [number, number];
  });
  const sq = (sign: number) => U_SAMPLES.map((u) => [uX(u), WY - sign * SUM_MAX * AMP * Math.exp(0.5 * u)] as [number, number]);
  const dotX = reX(betaDot);
  const ghost = ramp(f, B.right - 6, 8) * (1 - ramp(f, B.line2 + 10, 12));
  const betaLabel = ramp(f, B.farther + 10, 12) * (1 - ramp(f, B.line2 + 4, 12));
  const envLabelY = WY - AMP * Math.exp(betaWave * 4.7);

  return (
    <div style={{position: 'absolute', inset: 0, opacity: op}}>
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        <defs>
          <clipPath id="s04-wclip">
            <rect x={WX0 - 4} y={SY0 - 10} width={WX1 - WX0 + 8} height={SY1 - SY0 + 20} />
          </clipPath>
        </defs>
        {/* critical strip */}
        <rect x={SX0} y={SY0} width={SX1 - SX0} height={SY1 - SY0} fill={colors.strip} />
        <line x1={SX0} x2={SX0} y1={SY0} y2={SY1} stroke={colors.line} />
        <line x1={SX1} x2={SX1} y1={SY0} y2={SY1} stroke={colors.line} />
        <line x1={reX(0.5)} x2={reX(0.5)} y1={SY0} y2={SY1} stroke={colors.accent} strokeWidth={2} strokeOpacity={0.9} />
        {[
          [0, '0'],
          [0.5, '1/2'],
          [1, '1'],
        ].map(([v, t]) => (
          <text key={String(t)} x={reX(v as number)} y={SY1 + 30} textAnchor="middle" fontFamily={fonts.mono} fontSize={20} fill={colors.muted}>
            {t}
          </text>
        ))}
        {/* ghost of the on-line position */}
        <circle cx={reX(0.5)} cy={gY(gam[0])} r={9} fill="none" stroke={colors.accent} strokeDasharray="3 3" opacity={ghost * 0.8} />
        <line x1={reX(0.5) + 12} x2={dotX - 12} y1={gY(gam[0])} y2={gY(gam[0])} stroke={colors.accent} strokeOpacity={0.5 * ghost} strokeWidth={1.5} />
        {/* other zeros, all on the line */}
        {gam.slice(1, N_ZEROS).map((g, i) => (
          <circle key={g} cx={reX(0.5)} cy={gY(g)} r={7} fill={colors.accent} opacity={othersIn(i + 1)} style={{filter: glow(8)}} />
        ))}
        {/* the moving zero */}
        <circle cx={dotX} cy={gY(gam[0])} r={9} fill={colors.accent} style={{filter: glow(lerp(8, 16, (betaDot - 0.5) / (BETA_MAX - 0.5)))}} />

        {/* waves panel */}
        <line x1={WX0} x2={WX1} y1={WY} y2={WY} stroke={colors.line} />
        <text x={WX1 + 14} y={WY + 8} fontFamily={mathFont} fontStyle="italic" fontSize={28} fill={colors.muted}>
          x
        </text>
        <g clipPath="url(#s04-wclip)">
          {/* x^beta envelope */}
          <g opacity={envBeta}>
            <path d={pathFrom(env(1), drawIn)} fill="none" stroke={colors.muted} strokeWidth={1.5} strokeDasharray="6 7" />
            <path d={pathFrom(env(-1), drawIn)} fill="none" stroke={colors.muted} strokeWidth={1.5} strokeDasharray="6 7" />
          </g>
          {/* other waves (faint), then collapse into their sum */}
          {Array.from({length: N_ZEROS - 1}, (_, i) => i + 1).map((k) => {
            const pts = U_SAMPLES.map((u) => [uX(u), WY - AMP * aK[k] * Math.exp(0.5 * u) * waveK(k, u, f)] as [number, number]);
            return (
              <path
                key={k}
                d={pathFrom(pts)}
                fill="none"
                stroke={k % 2 ? colors.fg : colors.accent}
                strokeOpacity={0.5}
                strokeWidth={1.4}
                opacity={othersIn(k) * (1 - 0.85 * collapse)}
              />
            );
          })}
          {/* the first zero's wave */}
          <path
            d={pathFrom(w1, drawIn)}
            fill="none"
            stroke={colors.accent}
            strokeWidth={2.6}
            opacity={1 - 0.85 * collapse}
            style={{filter: glow(lerp(4, 10, (betaWave - 0.5) / (BETA_MAX - 0.5)))}}
          />
          {/* sum of all waves = the error */}
          <path d={pathFrom(sumPts)} fill="none" stroke={colors.fg} strokeWidth={2.4} opacity={collapse} />
          {/* sqrt(x) envelope */}
          <path d={pathFrom(sq(1), sqrtEnv)} fill="none" stroke={colors.accent} strokeWidth={2.2} style={{filter: glow(6)}} />
          <path d={pathFrom(sq(-1), sqrtEnv)} fill="none" stroke={colors.accent} strokeWidth={2.2} style={{filter: glow(6)}} />
        </g>
      </svg>

      {/* labels */}
      <div style={{position: 'absolute', left: dotX + 18, top: gY(gam[0]) - 52, opacity: betaLabel, whiteSpace: 'nowrap'}}>
        <M style={{fontSize: 30, color: colors.fg}}>β</M>
        <span style={{fontFamily: fonts.mono, fontSize: 20, color: colors.fg}}> = {betaDot.toFixed(2)}</span>
      </div>
      <div
        style={{
          position: 'absolute',
          left: uX(4.7) - 70,
          top: envLabelY - 50,
          opacity: envBeta * drawIn,
          whiteSpace: 'nowrap',
        }}
      >
        <M style={{fontSize: 30, color: colors.muted}}>
          size ~ x<sup style={{fontSize: 20}}>β</sup>
        </M>
      </div>
      <div style={{position: 'absolute', left: uX(5) - 40, top: WY - SUM_MAX * AMP * Math.exp(2.5) - 58, opacity: ramp(f, B.square - 4, 14), whiteSpace: 'nowrap'}}>
        <M style={{fontSize: 34, color: colors.accent}}>±√x</M>
      </div>
      <div style={{position: 'absolute', left: WX0, top: WY - 92, opacity: collapse, fontFamily: fonts.mono, fontSize: 20, color: colors.fg}}>
        total error = all the waves added up
      </div>
      <Tag style={{right: 160, top: 262}}>schematic</Tag>
    </div>
  );
};

// =====================================================================
// Beat D: GRH race, primes ending in 1, 3, 7, 9 up to 10^6
// =====================================================================
const DIG = ['1', '3', '7', '9'] as const;
const lx = lastdigit.x;
const I0 = lx.findIndex((v) => v >= 100);
const RX0 = 230;
const RX1 = 1250;
const RY0 = 330;
const RY1 = 760;
const rX = scale(2, 6, RX0, RX1);
const rY = scale(18, 32, RY1, RY0);
const totals = lx.map((_, i) => DIG.reduce((a, d) => a + lastdigit.counts[d][i], 0));
const share = (d: (typeof DIG)[number], i: number) => (100 * lastdigit.counts[d][i]) / totals[i];
const STYLE: Record<(typeof DIG)[number], {stroke: string; dash?: string; opacity: number}> = {
  '1': {stroke: colors.fg, opacity: 0.9},
  '3': {stroke: colors.fg, dash: '10 7', opacity: 0.7},
  '7': {stroke: colors.accent, opacity: 1},
  '9': {stroke: colors.muted, dash: '2 6', opacity: 0.9},
};
const SUP: Record<number, string> = {2: '²', 3: '³', 4: '⁴', 5: '⁵', 6: '⁶'};

const BeatD: React.FC<{f: number}> = ({f}) => {
  const op = win(f, B.line3 - 1, 14);
  if (op <= 0) return null;
  const sweep = ramp(f, B.generalized + 6, 112, inOut);
  const fi = I0 + sweep * (lx.length - 1 - I0);
  const iA = Math.floor(fi);
  const iB = Math.min(lx.length - 1, iA + 1);
  const t = fi - iA;
  const curX = Math.exp(lerp(Math.log(lx[iA]), Math.log(lx[iB]), t));
  const hi7 = ramp(f, B.ending - 6, 16);
  const path = (d: (typeof DIG)[number]) => {
    const pts: [number, number][] = [];
    for (let i = I0; i <= iA; i++) pts.push([rX(Math.log10(lx[i])), rY(share(d, i))]);
    pts.push([rX(Math.log10(curX)), rY(lerp(share(d, iA), share(d, iB), t))]);
    return pts;
  };
  const idxNow = t > 0.5 ? iB : iA;

  return (
    <div style={{position: 'absolute', inset: 0, opacity: op}}>
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        <defs>
          <clipPath id="s04-rclip">
            <rect x={RX0} y={RY0 - 6} width={RX1 - RX0 + 10} height={RY1 - RY0 + 12} />
          </clipPath>
        </defs>
        <g opacity={ramp(f, B.line3, 16)}>
          {[20, 25, 30].map((v) => (
            <g key={v}>
              <line
                x1={RX0}
                x2={RX1}
                y1={rY(v)}
                y2={rY(v)}
                stroke={v === 25 ? colors.faint : colors.line}
                strokeWidth={1}
                strokeDasharray={v === 25 ? '6 6' : '2 8'}
              />
              <text x={RX0 - 14} y={rY(v) + 6} textAnchor="end" fontFamily={fonts.mono} fontSize={18} fill={v === 25 ? colors.muted : colors.faint}>
                {v}%
              </text>
            </g>
          ))}
          <line x1={RX0} x2={RX1} y1={RY1} y2={RY1} stroke={colors.faint} strokeWidth={1.5} />
          {[2, 3, 4, 5, 6].map((e) => (
            <g key={e}>
              <line x1={rX(e)} x2={rX(e)} y1={RY1} y2={RY1 + 8} stroke={colors.faint} />
              <text x={rX(e)} y={RY1 + 38} textAnchor="middle" fontFamily={mathFont} fontSize={26} fill={colors.muted}>
                10{SUP[e]}
              </text>
            </g>
          ))}
        </g>
        <g clipPath="url(#s04-rclip)">
          {DIG.map((d) => {
            const st = STYLE[d];
            const dim = d === '7' ? 1 : 1 - 0.55 * hi7;
            return (
              <path
                key={d}
                d={pathFrom(path(d))}
                fill="none"
                stroke={st.stroke}
                strokeOpacity={st.opacity * dim}
                strokeDasharray={st.dash}
                strokeWidth={d === '7' ? 2.8 + hi7 : 2.2}
                strokeLinejoin="round"
                style={d === '7' ? {filter: glow(4 + 6 * hi7)} : undefined}
              />
            );
          })}
        </g>
      </svg>

      <div style={{position: 'absolute', left: RX0, top: RY0 - 52, fontFamily: fonts.mono, fontSize: 19, color: colors.muted, opacity: ramp(f, B.line3 + 4, 14)}}>
        share of primes so far, by last digit · even split: proven · GRH: how fast the gaps shrink
      </div>

      {/* leaderboard */}
      <div style={{position: 'absolute', left: 1360, top: RY0 - 10, width: 440, opacity: ramp(f, B.generalized, 16)}}>
        <div style={{fontFamily: fonts.mono, fontSize: 18, letterSpacing: '0.08em', textTransform: 'uppercase', color: colors.muted}}>primes up to</div>
        <div style={{fontFamily: fonts.display, fontStyle: 'italic', fontSize: 72, lineHeight: 1.05, color: colors.fg, marginTop: 4}}>{fmt(lx[idxNow])}</div>
        <div style={{marginTop: 34, display: 'flex', flexDirection: 'column', gap: 10}}>
          {DIG.map((d) => {
            const st = STYLE[d];
            const isHi = d === '7';
            const hiA = isHi ? hi7 : 0;
            return (
              <div
                key={d}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  height: 54,
                  padding: '0 14px',
                  borderRadius: 10,
                  background: `rgba(255,106,26,${0.13 * hiA})`,
                  opacity: isHi ? 1 : 1 - 0.35 * hi7,
                }}
              >
                <svg width={42} height={10} style={{marginRight: 16}}>
                  <line x1={0} x2={42} y1={5} y2={5} stroke={st.stroke} strokeOpacity={st.opacity} strokeWidth={3} strokeDasharray={st.dash} />
                </svg>
                <span style={{fontFamily: fonts.body, fontSize: 26, color: isHi ? colors.accent : colors.fg, width: 130}}>ends in {d}</span>
                <span style={{fontFamily: fonts.mono, fontSize: 26, color: colors.fg, width: 120, textAlign: 'right'}}>
                  {fmt(lastdigit.counts[d][idxNow])}
                </span>
                <span style={{fontFamily: fonts.mono, fontSize: 21, color: colors.muted, width: 104, textAlign: 'right'}}>
                  {share(d, idxNow).toFixed(2)}%
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* GRH honesty label */}
      <div
        style={{
          position: 'absolute',
          left: RX0,
          top: 832,
          fontFamily: fonts.body,
          fontSize: 28,
          color: colors.fg,
          display: 'flex',
          alignItems: 'center',
          opacity: ramp(f, B.primes7 - 4, 14),
        }}
      >
        primes ending in <span style={{color: colors.accent, margin: '0 0.25em'}}>7</span> = primes
        <span style={{fontFamily: mathFont, fontSize: 34, display: 'inline-flex'}}>
          <Equiv />
        </span>
        <span style={{color: colors.accent, marginRight: '0.25em'}}>7</span> mod 10
      </div>
    </div>
  );
};

// =====================================================================
export const S04Music: React.FC = () => {
  const f = useCurrentFrame();
  const titleA = 1 - ramp(f, B.line3 - 12, 10);
  return (
    <SceneFrame index={4} kicker="Music of the primes">
      <div style={{opacity: titleA}}>
        <Title size={78}>Music of the primes</Title>
      </div>
      {f >= B.line3 - 2 && (
        <Title size={78} start={B.line3}>
          Generalized RH
        </Title>
      )}
      <BeatA f={f} />
      <BeatBC f={f} />
      <BeatD f={f} />
    </SceneFrame>
  );
};
