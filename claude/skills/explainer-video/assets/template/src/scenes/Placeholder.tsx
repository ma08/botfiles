import React from 'react';
import {SceneFrame, Title, Body} from '../components/SceneFrame';
import {sceneById} from '../lib/timeline';

/** Stand-in for a scene that hasn't been built yet: shows its title and narration. */
export const Placeholder: React.FC<{id: string; index: number}> = ({id, index}) => {
  const s = sceneById(id);
  return (
    <SceneFrame index={index} kicker={s.title}>
      <Title>{s.title}</Title>
      <Body start={14} top={470}>
        {s.lines.map((l) => l.caption).join(' ')}
      </Body>
    </SceneFrame>
  );
};
