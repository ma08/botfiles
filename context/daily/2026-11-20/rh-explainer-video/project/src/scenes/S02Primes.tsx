import React from 'react';
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {SceneFrame} from '../components/SceneFrame';
import {colors, fonts, glow} from '../theme';
import {clamp, enter, ramp} from '../lib/anim';
import {sceneById, wordFrame} from '../lib/timeline';
import primesData from '../data/primes.json';
import {band, fmt, li, PI_MAX_X, PRIMES, primePi} from './s02/primeMath';

const s = sceneById('s02_primes');

// Narration beats (keyed to words so re-voicing keeps sync).
const B = {
  start: wordFrame(s, 'Start'),
  two: wordFrame(s, 'Two'),
  three: wordFrame(s, 'three'),
  five: wordFrame(s, 'five'),
  seven: wordFrame(s, 'seven'),
  eleven: wordFrame(s, 'eleven'),
  count: wordFrame(s, 'Count'),
  x: wordFrame(s, 'x'),
  stair: wordFrame(s, 'staircase'),
  smooth: wordFrame(s, 'smooth'),
  closely: wordFrame(s, 'closely'),
  trillion: wordFrame(s, 'trillion'),
  num: wordFrame(s, '37.6'),
  billion: wordFrame(s, 'billion'),
  misses: wordFrame(s, 'misses'),
  thousand: wordFrame(s, 'thousand'),
  does: wordFrame(s, 'Does'),
  forever: wordFrame(s, 'forever'),
};

// Derived timing.
const T = {
  sweepStart: B.eleven + 6, // remaining primes light up
  buildStart: B.count + 26, // cursor sweeps 0 -> 100, cells fly onto the stairs
  buildEnd: B.stair + 6,
  zoom1Start: B.stair + 22,
  zoom1End: B.closely - 4, // ~10^4 by "closely"
  zoom2Start: B.closely + 10,
  zoom2End: B.trillion + 4, // ~10^6 by "trillion"
  endStart: B.does,
  endEnd: B.does + 48,
};

// Grid geometry (10 x 10, numbers 1..100).
const CELL = 62;
const PITCH = 70;
const GX0 = 960 - (10 * PITCH - (PITCH - CELL)) / 2;
const GY0 = 150;
const cellCenter = (n: number): [number, number] => {
  const r = Math.floor((n - 1) / 10);
  const c = (n - 1) % 10;
  return [GX0 + c * PITCH + CELL / 2, GY0 + r * PITCH + CELL / 2];
};

// Plot geometry.
const PL = 230;
const PR = 1690;
const PT = 200;
const PB = 810;
const W = PR - PL;
const H = PB - PT;

const EARLY = [2, 3, 5, 7, 11];
const P100 = primesData.stair100.primes as number[];
const FACTS = primesData.facts;
const END_LOG = Math.log10(1.75e6);

const lightFrame = (p: number) => {
  const i = EARLY.indexOf(p);
  if (i >= 0) return [B.two, B.three, B.five, B.seven, B.eleven][i];
  const k = P100.indexOf(p) - EARLY.length;
  return T.sweepStart + k * 1.5;
};

const landFrame = (p: number) => interpolate(p, [0, 100], [T.buildStart, T.buildEnd]);

const SCENE_END = Math.round(s.duration * 30);
const camLog10 = (f: number) =>
  f > T.endEnd
    ? interpolate(f, [T.endEnd, SCENE_END], [END_LOG, END_LOG + 0.07], clamp) // slow drift outward, "forever"
    : interpolate(f, [T.zoom1Start, T.zoom1End, T.zoom2Start, T.zoom2End, T.endStart, T.endEnd], [2, 4, 4, 6, 6, END_LOG], {
        ...clamp,
        easing: Easing.inOut(Easing.cubic),
      });

const Sup: React.FC<{children: React.ReactNode}> = ({children}) => (
  <span style={{fontSize: '0.62em', verticalAlign: '0.62em', lineHeight: 0}}>{children}</span>
);

export const S02Primes: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // ---- camera ----
  const xmax = Math.pow(10, camLog10(frame));
  const ymax = li(xmax) * 1.12;
  const X = (x: number) => PL + (x / xmax) * W;
  const Y = (y: number) => PB - (y / ymax) * H;

  // ---- build phase: cursor sweep to x = 100 ----
  const drawX = interpolate(frame, [T.buildStart, T.buildEnd], [0, 100], clamp);
  const dataEnd = Math.min(PI_MAX_X, frame < T.zoom1Start ? drawX : xmax);
  const axesIn = ramp(frame, T.buildStart - 22, 24);

  // ---- staircase path ----
  let stair = `M${X(0).toFixed(1)},${Y(0).toFixed(1)}`;
  if (dataEnd > 1) {
    if (primePi(dataEnd) <= 1500) {
      for (const p of PRIMES) {
        if (p > dataEnd) break;
        stair += ` H${X(p).toFixed(1)} V${Y(primePi(p)).toFixed(1)}`;
      }
      stair += ` H${X(dataEnd).toFixed(1)}`;
    } else {
      const N = 900;
      for (let i = 1; i <= N; i++) {
        const x = (dataEnd * i) / N;
        stair += ` H${X(x).toFixed(1)} V${Y(primePi(x)).toFixed(1)}`;
      }
    }
  }

  // ---- li curve + band ----
  const liDraw = ramp(frame, B.smooth, 30, Easing.inOut(Easing.cubic));
  const liEnd = 2 + (xmax - 2) * liDraw;
  const NS = 260;
  const liPts: [number, number][] = [];
  const upPts: string[] = [];
  const loPts: string[] = [];
  for (let i = 0; i <= NS; i++) {
    const x = 2 + ((liEnd - 2) * i) / NS;
    const v = li(x);
    const b = band(x);
    liPts.push([X(x), Y(v)]);
    upPts.push(`${X(x).toFixed(1)},${Y(v + b).toFixed(1)}`);
    loPts.push(`${X(x).toFixed(1)},${Y(v - b).toFixed(1)}`);
  }
  const liSolid = liPts.filter((_, i) => 2 + ((liEnd - 2) * i) / NS <= PI_MAX_X);
  const liBeyond = liPts.filter((_, i) => 2 + ((liEnd - 2) * i) / NS >= PI_MAX_X);
  const toD = (pts: [number, number][]) => pts.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  const bandD = `M${upPts.join(' L')} L${loPts.reverse().join(' L')} Z`;
  const bandIn = ramp(frame, B.closely - 6, 24);
  const misses = ramp(frame, B.misses, 10) * (1 - ramp(frame, B.thousand + 12, 20));

  // ---- final beat: beyond 10^6 ----
  const endT = ramp(frame, T.endStart, 40, Easing.inOut(Easing.cubic));
  const qIn = ramp(frame, B.forever - 6, 20);
  const xData = X(PI_MAX_X);

  // ---- readouts ----
  const readoutIn = ramp(frame, T.buildStart, 16) * (1 - ramp(frame, B.trillion - 6, 12));
  const rx = frame < T.zoom1Start ? Math.floor(drawX) : Math.round(xmax);
  const rowLiIn = ramp(frame, B.smooth, 14);
  const calloutIn = ramp(frame, B.trillion, 16) * (1 - ramp(frame, T.endStart, 18));

  // gentle push during the hold at 10^6
  const push = interpolate(frame, [T.zoom2End, T.endStart], [1, 1.03], {...clamp, easing: Easing.inOut(Easing.sin)});
  const pushBack = interpolate(frame, [T.endStart, T.endEnd], [push, 1], clamp);
  const camScale = frame < T.endStart ? push : pushBack;

  // label for the right end of the x axis
  const axisEndLabel = frame >= T.endStart ? '' : fmt(rx > 100 ? xmax : Math.max(100, rx));

  return (
    <SceneFrame index={2} kicker={s.title}>
      {/* ---------- plot ---------- */}
      <AbsoluteFill style={{transform: `scale(${camScale})`, transformOrigin: `${PL}px ${PB}px`}}>
        <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0}}>
          <defs>
            <clipPath id="s02-clip">
              <rect x={PL - 4} y={PT - 60} width={W + 8} height={H + 64} />
            </clipPath>
            <linearGradient id="s02-fade" x1={xData} x2={PR} y1={0} y2={0} gradientUnits="userSpaceOnUse">
              <stop offset="0" stopColor="#fff" stopOpacity={1} />
              <stop offset="1" stopColor="#fff" stopOpacity={0.05} />
            </linearGradient>
            <mask id="s02-beyond">
              <rect x={0} y={0} width={xData} height={1080} fill="#fff" />
              <rect x={xData} y={0} width={1920 - xData} height={1080} fill="url(#s02-fade)" />
            </mask>
          </defs>

          {/* axes */}
          <g opacity={axesIn}>
            <line x1={PL} y1={PB} x2={PR + 30} y2={PB} stroke={colors.line} strokeWidth={2} />
            <path d={`M${PR + 30},${PB - 7} L${PR + 42},${PB} L${PR + 30},${PB + 7}`} fill="none" stroke={colors.line} strokeWidth={2} />
            <line x1={PL} y1={PB} x2={PL} y2={PT - 30} stroke={colors.line} strokeWidth={2} />
            <text x={PL} y={PB + 36} fill={colors.faint} fontFamily={fonts.mono} fontSize={20} textAnchor="middle">
              0
            </text>
            <text x={PR + 56} y={PB + 7} fill={colors.muted} fontFamily={fonts.mono} fontSize={22}>
              x
            </text>
            {axisEndLabel && (
              <>
                <line x1={PR} y1={PB} x2={PR} y2={PB + 10} stroke={colors.line} strokeWidth={2} />
                <text x={PR} y={PB + 36} fill={colors.muted} fontFamily={fonts.mono} fontSize={20} textAnchor="end">
                  {axisEndLabel}
                </text>
              </>
            )}
            {endT > 0 && (
              <g opacity={endT}>
                <line x1={xData} y1={PB} x2={xData} y2={PB + 10} stroke={colors.line} strokeWidth={2} />
                <text x={xData} y={PB + 36} fill={colors.muted} fontFamily={fonts.mono} fontSize={20} textAnchor="middle">
                  1,000,000
                </text>
              </g>
            )}
          </g>

          <g clipPath="url(#s02-clip)">
            {/* band li +/- sqrt(x) log x / 8 pi */}
            <g mask="url(#s02-beyond)" opacity={bandIn}>
              <path
                d={bandD}
                fill="rgba(242,237,228,0.2)"
                stroke="rgba(242,237,228,0.5)"
                strokeWidth={1.2}
                style={{filter: 'drop-shadow(0 0 6px rgba(242,237,228,0.28))'}}
              />
            </g>
            {/* li(x) */}
            {liDraw > 0 && (
              <>
                <path
                  d={toD(liSolid)}
                  fill="none"
                  stroke={colors.fg}
                  strokeWidth={2.4 + misses * 1.6}
                  strokeLinecap="round"
                  opacity={0.92}
                  style={{filter: `drop-shadow(0 0 ${4 + misses * 8}px rgba(242,237,228,${0.25 + misses * 0.4}))`}}
                />
                {liBeyond.length > 1 && (
                  <g mask="url(#s02-beyond)">
                    <path d={toD(liBeyond)} fill="none" stroke={colors.fg} strokeWidth={2.2} strokeDasharray="8 9" opacity={0.85} />
                  </g>
                )}
              </>
            )}
            {/* pi(x) staircase */}
            <path
              d={stair}
              fill="none"
              stroke={colors.accent}
              strokeWidth={3}
              strokeLinejoin="round"
              opacity={axesIn}
              style={{filter: glow(6)}}
            />
          </g>

          {/* build cursor */}
          {frame >= T.buildStart - 4 && frame < T.zoom1Start + 10 && (
            <g opacity={ramp(frame, T.buildStart - 4, 8) * (1 - ramp(frame, T.buildEnd + 4, 12))}>
              <line
                x1={X(drawX)}
                y1={PB}
                x2={X(drawX)}
                y2={Y(primePi(drawX)) - 40}
                stroke={colors.muted}
                strokeWidth={1.5}
                strokeDasharray="4 6"
              />
              <circle cx={X(drawX)} cy={Y(primePi(drawX))} r={6} fill={colors.fg} />
              <text
                x={X(drawX)}
                y={PB + 36}
                fill={colors.fg}
                fontFamily={fonts.mono}
                fontSize={22}
                textAnchor="middle"
                opacity={1 - interpolate(drawX, [86, 96], [0, 1], clamp)}
              >
                x
              </text>
            </g>
          )}
        </svg>

        {/* curve labels */}
        <div
          style={{
            position: 'absolute',
            left: Math.min(X(dataEnd), PR) + 14,
            top: Y(primePi(dataEnd)) + (frame > T.zoom1Start ? 6 : -16),
            fontFamily: fonts.mono,
            fontSize: 26,
            color: colors.accent,
            opacity: ramp(frame, T.buildEnd - 4, 14),
            whiteSpace: 'nowrap',
          }}
        >
          π(x)
        </div>
        {liDraw > 0.6 && (
          <div
            style={{
              position: 'absolute',
              left: X(0.62 * Math.min(xmax, 1.2 * PI_MAX_X)) - 92,
              top: Y(li(0.62 * Math.min(xmax, 1.2 * PI_MAX_X))) - 52,
              fontFamily: fonts.mono,
              fontSize: 26,
              color: colors.fg,
              opacity: ramp(frame, B.smooth + 18, 14),
              whiteSpace: 'nowrap',
            }}
          >
            li(x)
          </div>
        )}
        {bandIn > 0 && (
          <div
            style={{
              position: 'absolute',
              left: X(0.62 * Math.min(xmax, 1.2 * PI_MAX_X)) + 30,
              top: Y(li(0.62 * Math.min(xmax, 1.2 * PI_MAX_X))) + 26,
              fontFamily: fonts.mono,
              fontSize: 19,
              color: colors.muted,
              opacity: bandIn * 0.85,
              whiteSpace: 'nowrap',
            }}
          >
            band if RH holds: li(x) ± √x·log x / 8π
          </div>
        )}

        {/* question at the end */}
        {qIn > 0 && (
          <div
            style={{
              position: 'absolute',
              left: PR + 8,
              top: Y(li(xmax)) - 40,
              fontFamily: fonts.display,
              fontStyle: 'italic',
              fontSize: 140,
              lineHeight: 1,
              color: colors.accent,
              filter: glow(14, 'rgba(255,110,40,0.55)'),
              opacity: qIn,
              transform: `translateY(${(1 - qIn) * 20}px)`,
            }}
          >
            ?
          </div>
        )}
      </AbsoluteFill>

      {/* ---------- grid of 1..100 and flying primes ---------- */}
      {frame < T.zoom1Start + 24 &&
        Array.from({length: 100}, (_, i) => i + 1).map((n) => {
          const isP = P100.includes(n);
          const [cx, cy] = cellCenter(n);
          const gridIn = ramp(frame, B.start - 10 + ((n - 1) % 10) * 1.2 + Math.floor((n - 1) / 10) * 1.6, 14);
          if (!isP) {
            const fade = 1 - ramp(frame, B.count, 26);
            if (fade <= 0) return null;
            return (
              <div
                key={n}
                style={{
                  position: 'absolute',
                  left: cx - CELL / 2,
                  top: cy - CELL / 2,
                  width: CELL,
                  height: CELL,
                  borderRadius: 8,
                  border: `1px solid ${colors.line}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily: fonts.mono,
                  fontSize: 20,
                  color: colors.faint,
                  opacity: gridIn * fade * 0.85,
                }}
              >
                {n}
              </div>
            );
          }
          const lf = lightFrame(n);
          const lit = frame >= lf ? 1 : 0;
          const pop = spring({frame: frame - lf, fps, config: {damping: 12, mass: 0.6}});
          const popScale = lit ? 1 + 0.22 * Math.sin(Math.min(1, pop) * Math.PI) : 1;
          const land = landFrame(n);
          const u = interpolate(frame, [land - 22, land], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
          const tx = X(n);
          const ty = Y(primePi(n));
          const us = interpolate(frame, [land - 22, land - 8], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
          const px = cx + (tx - cx) * u;
          const py = cy + (ty - cy) * u - Math.sin(u * Math.PI) * 18;
          const size = CELL + (13 - CELL) * us;
          const dotFade = 1 - ramp(frame, T.zoom1Start, 18);
          return (
            <div
              key={n}
              style={{
                position: 'absolute',
                left: px - size / 2,
                top: py - size / 2,
                width: size,
                height: size,
                borderRadius: 8 + (size / 2 - 8) * us,
                border: `1px solid ${lit ? colors.accent : colors.line}`,
                background: lit ? `rgba(255,106,26,${0.16 + 0.84 * u})` : 'transparent',
                boxShadow: lit ? `0 0 ${18 - 6 * u}px rgba(255,110,40,${0.55 + 0.3 * u})` : 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: fonts.mono,
                fontSize: 20,
                color: lit ? colors.fg : colors.faint,
                opacity: gridIn * dotFade,
                transform: `scale(${popScale})`,
              }}
            >
              <span style={{opacity: 1 - Math.min(1, us * 2.2)}}>{n}</span>
            </div>
          );
        })}

      {/* ---------- live readout (x, pi(x), li(x)) ---------- */}
      {readoutIn > 0 && (
        <div style={{position: 'absolute', left: PL + 46, top: PT + 24, opacity: readoutIn, fontFamily: fonts.mono}}>
          <Row label="x" value={fmt(rx)} color={colors.fg} />
          <Row label="π(x)" value={fmt(primePi(rx))} color={colors.accent} />
          <div style={{opacity: rowLiIn}}>
            <Row label="li(x)" value={fmt(li(Math.max(2, rx)))} color={colors.fg} />
          </div>
        </div>
      )}

      {/* ---------- trillion callout ---------- */}
      {calloutIn > 0 && (
        <div style={{position: 'absolute', left: PL + 46, top: PT + 6, opacity: calloutIn}}>
          <div style={{fontFamily: fonts.mono, fontSize: 22, color: colors.muted, letterSpacing: '0.04em', ...enter(frame, B.trillion, 14, 8)}}>
            x = 10<Sup>12</Sup>, one trillion
          </div>
          <div style={{display: 'flex', alignItems: 'baseline', marginTop: 14, fontFamily: fonts.mono, fontSize: 58, color: colors.fg}}>
            <span style={{color: colors.accent, ...enter(frame, B.trillion + 6, 14, 8)}}>
              π(10<Sup>12</Sup>)
            </span>
            <span style={{margin: '0 22px', color: colors.muted, ...enter(frame, B.trillion + 10, 14, 8)}}>=</span>
            <Digits text={fmt(FACTS.pi_1e12)} start={B.num - 2} end={B.billion + 8} frame={frame} />
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'baseline',
              marginTop: 18,
              fontFamily: fonts.mono,
              fontSize: 40,
              color: colors.fg,
              ...enter(frame, B.misses - 4, 16, 10),
            }}
          >
            <span>li − π</span>
            <span style={{margin: '0 18px', color: colors.muted}}>=</span>
            <span style={{color: colors.fg}}>{fmt(FACTS.li_minus_pi_1e12)}</span>
          </div>
          <div style={{marginTop: 12, fontFamily: fonts.body, fontWeight: 300, fontSize: 26, color: colors.muted, ...enter(frame, B.thousand + 4, 16, 8)}}>
            about 1 part in a million
          </div>
        </div>
      )}
    </SceneFrame>
  );
};

const Row: React.FC<{label: string; value: string; color: string}> = ({label, value, color}) => (
  <div style={{display: 'flex', alignItems: 'baseline', gap: 18, height: 44}}>
    <span style={{width: 84, fontSize: 22, color: colors.muted}}>{label}</span>
    <span style={{fontSize: 32, color, minWidth: 150, textAlign: 'right'}}>{value}</span>
  </div>
);

/** Reveal an exact number digit by digit (never shows a wrong intermediate value). */
const Digits: React.FC<{text: string; start: number; end: number; frame: number}> = ({text, start, end, frame}) => {
  const n = text.length;
  return (
    <span>
      {text.split('').map((ch, i) => {
        const f0 = start + ((end - start) * i) / n;
        const t = ramp(frame, f0, 8);
        return (
          <span key={i} style={{opacity: t, display: 'inline-block', transform: `translateY(${(1 - t) * 10}px)`}}>
            {ch}
          </span>
        );
      })}
    </span>
  );
};
