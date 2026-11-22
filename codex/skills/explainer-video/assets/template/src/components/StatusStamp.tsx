import React from 'react';
import {useCurrentFrame} from 'remotion';
import {colors, fonts} from '../theme';
import {enter} from '../lib/anim';
import status from '../data/status.json';

/**
 * Top-right "as of" pill for scenes that state time-sensitive facts (a claim's verification status, a live count).
 * Text comes from script/status.json (copied to src/data/status.json by scripts/tts.py), so a status refresh
 * means editing one file, re-voicing changed lines, and re-rendering.
 */
export const StatusStamp: React.FC<{start?: number; text?: string}> = ({start = 10, text}) => {
  const frame = useCurrentFrame();
  const label = text ?? (status as {asof_onscreen?: string}).asof_onscreen;
  if (!label) return null;
  return (
    <div
      style={{
        position: 'absolute',
        right: 110,
        top: 96,
        fontFamily: fonts.mono,
        fontSize: 21,
        color: colors.muted,
        border: `1px solid ${colors.line}`,
        padding: '8px 14px',
        borderRadius: 999,
        ...enter(frame, start, 16, 6),
      }}
    >
      {label}
    </div>
  );
};
