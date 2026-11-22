import {Easing, interpolate, spring} from 'remotion';

export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** 0 -> 1 between frames [start, start + dur], eased. */
export const ramp = (frame: number, start: number, dur = 18, ease = Easing.out(Easing.cubic)) =>
  interpolate(frame, [start, start + dur], [0, 1], {...clamp, easing: ease});

/**
 * Fade + slight rise for an element entering at `start`. Spread into a style object; pass `opacity` here
 * (as the base) instead of alongside the spread, which would be overwritten.
 */
export const enter = (frame: number, start: number, dur = 18, rise = 18, opacity = 1) => {
  const t = ramp(frame, start, dur);
  return {opacity: t * opacity, transform: `translateY(${(1 - t) * rise}px)`};
};

/** 1 -> 0 between frames [start, start + dur]. */
export const exit = (frame: number, start: number, dur = 12) => 1 - ramp(frame, start, dur, Easing.in(Easing.cubic));

export const springIn = (frame: number, fps: number, start: number, damping = 18) =>
  spring({frame: frame - start, fps, config: {damping, mass: 0.8}});

/** Linear map for plots: scale(d0, d1, r0, r1)(v). */
export const scale = (d0: number, d1: number, r0: number, r1: number) => (v: number) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);

/** SVG path through the first `frac` (0..1) of the points: draw a line progressively. */
export const pathFrom = (pts: [number, number][], frac = 1) => {
  const n = Math.max(2, Math.floor(pts.length * Math.min(1, Math.max(0, frac))));
  return pts
    .slice(0, n)
    .map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`)
    .join(' ');
};

/** Staircase SVG path (for counting functions), progressive like pathFrom. */
export const stepPathFrom = (pts: [number, number][], frac = 1) => {
  const n = Math.max(2, Math.floor(pts.length * Math.min(1, Math.max(0, frac))));
  let d = '';
  for (let i = 0; i < n; i++) {
    const [x, y] = pts[i];
    d += i === 0 ? `M${x.toFixed(2)},${y.toFixed(2)}` : ` H${x.toFixed(2)} V${y.toFixed(2)}`;
  }
  return d;
};

/** Thousands separators without locale dependence (renders identically everywhere). */
export const fmt = (n: number) => Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
