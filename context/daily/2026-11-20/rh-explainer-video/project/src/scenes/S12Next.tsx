import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {SceneFrame} from '../components/SceneFrame';
import {colors, fonts, grid} from '../theme';
import {clamp, enter, pathFrom, ramp, springIn, stepPathFrom} from '../lib/anim';
import {lineEndFrame, lineStartFrame, sceneById, sceneFrames} from '../lib/timeline';
import lean from '../data/lean.json';
import status from '../data/status.json';
import primes from '../data/primes.json';
import zeros from '../data/zeros.json';
import {CodeWall} from './s10/CodeWall';
import {fmt, wordIn} from './s10/sync';

const S = sceneById('s12_next');
const END = sceneFrames(S);

const F = {
  no: wordIn(S, 0, 'no', 0, 0.35),
  and: wordIn(S, 0, 'and', 0, 0.68),
  argument: wordIn(S, 0, 'argument', 0, 0.83),
  lot: wordIn(S, 0, 'lot', 0, 0.96),
  L1: lineStartFrame(S, 1),
  L2: lineStartFrame(S, 2),
  L3: lineStartFrame(S, 3),
  L4: lineStartFrame(S, 4),
  // end card is not a narration beat: it starts after the final line ends (scene has a 4 s tail)
  endCard: Math.max(lineEndFrame(S, 4) + 12, END - 110),
};

const CREDITS = 'Narration: AI voice (ElevenLabs). Sources: alpo.ge/remark.pdf · math.mit.edu/~drew/grh · Lean Zulip';

// ---------- beat 0 ----------
const BlankPage: React.FC<{frame: number}> = ({frame}) => {
  const blink = Math.floor(frame / 16) % 2 === 0 ? 1 : 0.08;
  const drift = interpolate(frame, [0, F.L1], [0, 1], clamp);
  return (
    <div style={{position: 'absolute', inset: 0, ...enter(frame, 10, 20, 20)}}>
    <div
      style={{
        position: 'absolute',
        left: 200,
        top: 250,
        width: 460,
        height: 600,
        background: 'linear-gradient(180deg, #1d1a16 0%, #171410 100%)',
        border: `1px solid ${colors.line}`,
        borderRadius: 10,
        boxShadow: '0 30px 80px rgba(0,0,0,0.55)',
        transform: `scale(${1 + 0.02 * drift}) rotate(${-0.6 + 0.4 * drift}deg)`,
        transformOrigin: '50% 60%',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: '120px 34px 40px 34px',
          backgroundImage: 'repeating-linear-gradient(to bottom, rgba(242,237,228,0.045) 0px, rgba(242,237,228,0.045) 1px, transparent 1px, transparent 38px)',
        }}
      />
      <div style={{position: 'absolute', left: 50, top: 0, bottom: 0, width: 1, background: 'rgba(255,106,26,0.14)'}} />
      <div style={{position: 'absolute', left: 74, top: 66, width: 3, height: 38, background: colors.fg, opacity: blink}} />
    </div>
    </div>
  );
};

const Shrink: React.FC<{frame: number}> = ({frame}) => {
  const inn = ramp(frame, F.and, 18);
  const s = interpolate(frame, [F.argument - 4, F.lot + 8], [1, 0.22], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const swap = ramp(frame, F.lot - 6, 14);
  const W = 520;
  const H = 320;
  const TOP = 480;
  return (
    <div style={{opacity: inn}}>
      <div
        style={{
          position: 'absolute',
          left: 760,
          top: TOP,
          width: W,
          height: H,
          transform: `scale(${s})`,
          transformOrigin: 'bottom left',
          overflow: 'hidden',
          borderRadius: 6,
          border: `1px solid ${colors.line}`,
          background: 'rgba(26,23,20,0.7)',
        }}
      >
        <div style={{position: 'absolute', left: 12, top: 12}}>
          <CodeWall width={W - 24} height={H - 24} cols={6} gap={14} rowH={8} rows={60} scroll={frame * 1.2} seed="s12" dim="#4a443c" bright="#6d665c" />
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          left: 760 + W * s + 30,
          top: TOP + H,
          fontFamily: fonts.mono,
          fontSize: 28,
          lineHeight: 1.25,
          whiteSpace: 'nowrap',
        }}
      >
        <div style={{position: 'absolute', left: 0, bottom: 0, opacity: 1 - swap, color: colors.fg}}>
          {fmt(lean.lines)} lines
          <div style={{fontSize: 20, color: colors.muted}}>the Lean code, as released</div>
        </div>
        <div style={{position: 'absolute', left: 0, bottom: 0, opacity: swap, color: colors.fg}}>
          a much shorter argument?
          <div style={{fontSize: 20, color: colors.muted}}>what Alpöge expects · schematic</div>
        </div>
      </div>
    </div>
  );
};

// ---------- takeaway illustrations ----------
const ILL_W = 200;
const ILL_H = 96;
const Stair: React.FC<{t: number}> = ({t}) => {
  const xs = primes.stair100.x;
  const ys = primes.stair100.pi;
  const maxY = ys[ys.length - 1];
  const pts: [number, number][] = xs.map((x, i) => [(x / 100) * ILL_W, ILL_H - (ys[i] / maxY) * (ILL_H - 6)]);
  return (
    <svg width={ILL_W} height={ILL_H} style={{overflow: 'visible'}}>
      <line x1={0} y1={ILL_H} x2={ILL_W} y2={ILL_H} stroke={colors.line} strokeWidth={1} />
      <path d={stepPathFrom(pts, t)} fill="none" stroke={colors.accent} strokeWidth={2} style={{filter: 'drop-shadow(0 0 5px rgba(255,110,40,0.6))'}} />
    </svg>
  );
};
const Tangent: React.FC<{t: number}> = ({t}) => {
  const f = (x: number) => ILL_H - 10 - 70 * Math.pow(x / ILL_W, 1.6);
  const curve: [number, number][] = Array.from({length: 41}, (_, i) => {
    const x = (i / 40) * ILL_W;
    return [x, f(x)];
  });
  const dots = Array.from({length: 7}, (_, i) => 14 + i * 29);
  const k = dots[4];
  const slope = (f(k + 1) - f(k - 1)) / 2;
  const L = 52 * t;
  return (
    <svg width={ILL_W} height={ILL_H} style={{overflow: 'visible'}}>
      <path d={pathFrom(curve)} fill="none" stroke={colors.faint} strokeWidth={1.4} strokeDasharray="3 6" opacity={0.7} />
      {dots.map((x, i) => (
        <circle key={i} cx={x} cy={f(x)} r={i === 4 ? 5.5 : 4} fill={i === 4 ? colors.fg : '#b3a998'} opacity={ramp(t * 30, i * 2, 6)} />
      ))}
      <line
        x1={k - L}
        y1={f(k) - slope * L}
        x2={k + L}
        y2={f(k) + slope * L}
        stroke={colors.accent}
        strokeWidth={2}
        style={{filter: 'drop-shadow(0 0 5px rgba(255,110,40,0.6))'}}
      />
    </svg>
  );
};
const CheckedPage: React.FC<{t: number; frame: number}> = ({t, frame}) => {
  const blink = Math.floor(frame / 16) % 2 === 0 ? 1 : 0.1;
  return (
    <svg width={ILL_W} height={ILL_H} style={{overflow: 'visible'}}>
      <circle cx={46} cy={50} r={30} fill="rgba(159,211,138,0.08)" stroke={colors.good} strokeWidth={1.8} opacity={t} />
      <path
        d="M32,51 L42,61 L61,40"
        fill="none"
        stroke={colors.good}
        strokeWidth={3}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={44}
        strokeDashoffset={44 * (1 - t)}
        style={{filter: 'drop-shadow(0 0 5px rgba(159,211,138,0.55))'}}
      />
      <rect x={120} y={8} width={64} height={84} rx={4} fill="#1d1a16" stroke={colors.line} strokeWidth={1.4} opacity={t} />
      <rect x={132} y={22} width={2.4} height={14} fill={colors.fg} opacity={t * blink} />
    </svg>
  );
};

const TAKEAWAYS: React.ReactNode[] = [
  'RH is about how regular the primes are.',
  <>
    The note's key idea: a <span style={{whiteSpace: 'nowrap'}}>stand-in</span> for derivatives of whole numbers.
  </>,
  'If it holds up: maybe one of the first major proofs checked by machine before anyone could fully explain it.',
];

const Card: React.FC<{i: number; frame: number; start: number; dim: number}> = ({i, frame, start, dim}) => {
  const {fps} = useVideoConfig();
  const sp = springIn(frame, fps, start, 20);
  const t = ramp(frame, start + 6, 40, Easing.inOut(Easing.cubic));
  const W = 534;
  return (
    <div
      style={{
        position: 'absolute',
        left: 120 + i * (W + 39),
        top: 316,
        width: W,
        height: 420,
        boxSizing: 'border-box',
        padding: '34px 38px',
        background: colors.bgRaised,
        border: `1px solid ${dim > 0.9 ? 'rgba(255,106,26,0.32)' : colors.line}`,
        borderRadius: 16,
        opacity: Math.min(1, sp * 1.3) * (0.5 + 0.5 * dim),
        transform: `translateY(${(1 - sp) * 40}px)`,
      }}
    >
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', height: 120}}>
        <span style={{fontFamily: fonts.display, fontStyle: 'italic', fontSize: 92, lineHeight: 0.9, color: colors.accent}}>{i + 1}</span>
        <div style={{marginTop: 10}}>
          {i === 0 && <Stair t={t} />}
          {i === 1 && <Tangent t={t} />}
          {i === 2 && <CheckedPage t={t} frame={frame} />}
        </div>
      </div>
      <div style={{marginTop: 46, fontFamily: fonts.body, fontWeight: 400, fontSize: i === 2 ? 31 : 34, lineHeight: 1.32, color: colors.fg}}>
        {TAKEAWAYS[i]}
      </div>
    </div>
  );
};

// ---------- end card ----------
const EndCard: React.FC<{frame: number}> = ({frame}) => {
  const s = F.endCard;
  const rule = interpolate(frame, [s + 10, s + 40], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const gam = zeros.gammas.slice(0, 14);
  const g0 = gam[0];
  const g1 = gam[gam.length - 1];
  const rx0 = 700;
  const rx1 = 1220;
  const ry = 512;
  return (
    <>
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 330,
          textAlign: 'center',
          fontFamily: fonts.display,
          fontStyle: 'italic',
          fontSize: 136,
          lineHeight: 1,
          letterSpacing: '-0.02em',
          color: colors.fg,
          ...enter(frame, s, 26, 22),
        }}
      >
        The Riemann Hypothesis
      </div>
      <svg style={{position: 'absolute', left: 0, top: 0}} width={1920} height={1080}>
        <line
          x1={960 - ((rx1 - rx0) / 2) * rule}
          x2={960 + ((rx1 - rx0) / 2) * rule}
          y1={ry}
          y2={ry}
          stroke={colors.accent}
          strokeWidth={1.4}
          opacity={0.8}
        />
        {gam.map((g, i) => {
          const x = rx0 + ((g - g0) / (g1 - g0)) * (rx1 - rx0);
          const on = ramp(frame, s + 22 + i * 2, 8);
          return <circle key={i} cx={x} cy={ry} r={3.6 * on} fill={colors.accent} style={{filter: 'drop-shadow(0 0 6px rgba(255,110,40,0.9))'}} />;
        })}
      </svg>
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 548,
          textAlign: 'center',
          fontFamily: fonts.mono,
          fontSize: 25,
          color: colors.muted,
          ...enter(frame, s + 16, 18, 10),
        }}
      >
        {status.asof_onscreen}
      </div>
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 800,
          textAlign: 'center',
          fontFamily: fonts.body,
          fontWeight: 300,
          fontSize: 22,
          color: colors.muted,
          opacity: 0.85 * ramp(frame, s, 16),
        }}
      >
        {CREDITS}
      </div>
    </>
  );
};

export const S12Next: React.FC = () => {
  const frame = useCurrentFrame();
  const b0 = 1 - ramp(frame, F.L1 + 4, 20);
  const cardsOut = 1 - ramp(frame, F.endCard - 12, 16);
  const kicker = enter(frame, 4, 16, 8);
  const kickerOut = 1 - ramp(frame, F.endCard - 12, 14);
  const cardStarts = [F.L2, F.L3, F.L4];
  const active = cardStarts.filter((c) => frame >= c - 4).length - 1;
  return (
    <SceneFrame index={12} kicker="What's still missing" hideKicker>
      <div
        style={{
          position: 'absolute',
          left: grid.marginX,
          top: grid.kickerY - 10,
          fontFamily: fonts.mono,
          fontSize: 22,
          letterSpacing: '0.18em',
          textTransform: 'uppercase',
          color: colors.accent,
          ...kicker,
          opacity: (kicker.opacity as number) * kickerOut,
        }}
      >
        12 · What's still missing
      </div>

      {b0 > 0 && (
        <AbsoluteFill style={{opacity: b0}}>
          <BlankPage frame={frame} />
          <div
            style={{
              position: 'absolute',
              left: 760,
              top: 250,
              width: 980,
              fontFamily: fonts.display,
              fontStyle: 'italic',
              fontSize: 76,
              lineHeight: 1.04,
              letterSpacing: '-0.015em',
              color: colors.fg,
              ...enter(frame, F.no, 20, 18),
            }}
          >
            No human-readable proof released
          </div>
          <Shrink frame={frame} />
        </AbsoluteFill>
      )}

      {frame >= F.L1 - 2 && cardsOut > 0 && (
        <AbsoluteFill style={{opacity: cardsOut}}>
          <div
            style={{
              position: 'absolute',
              left: grid.marginX,
              top: 160,
              fontFamily: fonts.display,
              fontStyle: 'italic',
              fontSize: 88,
              lineHeight: 1,
              letterSpacing: '-0.02em',
              color: colors.fg,
              ...enter(frame, F.L1 + 4, 22, 20),
            }}
          >
            Three takeaways
          </div>
          {cardStarts.map((st, i) => (frame >= st - 6 ? <Card key={i} i={i} frame={frame} start={st - 4} dim={i === active ? 1 : 0.3} /> : null))}
        </AbsoluteFill>
      )}

      {frame >= F.endCard - 2 && <EndCard frame={frame} />}
    </SceneFrame>
  );
};
