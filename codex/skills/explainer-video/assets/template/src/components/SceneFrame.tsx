import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {colors, fonts, grid} from '../theme';
import {enter, exit} from '../lib/anim';

/**
 * Shared scene chrome: themed background with a soft accent glow and vignette, faint film grain,
 * a mono kicker ("03 · THE ZEROS"), and a fade at the scene edges (scenes dip through the background color).
 * Pass `instant` on the first scene so frame 0 (the poster frame many platforms show) isn't blank.
 */
export const SceneFrame: React.FC<{
  index: number;
  kicker: string;
  children: React.ReactNode;
  fadeIn?: number;
  fadeOut?: number;
  hideKicker?: boolean;
  instant?: boolean;
}> = ({index, kicker, children, fadeIn = 12, fadeOut = 12, hideKicker, instant}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const inT = instant ? 1 : Math.min(1, frame / Math.max(1, fadeIn));
  const outT = exit(frame, durationInFrames - fadeOut, fadeOut);
  return (
    <AbsoluteFill style={{backgroundColor: colors.bg, opacity: Math.min(inT, outT), fontVariantNumeric: 'lining-nums', fontFeatureSettings: '"lnum" 1'}}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(1400px 900px at 68% 42%, ${colors.strip} 0%, transparent 60%), radial-gradient(1200px 1200px at 50% 50%, transparent 55%, ${colors.vignette} 100%)`,
        }}
      />
      {!hideKicker && (
        <div
          style={{
            position: 'absolute',
            left: grid.marginX,
            top: grid.kickerY - 10,
            fontFamily: fonts.mono,
            fontSize: 22,
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            color: colors.accent,
            ...(instant ? {} : enter(frame, 4, 16, 8)),
          }}
        >
          {String(index).padStart(2, '0')} · {kicker}
        </div>
      )}
      {children}
      <Grain />
    </AbsoluteFill>
  );
};

/** Static, cheap film grain via SVG turbulence. */
const Grain: React.FC = () => (
  <AbsoluteFill style={{pointerEvents: 'none', opacity: 0.06, mixBlendMode: 'overlay'}}>
    <svg width="100%" height="100%">
      <filter id="grain">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" />
      </filter>
      <rect width="100%" height="100%" filter="url(#grain)" />
    </svg>
  </AbsoluteFill>
);

/** Large display title. */
export const Title: React.FC<{children: React.ReactNode; start?: number; size?: number; top?: number; left?: number; width?: number}> = ({
  children,
  start = 8,
  size = 92,
  top = grid.titleY,
  left = grid.marginX,
  width = 980,
}) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        position: 'absolute',
        left,
        top,
        width,
        fontFamily: fonts.display,
        fontStyle: fonts.displayStyle,
        fontWeight: 400,
        fontSize: size,
        lineHeight: 1.02,
        letterSpacing: '-0.02em',
        color: colors.fg,
        textWrap: 'balance',
        ...enter(frame, start, 22, 22),
      }}
    >
      {children}
    </div>
  );
};

/** Muted body copy. Keep on-screen text short: labels, numbers and honesty tags, not the narration. */
export const Body: React.FC<{children: React.ReactNode; start: number; top: number; left?: number; width?: number; size?: number}> = ({
  children,
  start,
  top,
  left = grid.marginX + 4,
  width = 760,
  size = 32,
}) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        position: 'absolute',
        left,
        top,
        width,
        fontFamily: fonts.body,
        fontWeight: 300,
        fontSize: size,
        lineHeight: 1.45,
        color: colors.muted,
        ...enter(frame, start, 18, 14),
      }}
    >
      {children}
    </div>
  );
};

export const Em: React.FC<{children: React.ReactNode; accent?: boolean}> = ({children, accent}) => (
  <span style={{color: accent ? colors.accent : colors.fg, fontWeight: 500}}>{children}</span>
);

/**
 * Small rounded honesty tag ("schematic", "from the note", "our reading"). 21px minimum so it reads on a phone.
 * Inline by default; position it with style={{position: 'absolute', left, top}}.
 */
export const Tag: React.FC<{children: React.ReactNode; style?: React.CSSProperties}> = ({children, style}) => (
  <span
    style={{
      display: 'inline-block',
      fontFamily: fonts.mono,
      fontSize: 21,
      color: colors.muted,
      border: `1px solid ${colors.line}`,
      background: colors.bgRaised,
      padding: '6px 14px',
      borderRadius: 999,
      whiteSpace: 'nowrap',
      ...style,
    }}
  >
    {children}
  </span>
);
