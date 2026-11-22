import timelineJson from '../data/timeline.json';

/**
 * Narration timing, written by scripts/tts.py (real voice) or scripts/tts.py --draft (estimated from word counts).
 * Times are seconds relative to the start of narration in a scene; helpers below add the scene's lead-in
 * and return frames relative to the scene start. Key every visual beat to a word, never to a hard-coded frame,
 * so re-voicing or editing a line keeps the picture in sync.
 */
export type Word = {text: string; start: number; end: number};
export type Line = {caption: string; start: number; end: number; status?: boolean};
export type SceneTiming = {
  id: string;
  title: string;
  audio: string | null; // path under public/, or null in draft mode
  audioDuration: number;
  leadIn: number;
  duration: number;
  lines: Line[];
  words: Word[];
};
export type Timeline = {
  fps: number;
  mode: 'draft' | 'voiced';
  meta: {title?: string; subtitle?: string; kicker?: string; attribution?: string};
  scenes: SceneTiming[];
  totalSeconds: number;
  music: {file: string; volume: number} | null;
};

export const timeline = timelineJson as unknown as Timeline;

export const sceneById = (id: string): SceneTiming => {
  const s = timeline.scenes.find((x) => x.id === id);
  if (!s) throw new Error(`scene "${id}" is missing from src/data/timeline.json (run scripts/tts.py or tts.py --draft)`);
  return s;
};

const norm = (t: string) =>
  t
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]/gu, '');

type Pick = number | {nth?: number; line?: number};

/**
 * Frame at which a spoken word starts (case and punctuation insensitive).
 *   wordFrame(S, 'zeros')                 first occurrence in the scene
 *   wordFrame(S, 'zeros', 2)              third occurrence in the scene
 *   wordFrame(S, 'squared', {line: 2})    first occurrence within line 2 (0-based)
 *   wordFrame(S, 'squared', {line: 2, nth: 1})
 * Line-scoped anchors are easier to keep right when a word repeats. `python3 scripts/words.py <scene>` prints
 * every spoken word with its line and occurrence number. Throws when the word isn't there, so a stale anchor
 * fails the render loudly instead of firing at frame 0; scripts/check_anchors.py checks all of them at once.
 */
export const wordFrame = (s: SceneTiming, needle: string, pick: Pick = 0, fps = timeline.fps) => {
  const {nth = 0, line} = typeof pick === 'number' ? {nth: pick, line: undefined} : pick;
  const l = line === undefined ? undefined : s.lines[line];
  if (line !== undefined && !l) throw new Error(`[${s.id}] line ${line} does not exist`);
  const pool = l ? s.words.filter((w) => w.start >= l.start - 0.01 && w.start <= l.end + 0.01) : s.words;
  const hits = pool.filter((w) => norm(w.text) === norm(needle));
  const w = hits[nth];
  if (!w) throw new Error(`[${s.id}] word "${needle}" #${nth}${line !== undefined ? ` in line ${line}` : ''} not found in narration (${hits.length} hits)`);
  return Math.round((s.leadIn + w.start) * fps);
};

export const lineStartFrame = (s: SceneTiming, i: number, fps = timeline.fps) => Math.round((s.leadIn + (s.lines[i]?.start ?? 0)) * fps);
export const lineEndFrame = (s: SceneTiming, i: number, fps = timeline.fps) => Math.round((s.leadIn + (s.lines[i]?.end ?? 0)) * fps);
export const sceneFrames = (s: SceneTiming, fps = timeline.fps) => Math.round(s.duration * fps);
