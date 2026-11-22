import React from 'react';
import {colors} from '../theme';

/**
 * Minimal math typesetting that doesn't depend on the display font having math glyphs.
 * Sizes follow the surrounding font-size (em units), so wrap in an element that sets fontFamily/fontSize.
 *
 *   <Radical>2</Radical>                 √2 with a proper vinculum (bar) over the radicand
 *   <Frac num="p" den="q" />             stacked fraction
 *   x<Sup>2</Sup>, a<Sub>n</Sub>         superscript / subscript
 */
export const Radical: React.FC<{children: React.ReactNode; color?: string; strokeWidth?: number}> = ({children, color = colors.fg, strokeWidth = 0.07}) => (
  <span style={{display: 'inline-flex', alignItems: 'stretch', lineHeight: 1}}>
    <svg viewBox="0 0 0.62 1.15" style={{height: '1.15em', width: '0.62em', overflow: 'visible', alignSelf: 'flex-end', marginBottom: '-0.12em'}}>
      <path d="M0.02 0.62 L0.14 0.55 L0.3 1.05 L0.58 0.04 L0.62 0.04" fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinejoin="round" strokeLinecap="round" />
    </svg>
    <span style={{borderTop: `${strokeWidth}em solid ${color}`, padding: '0.06em 0.08em 0 0.04em'}}>{children}</span>
  </span>
);

export const Frac: React.FC<{num: React.ReactNode; den: React.ReactNode; color?: string}> = ({num, den, color = colors.fg}) => (
  <span style={{display: 'inline-flex', flexDirection: 'column', alignItems: 'center', verticalAlign: 'middle', lineHeight: 1, margin: '0 0.12em', fontSize: '0.8em'}}>
    <span style={{padding: '0 0.15em 0.08em'}}>{num}</span>
    <span style={{alignSelf: 'stretch', borderTop: `0.06em solid ${color}`}} />
    <span style={{padding: '0.08em 0.15em 0'}}>{den}</span>
  </span>
);

export const Sup: React.FC<{children: React.ReactNode}> = ({children}) => (
  <sup style={{fontSize: '0.6em', lineHeight: 0, verticalAlign: '0.85em'}}>{children}</sup>
);

export const Sub: React.FC<{children: React.ReactNode}> = ({children}) => (
  <sub style={{fontSize: '0.6em', lineHeight: 0, verticalAlign: '-0.3em'}}>{children}</sub>
);
