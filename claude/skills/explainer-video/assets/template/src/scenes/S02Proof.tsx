import React from 'react';
import {useCurrentFrame} from 'remotion';
import {SceneFrame, Title, Tag} from '../components/SceneFrame';
import {colors, fonts} from '../theme';
import {enter, ramp} from '../lib/anim';
import {lineStartFrame, sceneById, wordFrame} from '../lib/timeline';

// Example scene: an equation that builds term by term, then remainder checks, then the conclusion.
const S = sceneById('s02_proof');

const B = {
  list: wordFrame(S, 'list'),
  two: wordFrame(S, 'two', {line: 0}),
  three: wordFrame(S, 'three'),
  five: wordFrame(S, 'five'),
  multiply: wordFrame(S, 'Multiply'),
  add: wordFrame(S, 'add'),
  thirtyOne: wordFrame(S, 'thirty-one.'),
  remainder: wordFrame(S, 'remainder'),
  newFactors: wordFrame(S, 'new.'),
  finite: lineStartFrame(S, 3),
  never: wordFrame(S, 'never'),
};

const Term: React.FC<{at: number; children: React.ReactNode; color?: string}> = ({at, children, color}) => {
  const frame = useCurrentFrame();
  return <span style={{display: 'inline-block', color: color ?? colors.fg, ...enter(frame, at - 3, 12, 14)}}>{children}</span>;
};

export const S02Proof: React.FC = () => {
  const frame = useCurrentFrame();
  const rows = [2, 3, 5];
  return (
    <SceneFrame index={2} kicker={S.title}>
      <Title size={84}>Suppose the list were complete</Title>

      {/* the supposed complete list */}
      <div style={{position: 'absolute', left: 124, top: 300, display: 'flex', gap: 18, fontFamily: fonts.mono, fontSize: 40}}>
        <span style={{color: colors.muted, ...enter(frame, B.list - 4)}}>list:</span>
        <Term at={B.two}>2</Term>
        <Term at={B.three}>3</Term>
        <Term at={B.five}>5</Term>
      </div>

      {/* the Euclid number */}
      <div style={{position: 'absolute', left: 124, top: 400, fontFamily: fonts.display, fontStyle: fonts.displayStyle, fontSize: 110, display: 'flex', gap: 26, alignItems: 'baseline'}}>
        <Term at={B.multiply}>2 × 3 × 5</Term>
        <Term at={B.add} color={colors.accent}>+ 1</Term>
        <Term at={B.thirtyOne}>= 31</Term>
      </div>

      {/* remainder checks */}
      <div style={{position: 'absolute', left: 124, top: 590, display: 'flex', flexDirection: 'column', gap: 10, fontFamily: fonts.mono, fontSize: 32, color: colors.fg}}>
        {rows.map((p, i) => (
          <div key={p} style={{...enter(frame, B.remainder + i * 8, 12, 8)}}>
            31 ÷ {p} = {Math.floor(31 / p)} <span style={{color: colors.accent}}>remainder 1</span>
          </div>
        ))}
      </div>
      <div style={{position: 'absolute', left: 820, top: 610, width: 900, fontFamily: fonts.body, fontSize: 32, lineHeight: 1.4, color: colors.muted, ...enter(frame, B.newFactors - 6)}}>
        So no prime on the list divides 31. Its prime factors are missing from the list.
      </div>

      {/* conclusion */}
      <div
        style={{
          position: 'absolute',
          left: 124,
          top: 800,
          fontFamily: fonts.display,
          fontStyle: fonts.displayStyle,
          fontSize: 56,
          color: colors.accent,
          ...enter(frame, B.finite),
        }}
      >
        Every finite list misses a prime.
      </div>
      <Tag style={{position: 'absolute', right: 120, top: 104, opacity: ramp(frame, B.never, 14)}}>here 31 happens to be prime; in general it only has a new prime factor</Tag>
    </SceneFrame>
  );
};
