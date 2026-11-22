import React from 'react';
import {colors, fonts, glow} from '../../theme';

export type Pt = [number, number];

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const lerpPt = (a: Pt, b: Pt, t: number): Pt => [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];

/** Point on a quadratic bezier. */
export const qPoint = (p0: Pt, c: Pt, p2: Pt, t: number): Pt => {
  const u = 1 - t;
  return [u * u * p0[0] + 2 * u * t * c[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * c[1] + t * t * p2[1]];
};
export const qPath = (p0: Pt, c: Pt, p2: Pt) =>
  `M${p0[0].toFixed(1)},${p0[1].toFixed(1)} Q${c[0].toFixed(1)},${c[1].toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;

/** Thousands separators, deterministic. */
export const fmt = (n: number) => String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ',');

/**
 * A highly symmetric object: 7 points on a circle joined as a star polygon.
 * `step` 2 -> {7/2}, 3 -> {7/3}; `mix` cross-fades from step a to step b.
 * Same vertex count throughout, so nothing suggests a "bigger" object.
 */
export const Star: React.FC<{cx: number; cy: number; r: number; rot: number; mix: number; opacity?: number; glowPx?: number}> = ({
  cx,
  cy,
  r,
  rot,
  mix,
  opacity = 1,
  glowPx = 8,
}) => {
  const n = 7;
  const pts: Pt[] = Array.from({length: n}, (_, k) => {
    const a = ((rot - 90) * Math.PI) / 180 + (k * 2 * Math.PI) / n;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  });
  const poly = (step: number) => {
    let d = '';
    let k = 0;
    for (let i = 0; i <= n; i++) {
      d += `${i === 0 ? 'M' : 'L'}${pts[k][0].toFixed(2)},${pts[k][1].toFixed(2)} `;
      k = (k + step) % n;
    }
    return d + 'Z';
  };
  const sw = Math.max(1.2, r * 0.045);
  return (
    <g opacity={opacity} style={{filter: glow(glowPx)}}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={colors.accent} strokeOpacity={0.25} strokeWidth={sw * 0.7} />
      <path d={poly(2)} fill="none" stroke={colors.accent} strokeWidth={sw} strokeLinejoin="round" opacity={1 - mix} />
      <path d={poly(3)} fill="none" stroke={colors.accent} strokeWidth={sw} strokeLinejoin="round" opacity={mix} />
      {pts.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={Math.max(2, r * 0.085)} fill={colors.fg} />
      ))}
    </g>
  );
};

/** Mono group label U(X_k) with a real subscript. */
export const GroupLabel: React.FC<{k: number | string; x: number; y: number; anchor?: 'start' | 'middle' | 'end'; size?: number; opacity?: number; fill?: string}> = ({
  k,
  x,
  y,
  anchor = 'middle',
  size = 24,
  opacity = 1,
  fill = colors.muted,
}) => (
  <text x={x} y={y} fontFamily={fonts.mono} fontSize={size} fill={fill} textAnchor={anchor} opacity={opacity}>
    U(X
    <tspan dy={size * 0.3} fontSize={size * 0.7} fontFamily={fonts.body}>
      {k}
    </tspan>
    <tspan dy={-size * 0.3}>)</tspan>
  </text>
);

/** Small rounded mono tag (honesty labels). */
export const Tag: React.FC<{x: number; y: number; text: string; opacity: number; anchor?: 'start' | 'middle' | 'end'; size?: number}> = ({
  x,
  y,
  text,
  opacity,
  anchor = 'middle',
  size = 21,
}) => {
  const w = text.length * size * 0.6 + 28; // DM Mono advance is 0.6em
  const h = size + 18;
  const left = anchor === 'middle' ? x - w / 2 : anchor === 'end' ? x - w : x;
  return (
    <g opacity={opacity}>
      <rect x={left} y={y - h / 2} width={w} height={h} rx={h / 2} fill="rgba(17,15,13,0.6)" stroke={colors.line} strokeWidth={1.2} />
      <text x={left + w / 2} y={y + size * 0.34} fontFamily={fonts.mono} fontSize={size} fill={colors.muted} textAnchor="middle">
        {text}
      </text>
    </g>
  );
};

/**
 * Tiny root glyph: y = x^m near a root. Higher m -> the curve hugs the axis longer
 * (a flatter touch-down). Non-integer m blends the two neighbouring powers.
 */
export const RootGlyph: React.FC<{x: number; y: number; w: number; h: number; m: number; opacity?: number}> = ({x, y, w, h, m, opacity = 1}) => {
  const lo = Math.floor(m);
  const hi = Math.ceil(m);
  const fr = m - lo;
  const N = 90;
  let d = '';
  for (let i = 0; i <= N; i++) {
    const u = -1 + (2 * i) / N;
    const v = (1 - fr) * Math.pow(u, lo) + fr * Math.pow(u, hi);
    const px = x + ((u + 1) / 2) * w;
    const py = y - v * (h * 0.46);
    d += `${i === 0 ? 'M' : 'L'}${px.toFixed(1)},${py.toFixed(1)} `;
  }
  return (
    <g opacity={opacity}>
      <line x1={x - 10} x2={x + w + 10} y1={y} y2={y} stroke={colors.line} strokeWidth={1.5} />
      <defs>
        <clipPath id="rootclip">
          <rect x={x - 12} y={y - h / 2} width={w + 24} height={h} />
        </clipPath>
      </defs>
      <path d={d} fill="none" stroke={colors.fg} strokeWidth={2.6} clipPath="url(#rootclip)" />
      <circle cx={x + w / 2} cy={y} r={5.5} fill={colors.accent} style={{filter: glow(6)}} />
    </g>
  );
};
