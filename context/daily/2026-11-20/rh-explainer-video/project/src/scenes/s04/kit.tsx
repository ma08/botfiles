// Shared helpers for scenes s04 to s06 (owned by the s04/s05/s06 builder).
import React from 'react';
import {Easing, interpolate} from 'remotion';
import {loadFont as loadEBGaramond} from '@remotion/google-fonts/EBGaramond';
import {colors, fonts} from '../../theme';
import {clamp} from '../../lib/anim';
import {SceneTiming, wordFrame} from '../../lib/timeline';

// Greek letters (ψ, β, γ) are not in the theme's latin-only subsets, so math glyphs come from EB Garamond.
const eb = loadEBGaramond('italic', {weights: ['400', '500'], subsets: ['latin', 'greek']});
const ebUp = loadEBGaramond('normal', {weights: ['400', '500'], subsets: ['latin', 'greek']});

export const mathFont = `${eb.fontFamily}, serif`;
export const mathFontUp = `${ebUp.fontFamily}, serif`;

/** wordFrame that fails loudly when a word or its nth occurrence is missing (re-voicing safety). */
export const wf = (s: SceneTiming, needle: string, nth = 0) => {
  const norm = (t: string) => t.toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');
  const hits = s.words.filter((w) => norm(w.text) === norm(needle));
  if (hits.length <= nth) throw new Error(`[${s.id}] word "${needle}" #${nth} not found (${hits.length} hits)`);
  return wordFrame(s, needle, nth);
};

/** Opacity window: fade in at [a, a+din], fade out at [b, b+dout]. */
export const win = (f: number, a: number, din: number, b = Infinity, dout = 14) => {
  const i = interpolate(f, [a, a + din], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const o = b === Infinity ? 1 : interpolate(f, [b, b + dout], [1, 0], {...clamp, easing: Easing.in(Easing.cubic)});
  return Math.min(i, o);
};

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/** Thousands separators (commas) for on-screen numbers. */
export const fmt = (n: number) => Math.round(n).toLocaleString('en-US');

/** Small honesty pill, e.g. "schematic". */
export const Tag: React.FC<{children: React.ReactNode; style?: React.CSSProperties; opacity?: number}> = ({children, style, opacity = 1}) => (
  <div
    style={{
      position: 'absolute',
      fontFamily: fonts.mono,
      fontSize: 21,
      letterSpacing: '0.06em',
      color: colors.muted,
      border: `1px solid ${colors.line}`,
      padding: '6px 12px',
      borderRadius: 999,
      whiteSpace: 'nowrap',
      opacity,
      ...style,
    }}
  >
    {children}
  </div>
);

/** Inline math run (italic serif with Greek coverage). */
export const M: React.FC<{children: React.ReactNode; style?: React.CSSProperties; up?: boolean}> = ({children, style, up}) => (
  <span style={{fontFamily: up ? mathFontUp : mathFont, fontStyle: up ? 'normal' : 'italic', ...style}}>{children}</span>
);

/** Hand-drawn check mark (no font dependency). */
export const Check: React.FC<{size?: number; color?: string; progress?: number; style?: React.CSSProperties}> = ({
  size = 26,
  color = colors.good,
  progress = 1,
  style,
}) => {
  const len = 30;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" style={{overflow: 'visible', ...style}}>
      <path
        d="M4 12.5 L9.5 18 L20 6"
        fill="none"
        stroke={color}
        strokeWidth={2.6}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={len}
        strokeDashoffset={len * (1 - progress)}
      />
    </svg>
  );
};

/** Radical sign drawn as a stroke, followed by its radicand. */
export const Sqrt: React.FC<{children: React.ReactNode; color?: string; size?: number; style?: React.CSSProperties}> = ({
  children,
  color = 'currentColor',
  size = 1,
  style,
}) => (
  <span style={{display: 'inline-flex', alignItems: 'stretch', ...style}}>
    <svg width={0.62 * size + 'em'} height="1.05em" viewBox="0 0 13 22" preserveAspectRatio="none" style={{overflow: 'visible', marginRight: '0.02em'}}>
      <path d="M0.5 13 L3.6 11.4 L7 20.5 L12.6 0.8 L13.5 0.8" fill="none" stroke={color} strokeWidth={1.5} strokeLinejoin="round" strokeLinecap="round" />
    </svg>
    <span style={{borderTop: `0.075em solid ${color}`, paddingTop: '0.02em', paddingLeft: '0.04em', lineHeight: 0.95}}>{children}</span>
  </span>
);

/** Congruence sign (three bars) drawn as strokes. */
export const Equiv: React.FC<{color?: string}> = ({color = 'currentColor'}) => (
  <svg width="0.62em" height="0.62em" viewBox="0 0 12 12" style={{margin: '0 0.18em', verticalAlign: '0.02em'}}>
    {[2.4, 6, 9.6].map((y) => (
      <line key={y} x1={0.8} x2={11.2} y1={y} y2={y} stroke={color} strokeWidth={1.25} strokeLinecap="round" />
    ))}
  </svg>
);
