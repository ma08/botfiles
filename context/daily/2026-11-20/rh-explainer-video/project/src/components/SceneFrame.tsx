import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {colors, fonts, grid} from '../theme';
import {enter, exit} from '../lib/anim';

/**
 * Shared scene chrome: warm-black background with a soft vignette and film grain,
 * a mono kicker ("03 · THE ZEROS"), and a fade in/out at the scene edges.
 */
export const SceneFrame: React.FC<{
  index: number;
  kicker: string;
  children: React.ReactNode;
  fadeIn?: number;
  fadeOut?: number;
  hideKicker?: boolean;
  /** Fully visible from frame 0 (no fade-in, kicker already in place). Used by the first scene so the poster frame isn't black. */
  instant?: boolean;
}> = ({index, kicker, children, fadeIn = 12, fadeOut = 12, hideKicker, instant}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const inT = instant ? 1 : Math.min(1, frame / fadeIn);
  const outT = exit(frame, durationInFrames - fadeOut, fadeOut);
  return (
    <AbsoluteFill style={{backgroundColor: colors.bg, opacity: Math.min(inT, outT)}}>
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(1400px 900px at 68% 42%, rgba(255,106,26,0.055) 0%, rgba(17,15,13,0) 60%), radial-gradient(1200px 1200px at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%)',
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

/** Static, cheap film grain via SVG turbulence (subtle). */
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

/** Big italic display title, Zone style. */
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
        fontStyle: 'italic',
        fontWeight: 400,
        fontSize: size,
        lineHeight: 1.02,
        letterSpacing: '-0.02em',
        color: colors.fg,
        ...enter(frame, start, 22, 22),
      }}
    >
      {children}
    </div>
  );
};

/** Muted body copy block. */
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

/** Inline emphasis inside Body. */
export const Em: React.FC<{children: React.ReactNode; accent?: boolean}> = ({children, accent}) => (
  <span style={{color: accent ? colors.accent : colors.fg, fontWeight: 500}}>{children}</span>
);

/** Small mono label. */
export const Label: React.FC<{children: React.ReactNode; style?: React.CSSProperties}> = ({children, style}) => (
  <span style={{fontFamily: fonts.mono, fontSize: 20, color: colors.muted, letterSpacing: '0.02em', ...style}}>{children}</span>
);
