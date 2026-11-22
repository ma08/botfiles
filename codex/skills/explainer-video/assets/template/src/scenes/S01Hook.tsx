import React from 'react';
import {useCurrentFrame} from 'remotion';
import {SceneFrame, Title, Tag} from '../components/SceneFrame';
import {colors, fonts, glow} from '../theme';
import {enter, ramp} from '../lib/anim';
import {lineStartFrame, sceneById, wordFrame} from '../lib/timeline';
import data from '../data/example.json';

// Example scene: a 10x10 grid of 1..100 whose primes light up in sync with the narration.
// Pattern to copy: anchor every beat to a spoken word (wordFrame), draw from real data, keep text short.
const S = sceneById('s01_hook');
const PRIMES = new Set<number>(data.primesUnder100);

const B = {
  two: wordFrame(S, 'Two'),
  three: wordFrame(S, 'three'),
  five: wordFrame(S, 'five'),
  seven: wordFrame(S, 'seven'),
  eleven: wordFrame(S, 'eleven'),
  primes: wordFrame(S, 'Primes'),
  split: wordFrame(S, 'split'),
  runOut: lineStartFrame(S, 2),
  euclid: wordFrame(S, 'Euclid'),
};
const FIRST: Record<number, number> = {2: B.two, 3: B.three, 5: B.five, 7: B.seven, 11: B.eleven};

const CELL = 64;
const GAP = 8;
const GX = 1060;
const GY = 210;

export const S01Hook: React.FC = () => {
  const frame = useCurrentFrame();
  // after "Primes", the remaining primes sweep in, ordered by value
  const sweep = (n: number) => B.primes + Math.round(((n - 11) / 89) * 45);
  return (
    <SceneFrame index={1} kicker={S.title} instant>
      <Title start={-30} size={104} width={860}>
        Primes never
        <br />
        run out
      </Title>
      <div style={{position: 'absolute', left: 124, top: 420, width: 780, fontFamily: fonts.body, fontSize: 34, lineHeight: 1.45, color: colors.muted, ...enter(frame, B.split - 6)}}>
        A prime has no factors except <span style={{color: colors.fg}}>1</span> and itself.
      </div>
      <div style={{position: 'absolute', left: 124, top: 560, fontFamily: fonts.display, fontStyle: fonts.displayStyle, fontSize: 64, color: colors.accent, ...enter(frame, B.runOut)}}>
        Do they ever run out?
      </div>
      <Tag style={{position: 'absolute', left: 124, top: 680, opacity: ramp(frame, B.euclid, 14)}}>Euclid, Elements IX.20 · about 300 BCE</Tag>

      {Array.from({length: 100}, (_, i) => i + 1).map((n) => {
        const r = Math.floor((n - 1) / 10);
        const c = (n - 1) % 10;
        const isP = PRIMES.has(n);
        const on = isP ? ramp(frame, (FIRST[n] ?? sweep(n)) - 2, 8) : 0;
        return (
          <div
            key={n}
            style={{
              position: 'absolute',
              left: GX + c * (CELL + GAP),
              top: GY + r * (CELL + GAP),
              width: CELL,
              height: CELL,
              borderRadius: 10,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: fonts.mono,
              fontSize: 22,
              color: on > 0.5 ? colors.bg : colors.faint,
              background: on > 0 ? colors.accent : 'transparent',
              border: `1px solid ${on > 0 ? colors.accent : colors.line}`,
              opacity: 0.35 + 0.65 * Math.max(on, ramp(frame, 0, 20) * 0.6),
              filter: on > 0.5 ? glow(8) : undefined,
            }}
          >
            {n}
          </div>
        );
      })}
    </SceneFrame>
  );
};
