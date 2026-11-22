import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {SceneFrame} from '../components/SceneFrame';
import {colors, fonts} from '../theme';
import {clamp, enter, ramp, springIn} from '../lib/anim';
import {lineStartFrame, sceneById} from '../lib/timeline';
import lean from '../data/lean.json';
import {CodeWall} from './s10/CodeWall';
import {CodeLine} from './s10/LeanCode';
import {fmt, wordIn} from './s10/sync';

const S = sceneById('s10_box');

// Narration beats (all keyed to words; see src/data/timeline.json)
const F = {
  seventeen: wordIn(S, 0, 'seventeen', 0, 0.18),
  lines: wordIn(S, 0, 'lines', 0, 0.3),
  k175: wordIn(S, 0, '175000', 0, 0.5),
  files: wordIn(S, 0, 'files', 0, 0.7),
  without: wordIn(S, 0, 'without', 0, 0.83),
  L1: lineStartFrame(S, 1),
  five: wordIn(S, 1, 'five', 0, 0.16),
  one: wordIn(S, 1, 'one', 0, 0.35),
  riemann: wordIn(S, 1, 'riemann', 0, 0.5),
  shared: wordIn(S, 1, 'shared', 0, 0.78),
  library: wordIn(S, 1, 'library', 0, 0.86),
  L2: lineStartFrame(S, 2),
  generalized: wordIn(S, 2, 'generalized', 0, 0.25),
  original: wordIn(S, 2, 'original', 0, 0.7),
  falls: wordIn(S, 2, 'falls', 0, 0.78),
  corollary: wordIn(S, 2, 'corollary', 0, 0.9),
  L3: lineStartFrame(S, 3),
  search: wordIn(S, 3, 'search', 0, 0.12),
  finds: wordIn(S, 3, 'finds', 0, 0.26),
  no: wordIn(S, 3, 'no', 0, 0.33),
  shortcuts: wordIn(S, 3, 'shortcuts', 0, 0.4),
  unfinished: wordIn(S, 3, 'unfinished', 0, 0.63),
  added: wordIn(S, 3, 'added', 0, 0.85),
};

const easeIO = Easing.inOut(Easing.cubic);

// ---------- Beat 0: counters over the wall ----------
const Counter: React.FC<{value: number; start: number; end: number; unit: string; top: number; frame: number}> = ({
  value,
  start,
  end,
  unit,
  top,
  frame,
}) => {
  const t = interpolate(frame, [start, end], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  return (
    <div style={{position: 'absolute', left: 120, top, display: 'flex', alignItems: 'baseline', gap: 28, ...enter(frame, start - 8, 14, 16)}}>
      <span
        style={{
          fontFamily: fonts.mono,
          fontSize: 150,
          lineHeight: 1,
          color: colors.fg,
          letterSpacing: '-0.03em',
          textShadow: t >= 1 ? '0 0 30px rgba(255,110,40,0.18)' : 'none',
        }}
      >
        {fmt(value * t)}
      </span>
      <span style={{fontFamily: fonts.body, fontWeight: 300, fontSize: 48, color: colors.muted}}>{unit}</span>
    </div>
  );
};

// ---------- Beat 1/2: editor card ----------
const CODE_SIZE = 22;
const LINE_H = 34;
const CARD_W = 1300;
const theoremIdx = lean.main_lean.map((l, i) => (l.startsWith('theorem') ? i : -1)).filter((i) => i >= 0);
const rhIdx = lean.main_lean.findIndex((l) => /^theorem riemannHypothesis\b/.test(l));
const rhTerm = (lean.main_lean[rhIdx] ?? '').split(':=').pop()?.trim() ?? '';

const Editor: React.FC<{frame: number}> = ({frame}) => {
  const focus = ramp(frame, F.one, 16); // dim others, light RH line
  const gen = ramp(frame, F.generalized - 4, 16); // L-function lines take focus
  const back = ramp(frame, F.original - 4, 14); // RH line returns
  const typeMark = ramp(frame, F.riemann, 18);
  const termMark = ramp(frame, F.falls, 16);
  return (
    <div
      style={{
        width: CARD_W,
        background: colors.bgRaised,
        border: `1px solid ${colors.line}`,
        borderRadius: 16,
        boxShadow: '0 30px 80px rgba(0,0,0,0.55)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          height: 54,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 28px',
          borderBottom: `1px solid ${colors.line}`,
          fontFamily: fonts.mono,
          fontSize: 19,
        }}
      >
        <span style={{color: colors.fg}}>
          Main.lean <span style={{color: colors.faint}}>· top of the released code</span>
        </span>
        <span style={{color: colors.faint}}>{lean.toolchain}</span>
      </div>
      <div style={{padding: '22px 30px 22px 0'}}>
        {lean.main_lean.map((line, i) => {
          const isThm = theoremIdx.includes(i);
          const k = theoremIdx.indexOf(i);
          const reveal = isThm ? ramp(frame, F.five + k * 5, 12) : ramp(frame, F.L1 + 6, 14);
          const isRH = i === rhIdx;
          let op = 1;
          if (line) {
            // focus on the RH line; during "generalized version comes first" the editor recedes
            // (attention moves to the dependency diagram, so no file-order implication)
            const dimmed = isRH ? 1 : 0.32;
            op = interpolate(focus, [0, 1], [1, dimmed]);
            if (isRH) op = interpolate(gen, [0, 1], [1, 0.45]) + 0.55 * back;
            else op *= 1 - 0.3 * gen;
          }
          const strip = isRH ? focus * (1 - 0.7 * gen + 0.7 * back) : 0;
          return (
            <div key={i} style={{height: LINE_H, display: 'flex', alignItems: 'center', position: 'relative'}}>
              {strip > 0 && (
                <div
                  style={{
                    position: 'absolute',
                    left: 0,
                    right: -30,
                    top: 0,
                    bottom: 0,
                    background: `rgba(255,106,26,${0.09 * strip})`,
                    borderLeft: `3px solid rgba(255,106,26,${strip})`,
                  }}
                />
              )}
              <span
                style={{
                  width: 64,
                  paddingRight: 22,
                  textAlign: 'right',
                  fontFamily: fonts.mono,
                  fontSize: 17,
                  color: colors.faint,
                  opacity: 0.8,
                  flexShrink: 0,
                }}
              >
                {i + 1}
              </span>
              <span style={{opacity: op * Math.min(1, reveal * 1.4), clipPath: reveal >= 1 ? 'none' : `inset(-8px ${(1 - reveal) * 100}% -8px 0)`, position: 'relative'}}>
                <CodeLine
                  line={line}
                  size={CODE_SIZE}
                  marks={isRH ? {RiemannHypothesis: typeMark, [rhTerm]: termMark} : {}}
                />
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const MathlibCard: React.FC<{frame: number}> = ({frame}) => {
  const mark = ramp(frame, F.library, 18);
  return (
    <div
      style={{
        background: '#15120f',
        border: `1px solid ${colors.line}`,
        borderRadius: 14,
        boxShadow: '0 24px 60px rgba(0,0,0,0.6)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          height: 46,
          display: 'flex',
          alignItems: 'center',
          padding: '0 26px',
          borderBottom: `1px solid ${colors.line}`,
          fontFamily: fonts.mono,
          fontSize: 19,
        }}
      >
        <span style={{color: colors.accent, whiteSpace: 'pre'}}>Mathlib</span>
        <span style={{color: colors.muted, whiteSpace: 'pre'}}>, Lean's shared math library</span>
      </div>
      <div style={{padding: '18px 30px 20px 30px'}}>
        {lean.mathlib_rh.map((line, i) => (
          <div key={i} style={{height: 32, display: 'flex', alignItems: 'center'}}>
            <CodeLine line={line} size={20} marks={{RiemannHypothesis: mark}} />
          </div>
        ))}
      </div>
    </div>
  );
};

// ---------- Beat 2: dependency diagram ----------
const Node: React.FC<{title: string; sub: string; style: React.CSSProperties; hot?: boolean}> = ({title, sub, style, hot}) => (
  <div
    style={{
      position: 'absolute',
      height: 150,
      border: `1px solid ${hot ? 'rgba(255,106,26,0.55)' : colors.line}`,
      background: hot ? 'rgba(255,106,26,0.06)' : colors.bgRaised,
      borderRadius: 14,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      padding: '0 30px',
      ...style,
    }}
  >
    <div style={{fontFamily: fonts.display, fontStyle: 'italic', fontSize: 66, lineHeight: 1, color: colors.fg}}>{title}</div>
    <div style={{fontFamily: fonts.mono, fontSize: 21, color: colors.muted, marginTop: 10}}>{sub}</div>
  </div>
);

const Diagram: React.FC<{frame: number}> = ({frame}) => {
  const a = ramp(frame, F.generalized - 6, 18);
  const arrow = interpolate(frame, [F.original - 6, F.falls + 8], [0, 1], {...clamp, easing: easeIO});
  const b = ramp(frame, F.falls, 16);
  const lab = ramp(frame, F.corollary - 6, 14);
  const tag = ramp(frame, F.generalized + 4, 14);
  const top = 640;
  const ax0 = 1196;
  const ax1 = 1366;
  return (
    <>
      <div style={{opacity: a, transform: `translateY(${(1 - a) * 14}px)`}}>
        <Node title="GRH" sub="all Dirichlet L-functions" style={{left: 760, top, width: 420}} hot />
      </div>
      <svg style={{position: 'absolute', left: 0, top: 0}} width={1920} height={1080}>
        <line
          x1={ax0}
          y1={top + 75}
          x2={ax0 + (ax1 - ax0) * arrow}
          y2={top + 75}
          stroke={colors.accent}
          strokeWidth={2.5}
          style={{filter: 'drop-shadow(0 0 6px rgba(255,110,40,0.7))'}}
        />
        {arrow > 0.95 && (
          <path d={`M${ax1 - 14},${top + 66} L${ax1},${top + 75} L${ax1 - 14},${top + 84}`} fill="none" stroke={colors.accent} strokeWidth={2.5} />
        )}
      </svg>
      <div
        style={{
          position: 'absolute',
          left: ax0,
          width: ax1 - ax0,
          top: top + 36,
          textAlign: 'center',
          fontFamily: fonts.mono,
          fontSize: 19,
          color: colors.accent,
          opacity: lab,
        }}
      >
        corollary
      </div>
      <div style={{opacity: b, transform: `translateX(${(1 - b) * -14}px)`}}>
        <Node title="RH" sub="the original, for zeta" style={{left: 1380, top, width: 420}} />
      </div>
      <div
        style={{
          position: 'absolute',
          right: 120,
          top: top + 166,
          fontFamily: fonts.mono,
          fontSize: 18,
          color: colors.muted,
          border: `1px solid ${colors.line}`,
          borderRadius: 999,
          padding: '5px 14px',
          opacity: tag,
        }}
      >
        dependency, simplified
      </div>
    </>
  );
};

// ---------- Beat 3: text search ----------
const Spinner: React.FC<{frame: number; size: number}> = ({frame, size}) => (
  <svg width={size} height={size} viewBox="0 0 20 20" style={{transform: `rotate(${frame * 9}deg)`}}>
    <circle cx={10} cy={10} r={7} fill="none" stroke={colors.line} strokeWidth={2.2} />
    <path d="M10,3 A7,7 0 0 1 17,10" fill="none" stroke={colors.muted} strokeWidth={2.2} strokeLinecap="round" />
  </svg>
);

const slots = [
  {kw: 'sorry', count: lean.sorry, gloss: 'unfinished step', glossAt: () => F.unfinished},
  {kw: 'axiom', count: lean.axiom_decls, gloss: 'added axiom', glossAt: () => F.added},
  {kw: 'native_decide', count: lean.native_decide, gloss: 'trusts compiled code', glossAt: () => F.shortcuts + 4},
];

const Search: React.FC<{frame: number}> = ({frame}) => {
  const SIZE = 54;
  const scanT = interpolate(frame, [F.search, F.finds + 12], [0, 1], {...clamp, easing: Easing.inOut(Easing.quad)});
  const head = enter(frame, F.L3 + 6, 18, 12);
  const note = enter(frame, F.no + 26, 18, 10);
  return (
    <>
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 268,
          textAlign: 'center',
          fontFamily: fonts.mono,
          fontSize: 23,
          color: colors.muted,
          ...head,
        }}
      >
        <span style={{color: colors.fg}}>{fmt(lean.files * scanT)}</span> / {fmt(lean.files)} files scanned
      </div>
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 360,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'flex-start',
          fontFamily: fonts.mono,
          fontSize: SIZE,
          lineHeight: 1,
          color: colors.fg,
          whiteSpace: 'pre',
          ...head,
        }}
      >
        <span style={{color: colors.muted}}>Text search: </span>
        {slots.map((s, i) => {
          const at = F.no + i * 6;
          const got = ramp(frame, at, 10);
          const g = enter(frame, s.glossAt(), 16, 8);
          return (
            <React.Fragment key={s.kw}>
              {i > 0 && <span style={{color: colors.faint}}> · </span>}
              <span style={{position: 'relative', display: 'inline-flex', alignItems: 'center'}}>
                <span style={{display: 'inline-block', width: SIZE * 0.6, height: SIZE, position: 'relative'}}>
                  {got < 1 && (
                    <span style={{position: 'absolute', left: 0, top: 0, width: SIZE * 0.6, height: SIZE, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 1 - got}}>
                      <Spinner frame={frame} size={30} />
                    </span>
                  )}
                  <span
                    style={{
                      position: 'absolute',
                      left: 0,
                      top: 0,
                      opacity: got,
                      color: colors.good,
                      textShadow: '0 0 18px rgba(159,211,138,0.35)',
                      transform: `scale(${1.25 - 0.25 * got})`,
                    }}
                  >
                    {s.count}
                  </span>
                </span>
                <span style={{color: colors.fg}}> {s.kw}</span>
                <span
                  style={{
                    position: 'absolute',
                    left: SIZE * 0.6 + SIZE * 0.6,
                    top: SIZE + 22,
                    fontFamily: fonts.body,
                    fontWeight: 300,
                    fontSize: 25,
                    color: colors.muted,
                    whiteSpace: 'nowrap',
                    ...g,
                  }}
                >
                  {s.gloss}
                </span>
              </span>
            </React.Fragment>
          );
        })}
      </div>
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 590,
          textAlign: 'center',
          fontFamily: fonts.body,
          fontWeight: 300,
          fontSize: 29,
          color: colors.muted,
          ...note,
        }}
      >
        (our scan; not a substitute for the kernel checks)
      </div>
    </>
  );
};

export const S10Box: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Wall: zooms out while counting, collapses into the editor, returns for the search.
  const wallIn = ramp(frame, 0, 30);
  const collapse = ramp(frame, F.L1, 24, easeIO);
  const wallBack = ramp(frame, F.L3 + 4, 30);
  const zoom = interpolate(frame, [F.seventeen - 10, F.files + 14], [1.9, 1], {...clamp, easing: easeIO});
  const wallScale = frame < F.L3 ? zoom * (1 - 0.82 * collapse) : interpolate(wallBack, [0, 1], [1.25, 1]);
  const wallOpacity = frame < F.L3 ? 0.62 * wallIn * (1 - collapse) : 0.42 * wallBack;
  const scanY = interpolate(frame, [F.search, F.finds + 12], [120, 960], {...clamp, easing: Easing.inOut(Easing.quad)});
  const scanOn = ramp(frame, F.search - 6, 10) * (1 - ramp(frame, F.finds + 8, 10));

  // Beat 0 out
  const b0 = 1 - ramp(frame, F.L1 - 6, 14);

  // Editor placement: centered -> upper-left at "shared math library" -> out at line 3
  const cardIn = springIn(frame, fps, F.L1 + 4, 20);
  const move = interpolate(frame, [F.shared - 10, F.shared + 14], [0, 1], {...clamp, easing: easeIO});
  const cardOut = ramp(frame, F.L3 - 2, 18);
  const cx = interpolate(move, [0, 1], [(1920 - CARD_W) / 2, 120]);
  const cy = interpolate(move, [0, 1], [196, 170]);
  const cs = interpolate(move, [0, 1], [1, 0.84]) * (0.6 + 0.4 * cardIn) * (1 - 0.04 * cardOut);
  const cardOpacity = Math.min(1, ramp(frame, F.L1 + 2, 12)) * (1 - cardOut);

  const mlIn = ramp(frame, F.shared - 2, 18);
  const mlOut = ramp(frame, F.generalized, 14);

  const diagOut = 1 - ramp(frame, F.L3 - 2, 18);

  return (
    <SceneFrame index={10} kicker="What's in the box">
      {/* the wall */}
      <AbsoluteFill
        style={{
          opacity: wallOpacity,
          transform: `scale(${wallScale})`,
          transformOrigin: frame < F.L3 ? '50% 46%' : '50% 50%',
          WebkitMaskImage: 'linear-gradient(to bottom, transparent 4%, black 22%, black 78%, transparent 96%)',
        }}
      >
        <div style={{position: 'absolute', left: -40, top: -40}}>
          <CodeWall width={2000} height={1160} cols={18} gap={20} rowH={9} rows={150} scroll={frame * 1.5} seed="s10" />
        </div>
      </AbsoluteFill>
      {/* scan band (beat 3) */}
      {scanOn > 0 && (
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: scanY - 90,
            height: 180,
            opacity: scanOn,
            background: 'linear-gradient(to bottom, rgba(255,106,26,0) 0%, rgba(255,106,26,0.07) 70%, rgba(255,140,70,0.35) 99%, rgba(255,106,26,0) 100%)',
          }}
        />
      )}

      {/* Beat 0: counters */}
      {b0 > 0 && (
        <AbsoluteFill style={{opacity: b0}}>
          <AbsoluteFill
            style={{background: 'radial-gradient(900px 620px at 28% 50%, rgba(17,15,13,0.94) 0%, rgba(17,15,13,0.75) 45%, rgba(17,15,13,0) 100%)'}}
          />
          <Counter value={lean.lines} start={F.seventeen} end={F.lines + 14} unit="lines" top={248} frame={frame} />
          <Counter value={lean.files} start={F.k175} end={F.files + 8} unit="files" top={436} frame={frame} />
          <div style={{position: 'absolute', left: 126, top: 630, fontFamily: fonts.mono, fontSize: 24, color: colors.muted, ...enter(frame, F.files + 6, 14, 8)}}>
            (our count)
          </div>
          <div
            style={{
              position: 'absolute',
              left: 120,
              top: 690,
              fontFamily: fonts.mono,
              fontSize: 30,
              color: colors.muted,
              border: `1px solid ${colors.line}`,
              background: 'rgba(26,23,20,0.85)',
              borderRadius: 10,
              padding: '10px 18px',
              ...enter(frame, F.without + 4, 14, 10),
            }}
          >
            comments: <span style={{color: colors.accent}}>{lean.comments}</span>
          </div>
        </AbsoluteFill>
      )}

      {/* Beat 1/2: editor + Mathlib + diagram */}
      {cardOpacity > 0 && (
        <div
          style={{
            position: 'absolute',
            left: cx,
            top: cy,
            transform: `scale(${cs})`,
            transformOrigin: 'top left',
            opacity: cardOpacity,
          }}
        >
          <Editor frame={frame} />
        </div>
      )}
      {mlIn > 0 && mlOut < 1 && (
        <div
          style={{
            position: 'absolute',
            right: 120,
            top: 628,
            opacity: mlIn * (1 - mlOut),
            transform: `translateY(${(1 - mlIn) * 30 + mlOut * 20}px)`,
          }}
        >
          <MathlibCard frame={frame} />
        </div>
      )}
      {frame >= F.generalized - 8 && diagOut > 0 && (
        <AbsoluteFill style={{opacity: diagOut}}>
          <Diagram frame={frame} />
        </AbsoluteFill>
      )}

      {/* Beat 3: search */}
      {frame >= F.L3 && (
        <AbsoluteFill>
          <AbsoluteFill
            style={{background: 'radial-gradient(1100px 420px at 50% 44%, rgba(17,15,13,0.95) 0%, rgba(17,15,13,0.82) 50%, rgba(17,15,13,0) 100%)', opacity: ramp(frame, F.L3, 20)}}
          />
          <Search frame={frame} />
        </AbsoluteFill>
      )}
    </SceneFrame>
  );
};
