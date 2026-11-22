import React from 'react';
import {colors} from '../../theme';

export type CheckState = 'pass' | 'pending' | 'missing' | string;

/** State icon: queued ring -> pass check / pending rotating ring / missing dash. All SVG, deterministic. */
export const StateIcon: React.FC<{state: CheckState; t: number; frame: number; size?: number}> = ({state, t, frame, size = 38}) => {
  const queuedOp = 1 - t;
  const pop = 0.7 + 0.3 * Math.min(1, t * 1.2) + 0.08 * Math.sin(Math.min(1, t) * Math.PI);
  return (
    <svg width={size} height={size} viewBox="0 0 36 36" style={{overflow: 'visible'}}>
      {queuedOp > 0 && (
        <circle cx={18} cy={18} r={13} fill="none" stroke={colors.faint} strokeWidth={1.6} strokeDasharray="2.2 4.2" opacity={queuedOp} />
      )}
      {t > 0 && (
        <g opacity={Math.min(1, t * 1.5)} transform={`translate(18 18) scale(${pop}) translate(-18 -18)`}>
          {state === 'pass' && (
            <>
              <circle cx={18} cy={18} r={14} fill="rgba(159,211,138,0.10)" stroke={colors.good} strokeWidth={1.8} />
              <path
                d="M11.5,18.6 L16.2,23.2 L25,13.6"
                fill="none"
                stroke={colors.good}
                strokeWidth={2.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeDasharray={22}
                strokeDashoffset={22 * (1 - Math.min(1, t * 1.3))}
                style={{filter: 'drop-shadow(0 0 5px rgba(159,211,138,0.55))'}}
              />
            </>
          )}
          {state === 'pending' && (
            <g transform={`rotate(${(frame * 5) % 360} 18 18)`}>
              <circle cx={18} cy={18} r={13} fill="none" stroke="rgba(232,196,106,0.22)" strokeWidth={2.2} />
              <path
                d="M18,5 A13,13 0 1 1 5,18"
                fill="none"
                stroke={colors.pending}
                strokeWidth={2.4}
                strokeLinecap="round"
                style={{filter: 'drop-shadow(0 0 5px rgba(232,196,106,0.5))'}}
              />
            </g>
          )}
          {state !== 'pass' && state !== 'pending' && (
            <>
              <circle cx={18} cy={18} r={14} fill="rgba(201,131,122,0.07)" stroke="rgba(201,131,122,0.55)" strokeWidth={1.6} />
              <line x1={11.5} y1={18} x2={24.5} y2={18} stroke={colors.missing} strokeWidth={2.4} strokeLinecap="round" />
            </>
          )}
        </g>
      )}
    </svg>
  );
};

export const stateColor = (state: CheckState) =>
  state === 'pass' ? colors.good : state === 'pending' ? colors.pending : colors.missing;
