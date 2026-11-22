import React from 'react';
import {Easing, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {SceneFrame, Title} from '../components/SceneFrame';
import {colors, fonts, glow} from '../theme';
import {ramp, scale} from '../lib/anim';
import {lineStartFrame, sceneById} from '../lib/timeline';
import curve from '../data/curve.json';
import {Check, M, lerp, wf, win} from './s04/kit';

const s = sceneById('s05_parallel');
const inOut = Easing.inOut(Easing.cubic);

const B = {
  parallel: wf(s, 'parallel'),
  where: wf(s, 'where', 0),
  theorem: wf(s, 'theorem'),
  polynomials: wf(s, 'polynomials'),
  finite: wf(s, 'finite'),
  becomes: wf(s, 'becomes'),
  counting: wf(s, 'counting'),
  curves: wf(s, 'curves', 0),
  line1: lineStartFrame(s, 1),
  proved: wf(s, 'proved'),
  y1940: wf(s, '1940s'),
  deligne: wf(s, 'deligne'),
  y1974: wf(s, '1974'),
  line2: lineStartFrame(s, 2),
  y1969: wf(s, '1969'),
  stepanov: wf(s, 'stepanov'),
  certain: wf(s, 'certain'),
};

// ---------------- left: whole numbers ----------------
const NL_N = 36;
const NLX0 = 160;
const NLX1 = 840;
const NLY = 560;
const nX = scale(1, NL_N, NLX0, NLX1);
const isPrime = (n: number) => {
  if (n < 2) return false;
  for (let d = 2; d * d <= n; d++) if (n % d === 0) return false;
  return true;
};

// ---------------- right: F_31 grid ----------------
const P = curve.p;
const GX0 = 1000;
const GY0 = 344;
const GS = 12.4;
const gX = (x: number) => GX0 + x * GS;
const gY = (y: number) => GY0 + (P - 1 - y) * GS;
const PTS = curve.points as [number, number][];
const LIGHT0 = B.counting - 2;
const LIGHT_STEP = 1.9;
const lightFrame = (i: number) => LIGHT0 + i * LIGHT_STEP;
const INF_FRAME = Math.round(lightFrame(PTS.length) + 8);

// gauge: count vs expected with the +-2 sqrt(p) bound
const GA0 = 16;
const GA1 = 48;
const gaX = scale(GA0, GA1, 1432, 1790);
const GAY = 660;
const EXPECTED = curve.expected;
const BOUND = curve.bound;
const COUNT = curve.count_projective;

// ---------------- timeline ----------------
const CHIPS = [
  {name: 'Weil', when: '1940s', x: 500, at: B.y1940},
  {name: 'Stepanov', when: '1969', x: 960, at: B.y1969},
  {name: 'Deligne', when: '1974', x: 1420, at: wf(s, 'Deligne')},
];
const TLY = 806;
const HONEST = [
  {text: 'Weil: curves over finite fields', at: B.y1940 + 6},
  {text: ' · Deligne: all dimensions', at: wf(s, 'Deligne') + 6},
  {text: ' · Stepanov: certain curves (Bombieri 1973: all curves)', at: B.stepanov + 12},
];

const Header: React.FC<{x: number; title: string; sub: string; f: number; at: number}> = ({x, title, sub, f, at}) => (
  <div style={{position: 'absolute', left: x, top: 270, opacity: ramp(f, at, 16), transform: `translateY(${(1 - ramp(f, at, 16)) * 10}px)`}}>
    <div style={{fontFamily: fonts.body, fontSize: 30, color: colors.fg, fontWeight: 400}}>{title}</div>
    <div style={{fontFamily: fonts.mono, fontSize: 18, color: colors.muted, marginTop: 4, letterSpacing: '0.02em'}}>{sub}</div>
  </div>
);

export const S05Parallel: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const panelDim = 1 - 0.45 * ramp(f, B.y1940 - 6, 20);
  const panelScale = 1 - 0.16 * ramp(f, B.y1940 - 12, 26, inOut);
  const leftDim = 1 - 0.35 * ramp(f, B.polynomials, 20);
  const lineDraw = ramp(f, B.parallel, 26, inOut);
  const lit = PTS.filter((_, i) => f >= lightFrame(i)).length;
  const infOn = ramp(f, INF_FRAME, 10);
  const shownCount = lit + (f >= INF_FRAME ? 1 : 0);
  const gaugeIn = ramp(f, INF_FRAME + 6, 18);
  const markerT = ramp(f, INF_FRAME + 16, 20, inOut);
  const insideOk = ramp(f, B.proved, 14);
  const chipsIn = ramp(f, B.y1940 - 10, 16);
  const stepanovHi = ramp(f, B.stepanov, 18);

  return (
    <SceneFrame index={5} kicker="A parallel world">
      <Title size={78}>A parallel world</Title>

      {/* ============ panels ============ */}
      <div style={{position: 'absolute', inset: 0, opacity: panelDim, transform: `scale(${panelScale})`, transformOrigin: '960px 262px'}}>
        {/* left */}
        <div style={{position: 'absolute', inset: 0, opacity: leftDim}}>
          <Header x={NLX0} title="whole numbers" sub="1, 2, 3, … with the primes marked" f={f} at={B.parallel - 4} />
        </div>
        <Header x={GX0} title="a finite field" sub="arithmetic mod 31, numbers 0 to 30" f={f} at={B.polynomials - 6} />

        <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
          {/* divider */}
          <line x1={915} x2={915} y1={290} y2={290 + 450 * ramp(f, B.parallel, 30, inOut)} stroke={colors.line} />

          {/* number line */}
          <g opacity={leftDim}>
            <line x1={NLX0 - 10} x2={lerp(NLX0 - 10, NLX1 + 30, lineDraw)} y1={NLY} y2={NLY} stroke={colors.faint} strokeWidth={1.5} />
            {Array.from({length: NL_N}, (_, i) => i + 1).map((n) => {
              const at = B.parallel + 4 + n * 1.5;
              const t = ramp(f, at, 8);
              const pr = isPrime(n);
              if (!pr) return <line key={n} x1={nX(n)} x2={nX(n)} y1={NLY - 8} y2={NLY + 8} stroke={colors.faint} strokeWidth={1.5} opacity={t} />;
              const sp = spring({frame: f - at, fps, config: {damping: 14, mass: 0.6}});
              return (
                <g key={n}>
                  <line
                    x1={nX(n)}
                    x2={nX(n)}
                    y1={NLY + 4}
                    y2={NLY - 4 - 64 * sp}
                    stroke={colors.accent}
                    strokeWidth={4}
                    strokeLinecap="round"
                    style={{filter: glow(6)}}
                    opacity={Math.min(1, sp * 1.5)}
                  />
                  <text x={nX(n)} y={NLY + 36} textAnchor="middle" fontFamily={fonts.mono} fontSize={18} fill={colors.fg} fillOpacity={0.75} opacity={t}>
                    {n}
                  </text>
                </g>
              );
            })}
            <text x={NLX1 + 40} y={NLY + 6} fontFamily={fonts.mono} fontSize={20} fill={colors.faint} opacity={lineDraw}>
              …
            </text>
          </g>

          {/* F_31 x F_31 grid */}
          {Array.from({length: P}, (_, x) =>
            Array.from({length: P}, (_, y) => {
              const t = ramp(f, B.finite - 8 + (x + (P - 1 - y)) * 0.75, 10);
              return t > 0 ? <circle key={`${x}-${y}`} cx={gX(x)} cy={gY(y)} r={1.7} fill={colors.muted} opacity={0.55 * t} /> : null;
            }),
          )}
          <g opacity={ramp(f, B.finite + 10, 16)} fontFamily={fonts.mono} fontSize={15} fill={colors.faint}>
            <text x={gX(0)} y={gY(0) + 28} textAnchor="middle">0</text>
            <text x={gX(30)} y={gY(0) + 28} textAnchor="middle">30</text>
            <text x={gX(0) - 16} y={gY(30) + 5} textAnchor="end">30</text>
            <text x={gX(15)} y={gY(0) + 30} textAnchor="middle" fontFamily={'inherit'} fontSize={18} fill={colors.muted}>
              x
            </text>
            <text x={gX(0) - 20} y={gY(15) + 6} textAnchor="end" fontSize={18} fill={colors.muted}>
              y
            </text>
          </g>
          {/* curve points lighting up */}
          {PTS.map(([x, y], i) => {
            const at = lightFrame(i);
            if (f < at) return null;
            const sp = spring({frame: f - at, fps, config: {damping: 12, mass: 0.5}});
            return <circle key={i} cx={gX(x)} cy={gY(y)} r={4.6 * Math.min(1.25, sp)} fill={colors.accent} style={{filter: glow(7)}} />;
          })}

          {/* gauge */}
          <g opacity={gaugeIn}>
            <line x1={gaX(GA0)} x2={gaX(GA1)} y1={GAY} y2={GAY} stroke={colors.faint} strokeWidth={1.5} />
            <rect
              x={gaX(EXPECTED - BOUND)}
              y={GAY - 12}
              width={gaX(EXPECTED + BOUND) - gaX(EXPECTED - BOUND)}
              height={24}
              fill={colors.accentSoft}
              stroke={colors.accent}
              strokeOpacity={0.55 + 0.45 * insideOk}
              rx={3}
            />
            <line x1={gaX(EXPECTED)} x2={gaX(EXPECTED)} y1={GAY - 18} y2={GAY + 18} stroke={colors.fg} strokeWidth={2} />
            <text x={gaX(EXPECTED)} y={GAY + 44} textAnchor="middle" fontFamily={fonts.mono} fontSize={17} fill={colors.muted}>
              expected 32
            </text>
            <g opacity={markerT}>
              <circle cx={lerp(gaX(EXPECTED), gaX(COUNT), markerT)} cy={GAY} r={8} fill={colors.accent} style={{filter: glow(8)}} />
              <text x={gaX(COUNT)} y={GAY - 26} textAnchor="middle" fontFamily={fonts.mono} fontSize={18} fill={colors.accent}>
                41
              </text>
            </g>
          </g>
        </svg>

        {/* theorem chip on the right */}
        <div
          style={{
            position: 'absolute',
            left: 1432,
            top: 278,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontFamily: fonts.mono,
            fontSize: 18,
            color: colors.good,
            border: `1px solid rgba(159,211,138,0.4)`,
            borderRadius: 999,
            padding: '6px 14px 6px 10px',
            opacity: win(f, B.theorem - 2, 12, B.becomes - 4, 12),
          }}
        >
          <Check size={20} progress={ramp(f, B.theorem + 2, 10)} />
          RH's analogue here: a theorem
        </div>

        {/* equation + counter column */}
        <div style={{position: 'absolute', left: 1432, top: 330, opacity: ramp(f, B.becomes - 2, 16)}}>
          <M up style={{fontSize: 46, color: colors.fg, whiteSpace: 'nowrap'}}>
            <i>y</i>² = <i>x</i>³ + <i>x</i> + 3
          </M>
          <div style={{fontFamily: fonts.mono, fontSize: 19, color: colors.muted, marginTop: 2}}>mod 31</div>
        </div>
        <div style={{position: 'absolute', left: 1432, top: 450, opacity: ramp(f, B.counting - 4, 12)}}>
          <div style={{fontFamily: fonts.mono, fontSize: 18, letterSpacing: '0.08em', textTransform: 'uppercase', color: colors.muted}}>points on the curve</div>
          <div style={{display: 'flex', alignItems: 'baseline', gap: 16}}>
            <div style={{fontFamily: fonts.display, fontStyle: 'italic', fontSize: 96, lineHeight: 1.02, color: colors.accent, width: 100}}>{shownCount}</div>
            <div style={{fontFamily: fonts.mono, fontSize: 16, color: colors.muted, opacity: infOn, lineHeight: 1.35}}>
              40 in the grid
              <br />+ 1 at infinity
            </div>
          </div>
        </div>
        {/* bound label */}
        <div
          style={{
            position: 'absolute',
            left: gaX(EXPECTED - BOUND),
            width: gaX(EXPECTED + BOUND) - gaX(EXPECTED - BOUND),
            top: GAY + 54,
            textAlign: 'center',
            opacity: gaugeIn,
            whiteSpace: 'nowrap',
          }}
        >
          <M up style={{fontSize: 26, color: colors.fg}}>
            ±2√31 ≈ 11.1
          </M>
        </div>
        <div
          style={{
            position: 'absolute',
            left: 1432,
            top: GAY - 70,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontFamily: fonts.mono,
            fontSize: 17,
            color: colors.good,
            opacity: insideOk,
          }}
        >
          <Check size={18} progress={ramp(f, B.proved + 4, 10)} /> inside the bound
        </div>
      </div>

      {/* ============ timeline ============ */}
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        <line x1={300} x2={lerp(300, 1620, ramp(f, B.y1940 - 10, 24, inOut))} y1={TLY} y2={TLY} stroke={colors.line} strokeWidth={1.5} opacity={chipsIn} />
        {CHIPS.map((c) => {
          const t = ramp(f, c.at - 4, 12);
          const hi = c.name === 'Stepanov' ? stepanovHi : 0;
          return (
            <g key={c.name} opacity={t}>
              <line x1={c.x} x2={c.x} y1={TLY - 18} y2={TLY} stroke={hi > 0.5 ? colors.accent : colors.faint} />
              <circle cx={c.x} cy={TLY} r={5 + 2 * hi} fill={hi > 0 ? colors.accent : colors.fg} style={hi > 0 ? {filter: glow(8 * hi)} : undefined} />
            </g>
          );
        })}
      </svg>
      {CHIPS.map((c) => {
        const t = ramp(f, c.at - 4, 12);
        const hi = c.name === 'Stepanov' ? stepanovHi : 0;
        const dimOthers = c.name === 'Stepanov' ? 1 : 1 - 0.4 * stepanovHi;
        return (
          <div
            key={c.name}
            style={{
              position: 'absolute',
              left: c.x,
              top: TLY - 74,
              transform: `translateX(-50%) translateY(${(1 - t) * 10}px) scale(${1 + 0.06 * hi})`,
              opacity: t * dimOthers,
              fontFamily: fonts.body,
              fontSize: 28,
              color: hi > 0.5 ? colors.accent : colors.fg,
              border: `1px solid ${hi > 0.5 ? colors.accent : colors.line}`,
              background: hi > 0.5 ? colors.accentSoft : colors.bgRaised,
              borderRadius: 999,
              padding: '8px 22px',
              whiteSpace: 'nowrap',
            }}
          >
            {c.name} <span style={{fontFamily: fonts.mono, fontSize: 22, color: colors.muted}}>· {c.when}</span>
          </div>
        );
      })}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: TLY + 32,
          textAlign: 'center',
          fontFamily: fonts.mono,
          fontSize: 19,
          color: colors.muted,
          whiteSpace: 'nowrap',
        }}
      >
        {HONEST.map((h, i) => (
          <span key={i} style={{opacity: ramp(f, h.at, 14), color: i === 2 ? lerpColor(stepanovHi) : undefined}}>
            {h.text}
          </span>
        ))}
      </div>
    </SceneFrame>
  );
};

const lerpColor = (t: number) => (t > 0.5 ? colors.fg : colors.muted);
