import React from 'react';
import {Easing, interpolate, interpolateColors, useCurrentFrame} from 'remotion';
import {SceneFrame} from '../components/SceneFrame';
import {colors, fonts, glow} from '../theme';
import {clamp, ramp} from '../lib/anim';
import {lineStartFrame, sceneById, wordFrame} from '../lib/timeline';

// s07 · The wall. Polynomials can be differentiated; whole numbers cannot.
const S = sceneById('s07_wall');
const W = (w: string, n = 0) => wordFrame(S, w, n);

const B = {
  open: lineStartFrame(S, 0),
  push: W('push'),
  diff1: W('differentiate', 0),
  poly: W('polynomial'),
  diff2: W('differentiate', 1),
  seven: W('seven'),
  get: W('get'),
  zero: W('zero'),
  alp: W('alpöge'),
  names: W('names'),
  gap: W('gap'),
};

// ---- layout (local equation units are at font-size 100, then scaled) ----
const EQ_SCALE = 1.3;
const BASE = 560; // equation baseline
const GAP = 112; // distance from each equation to the wall
// left eq local extent [-30, 505], right eq local extent [-36, 312]
const L_W = (505 + 30) * EQ_SCALE;
const R_W = (312 + 36) * EQ_SCALE;
const TOTAL = L_W + R_W + 2 * GAP;
const START = (1920 - TOTAL) / 2;
const L_ORIGIN = START + 30 * EQ_SCALE;
const WALL_X = START + L_W + GAP;
const R_ORIGIN = WALL_X + GAP + 36 * EQ_SCALE;
const L_CENTER = START + L_W / 2;
const R_CENTER = WALL_X + GAP + R_W / 2;

const up = fonts.displayUpright;
const it = fonts.display;

type Glyph = {t: string; x: number; y?: number; size?: number; italic?: boolean; anchor?: 'start' | 'middle' | 'end'};

const G: React.FC<Glyph & {opacity?: number; fill?: string; style?: React.CSSProperties}> = ({
  t,
  x,
  y = 0,
  size = 100,
  italic,
  anchor = 'start',
  opacity = 1,
  fill = colors.fg,
  style,
}) => (
  <text
    x={x}
    y={y}
    fontFamily={italic ? it : up}
    fontStyle={italic ? 'italic' : 'normal'}
    fontSize={size}
    textAnchor={anchor}
    fill={fill}
    opacity={opacity}
    style={style}
  >
    {t}
  </text>
);

/** Stacked d/d(var) fraction. */
const Frac: React.FC<{den: React.ReactNode; opacity: number; barW?: number}> = ({den, opacity, barW = 30}) => (
  <g opacity={opacity}>
    <text x={0} y={-46} fontFamily={it} fontStyle="italic" fontSize={66} fill={colors.fg} textAnchor="middle">
      d
    </text>
    <line x1={-barW} x2={barW} y1={-30} y2={-30} stroke={colors.fg} strokeWidth={2.4} />
    <text x={0} y={22} fontFamily={it} fontStyle="italic" fontSize={66} fill={colors.fg} textAnchor="middle">
      {den}
    </text>
  </g>
);

export const S07Wall: React.FC = () => {
  const f = useCurrentFrame();

  // --- opening: two worlds (labels + small illustrations) ---
  const labelsIn = ramp(f, B.open, 16);
  const illusDim = interpolate(f, [B.diff1 - 6, B.diff1 + 14], [1, 0.45], clamp);
  const parabolaDraw = ramp(f, B.open + 4, 30, Easing.inOut(Easing.cubic));
  const tangentT = interpolate(f, [B.open + 30, B.diff1 + 40], [-1.25, 1.1], {...clamp, easing: Easing.inOut(Easing.sin)});
  // integers "push back": a short recoil on "push"
  const pushT = f - B.push;
  const recoil = pushT >= 0 && pushT < 24 ? Math.sin((pushT / 24) * Math.PI * 3) * 9 * Math.exp(-pushT / 7) : 0;

  // --- left equation, term by term ---
  const lFrac = ramp(f, B.diff1, 10);
  const lParen = ramp(f, B.diff1 + 7, 10);
  const lEq = ramp(f, B.poly - 3, 8);
  const flyT = ramp(f, B.poly + 1, 13, Easing.inOut(Easing.cubic));
  const lX = ramp(f, B.poly + 10, 9);
  const glowAmt = interpolate(f, [B.poly + 10, B.poly + 22, B.poly + 60], [0, 1, 0.65], clamp);

  // --- right equation, typed ---
  const typeAt = [B.diff2, B.diff2 + 4, B.diff2 + 9, B.seven - 4, B.seven, B.seven + 4, B.get];
  const typed = typeAt.map((t) => ramp(f, t, 3, Easing.linear));
  const lastTyped = typeAt.filter((t) => f >= t).length; // 0..7
  // "0" thud: falls, squashes, settles
  const zT = f - (B.zero - 4);
  const fall = interpolate(zT, [0, 5], [-80, 0], {...clamp, easing: Easing.in(Easing.quad)});
  const zeroOpacity = interpolate(zT, [0, 2], [0, 1], clamp);
  const squash = zT >= 5 ? Math.exp(-(zT - 5) / 4) * Math.cos((zT - 5) * 0.9) : 0;
  const zsx = 1 + 0.12 * squash;
  const zsy = 1 - 0.16 * squash;
  const shake = zT >= 5 && zT < 20 ? Math.sin((zT - 5) * 1.6) * 5 * Math.exp(-(zT - 5) / 4) : 0;
  const dust = zT >= 5 ? interpolate(zT, [5, 8, 26], [0, 0.55, 0], clamp) : 0;
  const dustW = interpolate(zT, [5, 26], [40, 120], clamp);

  // --- wall ---
  const wallT = ramp(f, B.zero + 10, 16, Easing.out(Easing.cubic));
  const wallTop = 188;
  const wallBot = 650;
  const gapPulse = interpolate(f, [B.gap - 2, B.gap + 8, B.gap + 40], [0, 1, 0.25], clamp);
  const spread = interpolate(f, [B.gap - 4, B.gap + 18], [0, 14], {...clamp, easing: Easing.out(Easing.cubic)});

  // --- quote ---
  const quoteT = ramp(f, B.names - 2, 20);
  const attribT = ramp(f, B.names + 14, 16);
  const eqDim = interpolate(f, [B.names - 4, B.names + 16], [1, 0.78], clamp);

  // caret after last typed char (right equation, local units)
  const caretX = [-40, 26, 26, 82, 116, 158, 214, 290][lastTyped];
  const caretY = lastTyped >= 1 && lastTyped <= 2 ? 22 : 0;
  const caretOn = f >= B.diff2 && f < B.zero - 3 && Math.floor((f - B.diff2) / 8) % 2 === 0;

  // parabola illustration (left)
  const pw = 340;
  const ph = 130;
  const pTop = 248;
  const px = (u: number) => L_CENTER + (u / 1.6) * (pw / 2);
  const py = (u: number) => pTop + ph - ((u * u + 1 - 1) / (1.6 * 1.6)) * (ph - 14);
  const parPts: string[] = [];
  const nPts = 64;
  const nDraw = Math.max(2, Math.round(nPts * parabolaDraw));
  for (let i = 0; i < nDraw; i++) {
    const u = -1.6 + (3.2 * i) / (nPts - 1);
    parPts.push(`${i === 0 ? 'M' : 'L'}${px(u).toFixed(1)},${py(u).toFixed(1)}`);
  }
  const tx = px(tangentT);
  const ty = py(tangentT);
  // slope in screen units: dy/du * (du/dx_screen)
  const slopeScreen = (-(2 * tangentT) / (1.6 * 1.6)) * (ph - 14) / (pw / 2 / 1.6);
  const tanLen = 74;
  const tdx = tanLen / Math.sqrt(1 + slopeScreen * slopeScreen);
  const tangentIn = ramp(f, B.open + 30, 10);

  return (
    <SceneFrame index={7} kicker="The wall">
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0, fontVariantNumeric: 'lining-nums', fontFeatureSettings: '"lnum" 1'}}>
        {/* column labels */}
        <g
          opacity={labelsIn}
          fontFamily={fonts.mono}
          fontSize={20}
          letterSpacing="0.16em"
          fill={colors.muted}
          textAnchor="middle"
        >
          <text x={L_CENTER - spread} y={214}>
            A POLYNOMIAL
          </text>
          <text x={R_CENTER + spread + recoil} y={214}>
            A WHOLE NUMBER
          </text>
        </g>

        {/* left illustration: smooth curve, slope everywhere */}
        <g opacity={illusDim} transform={`translate(${-spread},0)`}>
          <path d={parPts.join(' ')} fill="none" stroke={colors.fg} strokeOpacity={0.7} strokeWidth={2.2} />
          <g opacity={tangentIn}>
            <line
              x1={tx - tdx}
              y1={ty - tdx * slopeScreen}
              x2={tx + tdx}
              y2={ty + tdx * slopeScreen}
              stroke={colors.accent}
              strokeWidth={2}
              strokeOpacity={0.9}
            />
            <circle cx={tx} cy={ty} r={5} fill={colors.accent} />
          </g>
        </g>

        {/* right illustration: isolated integers, nothing in between */}
        <g opacity={illusDim * labelsIn} transform={`translate(${spread + recoil},0)`}>
          <line x1={R_CENTER - 190} x2={R_CENTER + 190} y1={340} y2={340} stroke={colors.line} strokeWidth={1.5} />
          {[3, 4, 5, 6, 7, 8, 9, 10, 11].map((n, i) => {
            const cx = R_CENTER + (n - 7) * 44;
            const pop = ramp(f, B.open + 6 + i * 2, 8);
            const is7 = n === 7;
            return (
              <g key={n} opacity={pop}>
                <circle cx={cx} cy={340} r={is7 ? 7 : 4.5} fill={is7 ? colors.fg : colors.muted} />
                <text x={cx} y={378} fontFamily={fonts.mono} fontSize={18} fill={is7 ? colors.fg : colors.faint} textAnchor="middle">
                  {n}
                </text>
              </g>
            );
          })}
        </g>

        {/* LEFT equation: d/dx (x^2 + 1) = 2x */}
        <g transform={`translate(${L_ORIGIN - spread},${BASE}) scale(${EQ_SCALE})`} opacity={eqDim}>
          <g opacity={lFrac} transform={`translate(0,${(1 - lFrac) * 10})`}>
            <Frac den="dx" opacity={1} />
          </g>
          <g opacity={lParen} transform={`translate(0,${(1 - lParen) * 10})`}>
            <G t="(" x={44} />
            <G t="x" x={78} italic />
            <G t="2" x={124} y={-44} size={58} />
            <G t="+" x={166} />
            <G t="1" x={240} />
            <G t=")" x={284} />
          </g>
          <G t="=" x={334} opacity={lEq} />
          {/* exponent 2 comes down to become the coefficient */}
          {flyT > 0 && (
            <text
              x={interpolate(flyT, [0, 1], [124, 396])}
              y={interpolate(flyT, [0, 1], [-44, 0]) - Math.sin(flyT * Math.PI) * 70}
              fontFamily={up}
              fontSize={interpolate(flyT, [0, 1], [58, 100])}
              fill={flyT < 1 ? colors.accent : colors.accent}
              style={{filter: glow(6 + 10 * glowAmt)}}
            >
              2
            </text>
          )}
          <G t="x" x={444} italic opacity={lX} fill={colors.accent} style={{filter: glow(6 + 10 * glowAmt)}} />
        </g>

        {/* RIGHT equation: d/d? (7) = 0 */}
        <g transform={`translate(${R_ORIGIN + spread},${BASE + shake}) scale(${EQ_SCALE})`} opacity={eqDim}>
          <g>
            <text x={0} y={-46} fontFamily={it} fontStyle="italic" fontSize={66} fill={colors.fg} textAnchor="middle" opacity={typed[0]}>
              d
            </text>
            <line x1={-34} x2={34} y1={-30} y2={-30} stroke={colors.fg} strokeWidth={2.4} opacity={typed[1]} />
            <text x={-12} y={22} fontFamily={it} fontStyle="italic" fontSize={66} fill={colors.fg} textAnchor="middle" opacity={typed[1]}>
              d
            </text>
            <text
              x={16}
              y={22}
              fontFamily={up}
              fontSize={66}
              fill={colors.muted}
              textAnchor="middle"
              opacity={typed[2]}
              transform={`rotate(${Math.sin((f - B.diff2) / 7) * 6} 16 4)`}
            >
              ?
            </text>
          </g>
          <G t="(" x={50} opacity={typed[3]} />
          <G t="7" x={84} opacity={typed[4]} />
          <G t=")" x={128} opacity={typed[5]} />
          <G t="=" x={180} opacity={typed[6]} />
          {/* the thud */}
          <ellipse cx={282} cy={6} rx={dustW / 2} ry={5} fill={colors.muted} opacity={dust * 0.5} />
          <g transform={`translate(282,${fall}) scale(${zsx},${zsy})`} opacity={zeroOpacity}>
            <text x={0} y={0} fontFamily={up} fontSize={100} fill={colors.muted} textAnchor="middle">
              0
            </text>
          </g>
          {caretOn && <rect x={caretX} y={caretY - 70} width={3} height={78} fill={colors.muted} opacity={0.8} />}
        </g>

        {/* the wall */}
        <g>
          <line
            x1={WALL_X}
            x2={WALL_X}
            y1={wallTop}
            y2={wallTop + (wallBot - wallTop) * wallT}
            stroke={interpolateColors(gapPulse, [0, 1], [colors.fg, colors.accent])}
            strokeOpacity={0.55 + 0.45 * Math.max(wallT * 0.6, gapPulse)}
            strokeWidth={2.5}
            style={{filter: glow(4 + 12 * gapPulse, interpolateColors(gapPulse, [0, 1], ['rgba(242,237,228,0.5)', colors.accentGlow]))}}
          />
        </g>

        {/* the note names the gap */}
        <g textAnchor="middle">
          <text
            x={960}
            y={752 + (1 - quoteT) * 14}
            fontFamily={it}
            fontStyle="italic"
            fontSize={54}
            fill={colors.fg}
            opacity={quoteT}
          >
            “multiplicity is hard to find over the integers”
          </text>
          <text x={960} y={808} fontFamily={fonts.mono} fontSize={20} fill={colors.muted} letterSpacing="0.06em" opacity={attribT}>
            Alpöge, Nov 20 note
          </text>
        </g>
      </svg>
    </SceneFrame>
  );
};
