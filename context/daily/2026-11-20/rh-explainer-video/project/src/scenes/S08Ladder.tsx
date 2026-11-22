import React from 'react';
import {Easing, interpolate, interpolateColors, useCurrentFrame} from 'remotion';
import {SceneFrame} from '../components/SceneFrame';
import {colors, fonts, glow} from '../theme';
import {clamp, ramp} from '../lib/anim';
import {lineStartFrame, sceneById, sceneFrames, wordFrame} from '../lib/timeline';
import {fmt, GroupLabel, lerp, lerpPt, Pt, qPath, qPoint, RootGlyph, Star, Tag} from './s08/parts';

// s08 · The ladder. The video's one deep beat.
const S = sceneById('s08_ladder');
const W = (w: string, n = 0) => wordFrame(S, w, n);
const END = sceneFrames(S);

const B = {
  way: W('way'),
  it: W('it'),
  line1: lineStartFrame(S, 1),
  theta: W('theta'),
  lift: W('lift', 0),
  symmetric: W('symmetric'),
  from: W('from'),
  group: W('group'),
  another: W('another'),
  according: W('according'),
  each: W('each'),
  moreOrder: W('more', 0),
  chain: W('chain'),
  them: W('them'),
  ladder: W('ladder'),
  every: W('every'),
  rung: W('rung'),
  buys: W('buys'),
  moreEnd: W('more', 1),
  forX: W('for'),
  sum: W('sum'),
  x1: W('x', 0),
  claude: W('claude'),
  suggested: W('suggested'),
  square: W('square'),
  root: W('root'),
  rungs: W('rungs'),
  alp: W('alpöge'),
  lineQ: W('line'),
  mathematicians: W('mathematicians'),
  fall: W('fall'),
  chairs: W('chairs'),
};

// ---- geometry ----
const WALL_X = 960;
const P0: Pt = [590, 610]; // U(X0) in the lift picture
const P2: Pt = [1330, 610]; // U(X1)
const PC: Pt = [960, 120]; // arc control: passes over the wall
const RING_R = 98;

const LX = 640; // ladder centre x
const LB = 800; // ladder base y
const LT = 260; // ladder top y
const LH = LB - LT;
const HALF = 96; // half rung width
const BEAT2_RUNGS = 8;
const HOP_BULGE = 84; // lifts drawn as arcs between rung centres

// rung k (1..8) is complete when its word is spoken
const T = [0, B.moreOrder, B.chain, B.them, B.ladder, B.every, B.rung, B.buys, B.moreEnd];
const hopDur = (k: number) => (k <= 1 ? 0 : Math.min(12, T[k] - T[k - 1] - 1));

const PANEL_X = 1110;
const LOUPE: Pt = [900, 470];
const LOUPE_R = 78;

export const S08Ladder: React.FC = () => {
  const f = useCurrentFrame();

  // ================= beat 0/1: the wall, the way around, the lift =================
  const wallOp = interpolate(f, [0, 8, B.line1, B.line1 + 20], [0, 1, 1, 0], clamp);
  const arcDraw = ramp(f, B.way - 4, 22, Easing.inOut(Easing.cubic));
  const ringIn = ramp(f, B.theta - 2, 18, Easing.out(Easing.back(1.4)));
  const thetaLabel = ramp(f, B.lift, 14) * (1 - ramp(f, B.according, 14));
  const starIn = ramp(f, B.symmetric - 4, 16, Easing.out(Easing.back(1.6)));
  const travel = ramp(f, B.from - 4, B.another - B.from + 4, Easing.inOut(Easing.cubic));
  const rewire = ramp(f, B.another, 16, Easing.inOut(Easing.cubic));
  const label0 = ramp(f, B.group - 4, 14);
  const label1 = ramp(f, B.another - 2, 14);
  const arrivePulse = interpolate(f, [B.another, B.another + 6, B.another + 30], [0, 1, 0], clamp);

  // ================= fold into a ladder =================
  const fold = ramp(f, B.according, 40, Easing.inOut(Easing.cubic));
  const sp2 = LH / BEAT2_RUNGS; // beat-2 spacing
  const r0Pos = lerpPt(P0, [LX, LB], fold);
  const r1Pos = lerpPt(P2, [LX, LB - sp2], fold);
  const ringR = lerp(RING_R, 11, fold);
  const arc0 = lerpPt(P0, [LX, LB], fold);
  const arcC = lerpPt(PC, [LX + HOP_BULGE, LB - sp2 / 2], fold);
  const arc2 = lerpPt(P2, [LX, LB - sp2], fold);
  const barsIn = ramp(f, B.according + 22, 18);
  const pictureLabelsOut = 1 - ramp(f, B.according, 10);

  // ================= beat 3: X grows, rungs ~ sqrt(X) =================
  const s3a = ramp(f, B.forX - 4, 14, Easing.inOut(Easing.cubic)); // 8 -> 10 rungs, done before the X panel shows
  const s3b = ramp(f, B.suggested, 30, Easing.inOut(Easing.cubic)); // 10 -> 100
  const s3c = ramp(f, B.square, 26, Easing.inOut(Easing.cubic)); // 100 -> 1000
  const logN = Math.log10(BEAT2_RUNGS) + s3a * (1 - Math.log10(BEAT2_RUNGS)) + s3b + s3c;
  const inBeat3 = f >= B.forX;
  const nRungs = inBeat3 ? Math.pow(10, logN) : BEAT2_RUNGS;
  const spacing = LH / nRungs;
  const X = f < B.suggested ? Math.pow(lerp(BEAT2_RUNGS, 10, s3a), 2) : Math.pow(10, 2 + 2 * s3b + 2 * s3c);
  const rungCount = Math.round(Math.sqrt(X));

  // which beat-2 rungs exist, and the object's hop
  const rungAppear = (k: number) => {
    if (k <= 1) return barsIn;
    return ramp(f, T[k] - hopDur(k) - 6, 10);
  };
  const litCount = T.filter((t, k) => k >= 1 && f >= t).length; // 0..8
  const multiplicity = 1 + litCount;
  const mSmooth = 1 + T.reduce((acc, t, k) => (k >= 1 ? acc + ramp(f, t - 3, 9, Easing.out(Easing.cubic)) : acc), 0);
  const lastTick = T.filter((t, k) => k >= 1 && f >= t).pop() ?? -999;
  const tickFlash = interpolate(f - lastTick, [0, 4, 22], [0.0, 1, 0], clamp);

  const yRung = (k: number) => LB - k * (inBeat3 ? spacing : sp2);

  // object position
  let star: Pt;
  let starR: number;
  if (f < B.according) {
    star = travel <= 0 ? P0 : qPoint(P0, PC, P2, travel);
    starR = 56;
  } else if (!inBeat3) {
    // ride the ladder
    star = r1Pos;
    starR = lerp(56, 22, fold);
    for (let k = 2; k <= BEAT2_RUNGS; k++) {
      const d = hopDur(k);
      const t = interpolate(f, [T[k] - d, T[k]], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
      if (f >= T[k] - d) {
        const a: Pt = [LX, yRung(k - 1)];
        const c: Pt = [LX + HOP_BULGE, (yRung(k - 1) + yRung(k)) / 2];
        const b: Pt = [LX, yRung(k)];
        star = qPoint(a, c, b, t);
      }
    }
  } else {
    star = [LX, LT];
    starR = 22;
  }
  if (inBeat3) starR = lerp(22, 18, s3b);

  // ================= panels =================
  const multPanel = ramp(f, B.each - 6, 16) * (1 - ramp(f, B.forX, 14));
  const xPanel = ramp(f, B.forX + 12, 18) * (1 - ramp(f, B.alp - 8, 14));
  const claudeAttr = ramp(f, B.claude, 14);
  const sqrtFlash = interpolate(f, [B.square - 2, B.square + 6, B.square + 34], [0, 1, 0.25], clamp);
  const fromNote = ramp(f, B.according, 14);
  const schematicPos = ramp(f, B.according, 40, Easing.inOut(Easing.cubic));
  const schematicOp = ramp(f, B.theta + 6, 14);

  // ================= finale: the chairs quote =================
  const fin = ramp(f, B.alp - 8, 26, Easing.inOut(Easing.cubic));
  const ladderDim = lerp(1, 0.36, fin);
  const ladderShift = lerp(0, -70, fin);
  const qMark = ramp(f, B.alp, 18);
  const q1 = ramp(f, B.lineQ - 6, 14);
  const q2 = ramp(f, B.mathematicians - 10, 14);
  const q3 = ramp(f, B.fall - 6, 14);
  const qAttr = ramp(f, B.chairs - 4, 16);
  const tagsOut = 1 - fin;

  // loupe appears once rungs are too dense to see
  const loupe = interpolate(spacing, [1.6, 3.2], [1, 0], clamp) * ramp(f, B.root, 20);
  const loupeSpacing = 13;

  // ladder labels fade once the ladder gets dense
  const labelsFade = 1 - ramp(f, B.forX, 16);
  const hopFade = interpolate(spacing, [14, 40], [0, 1], clamp);

  // ----- rungs -----
  const rungEls: React.ReactNode[] = [];
  const maxK = inBeat3 ? Math.ceil(nRungs) : BEAT2_RUNGS;
  const sw = inBeat3 ? Math.min(2.6, Math.max(0.55, spacing * 0.42)) : 2.6;
  const dense = interpolate(spacing, [0.5, 2, 6], [0.2, 0.42, 1], clamp);
  const lineFade = inBeat3 ? interpolate(spacing, [1.4, 3.2], [0, 1], clamp) : 1;
  for (let k = 0; k <= maxK; k++) {
    if (lineFade <= 0) break;
    const y = yRung(k);
    if (y < LT - 0.5) continue;
    let op: number;
    let lit: boolean;
    if (!inBeat3) {
      op = k === 0 ? barsIn : rungAppear(k);
      lit = k === 0 ? false : k === 1 ? true : f >= T[k] - 2;
    } else {
      op = Math.min(1, Math.max(0, nRungs - k + 1));
      lit = k > 0;
    }
    if (op <= 0) continue;
    const grow = inBeat3 ? 1 : op;
    rungEls.push(
      <line
        key={k}
        x1={LX - HALF * grow}
        x2={LX + HALF * grow}
        y1={y}
        y2={y}
        stroke={lit ? colors.accent : colors.fg}
        strokeOpacity={(lit ? 0.95 : 0.55) * (inBeat3 ? dense : 1)}
        strokeWidth={sw}
        opacity={(inBeat3 ? op : 1) * lineFade}
      />,
    );
  }

  // ----- hop arcs (beat 2) -----
  const hopEls: React.ReactNode[] = [];
  if (f >= B.according + 30) {
    const nh = inBeat3 ? Math.min(14, Math.ceil(nRungs)) : BEAT2_RUNGS;
    for (let k = 2; k <= nh; k++) {
      const a: Pt = [LX, yRung(k - 1)];
      const c: Pt = [LX + HOP_BULGE, (yRung(k - 1) + yRung(k)) / 2];
      const b: Pt = [LX, yRung(k)];
      const draw = inBeat3 ? 1 : interpolate(f, [T[k] - hopDur(k), T[k]], [0, 1], clamp);
      if (draw <= 0) continue;
      hopEls.push(
        <path
          key={k}
          d={qPath(a, c, b)}
          fill="none"
          stroke={colors.accent}
          strokeOpacity={0.7 * (inBeat3 ? hopFade : 1)}
          strokeWidth={1.8}
          pathLength={1}
          strokeDasharray={`${draw} 1`}
        />,
      );
    }
  }

  // ----- labels -----
  const labelEls: React.ReactNode[] = [];
  if (f >= B.according + 20) {
    for (let k = 0; k <= BEAT2_RUNGS; k++) {
      const appear = k <= 1 ? ramp(f, B.according + 26, 14) : rungAppear(k);
      const fadeK = k === 0 ? 1 : labelsFade;
      const op = appear * fadeK;
      if (op <= 0) continue;
      labelEls.push(
        <GroupLabel key={k} k={k} x={LX - HALF - 22} y={yRung(k) + 8} anchor="end" size={22} opacity={op} fill={k === 0 ? colors.muted : colors.faint} />,
      );
    }
  }

  // arc (beat 0/1 picture, then the first hop)
  const arcD = qPath(arc0, arcC, arc2);
  const arcTrail = f < B.according ? travel : 1;

  return (
    <SceneFrame index={8} kicker="The ladder">
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0, fontVariantNumeric: 'lining-nums', fontFeatureSettings: '"lnum" 1'}}>
        <defs>
          <linearGradient id="s08dense" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={colors.accent} stopOpacity={0.5} />
            <stop offset="1" stopColor={colors.accent} stopOpacity={0.26} />
          </linearGradient>
          <mask id="s08arcReveal">
            <path d={arcD} fill="none" stroke="#fff" strokeWidth={12} pathLength={1} strokeDasharray={`${arcDraw} 1`} />
          </mask>
        </defs>

        {/* ---------------- ladder world (dims + shifts in the finale) ---------------- */}
        <g opacity={ladderDim} transform={`translate(${ladderShift},0)`}>
          {/* the wall from s07 */}
          <line x1={WALL_X} x2={WALL_X} y1={400} y2={760} stroke={colors.fg} strokeOpacity={0.8 * wallOp} strokeWidth={2.5} style={{filter: glow(4, 'rgba(242,237,228,0.45)')}} />

          {/* the way around: dashed, then the lift's glowing trail */}
          <g mask="url(#s08arcReveal)">
            <path d={arcD} fill="none" stroke={colors.fg} strokeOpacity={0.5 * (1 - fold * 0.6) * (inBeat3 ? hopFade : 1)} strokeWidth={2} strokeDasharray="7 11" />
          </g>
          {arcTrail > 0 && (
            <path
              d={arcD}
              fill="none"
              stroke={colors.accent}
              strokeWidth={lerp(3, 1.8, fold)}
              pathLength={1}
              strokeDasharray={`${arcTrail} 1`}
              strokeOpacity={0.9 * (inBeat3 ? hopFade : 1)}
              style={{filter: glow(lerp(8, 3, fold))}}
            />
          )}
          {/* pen tip while the way around is drawn */}
          {arcDraw > 0 && arcDraw < 1 && (
            <circle cx={qPoint(P0, PC, P2, arcDraw)[0]} cy={qPoint(P0, PC, P2, arcDraw)[1]} r={5} fill={colors.fg} />
          )}

          {/* theta-lift label on the arc */}
          <text x={960} y={345} fontFamily={fonts.mono} fontSize={22} fill={colors.accent} textAnchor="middle" opacity={thetaLabel} letterSpacing="0.08em">
            θ-lift
          </text>

          {/* rails */}
          {f >= B.according + 20 && (
            <g opacity={barsIn * 0.35}>
              <line x1={LX - HALF} x2={LX - HALF} y1={LB} y2={inBeat3 ? LT : yRung(litCount >= 1 ? Math.max(1, litCount) : 1)} stroke={colors.fg} strokeWidth={1.2} />
              <line x1={LX + HALF} x2={LX + HALF} y1={LB} y2={inBeat3 ? LT : yRung(litCount >= 1 ? Math.max(1, litCount) : 1)} stroke={colors.fg} strokeWidth={1.2} />
            </g>
          )}

          {rungEls}
          {inBeat3 && lineFade < 1 && (
            <rect x={LX - HALF} y={LT} width={HALF * 2} height={LH} fill="url(#s08dense)" opacity={1 - lineFade} />
          )}
          {hopEls}
          {labelEls}

          {/* nodes for the later rungs */}
          {f >= B.according + 20 &&
            Array.from({length: BEAT2_RUNGS - 1}, (_, i) => i + 2).map((k) => {
              const op = rungAppear(k) * (inBeat3 ? 1 - ramp(f, B.forX, 12) : 1);
              if (op <= 0) return null;
              return <circle key={k} cx={LX} cy={yRung(k)} r={11 * op} fill={colors.bg} stroke={colors.fg} strokeOpacity={0.6} strokeWidth={1.5} opacity={op} />;
            })}
          {/* group rings (the two symmetry groups), shrink into ladder nodes */}
          {[r0Pos, r1Pos].map(([cx, cy], i) => (
            <circle
              key={i}
              cx={cx}
              cy={cy}
              r={ringR * ringIn}
              fill={colors.bg}
              fillOpacity={0.6}
              stroke={i === 1 && arrivePulse > 0 ? colors.accent : colors.fg}
              strokeOpacity={0.6 + 0.4 * arrivePulse * (i === 1 ? 1 : 0)}
              strokeWidth={lerp(2, 1.5, fold)}
              opacity={inBeat3 ? 1 - ramp(f, B.forX, 12) : 1}
            />
          ))}
          {/* picture labels under the rings */}
          <GroupLabel k={0} x={P0[0]} y={P0[1] + RING_R + 46} size={28} opacity={label0 * pictureLabelsOut} />
          <GroupLabel k={1} x={P2[0]} y={P2[1] + RING_R + 46} size={28} opacity={label1 * pictureLabelsOut} />

          {/* the symmetric object */}
          <Star cx={star[0]} cy={star[1]} r={starR * starIn} rot={f * 0.55} mix={rewire} opacity={starIn} glowPx={8 + 8 * arrivePulse + 6 * tickFlash} />

          {/* tags on the ladder */}
          <Tag x={lerp(960, LX, schematicPos)} y={lerp(860, 862, schematicPos)} text="schematic" opacity={schematicOp * tagsOut} />
          <Tag x={LX} y={214} text="from the note" opacity={fromNote * tagsOut} />
        </g>

        {/* ---------------- loupe: the dense ladder is still rungs ---------------- */}
        {loupe > 0 && (
          <g opacity={loupe * (1 - fin)}>
            <defs>
              <clipPath id="s08loupe">
                <circle cx={LOUPE[0]} cy={LOUPE[1]} r={LOUPE_R} />
              </clipPath>
            </defs>
            <line x1={LX + HALF + 4} y1={LOUPE[1]} x2={LOUPE[0] - LOUPE_R} y2={LOUPE[1]} stroke={colors.muted} strokeWidth={1.2} strokeDasharray="3 5" />
            <rect x={LX + HALF - 26} y={LOUPE[1] - 9} width={30} height={18} rx={4} fill="none" stroke={colors.fg} strokeOpacity={0.7} strokeWidth={1.4} />
            <circle cx={LOUPE[0]} cy={LOUPE[1]} r={LOUPE_R} fill={colors.bg} />
            <g clipPath="url(#s08loupe)">
              {Array.from({length: 15}, (_, i) => {
                const y = LOUPE[1] - LOUPE_R + 4 + i * loupeSpacing + ((f * 0.6) % loupeSpacing);
                return <line key={i} x1={LOUPE[0] - LOUPE_R} x2={LOUPE[0] + 40} y1={y} y2={y} stroke={colors.accent} strokeWidth={2.2} strokeOpacity={0.95} />;
              })}
              <line x1={LOUPE[0] + 40} x2={LOUPE[0] + 40} y1={LOUPE[1] - LOUPE_R} y2={LOUPE[1] + LOUPE_R} stroke={colors.fg} strokeOpacity={0.4} strokeWidth={1.4} />
            </g>
            <circle cx={LOUPE[0]} cy={LOUPE[1]} r={LOUPE_R} fill="none" stroke={colors.fg} strokeOpacity={0.75} strokeWidth={1.8} />
            <text x={LOUPE[0]} y={LOUPE[1] + LOUPE_R + 30} fontFamily={fonts.mono} fontSize={17} fill={colors.faint} textAnchor="middle">
              zoomed in
            </text>
          </g>
        )}

        {/* ---------------- multiplicity panel (beat 2) ---------------- */}
        <g opacity={multPanel}>
          <text x={PANEL_X} y={360} fontFamily={fonts.mono} fontSize={20} fill={colors.muted} letterSpacing="0.18em">
            MULTIPLICITY, MIMICKED
          </text>
          <text
            x={PANEL_X - 8}
            y={600}
            fontFamily={fonts.displayUpright}
            fontSize={230}
            fill={interpolateColors(tickFlash, [0, 1], [colors.fg, colors.accent])}
            style={{filter: glow(2 + 14 * tickFlash)}}
          >
            {multiplicity}
          </text>
          <RootGlyph x={1400} y={500} w={330} h={190} m={mSmooth} />
          <text x={1565} y={640} fontFamily={fonts.mono} fontSize={18} fill={colors.faint} textAnchor="middle">
            flatter at the root
          </text>
          <text x={PANEL_X} y={700} fontFamily={fonts.mono} fontSize={18} fill={colors.faint}>
            +1 per rung, per the note
          </text>
        </g>

        {/* ---------------- X gauge + sqrt(X) rungs (beat 3) ---------------- */}
        <g opacity={xPanel}>
          <text x={PANEL_X} y={300} fontFamily={fonts.mono} fontSize={20} fill={colors.muted}>
            X = length of the prime sum (von Mangoldt sum)
          </text>
          <text x={PANEL_X - 4} y={398} fontFamily={fonts.displayUpright} fontSize={84} fill={colors.fg}>
            <tspan fontFamily={fonts.display} fontStyle="italic">
              X
            </tspan>{' '}
            = {fmt(X)}
          </text>
          {/* log gauge 10^2 .. 10^6 */}
          {(() => {
            const gx0 = PANEL_X + 6;
            const gx1 = 1760;
            const gy = 448;
            const pos = (v: number) => gx0 + ((Math.log10(v) - 2) / 4) * (gx1 - gx0);
            const thumb = Math.max(gx0, pos(X));
            return (
              <g>
                <line x1={gx0} x2={gx1} y1={gy} y2={gy} stroke={colors.line} strokeWidth={3} strokeLinecap="round" />
                <line x1={gx0} x2={thumb} y1={gy} y2={gy} stroke={colors.accent} strokeWidth={3} strokeLinecap="round" />
                {[2, 3, 4, 5, 6].map((e) => (
                  <g key={e}>
                    <line x1={pos(10 ** e)} x2={pos(10 ** e)} y1={gy + 10} y2={gy + (e % 2 === 0 ? 20 : 15)} stroke={colors.faint} strokeWidth={1.5} />
                    {e % 2 === 0 && (
                      <text x={pos(10 ** e)} y={gy + 44} fontFamily={fonts.mono} fontSize={17} fill={colors.faint} textAnchor="middle">
                        {fmt(10 ** e)}
                      </text>
                    )}
                  </g>
                ))}
                <circle cx={thumb} cy={gy} r={9} fill={colors.accent} style={{filter: glow(8)}} />
              </g>
            );
          })()}
          <text x={PANEL_X} y={572} fontFamily={fonts.mono} fontSize={20} fill={colors.muted} letterSpacing="0.06em">
            rungs ≈{' '}
            <tspan fill={interpolateColors(sqrtFlash, [0, 1], [colors.muted, colors.accent])}>
              √X
            </tspan>
          </text>
          <text x={PANEL_X - 6} y={724} fontFamily={fonts.displayUpright} fontSize={156} fill={colors.accent} style={{filter: glow(6 + 6 * s3c)}}>
            {fmt(rungCount)}
          </text>
          <text x={PANEL_X} y={784} fontFamily={fonts.mono} fontSize={19} fill={colors.muted} opacity={Math.max(claudeAttr, xPanel)}>
            Claude's suggestion, per the note
          </text>
        </g>

        {/* ---------------- finale: the chairs quote ---------------- */}
        <g>
          <text x={846} y={500} fontFamily={fonts.display} fontStyle="italic" fontSize={260} fill={colors.accent} opacity={qMark * 0.55} style={{filter: glow(10)}}>
            “
          </text>
          <g fontFamily={fonts.display} fontStyle="italic" fontSize={70} fill={colors.fg}>
            <text x={980} y={440} opacity={q1} transform={`translate(0,${(1 - q1) * 14})`}>
              <tspan fill={colors.accent}>one line</tspan> which will suffice
            </text>
            <text x={980} y={526} opacity={q2} transform={`translate(0,${(1 - q2) * 14})`}>
              to make fellow mathematicians
            </text>
            <text x={980} y={612} opacity={q3} transform={`translate(0,${(1 - q3) * 14})`}>
              fall out of their chairs”
            </text>
          </g>
          <text x={984} y={690} fontFamily={fonts.mono} fontSize={20} fill={colors.muted} letterSpacing="0.06em" opacity={qAttr}>
            Alpöge, Nov 20 note
          </text>
        </g>
      </svg>
    </SceneFrame>
  );
};

// keep END referenced for future tail tweaks
void END;
