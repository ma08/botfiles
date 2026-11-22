import {loadFont as loadCormorant} from '@remotion/google-fonts/CormorantGaramond';
import {loadFont as loadDMSans} from '@remotion/google-fonts/DMSans';
import {loadFont as loadDMMono} from '@remotion/google-fonts/DMMono';

// Zone night: Zone brand type + orange accent on warm black.
const cormorant = loadCormorant('italic', {weights: ['400', '500'], subsets: ['latin', 'latin-ext']});
const cormorantUpright = loadCormorant('normal', {weights: ['400', '500'], subsets: ['latin', 'latin-ext']});
const dmSans = loadDMSans('normal', {weights: ['300', '400', '500'], subsets: ['latin', 'latin-ext']});
const dmMono = loadDMMono('normal', {weights: ['400'], subsets: ['latin', 'latin-ext']});

export const fonts = {
  display: cormorant.fontFamily, // use with fontStyle: 'italic'
  displayUpright: cormorantUpright.fontFamily,
  body: dmSans.fontFamily,
  mono: dmMono.fontFamily,
};

export const colors = {
  bg: '#110f0d',
  bgRaised: '#1a1714',
  fg: '#f2ede4',
  muted: '#8f887d',
  faint: '#5d574f',
  line: '#3a352f',
  accent: '#ff6a1a',
  accentSoft: 'rgba(255,106,26,0.14)',
  accentGlow: 'rgba(255,110,40,0.85)',
  good: '#9fd38a',
  pending: '#e8c46a',
  missing: '#c9837a',
  strip: 'rgba(255,106,26,0.07)',
};

export const glow = (px = 10, c = colors.accentGlow) => `drop-shadow(0 0 ${px}px ${c})`;

export const VIDEO = {width: 1920, height: 1080, fps: 30};

// Layout grid
export const grid = {
  marginX: 120,
  kickerY: 110,
  titleY: 150,
  safeBottom: 160, // keep content above the caption area
};
