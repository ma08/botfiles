import {SceneTiming, lineEndFrame, lineStartFrame, timeline} from '../../lib/timeline';

// Shared helpers for scenes s10 to s12 (same builder).

const norm = (t: string) =>
  t
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]/gu, '');

/**
 * Frame of the nth occurrence of `needle` inside line `line` only.
 * If the word is missing (re-voiced line), falls back to `frac` of the way through that line,
 * so a missed anchor never fires at frame 0.
 */
export const wordIn = (s: SceneTiming, line: number, needle: string, nth = 0, frac = 0.5, fps = timeline.fps) => {
  const l = s.lines[line];
  const a = lineStartFrame(s, line, fps);
  const b = lineEndFrame(s, line, fps);
  if (!l) return a;
  const target = norm(needle);
  const hits = s.words.filter((w) => w.start >= l.start - 0.05 && w.start <= l.end + 0.05 && norm(w.text) === target);
  const w = hits[nth];
  if (w) return Math.round((s.leadIn + w.start) * fps);
  return Math.round(a + (b - a) * frac);
};

/** Thousands separators without locale dependence. */
export const fmt = (n: number) => Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
