import React from 'react';
import {AbsoluteFill, Audio, Composition, Sequence, Series, staticFile} from 'remotion';
import {timeline, sceneFrames, SceneTiming} from './lib/timeline';
import {Captions} from './components/Captions';
import {colors, fonts, VIDEO} from './theme';
import {SCENES} from './scenes';
import {Thumbnail} from './Thumbnail';

const SceneWithAudio: React.FC<{scene: SceneTiming; captions: boolean}> = ({scene, captions}) => {
  const Comp = SCENES[scene.id];
  if (!Comp) throw new Error(`No component registered for scene "${scene.id}" in src/scenes/index.ts`);
  const lead = Math.round(scene.leadIn * timeline.fps);
  return (
    <AbsoluteFill>
      <Comp />
      {scene.audio && (
        <Sequence from={lead} layout="none">
          <Audio src={staticFile(scene.audio)} />
        </Sequence>
      )}
      {captions && <Captions scene={scene} fps={timeline.fps} />}
    </AbsoluteFill>
  );
};

export const Main: React.FC<{captions: boolean}> = ({captions}) => (
  <AbsoluteFill style={{backgroundColor: colors.bg}}>
    {timeline.music && <Audio src={staticFile(timeline.music.file)} volume={timeline.music.volume} />}
    <Series>
      {timeline.scenes.map((s) => (
        <Series.Sequence key={s.id} durationInFrames={sceneFrames(s)}>
          <SceneWithAudio scene={s} captions={captions} />
        </Series.Sequence>
      ))}
    </Series>
    {timeline.mode === 'draft' && <DraftBadge />}
  </AbsoluteFill>
);

/** Shown on every frame of draft renders (estimated timings, no voice) so a draft is never posted by mistake. */
const DraftBadge: React.FC = () => (
  <div style={{position: 'absolute', right: 24, bottom: 20, fontFamily: fonts.mono, fontSize: 18, letterSpacing: '0.12em', color: colors.muted, background: colors.bgRaised, border: `1px solid ${colors.line}`, padding: '6px 12px', borderRadius: 6}}>
    DRAFT · ESTIMATED TIMING · NO VOICE
  </div>
);

const total = Math.max(1, timeline.scenes.reduce((a, s) => a + sceneFrames(s), 0));
const common = {fps: VIDEO.fps, width: VIDEO.width, height: VIDEO.height};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Explainer" component={Main} durationInFrames={total} {...common} defaultProps={{captions: false}} />
    <Composition id="ExplainerCaptioned" component={Main} durationInFrames={total} {...common} defaultProps={{captions: true}} />
    <Composition id="Thumbnail" component={Thumbnail} durationInFrames={1} {...common} />
    {/* One composition per scene (captions on) for fast stills while building: Scene-s01-hook, ... */}
    {timeline.scenes.map((s) => (
      <Composition
        key={s.id}
        id={`Scene-${s.id.replace(/_/g, '-')}`}
        component={SceneWithAudio as unknown as React.FC<Record<string, unknown>>}
        durationInFrames={sceneFrames(s)}
        {...common}
        defaultProps={{scene: s, captions: true}}
      />
    ))}
  </>
);
