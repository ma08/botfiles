import React from 'react';
import {AbsoluteFill} from 'remotion';
import {colors, fonts, glow} from './theme';
import zeros from './data/zeros.json';
import explicit from './data/explicit.json';

// LinkedIn / X cover image, 1920x1080, Zone-night look. Every math element is drawn from real data:
// zeta zeros on the critical line, psi(x) rebuilt from 30 zeros (explicit formula), the first primes.
const GAMMAS: number[] = (zeros as {gammas: number[]}).gammas;
const EX = explicit as {x: number[]; psi: number[]; partials: Record<string, number[]>};

const STRIP = {x0: 1330, x1: 1730};
const T_MAX = 118;
const reX = (re: number) => STRIP.x0 + re * (STRIP.x1 - STRIP.x0);
const tY = (t: number) => 1040 - (t / T_MAX) * 1080;

const PRIMES = (() => {
  const out: number[] = [];
  for (let n = 2; out.length < 60; n++) if (out.every((p) => n % p !== 0)) out.push(n);
  return out;
})();

// explicit-formula band along the bottom
const BAND = {x0: 0, x1: 1920, y0: 760, y1: 1080};
const exX = (x: number) => BAND.x0 + ((x - EX.x[0]) / (EX.x[EX.x.length - 1] - EX.x[0])) * (BAND.x1 - BAND.x0);
const exY = (v: number) => BAND.y1 - 30 - (v / 42) * (BAND.y1 - BAND.y0 - 40);
const path = (ys: number[], step = false) =>
  EX.x
    .map((x, i) => {
      const X = exX(x).toFixed(1);
      const Y = exY(ys[i]).toFixed(1);
      if (i === 0) return `M${X},${Y}`;
      return step ? `H${X} V${Y}` : `L${X},${Y}`;
    })
    .join(' ');

export const Thumbnail: React.FC = () => {
  const shown = GAMMAS.filter((g) => g <= T_MAX);
  return (
    <AbsoluteFill style={{backgroundColor: colors.bg, fontFamily: fonts.body}}>
      {/* atmosphere: warm glow behind the strip, vignette */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(900px 1100px at 80% 45%, rgba(255,106,26,0.17) 0%, rgba(17,15,13,0) 62%), radial-gradient(1500px 1200px at 40% 50%, rgba(0,0,0,0) 50%, rgba(0,0,0,0.55) 100%)',
        }}
      />

      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        <defs>
          <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
            <path d="M48 0H0V48" fill="none" stroke="rgba(242,237,228,0.05)" strokeWidth={1} />
          </pattern>
          <linearGradient id="bandFade" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0" stopColor="#fff" stopOpacity="0.9" />
            <stop offset="0.55" stopColor="#fff" stopOpacity="1" />
            <stop offset="0.68" stopColor="#fff" stopOpacity="0" />
          </linearGradient>
          <mask id="bandMask">
            <rect x={0} y={BAND.y0} width={1920} height={BAND.y1 - BAND.y0} fill="url(#bandFade)" />
          </mask>
        </defs>
        <rect width={1920} height={1080} fill="url(#grid)" />

        {/* top edge: the first primes */}
        <text x={-6} y={52} fontFamily={fonts.mono} fontSize={26} letterSpacing="0.06em" fill="rgba(242,237,228,0.22)">
          {PRIMES.join('  ')}
        </text>

        {/* explicit formula: psi(x) staircase and its rebuild from the first 30 zeros */}
        <g mask="url(#bandMask)" opacity={0.75}>
          <path d={path(EX.psi, true)} fill="none" stroke="rgba(242,237,228,0.30)" strokeWidth={2.5} />
          <path d={path(EX.partials['30'])} fill="none" stroke={colors.accent} strokeWidth={3} opacity={0.55} style={{filter: glow(5)}} />
        </g>
        <text x={110} y={1052} fontFamily={fonts.mono} fontSize={22} fill="rgba(242,237,228,0.5)">
          ψ(x), rebuilt from the first 30 zeros
        </text>

        {/* critical strip with real zeros */}
        <rect x={reX(0)} y={0} width={reX(1) - reX(0)} height={1080} fill="rgba(255,106,26,0.07)" />
        <line x1={reX(0)} y1={0} x2={reX(0)} y2={1080} stroke={colors.line} strokeWidth={2} />
        <line x1={reX(1)} y1={0} x2={reX(1)} y2={1080} stroke={colors.line} strokeWidth={2} />
        <line x1={reX(0.5)} y1={0} x2={reX(0.5)} y2={1080} stroke={colors.accent} strokeWidth={4} style={{filter: glow(8)}} />
        {shown.map((g) => (
          <circle key={g} cx={reX(0.5)} cy={tY(g)} r={10} fill="#ff8a3d" style={{filter: glow(14)}} />
        ))}
        {shown.slice(0, 4).map((g) => (
          <text key={`l${g}`} x={reX(0.5) + 24} y={tY(g) + 8} fontFamily={fonts.mono} fontSize={22} fill="rgba(242,237,228,0.55)">
            1/2 + {g.toFixed(2)}i
          </text>
        ))}
        <circle cx={reX(0.84)} cy={tY(66)} r={15} fill="none" stroke={colors.muted} strokeWidth={3} strokeDasharray="7 8" />
        <text x={reX(0.84) + 28} y={tY(66) + 18} fontFamily={fonts.display} fontStyle="italic" fontSize={64} fill={colors.muted}>
          ?
        </text>
        <text x={reX(0.5) - 18} y={1010} fontFamily={fonts.mono} fontSize={26} fill={colors.accent} textAnchor="end">
          Re(s) = 1/2
        </text>
      </svg>

      {/* Euler product, floating over the strip's upper left */}
      <div
        style={{
          position: 'absolute',
          left: 1060,
          top: 104,
          padding: '14px 26px',
          borderRadius: 14,
          background: 'rgba(17,15,13,0.96)',
          border: `1.5px solid ${colors.line}`,
          fontFamily: fonts.displayUpright,
          fontSize: 50,
          color: colors.fg,
          whiteSpace: 'nowrap',
          fontVariantNumeric: 'lining-nums',
          fontFeatureSettings: '"lnum" 1',
        }}
      >
        <i style={{fontFamily: fonts.display}}>ζ</i>(<i style={{fontFamily: fonts.display}}>s</i>) = Σ 1/<i style={{fontFamily: fonts.display}}>n</i>
        <sup style={{fontSize: 30}}>
          <i>s</i>
        </sup>{' '}
        = ∏<sub style={{fontSize: 28}}>
          <i>p</i>
        </sub>{' '}
        (1 − <i style={{fontFamily: fonts.display}}>p</i>
        <sup style={{fontSize: 30}}>
          −<i>s</i>
        </sup>
        )<sup style={{fontSize: 30}}>−1</sup>
      </div>

      {/* left column: title and attribution */}
      <div style={{position: 'absolute', left: 110, top: 128, width: 1000, display: 'flex', flexDirection: 'column'}}>
        <div style={{fontFamily: fonts.mono, fontSize: 30, letterSpacing: '0.16em', textTransform: 'uppercase', color: colors.accent}}>
          A claimed proof · Nov 20, 2026
        </div>
        <div
          style={{
            fontFamily: fonts.display,
            fontStyle: 'italic',
            fontWeight: 500,
            fontSize: 176,
            lineHeight: 0.92,
            letterSpacing: '-0.025em',
            color: colors.fg,
            marginTop: 26,
          }}
        >
          The Riemann
          <br />
          Hypothesis
        </div>
        <div style={{fontFamily: fonts.display, fontStyle: 'italic', fontSize: 76, lineHeight: 1, color: colors.accent, marginTop: 22}}>
          explained in 5 minutes
        </div>
        <div style={{fontFamily: fonts.body, fontSize: 34, lineHeight: 1.35, color: colors.muted, marginTop: 30}}>
          Claimed by <span style={{color: colors.fg, fontWeight: 500}}>Levent Alpöge</span> (Anthropic),
          <br />
          working with <span style={{color: colors.fg, fontWeight: 500}}>Claude</span>
        </div>
        <div
          style={{
            marginTop: 30,
            alignSelf: 'flex-start',
            borderRadius: 12,
            border: `1.5px solid ${colors.line}`,
            background: 'rgba(26,23,20,0.9)',
            padding: '14px 22px 12px',
            fontFamily: fonts.mono,
          }}
        >
          <div style={{fontSize: 26, color: colors.fg, whiteSpace: 'nowrap'}}>
            <span style={{color: colors.accent}}>theorem</span> riemannHypothesis : RiemannHypothesis
          </div>
          <div style={{fontSize: 20, color: colors.muted, marginTop: 8, letterSpacing: '0.02em'}}>
            Lean · 17.4M lines · 0 comments · 6+ independent checkers accept
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
