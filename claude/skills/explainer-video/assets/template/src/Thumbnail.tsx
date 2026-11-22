import React from 'react';
import {AbsoluteFill} from 'remotion';
import {colors, fonts, glow} from './theme';
import timelineJson from './data/timeline.json';

// Cover image / poster (1920x1080). Text comes from script.json "meta". Replace the motif on the right with
// the topic's own visual drawn from real data (the worked example plots zeta zeros and an explicit-formula band).
type Meta = {title?: string; subtitle?: string; kicker?: string; attribution?: string};
const meta: Meta = (timelineJson as {meta?: Meta}).meta ?? {};

const WAVES = Array.from({length: 5}, (_, k) => {
  const pts: string[] = [];
  for (let i = 0; i <= 120; i++) {
    const x = 1080 + i * 7;
    const y = 540 + Math.sin(i * (0.09 + k * 0.035) + k) * (70 + k * 28) * Math.exp(-((i - 60) ** 2) / 4200);
    pts.push(`${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`);
  }
  return pts.join(' ');
});

export const Thumbnail: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: colors.bg, fontVariantNumeric: 'lining-nums', fontFeatureSettings: '"lnum" 1'}}>
    <AbsoluteFill style={{background: `radial-gradient(900px 1000px at 78% 50%, ${colors.accentSoft} 0%, transparent 62%), radial-gradient(1500px 1200px at 40% 50%, transparent 50%, ${colors.vignette} 100%)`}} />
    <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
      <defs>
        <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
          <path d="M48 0H0V48" fill="none" stroke={colors.line} strokeOpacity={0.5} strokeWidth={1} />
        </pattern>
      </defs>
      <rect width={1920} height={1080} fill="url(#grid)" opacity={0.35} />
      {WAVES.map((d, k) => (
        <path key={k} d={d} fill="none" stroke={k === 0 ? colors.accent : colors.muted} strokeWidth={k === 0 ? 5 : 2} opacity={k === 0 ? 1 : 0.45} style={k === 0 ? {filter: glow(10)} : undefined} />
      ))}
    </svg>
    <div style={{position: 'absolute', left: 110, top: 170, width: 1000, display: 'flex', flexDirection: 'column', gap: 26}}>
      {meta.kicker && <div style={{fontFamily: fonts.mono, fontSize: 30, letterSpacing: '0.16em', textTransform: 'uppercase', color: colors.accent}}>{meta.kicker}</div>}
      <div style={{fontFamily: fonts.display, fontStyle: fonts.displayStyle, fontSize: 168, lineHeight: 0.95, letterSpacing: '-0.025em', color: colors.fg, textWrap: 'balance'}}>
        {meta.title ?? 'Untitled explainer'}
      </div>
      {meta.subtitle && <div style={{fontFamily: fonts.display, fontStyle: fonts.displayStyle, fontSize: 72, lineHeight: 1.05, color: colors.accent}}>{meta.subtitle}</div>}
      {meta.attribution && <div style={{fontFamily: fonts.body, fontSize: 34, lineHeight: 1.35, color: colors.muted, marginTop: 10}}>{meta.attribution}</div>}
    </div>
  </AbsoluteFill>
);
