import timelineJson from '../data/timeline.json';

export type Word = {text: string; start: number; end: number}; // seconds, relative to scene start
export type Line = {caption: string; start: number; end: number; status?: boolean};
export type SceneTiming = {
  id: string;
  title: string;
  audio: string; // path under public/
  audioDuration: number; // seconds
  leadIn: number; // seconds of silence before narration starts
  duration: number; // total scene seconds (lead-in + audio + tail)
  lines: Line[];
  words: Word[];
};
export type Timeline = {fps: number; scenes: SceneTiming[]; totalSeconds: number};

export const timeline = timelineJson as unknown as Timeline;

export const sceneById = (id: string): SceneTiming => {
  const s = timeline.scenes.find((x) => x.id === id);
  if (!s) throw new Error(`scene ${id} missing from timeline.json`);
  return s;
};

/** Frame (relative to scene start) at which line `i` starts being spoken. */
export const lineStartFrame = (s: SceneTiming, i: number, fps = timeline.fps) =>
  Math.round((s.leadIn + (s.lines[i]?.start ?? 0)) * fps);
export const lineEndFrame = (s: SceneTiming, i: number, fps = timeline.fps) =>
  Math.round((s.leadIn + (s.lines[i]?.end ?? 0)) * fps);

/** Frame at which the first word matching `needle` (case-insensitive, punctuation stripped) is spoken. */
export const wordFrame = (s: SceneTiming, needle: string, nth = 0, fps = timeline.fps) => {
  const norm = (t: string) => t.toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');
  const target = norm(needle);
  const hits = s.words.filter((w) => norm(w.text) === target);
  const w = hits[nth] ?? hits[0];
  return w ? Math.round((s.leadIn + w.start) * fps) : 0;
};

export const sceneFrames = (s: SceneTiming, fps = timeline.fps) => Math.round(s.duration * fps);
