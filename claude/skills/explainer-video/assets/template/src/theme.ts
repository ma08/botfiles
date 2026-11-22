import {loadFont as loadInstrumentSerif} from '@remotion/google-fonts/InstrumentSerif';
import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
import {loadFont as loadJetBrainsMono} from '@remotion/google-fonts/JetBrainsMono';
import {loadFont as loadCormorant} from '@remotion/google-fonts/CormorantGaramond';
import {loadFont as loadDMSans} from '@remotion/google-fonts/DMSans';
import {loadFont as loadDMMono} from '@remotion/google-fonts/DMMono';
import {loadFont as loadNewsreader} from '@remotion/google-fonts/Newsreader';
import {loadFont as loadPlexSans} from '@remotion/google-fonts/IBMPlexSans';
import {loadFont as loadPlexMono} from '@remotion/google-fonts/IBMPlexMono';

/**
 * Theme presets. Pick one with PRESET below (scripts/new_project.py --theme rewrites that line),
 * or add your own preset / map a project's existing design system onto these token names.
 * Every scene reads colors and fonts from `colors` and `fonts`, so switching presets restyles the whole video.
 */
export type PresetName = 'ink' | 'zone-night' | 'paper' | 'observatory';
export const PRESET: PresetName = 'ink';

type Palette = {
  bg: string; // page background
  bgRaised: string; // cards, panels
  fg: string; // primary text
  muted: string; // secondary text, labels
  faint: string; // tertiary text, minor ticks
  line: string; // rules, axes, borders
  accent: string; // the one highlight color
  accentSoft: string; // accent at low alpha (fills, focus)
  accentGlow: string; // accent for drop-shadow glows
  strip: string; // very faint accent fill (bands, regions)
  good: string; // semantic: pass
  pending: string; // semantic: in progress
  missing: string; // semantic: absent / fail
  vignette: string; // edge darkening/lightening color at full strength
};

type FontSet = {display: string; displayStyle: 'italic' | 'normal'; body: string; mono: string};

const PALETTES: Record<PresetName, Palette> = {
  // Neutral default: cool near-black, warm off-white text, clear blue accent.
  ink: {
    bg: '#0f1115', bgRaised: '#171a20', fg: '#ebe8e1', muted: '#8d929b', faint: '#5b606a', line: '#2c3038',
    accent: '#4fb3ff', accentSoft: 'rgba(79,179,255,0.14)', accentGlow: 'rgba(79,179,255,0.8)', strip: 'rgba(79,179,255,0.07)',
    good: '#8fd19c', pending: '#e8c46a', missing: '#d48a80', vignette: 'rgba(0,0,0,0.5)',
  },
  // The look of the worked example (Zone's brand type and orange on warm black).
  'zone-night': {
    bg: '#110f0d', bgRaised: '#1a1714', fg: '#f2ede4', muted: '#8f887d', faint: '#5d574f', line: '#3a352f',
    accent: '#ff6a1a', accentSoft: 'rgba(255,106,26,0.14)', accentGlow: 'rgba(255,110,40,0.85)', strip: 'rgba(255,106,26,0.07)',
    good: '#9fd38a', pending: '#e8c46a', missing: '#c9837a', vignette: 'rgba(0,0,0,0.45)',
  },
  // Light, editorial.
  paper: {
    bg: '#f5f2ea', bgRaised: '#ffffff', fg: '#18181b', muted: '#5f5b54', faint: '#a19c92', line: '#ddd7cc',
    accent: '#c2410c', accentSoft: 'rgba(194,65,12,0.12)', accentGlow: 'rgba(194,65,12,0.35)', strip: 'rgba(194,65,12,0.06)',
    good: '#2f7a3e', pending: '#a16207', missing: '#b4433a', vignette: 'rgba(120,100,70,0.18)',
  },
  // Deep navy with a warm gold accent.
  observatory: {
    bg: '#070b19', bgRaised: '#0e1530', fg: '#e9eefc', muted: '#7f8bab', faint: '#4d5878', line: '#26304d',
    accent: '#ffd27a', accentSoft: 'rgba(255,210,122,0.14)', accentGlow: 'rgba(255,214,130,0.9)', strip: 'rgba(127,212,255,0.06)',
    good: '#8fd19c', pending: '#ffd27a', missing: '#e0918a', vignette: 'rgba(0,0,0,0.5)',
  },
};

// All character subsets load (Greek, symbols, extended Latin). Display serifs often lack math glyphs such as √ ∑ ∏;
// use the components in src/components/Math.tsx for radicals and fractions instead of relying on font fallback.
const loadFontsFor = (p: PresetName): FontSet => {
  switch (p) {
    case 'zone-night':
      return {
        display: loadCormorant('italic', {weights: ['400', '500']}).fontFamily,
        displayStyle: 'italic',
        body: loadDMSans('normal', {weights: ['300', '400', '500']}).fontFamily,
        mono: loadDMMono('normal', {weights: ['400']}).fontFamily,
      };
    case 'paper':
      return {
        display: loadNewsreader('italic', {weights: ['400', '500']}).fontFamily,
        displayStyle: 'italic',
        body: loadPlexSans('normal', {weights: ['300', '400', '500']}).fontFamily,
        mono: loadPlexMono('normal', {weights: ['400']}).fontFamily,
      };
    case 'observatory':
      return {
        display: loadInstrumentSerif('italic', {weights: ['400']}).fontFamily,
        displayStyle: 'italic',
        body: loadPlexSans('normal', {weights: ['300', '400', '500']}).fontFamily,
        mono: loadPlexMono('normal', {weights: ['400']}).fontFamily,
      };
    case 'ink':
    default:
      return {
        display: loadInstrumentSerif('normal', {weights: ['400']}).fontFamily,
        displayStyle: 'normal',
        body: loadInter('normal', {weights: ['300', '400', '500']}).fontFamily,
        mono: loadJetBrainsMono('normal', {weights: ['400']}).fontFamily,
      };
  }
};

export const colors: Palette = PALETTES[PRESET];
export const fonts: FontSet = loadFontsFor(PRESET);

/** CSS/SVG drop-shadow glow in the accent color. */
export const glow = (px = 10, c = colors.accentGlow) => `drop-shadow(0 0 ${px}px ${c})`;

export const VIDEO = {width: 1920, height: 1080, fps: 30};

/** Layout grid for 1920x1080. Keep scene content above `safeBottom` so burned-in captions never cover it. */
export const grid = {marginX: 120, kickerY: 110, titleY: 150, safeBottom: 900};
