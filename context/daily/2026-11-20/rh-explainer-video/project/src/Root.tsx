import React from 'react';
import {AbsoluteFill, Audio, Composition, Sequence, Series, staticFile} from 'remotion';
import {timeline, sceneFrames, SceneTiming} from './lib/timeline';
import {Captions} from './components/Captions';
import {VIDEO} from './theme';
import {SCENES} from './scenes';
import {Thumbnail} from './Thumbnail';

type Props = {captions: boolean};

const SceneWithAudio: React.FC<{scene: SceneTiming; captions: boolean}> = ({scene, captions}) => {
  const Comp = SCENES[scene.id];
  const lead = Math.round(scene.leadIn * timeline.fps);
  return (
    <AbsoluteFill>
      <Comp />
      <Sequence from={lead} layout="none">
        <Audio src={staticFile(scene.audio)} />
      </Sequence>
      {captions && <Captions scene={scene} fps={timeline.fps} />}
    </AbsoluteFill>
  );
};

export const Main: React.FC<Props> = ({captions}) => (
  <AbsoluteFill style={{backgroundColor: '#110f0d'}}>
    {/* Ambient bed (ElevenLabs Music), pre-normalized to about -30 LUFS, ~10 dB under the voice. */}
    <Audio src={staticFile('music/bed.mp3')} volume={0.8} />
    <Series>
      {timeline.scenes.map((s) => (
        <Series.Sequence key={s.id} durationInFrames={sceneFrames(s)}>
          <SceneWithAudio scene={s} captions={captions} />
        </Series.Sequence>
      ))}
    </Series>
  </AbsoluteFill>
);

const total = timeline.scenes.reduce((a, s) => a + sceneFrames(s), 0);

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Thumbnail" component={Thumbnail} durationInFrames={1} fps={VIDEO.fps} width={VIDEO.width} height={VIDEO.height} />
    <Composition id="RHExplainer" component={Main} durationInFrames={total} fps={VIDEO.fps} width={VIDEO.width} height={VIDEO.height} defaultProps={{captions: false}} />
    <Composition id="RHExplainerCaptioned" component={Main} durationInFrames={total} fps={VIDEO.fps} width={VIDEO.width} height={VIDEO.height} defaultProps={{captions: true}} />
    {timeline.scenes.map((s) => (
      <Composition
        key={s.id}
        id={`Scene-${s.id.replace(/_/g, '-')}`}
        component={SceneWithAudio as unknown as React.FC<Record<string, unknown>>}
        durationInFrames={sceneFrames(s)}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
        defaultProps={{scene: s, captions: true}}
      />
    ))}
  </>
);
