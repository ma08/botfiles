import React from 'react';
import {Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {SceneFrame} from '../components/SceneFrame';
import {colors, fonts, glow} from '../theme';
import {clamp, enter, ramp} from '../lib/anim';
import {sceneById, wordFrame} from '../lib/timeline';
import zerosData from '../data/zeros.json';
import {QuestionThumb} from './s03/QuestionThumb';

const s = sceneById('s03_zeros');

const B = {
  year: wordFrame(s, '1859'),
  bernhard: wordFrame(s, 'Bernhard'),
  question: wordFrame(s, 'question'),
  zeta: wordFrame(s, 'zeta'),
  built: wordFrame(s, 'built'),
  whole: wordFrame(s, 'whole'),
  encodes: wordFrame(s, 'encodes'),
  primes: wordFrame(s, 'primes'),
  has: wordFrame(s, 'has'),
  infinitely: wordFrame(s, 'infinitely'),
  zeros: wordFrame(s, 'zeros'),
  narrow: wordFrame(s, 'narrow'),
  strip: wordFrame(s, 'strip'),
  plane: wordFrame(s, 'plane'),
  riemann2: wordFrame(s, 'Riemann', 1),
  guessed: wordFrame(s, 'guessed'),
  center: wordFrame(s, 'center'),
  computers: wordFrame(s, 'Computers'),
  checked: wordFrame(s, 'checked'),
  allOn: wordFrame(s, 'All', 1),
  but: wordFrame(s, 'But'),
  isnt: wordFrame(s, "isn't"),
  every: wordFrame(s, 'every'),
};

// ---- plane geometry (right side) ----
const X0 = 1290; // Re s = 0
const X1 = 1650; // Re s = 1
const XH = (X0 + X1) / 2; // Re s = 1/2
const reX = (re: number) => X0 + (X1 - X0) * re;
const YT = 150; // top of plot
const YB = 852; // real axis
const PXU = 8.8; // px per unit of Im s
const GAMMAS = zerosData.gammas as number[];
const N_FIRST = GAMMAS.filter((g) => g < (YB - YT) / PXU - 1).length; // zeros visible before scrolling
const SCROLL_TO = 165;
const BREAK_Y = YT + 150;

const Sup: React.FC<{children: React.ReactNode}> = ({children}) => (
  <span style={{fontSize: '0.58em', verticalAlign: '0.7em', lineHeight: 0, marginLeft: 1}}>{children}</span>
);

const fmt2 = (g: number) => g.toFixed(2);

export const S03Zeros: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // ---- camera: scroll up the critical line ----
  const T0 = interpolate(frame, [B.computers, B.computers + 96], [0, SCROLL_TO], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const zy = (g: number) => YB - (g - T0) * PXU;

  // ---- reveals ----
  const planeIn = ramp(frame, B.has - 6, 24);
  const stripIn = ramp(frame, B.narrow, 20);
  const lineDraw = ramp(frame, B.center - 8, 26, Easing.inOut(Easing.cubic));
  const breakIn = ramp(frame, B.but, 22);
  const ghostIn = ramp(frame, B.isnt - 4, 18);
  const pulseCenter = B.allOn + 2;

  // "that question" (end of scene 2) gets tied to zeta
  const thumbIn = ramp(frame, B.question - 10, 20);
  const absorb = ramp(frame, B.zeta - 18, 26, Easing.inOut(Easing.cubic));

  // left column
  const headOut = 1 - ramp(frame, B.has - 12, 18);
  const formulaMove = ramp(frame, B.has - 14, 30, Easing.inOut(Easing.cubic));
  const eulerOut = 1 - ramp(frame, B.has - 16, 14);

  // ---- grid of the complex plane (faint) ----
  const gridLines: React.ReactNode[] = [];
  for (let re = -0.5; re <= 1.5001; re += 0.25) {
    if (Math.abs(re) < 1e-6 || Math.abs(re - 1) < 1e-6) continue;
    gridLines.push(<line key={`v${re}`} x1={reX(re)} y1={YT} x2={reX(re)} y2={YB} stroke={colors.line} strokeWidth={1} />);
  }
  const firstTick = Math.ceil(T0 / 20) * 20;
  for (let im = firstTick; im < T0 + (YB - YT) / PXU; im += 20) {
    if (im === 0) continue;
    const y = zy(im);
    gridLines.push(<line key={`h${im}`} x1={reX(-0.55)} y1={y} x2={reX(1.55)} y2={y} stroke={colors.line} strokeWidth={1} />);
  }
  const imTicks: React.ReactNode[] = [];
  for (let im = firstTick; im < T0 + (YB - YT) / PXU - 4; im += 20) {
    if (im === 0) continue;
    const y = zy(im);
    const topFade = interpolate(y, [YT, YT + 40], [0, 1], clamp) * (1 - breakIn * interpolate(y, [BREAK_Y, BREAK_Y + 30], [1, 0], clamp));
    imTicks.push(
      <text key={`t${im}`} x={X0 - 14} y={y + 6} fill={colors.faint} fontFamily={fonts.mono} fontSize={17} textAnchor="end" opacity={topFade}>
        {im}
      </text>,
    );
  }

  // ---- zeros ----
  const zeroNodes: React.ReactNode[] = [];
  const labelNodes: React.ReactNode[] = [];
  GAMMAS.forEach((g, i) => {
    const y = zy(g);
    if (y < YT - 20 || y > YB + 20) return;
    let pop: number;
    if (i < N_FIRST) {
      const pf = B.zeros - 4 + i * 3.2;
      pop = frame < pf ? 0 : spring({frame: frame - pf, fps, config: {damping: 11, mass: 0.5}});
    } else {
      pop = interpolate(y, [YT + 4, YT + 46], [0, 1], {...clamp, easing: Easing.out(Easing.back(2.2))});
    }
    if (pop <= 0) return;
    // ripple pulse on "All on the line", bottom to top
    const delay = interpolate(y, [YT, YB], [22, 0], clamp);
    const pulse = Math.max(0, Math.sin(Math.PI * interpolate(frame, [pulseCenter + delay, pulseCenter + delay + 16], [0, 1], clamp)));
    const fadeTop = interpolate(y, [YT - 10, YT + 14], [0, 1], clamp);
    const breakFade = 1 - breakIn * interpolate(y, [BREAK_Y - 10, BREAK_Y + 40], [1, 0], clamp);
    zeroNodes.push(
      <circle key={g} cx={XH} cy={y} r={6.8 * pop * (1 + 0.55 * pulse)} fill={pulse > 0.05 ? '#ffb27a' : colors.accent} opacity={fadeTop * breakFade} />,
    );
    if (i < 6) {
      const lIn = frame < B.zeros - 4 + i * 3.2 + 6 ? 0 : ramp(frame, B.zeros - 4 + i * 3.2 + 6, 12);
      const lOut = 1 - ramp(frame, B.computers - 6, 14);
      labelNodes.push(
        <text key={`l${g}`} x={XH + 24} y={y + 6} fill={colors.muted} fontFamily={fonts.mono} fontSize={19} opacity={lIn * lOut}>
          <tspan fontFamily={fonts.displayUpright} fontSize={27}>
            ½
          </tspan>{' '}
          + {fmt2(g)}i
        </text>,
      );
    }
  });

  return (
    <SceneFrame index={3} kicker={s.title}>
      {/* ================= right: the critical strip ================= */}
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0}}>
        <defs>
          <clipPath id="s03-clip">
            <rect x={reX(-0.6)} y={YT - 14} width={reX(1.6) - reX(-0.6)} height={YB - YT + 14} />
          </clipPath>
          <linearGradient id="s03-topfade" x1={0} x2={0} y1={YT} y2={YT + 80} gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor={colors.bg} stopOpacity={1} />
            <stop offset="1" stopColor={colors.bg} stopOpacity={0} />
          </linearGradient>
        </defs>

        <g clipPath="url(#s03-clip)">
          {/* faint plane grid, dims when the strip is singled out */}
          <g opacity={planeIn * (0.55 - 0.35 * stripIn)}>{gridLines}</g>
          {/* strip */}
          <rect x={X0} y={YT - 14} width={X1 - X0} height={YB - YT + 14} fill={colors.strip} opacity={stripIn * 1.6} />
          <rect x={X0} y={YT - 14} width={X1 - X0} height={YB - YT + 14} fill="rgba(255,106,26,0.035)" opacity={stripIn} />
          {/* strip edges: Re s = 0 (the imaginary axis) and Re s = 1 */}
          <line x1={X0} y1={YT - 14} x2={X0} y2={YB} stroke={colors.faint} strokeWidth={1.5} opacity={planeIn} />
          <line x1={X1} y1={YT - 14} x2={X1} y2={YB} stroke={colors.faint} strokeWidth={1.5} opacity={planeIn * (0.4 + 0.6 * stripIn)} />

          {/* critical line Re s = 1/2 */}
          {lineDraw > 0 && (
            <>
              <line
                x1={XH}
                y1={YB}
                x2={XH}
                y2={YB - (YB - (frame >= B.but ? BREAK_Y : YT - 14)) * lineDraw}
                stroke={colors.accent}
                strokeWidth={3}
                style={{filter: glow(8)}}
              />
              {breakIn > 0 && (
                <line
                  x1={XH}
                  y1={BREAK_Y - 26}
                  x2={XH}
                  y2={YT - 14}
                  stroke={colors.accent}
                  strokeWidth={2.4}
                  strokeDasharray="7 9"
                  opacity={breakIn * 0.6}
                />
              )}
            </>
          )}

          {/* zeros */}
          <g style={{filter: glow(9)}}>{zeroNodes}</g>
          {labelNodes}

          {/* fade toward the top: more zeros keep coming */}
          <rect x={reX(-0.6)} y={YT - 14} width={reX(1.6) - reX(-0.6)} height={94} fill="url(#s03-topfade)" opacity={planeIn * 0.9} />
        </g>

        {/* axis break: far above anything checked */}
        {breakIn > 0 && (
          <g opacity={breakIn}>
            {[0, 12].map((dy) => (
              <path
                key={dy}
                d={`M${X0 - 26},${BREAK_Y - dy} C${X0 + 60},${BREAK_Y - dy - 14} ${X0 + 120},${BREAK_Y - dy + 14} ${XH},${BREAK_Y - dy} S${X1 - 60},${BREAK_Y - dy - 14} ${X1 + 26},${BREAK_Y - dy}`}
                fill="none"
                stroke={colors.muted}
                strokeWidth={1.4}
                opacity={0.7}
              />
            ))}
          </g>
        )}

        {/* ghost zero off the line */}
        {ghostIn > 0 && (
          <g opacity={ghostIn} transform={`translate(${reX(0.79)}, ${YT + 62}) scale(${0.7 + 0.3 * ghostIn})`}>
            <line x1={XH - reX(0.79) + 6} y1={0} x2={-24} y2={0} stroke={colors.muted} strokeWidth={1.4} strokeDasharray="2 6" />
            <circle r={17} fill="none" stroke={colors.fg} strokeWidth={2.2} strokeDasharray="6 5" opacity={0.9} />
            <circle r={17} fill="rgba(255,106,26,0.1)" />
          </g>
        )}

        {/* axes and labels */}
        <g opacity={planeIn}>
          <line x1={reX(-0.55)} y1={YB} x2={reX(1.55)} y2={YB} stroke={colors.line} strokeWidth={2} />
          <text x={X0} y={YB + 34} fill={colors.muted} fontFamily={fonts.mono} fontSize={22} textAnchor="middle">
            0
          </text>
          <text
            x={XH}
            y={YB + 34}
            fill={lineDraw > 0.5 ? colors.accent : colors.muted}
            fontFamily={fonts.displayUpright}
            fontSize={32}
            textAnchor="middle"
          >
            ½
          </text>
          <text x={X1} y={YB + 34} fill={colors.muted} fontFamily={fonts.mono} fontSize={22} textAnchor="middle">
            1
          </text>
          <text x={reX(1.55)} y={YB + 34} fill={colors.faint} fontFamily={fonts.mono} fontSize={20} textAnchor="end">
            Re(s)
          </text>
          <text x={X0 - 14} y={YT - 22} fill={colors.faint} fontFamily={fonts.mono} fontSize={18} textAnchor="end">
            Im(s)
          </text>
          {imTicks}
        </g>
      </svg>

      {/* strip label */}
      <div
        style={{
          position: 'absolute',
          left: X1 + 22,
          top: YB - 92,
          fontFamily: fonts.mono,
          fontSize: 19,
          lineHeight: 1.5,
          color: colors.muted,
          opacity: stripIn * (1 - ramp(frame, B.computers, 16) * 0.6),
        }}
      >
        critical strip
        <br />
        <span style={{color: colors.faint}}>0 &lt; Re(s) &lt; 1</span>
      </div>

      {/* line label */}
      <div
        style={{
          position: 'absolute',
          left: XH - 120,
          width: 240,
          textAlign: 'center',
          top: YT - 58,
          fontFamily: fonts.mono,
          fontSize: 21,
          color: colors.accent,
          opacity: ramp(frame, B.center + 8, 14) * (1 - breakIn),
        }}
      >
        Re(s) = <span style={{fontFamily: fonts.displayUpright, fontSize: 30, lineHeight: 0}}>½</span>
      </div>

      {/* ghost question mark */}
      {ghostIn > 0 && (
        <div
          style={{
            position: 'absolute',
            left: reX(0.79) + 28,
            top: YT + 62 - 62,
            fontFamily: fonts.display,
            fontStyle: 'italic',
            fontSize: 100,
            lineHeight: 1,
            color: colors.accent,
            opacity: ghostIn,
            filter: glow(10, 'rgba(255,110,40,0.5)'),
          }}
        >
          ?
        </div>
      )}

      {absorb < 1 && (
        <QuestionThumb
          left={interpolate(absorb, [0, 1], [1150, 140])}
          top={interpolate(absorb, [0, 1], [190, 360])}
          scale={interpolate(absorb, [0, 1], [1, 0.16])}
          opacity={thumbIn * (1 - absorb * absorb)}
        />
      )}

      {/* ================= left column ================= */}
      {/* 1859 header */}
      {headOut > 0 && (
        <div style={{position: 'absolute', left: 120, top: 150, opacity: headOut}}>
          <div
            style={{
              fontFamily: fonts.display,
              fontStyle: 'italic',
              fontSize: 168,
              lineHeight: 1,
              letterSpacing: '-0.02em',
              color: colors.fg,
              ...enter(frame, B.year - 4, 22, 20),
            }}
          >
            1859
          </div>
          <div style={{marginTop: 14, fontFamily: fonts.body, fontWeight: 300, fontSize: 36, color: colors.muted, ...enter(frame, B.bernhard - 2, 18, 12)}}>
            Bernhard Riemann
          </div>
        </div>
      )}

      {/* zeta formula: big while introduced, then parked bottom-left */}
      <div
        style={{
          position: 'absolute',
          left: 120,
          top: interpolate(formulaMove, [0, 1], [440, 700]),
          transform: `scale(${interpolate(formulaMove, [0, 1], [1, 0.82])})`,
          transformOrigin: '0 0',
          fontFamily: fonts.display,
          fontStyle: 'italic',
          fontSize: 92,
          lineHeight: 1.1,
          color: colors.fg,
          whiteSpace: 'nowrap',
        }}
      >
        <span style={{...enter(frame, B.zeta - 4, 18, 14), display: 'inline-block'}}>ζ(s)</span>
        <span style={{display: 'inline-block', margin: '0 22px', ...enter(frame, B.built, 16, 10)}}>=</span>
        {/* expanded sum: 1 + 1/2^s + 1/3^s + ... */}
        <span style={{display: 'inline-block', opacity: 1 - formulaMove}}>
          {['1', '1/2', '1/3', '1/4'].map((t, k) => (
            <span key={t} style={{display: 'inline-block', ...enter(frame, B.whole - 6 + k * 6, 14, 10)}}>
              {k > 0 && <span style={{margin: '0 16px', color: colors.muted}}>+</span>}
              {t}
              {k > 0 && <Sup>s</Sup>}
            </span>
          ))}
          <span style={{display: 'inline-block', marginLeft: 16, color: colors.muted, ...enter(frame, B.whole + 20, 14, 10)}}>+ …</span>
        </span>
        {/* compact form once parked */}
        <span style={{position: 'absolute', left: 0, top: 0, opacity: formulaMove, whiteSpace: 'nowrap'}}>
          <span style={{visibility: 'hidden'}}>ζ(s)</span>
          <span style={{margin: '0 22px'}}>=</span>Σ 1/n<Sup>s</Sup>
        </span>
      </div>

      {/* Euler product: the primes, exactly */}
      {eulerOut > 0 && (
        <div style={{position: 'absolute', left: 120, top: 580, opacity: eulerOut}}>
          <div style={{fontFamily: fonts.display, fontStyle: 'italic', fontSize: 64, color: colors.fg, whiteSpace: 'nowrap', ...enter(frame, B.encodes - 4, 18, 12)}}>
            <span style={{marginRight: 18, color: colors.muted}}>=</span>
            {[2, 3, 5, 7].map((p, k) => (
              <span key={p} style={{display: 'inline-block', marginRight: 14, ...enter(frame, B.primes - 6 + k * 5, 12, 8)}}>
                1/(1 − <span style={{color: colors.accent}}>{p}</span>
                <Sup>−s</Sup>)
              </span>
            ))}
            <span style={{color: colors.muted, ...enter(frame, B.primes + 16, 12, 8), display: 'inline-block'}}>…</span>
          </div>
          <div style={{marginTop: 10, fontFamily: fonts.mono, fontSize: 20, color: colors.muted, ...enter(frame, B.primes + 8, 14, 8)}}>
            one factor for every prime <span style={{color: colors.faint}}>· series and product valid for Re(s) &gt; 1</span>
          </div>
        </div>
      )}

      {/* Riemann's guess */}
      <div style={{position: 'absolute', left: 120, top: 168, fontFamily: fonts.mono, fontSize: 21, letterSpacing: '0.14em', color: colors.muted, ...enter(frame, B.riemann2, 16, 8)}}>
        RIEMANN'S GUESS · 1859
      </div>
      <div
        style={{
          position: 'absolute',
          left: 120,
          top: 210,
          width: 830,
          fontFamily: fonts.display,
          fontStyle: 'italic',
          fontSize: 92,
          lineHeight: 1.02,
          letterSpacing: '-0.02em',
          color: colors.fg,
          ...enter(frame, B.guessed - 4, 22, 20),
        }}
      >
        Every nontrivial zero sits on one line.
      </div>

      {/* numerical checks */}
      <div
        style={{
          position: 'absolute',
          left: 124,
          top: 470,
          width: 820,
          fontFamily: fonts.body,
          fontWeight: 300,
          fontSize: 36,
          lineHeight: 1.4,
          color: colors.muted,
          ...enter(frame, B.checked - 4, 18, 12),
        }}
      >
        Checked numerically: <span style={{color: colors.fg, fontWeight: 500}}>more than 10 trillion zeros</span>
      </div>
    </SceneFrame>
  );
};
