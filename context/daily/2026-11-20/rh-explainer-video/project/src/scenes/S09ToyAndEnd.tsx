import React from 'react';
import {Easing, interpolate, interpolateColors, useCurrentFrame, useVideoConfig, spring} from 'remotion';
import {SceneFrame} from '../components/SceneFrame';
import {colors, fonts, glow} from '../theme';
import {clamp, ramp} from '../lib/anim';
import {sceneById, wordFrame} from '../lib/timeline';
import {GZ_POINTS, GZ_XMAX} from './s09/gz';

// s09 · Where it starts (the toy) and where it ends (Landau).
const S = sceneById('s09_toy_and_end');
const W = (w: string, n = 0) => wordFrame(S, w, n);

const B = {
  ladder: W('ladder'),
  toy: W('toy', 0),
  unpublished: W('unpublished'),
  proof: W('proof'),
  weils: W("weil's"),
  theorem: W('theorem'),
  uses: W('uses'),
  signs: W('signs'),
  early: W('early'),
  cant: W("can't"),
  toy2: W('toy', 1),
  code: W('code'),
  what: W('what'),
  ending: W('ending'),
  classical: W('classical'),
  landau: W("landau's"),
  turns: W('turns'),
  oneSided: W('one-sided'),
  bound: W('bound'),
  smoothed: W('smoothed'),
  count: W('count'),
  into: W('into'),
  ban: W('ban'),
  zeros: W('zeros'),
  right: W('right'),
  line: W('line'),
  symmetry: W('symmetry'),
  covers: W('covers'),
  left: W('left'),
};

const HATCH = '#e8653f';

// ---------------- plot geometry (left) ----------------
const PX0 = 150;
const PX1 = 830;
const PY0 = 300; // top
const PY1 = 640; // bottom
const YMIN = -4;
const YMAX = 19;
const sx = (x: number) => PX0 + (x / GZ_XMAX) * (PX1 - PX0);
const sy = (y: number) => PY1 - ((y - YMIN) / (YMAX - YMIN)) * (PY1 - PY0);
const ceiling = (x: number) => 2.5 + 0.05 * Math.sqrt(x); // illustrative one-sided bound ~ x^(1/2)

// ---------------- strip geometry (right) ----------------
const SX0 = 1180; // Re = 0
const SX1 = 1600; // Re = 1
const SXC = (SX0 + SX1) / 2; // Re = 1/2
const ST = 270;
const SB = 720;

const Pill: React.FC<{x: number; y: number; children: React.ReactNode; w: number; opacity: number; anchor?: 'middle' | 'end' | 'start'; size?: number}> = ({
  x,
  y,
  children,
  w,
  opacity,
  anchor = 'middle',
  size = 22,
}) => {
  const h = size + 18;
  const left = anchor === 'middle' ? x - w / 2 : anchor === 'end' ? x - w : x;
  return (
    <g opacity={opacity}>
      <rect x={left} y={y - h / 2} width={w} height={h} rx={h / 2} fill="rgba(17,15,13,0.7)" stroke={colors.line} strokeWidth={1.2} />
      <text x={left + w / 2} y={y + size * 0.34} fontFamily={fonts.mono} fontSize={size} fill={colors.muted} textAnchor="middle">
        {children}
      </text>
    </g>
  );
};
const pillW = (t: string, size = 22) => t.length * size * 0.6 + 30;

const TAG_A = "Author's account · unpublished · schematic";
const TAG_B = ' · reported absent from the released Lean (Lean Zulip, Nov 20)';
const TAG_CODE = 'Our reading of the released code, simplified';
const TAG_FAMILY = 'applied to zeta and to families of Dirichlet L-functions';

export const S09ToyAndEnd: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();

  // ======================= Part A: the toy =======================
  const partAOut = 1 - ramp(f, B.what - 4, 20);
  const ladderIcon = ramp(f, B.ladder - 4, 16);
  const toyIn = ramp(f, B.toy - 6, 18);
  const headerSub = ramp(f, B.weils - 4, 14);
  // bars: grow, then press against zero without crossing
  const grow = ramp(f, B.proof - 10, 22, Easing.out(Easing.cubic));
  const wob = interpolate(f, [B.theorem - 6, B.uses, B.signs + 10], [0, 1, 0], clamp);
  const wave = Math.sin((f - B.theorem) / 4.2);
  const hA = grow * (170 - wob * 125 * (0.5 + 0.5 * wave));
  const hB = grow * (150 - wob * 115 * (0.5 - 0.5 * Math.sin((f - B.theorem) / 3.6)));
  const signPop = spring({frame: f - (B.signs - 4), fps, config: {damping: 12, mass: 0.6}});
  const ghost = ramp(f, B.cant - 4, 18);
  const tagA = ramp(f, B.unpublished - 2, 14);
  const tagB = ramp(f, B.early - 2, 22, Easing.inOut(Easing.cubic));
  const zeroPress = wob; // the zero line brightens while the bars press on it
  // solid outline breaks smoothly into dashes as the toy goes missing
  const dissolve = (d: number) => (ghost <= 0 ? undefined : `${(d + 400 * (1 - ghost) ** 2).toFixed(2)} ${(d * ghost).toFixed(2)}`);

  const TX = 800; // toy centre
  const ZY = 500; // zero line
  const barW = 116;
  const aX = TX - 150;
  const bX = TX + 150;

  // tag geometry (one pill that grows)
  const tagSize = 21;
  const wA = pillW(TAG_A, tagSize);
  const wFull = pillW(TAG_A + TAG_B, tagSize);
  const tagWidth = wA + (wFull - wA) * tagB;
  const tagY = 812;

  // ======================= Part B: the ending =======================
  const partB = ramp(f, B.what + 10, 18);
  const codeTag = ramp(f, B.ending - 4, 16);
  const axesIn = ramp(f, B.what + 24, 18);
  const curveDraw = ramp(f, B.classical, B.turns - B.classical + 10, Easing.inOut(Easing.cubic));
  const ceilDraw = ramp(f, B.oneSided - 4, 26, Easing.inOut(Easing.cubic));
  const plotLabel = ramp(f, B.smoothed - 4, 14);
  const formulaIn = ramp(f, B.count - 2, 18);
  const arrowDraw = ramp(f, B.turns - 4, 22, Easing.inOut(Easing.cubic));
  const stripFrame = ramp(f, B.ending - 2, 20);
  const hatchRight = ramp(f, B.ban - 4, B.line - B.ban + 4, Easing.inOut(Easing.cubic));
  const noZeros = ramp(f, B.zeros - 2, 14);
  const familyTag = ramp(f, B.right, 16);
  const mirrorArrow = ramp(f, B.symmetry - 4, 18, Easing.inOut(Easing.cubic));
  const flip = ramp(f, B.covers - 8, 24, Easing.inOut(Easing.cubic));
  const lineGlow = interpolate(f, [B.left - 4, B.left + 20], [0, 1], clamp);
  const push = interpolate(f, [B.symmetry, B.left + 40], [1, 1.035], clamp);

  // Gz curve path (real data: computed from a sieve up to 100,000)
  const nDraw = Math.max(2, Math.floor(GZ_POINTS.length * curveDraw));
  let curveD = '';
  for (let i = 0; i < nDraw; i++) {
    const [x, y] = GZ_POINTS[i];
    curveD += `${i === 0 ? 'M' : 'L'}${sx(x).toFixed(1)},${sy(y).toFixed(1)} `;
  }
  const tip = GZ_POINTS[nDraw - 1];
  let ceilD = '';
  const nC = 120;
  const nCDraw = Math.max(2, Math.floor(nC * ceilDraw));
  for (let i = 0; i < nCDraw; i++) {
    const x = 100 + ((GZ_XMAX - 100) * i) / (nC - 1);
    ceilD += `${i === 0 ? 'M' : 'L'}${sx(x).toFixed(1)},${sy(ceiling(x)).toFixed(1)} `;
  }

  // flip copy: scaleX goes 1 -> -1 about the centre line
  const flipSX = Math.cos(flip * Math.PI);

  return (
    <SceneFrame index={9} kicker="The toy, and the ending">
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0, fontVariantNumeric: 'lining-nums', fontFeatureSettings: '"lnum" 1'}}>
        <defs>
          <pattern id="s09hatch" width={14} height={14} patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width={14} height={14} fill="rgba(232,101,63,0.10)" />
            <line x1={0} y1={0} x2={0} y2={14} stroke={HATCH} strokeWidth={2.2} strokeOpacity={0.55} />
          </pattern>
          <clipPath id="s09hatchRight">
            <rect x={SXC + 2} y={ST} width={(SX1 - SXC - 2) * hatchRight} height={SB - ST} />
          </clipPath>
          <marker id="s09arrow" viewBox="0 0 10 10" refX={8} refY={5} markerWidth={7} markerHeight={7} orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill={colors.muted} />
          </marker>
          <marker id="s09arrowAcc" viewBox="0 0 10 10" refX={8} refY={5} markerWidth={7} markerHeight={7} orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill={colors.accent} />
          </marker>
        </defs>

        {/* ======================= Part A ======================= */}
        <g opacity={partAOut}>
          <text x={120} y={200} fontFamily={fonts.mono} fontSize={20} letterSpacing="0.18em" fill={colors.muted} opacity={toyIn}>
            THE TOY
            <tspan letterSpacing="0.02em" fill={colors.faint} fillOpacity={headerSub}>
              {'  ·  his unpublished proof of Weil’s theorem, he says'}
            </tspan>
          </text>

          {/* toy: two quantities, decided by sign alone */}
          <g opacity={toyIn * (1 - 0.5 * ghost)}>
            <line
              x1={TX - 330}
              x2={TX + 330}
              y1={ZY}
              y2={ZY}
              stroke={interpolateColors(zeroPress, [0, 1], [colors.muted, colors.fg])}
              strokeOpacity={0.6 + 0.4 * zeroPress}
              strokeWidth={2.4}
              strokeDasharray={dissolve(8)}
              style={{filter: glow(2 + 8 * zeroPress, 'rgba(242,237,228,0.5)')}}
            />
            <text x={TX - 352} y={ZY + 7} fontFamily={fonts.mono} fontSize={20} fill={colors.muted} textAnchor="end">
              0
            </text>
            {/* forced positive */}
            <rect
              x={aX - barW / 2}
              y={ZY - hA}
              width={barW}
              height={Math.max(0, hA)}
              fill={colors.accent}
              fillOpacity={0.22 * (1 - ghost)}
              stroke={colors.accent}
              strokeWidth={2}
              strokeDasharray={dissolve(7)}
            />
            {/* forced negative */}
            <rect
              x={bX - barW / 2}
              y={ZY}
              width={barW}
              height={Math.max(0, hB)}
              fill={colors.fg}
              fillOpacity={0.12 * (1 - ghost)}
              stroke={colors.fg}
              strokeOpacity={0.8}
              strokeWidth={2}
              strokeDasharray={dissolve(7)}
            />
            {/* sign glyphs */}
            <g opacity={Math.min(1, signPop)}>
              <g transform={`translate(${aX},${ZY - hA - 52}) scale(${signPop})`} style={{filter: glow(8 * (1 - ghost))}}>
                <line x1={-24} x2={24} y1={0} y2={0} stroke={colors.accent} strokeWidth={6} strokeLinecap="round" />
                <line x1={0} x2={0} y1={-24} y2={24} stroke={colors.accent} strokeWidth={6} strokeLinecap="round" />
              </g>
              <g transform={`translate(${bX},${ZY + hB + 52}) scale(${signPop})`}>
                <line x1={-24} x2={24} y1={0} y2={0} stroke={colors.fg} strokeWidth={6} strokeLinecap="round" />
              </g>
            </g>
            <text x={aX} y={ZY + 36} fontFamily={fonts.mono} fontSize={17} fill={colors.faint} textAnchor="middle" opacity={grow}>
              one sign
            </text>
            <text x={bX} y={ZY - 20} fontFamily={fonts.mono} fontSize={17} fill={colors.faint} textAnchor="middle" opacity={grow}>
              the opposite sign
            </text>
          </g>

          {/* ghost marker when readers can't find it */}
          <g opacity={ghost}>
            <rect x={TX - 380} y={ZY - 260} width={760} height={510} rx={18} fill="none" stroke={colors.muted} strokeOpacity={0.55} strokeWidth={1.5} strokeDasharray="10 10" />
          </g>

          {/* the ladder it grew into (small) */}
          <g opacity={ladderIcon * 0.9}>
            {Array.from({length: 14}, (_, k) => (
              <line key={k} x1={1540} x2={1640} y1={620 - k * 26} y2={620 - k * 26} stroke={colors.accent} strokeOpacity={0.85} strokeWidth={2} />
            ))}
            <line x1={1540} x2={1540} y1={620} y2={282} stroke={colors.fg} strokeOpacity={0.3} strokeWidth={1.2} />
            <line x1={1640} x2={1640} y1={620} y2={282} stroke={colors.fg} strokeOpacity={0.3} strokeWidth={1.2} />
            <text x={1590} y={664} fontFamily={fonts.mono} fontSize={17} fill={colors.faint} textAnchor="middle">
              the ladder
            </text>
          </g>
          <path
            d={`M${TX + 400},${ZY} C${TX + 520},${ZY} ${1420},${ZY - 20} ${1515},${ZY - 30}`}
            fill="none"
            stroke={colors.muted}
            strokeWidth={1.6}
            strokeDasharray="5 7"
            markerEnd="url(#s09arrow)"
            opacity={toyIn * ladderIcon * (1 - 0.6 * ghost)}
          />
          <text x={1300} y={ZY - 44} fontFamily={fonts.mono} fontSize={17} fill={colors.faint} textAnchor="middle" opacity={toyIn * ladderIcon * (1 - 0.6 * ghost)}>
            grew into
          </text>

          {/* honesty tag, extended when the absence is reported */}
          <g opacity={tagA}>
            <rect x={960 - tagWidth / 2} y={tagY - 18} width={tagWidth} height={36} rx={18} fill="rgba(17,15,13,0.7)" stroke={colors.line} strokeWidth={1.2} />
            <clipPath id="s09tagclip">
              <rect x={960 - tagWidth / 2 + 6} y={tagY - 18} width={tagWidth - 12} height={36} />
            </clipPath>
            <text x={960 - tagWidth / 2 + 15} y={tagY + 6} fontFamily={fonts.mono} fontSize={tagSize} fill={colors.muted} clipPath="url(#s09tagclip)">
              {TAG_A}
              <tspan fill={colors.fg} fillOpacity={tagB}>
                {TAG_B}
              </tspan>
            </text>
          </g>
        </g>

        {/* ======================= Part B ======================= */}
        <g opacity={partB}>
          <text x={120} y={200} fontFamily={fonts.mono} fontSize={20} letterSpacing="0.18em" fill={colors.muted}>
            THE ENDING
          </text>
          <Pill x={1810} y={110} w={pillW(TAG_CODE)} anchor="end" opacity={codeTag}>
            {TAG_CODE}
          </Pill>

          {/* ---- left: smoothed prime sum under a one-sided ceiling ---- */}
          <g opacity={axesIn}>
            <text x={PX0} y={268} fontFamily={fonts.mono} fontSize={20} fill={colors.fg} opacity={plotLabel}>
              smoothed, weighted prime sum
            </text>
            <line x1={PX0} x2={PX1} y1={sy(0)} y2={sy(0)} stroke={colors.line} strokeWidth={1.5} />
            <line x1={PX0} x2={PX0} y1={PY0 + 10} y2={PY1} stroke={colors.line} strokeWidth={1.5} />
            <text x={PX0 - 14} y={sy(0) + 6} fontFamily={fonts.mono} fontSize={17} fill={colors.faint} textAnchor="end">
              0
            </text>
            {[50000, 100000].map((v) => (
              <g key={v}>
                <line x1={sx(v)} x2={sx(v)} y1={PY1 - 6} y2={PY1 + 6} stroke={colors.faint} strokeWidth={1.2} />
                <text x={sx(v)} y={PY1 + 30} fontFamily={fonts.mono} fontSize={16} fill={colors.faint} textAnchor="middle">
                  {v === 50000 ? '50,000' : 'x = 100,000'}
                </text>
              </g>
            ))}
          </g>
          {curveDraw > 0 && <path d={curveD} fill="none" stroke={colors.fg} strokeWidth={2} strokeOpacity={0.92} strokeLinejoin="round" />}
          {curveDraw > 0 && curveDraw < 1 && <circle cx={sx(tip[0])} cy={sy(tip[1])} r={4} fill={colors.fg} />}
          {ceilDraw > 0 && (
            <path d={ceilD} fill="none" stroke={colors.accent} strokeWidth={2.6} style={{filter: glow(6)}} />
          )}
          <g opacity={ramp(f, B.bound, 14)}>
            <text x={PX1 - 4} y={sy(ceiling(GZ_XMAX)) - 18} fontFamily={fonts.mono} fontSize={18} fill={colors.accent} textAnchor="end">
              one-sided bound ≈ x^(½+ε), for large x
            </text>
            <text x={PX1 - 4} y={PY1 + 58} fontFamily={fonts.mono} fontSize={19} fill={colors.muted} textAnchor="end">
              curve computed to x = 100,000 · ceiling illustrative
            </text>
          </g>

          {/* zeta-only formula */}
          <g opacity={formulaIn}>
            <text x={PX0} y={762} fontFamily={fonts.displayUpright} fontSize={36} fill={colors.fg}>
              <tspan fontFamily={fonts.display} fontStyle="italic">
                G
              </tspan>
              <tspan fontFamily={fonts.display} fontStyle="italic" fontSize={24} dy={8}>
                z
              </tspan>
              <tspan dy={-8}>(</tspan>
              <tspan fontFamily={fonts.display} fontStyle="italic">
                x
              </tspan>
              <tspan>) = Σ</tspan>
              <tspan fontSize={22} dy={10}>
                n≤x
              </tspan>
              <tspan dy={-10}> Λ(</tspan>
              <tspan fontFamily={fonts.display} fontStyle="italic">
                n
              </tspan>
              <tspan>)(</tspan>
              <tspan fontFamily={fonts.display} fontStyle="italic">
                x
              </tspan>
              <tspan>/</tspan>
              <tspan fontFamily={fonts.display} fontStyle="italic">
                n
              </tspan>
              <tspan> − 1) − </tspan>
              <tspan fontFamily={fonts.display} fontStyle="italic">
                x
              </tspan>
              <tspan> log </tspan>
              <tspan fontFamily={fonts.display} fontStyle="italic">
                x
              </tspan>
              <tspan> + (1 + γ)</tspan>
              <tspan fontFamily={fonts.display} fontStyle="italic">
                x
              </tspan>
            </text>
            <text x={PX0} y={800} fontFamily={fonts.mono} fontSize={19} fill={colors.muted}>
              zeta-only version
            </text>
          </g>

          {/* ---- Landau's arrow ---- */}
          <g opacity={arrowDraw > 0 ? 1 : 0}>
            <path
              d={`M${PX1 + 50},470 L${SX0 - 50},470`}
              fill="none"
              stroke={colors.accent}
              strokeWidth={2}
              pathLength={1}
              strokeDasharray={`${arrowDraw} 1`}
              markerEnd={arrowDraw > 0.95 ? 'url(#s09arrowAcc)' : undefined}
            />
            <text x={(PX1 + SX0) / 2} y={448} fontFamily={fonts.mono} fontSize={18} fill={colors.accent} textAnchor="middle" opacity={arrowDraw}>
              Landau
            </text>
            <text x={(PX1 + SX0) / 2} y={502} fontFamily={fonts.mono} fontSize={15} fill={colors.faint} textAnchor="middle" opacity={arrowDraw}>
              classical
            </text>
          </g>

          {/* ---- right: the critical strip ---- */}
          <g opacity={stripFrame} transform={`translate(${SXC},${(ST + SB) / 2}) scale(${push}) translate(${-SXC},${-(ST + SB) / 2})`}>
            <rect x={SX0} y={ST} width={SX1 - SX0} height={SB - ST} fill={colors.strip} />
            <line x1={SX0} x2={SX0} y1={ST} y2={SB} stroke={colors.line} strokeWidth={1.5} />
            <line x1={SX1} x2={SX1} y1={ST} y2={SB} stroke={colors.line} strokeWidth={1.5} />
            <line x1={SX0 - 60} x2={SX1 + 60} y1={SB} y2={SB} stroke={colors.line} strokeWidth={1.5} />

            {/* hatch: right of the line */}
            <rect x={SXC + 2} y={ST} width={SX1 - SXC - 2} height={SB - ST} fill="url(#s09hatch)" clipPath="url(#s09hatchRight)" />
            {/* mirrored copy: flips over the centre line */}
            {flip > 0 && (
              <g transform={`translate(${SXC},0) scale(${flipSX},1) translate(${-SXC},0)`} opacity={0.35 + 0.65 * Math.abs(flipSX)}>
                <rect x={SXC + 2} y={ST} width={SX1 - SXC - 2} height={SB - ST} fill="url(#s09hatch)" />
              </g>
            )}

            {/* labels inside */}
            <g opacity={noZeros}>
              <rect x={SXC + 105 - 82} y={430} width={164} height={34} rx={17} fill={colors.bg} fillOpacity={0.85} />
              <text x={SXC + 105} y={453} fontFamily={fonts.mono} fontSize={18} fill={colors.fg} textAnchor="middle">
                no zeros here
              </text>
            </g>
            <g opacity={ramp(f, B.left + 4, 14)}>
              <rect x={SXC - 105 - 82} y={430} width={164} height={34} rx={17} fill={colors.bg} fillOpacity={0.85} />
              <text x={SXC - 105} y={453} fontFamily={fonts.mono} fontSize={18} fill={colors.fg} textAnchor="middle">
                no zeros here
              </text>
            </g>

            {/* the centre line */}
            <line
              x1={SXC}
              x2={SXC}
              y1={ST - 10}
              y2={SB}
              stroke={colors.accent}
              strokeWidth={2.6 + 1.4 * lineGlow}
              style={{filter: glow(6 + 16 * lineGlow)}}
            />

            {/* axis labels */}
            <g fontFamily={fonts.mono} fontSize={19} fill={colors.muted} textAnchor="middle">
              <text x={SX0} y={SB + 36}>
                0
              </text>
              <text x={SXC} y={SB + 38} fontFamily={fonts.displayUpright} fontSize={30}>
                ½
              </text>
              <text x={SX1} y={SB + 36}>
                1
              </text>
              <text x={SX1 + 70} y={SB + 36} fill={colors.faint}>
                Re(s)
              </text>
            </g>

            {/* symmetry arrow */}
            <g opacity={mirrorArrow > 0 ? 1 : 0}>
              <path
                d={`M${SXC + 105},${ST - 24} Q${SXC},${ST - 96} ${SXC - 105},${ST - 24}`}
                fill="none"
                stroke={colors.fg}
                strokeOpacity={0.8}
                strokeWidth={1.8}
                pathLength={1}
                strokeDasharray={`${mirrorArrow} 1`}
                markerEnd={mirrorArrow > 0.95 ? 'url(#s09arrow)' : undefined}
              />
              <text x={SXC} y={ST - 72} fontFamily={fonts.mono} fontSize={17} fill={colors.muted} textAnchor="middle" opacity={mirrorArrow}>
                symmetry
              </text>
            </g>
          </g>

          <Pill x={SXC} y={850} w={pillW(TAG_FAMILY)} opacity={familyTag}>
            {TAG_FAMILY}
          </Pill>
        </g>
      </svg>
    </SceneFrame>
  );
};
