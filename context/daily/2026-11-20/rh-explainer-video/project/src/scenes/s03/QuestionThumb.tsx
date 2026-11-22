import React from 'react';
import {colors, fonts} from '../../theme';
import {band, li, PI_MAX_X, primePi} from '../s02/primeMath';

// Miniature of the end of scene 2 (pi(x), li(x), the band, and the open question),
// real data, used to show "that question" being tied to zeta.
const W = 600;
const H = 290;
const XMAX = 2.0e6;
const YMAX = li(XMAX) * 1.12;
const X = (x: number) => (x / XMAX) * W;
const Y = (y: number) => H - (y / YMAX) * H;

const build = () => {
  let stair = `M0,${H}`;
  const N = 300;
  for (let i = 1; i <= N; i++) {
    const x = (PI_MAX_X * i) / N;
    stair += ` H${X(x).toFixed(1)} V${Y(primePi(x)).toFixed(1)}`;
  }
  const up: string[] = [];
  const lo: string[] = [];
  const liSolid: string[] = [];
  const liDash: string[] = [];
  for (let i = 0; i <= 160; i++) {
    const x = 2 + ((XMAX - 2) * i) / 160;
    const v = li(x);
    const b = band(x);
    up.push(`${X(x).toFixed(1)},${Y(v + b).toFixed(1)}`);
    lo.push(`${X(x).toFixed(1)},${Y(v - b).toFixed(1)}`);
    (x <= PI_MAX_X ? liSolid : liDash).push(`${X(x).toFixed(1)},${Y(v).toFixed(1)}`);
  }
  liDash.unshift(liSolid[liSolid.length - 1]);
  return {
    stair,
    band: `M${up.join(' L')} L${lo.reverse().join(' L')} Z`,
    liSolid: `M${liSolid.join(' L')}`,
    liDash: `M${liDash.join(' L')}`,
  };
};
const P = build();

export const QuestionThumb: React.FC<{left: number; top: number; opacity: number; scale?: number}> = ({left, top, opacity, scale = 1}) => (
  <div style={{position: 'absolute', left, top, width: W, height: H, opacity, transform: `scale(${scale})`, transformOrigin: '0 50%'}}>
    <svg width={W + 80} height={H + 40} viewBox={`0 0 ${W + 80} ${H + 40}`} style={{overflow: 'visible'}}>
      <defs>
        <linearGradient id="s03-thumb-fade" x1={X(PI_MAX_X)} x2={W} y1={0} y2={0} gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#fff" stopOpacity={1} />
          <stop offset="1" stopColor="#fff" stopOpacity={0.1} />
        </linearGradient>
        <mask id="s03-thumb-mask">
          <rect x={-10} y={-40} width={X(PI_MAX_X) + 10} height={H + 80} fill="#fff" />
          <rect x={X(PI_MAX_X)} y={-40} width={W} height={H + 80} fill="url(#s03-thumb-fade)" />
        </mask>
      </defs>
      <line x1={0} y1={H} x2={W + 20} y2={H} stroke={colors.line} strokeWidth={1.5} />
      <line x1={0} y1={H} x2={0} y2={-10} stroke={colors.line} strokeWidth={1.5} />
      <g mask="url(#s03-thumb-mask)">
        <path d={P.band} fill="rgba(242,237,228,0.2)" stroke="rgba(242,237,228,0.45)" strokeWidth={1} />
        <path d={P.liDash} fill="none" stroke={colors.fg} strokeWidth={1.6} strokeDasharray="6 7" opacity={0.85} />
      </g>
      <path d={P.liSolid} fill="none" stroke={colors.fg} strokeWidth={1.8} opacity={0.9} />
      <path d={P.stair} fill="none" stroke={colors.accent} strokeWidth={2.2} style={{filter: 'drop-shadow(0 0 5px rgba(255,110,40,0.8))'}} />
      <text x={W + 14} y={30} fill={colors.accent} fontFamily={fonts.display} fontStyle="italic" fontSize={84}>
        ?
      </text>
      <text x={X(PI_MAX_X) - 40} y={Y(primePi(PI_MAX_X)) + 30} fill={colors.accent} fontFamily={fonts.mono} fontSize={18}>
        π(x)
      </text>
      <text x={X(0.55e6) - 70} y={Y(li(0.55e6)) - 18} fill={colors.fg} fontFamily={fonts.mono} fontSize={18}>
        li(x)
      </text>
    </svg>
  </div>
);
