import React from 'react';
import {useCurrentFrame} from 'remotion';
import {colors, fonts} from '../theme';
import {enter} from '../lib/anim';
import status from '../data/status.json';

/** Small top-right pill with the "as of" status, used on scenes that state verification status. */
export const StatusStamp: React.FC<{start?: number; text?: string}> = ({start = 10, text}) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        position: 'absolute',
        right: 110,
        top: 96,
        fontFamily: fonts.mono,
        fontSize: 19,
        color: colors.muted,
        border: `1px solid ${colors.line}`,
        padding: '8px 14px',
        borderRadius: 999,
        ...enter(frame, start, 16, 6),
      }}
    >
      {text ?? status.asof_onscreen}
    </div>
  );
};
