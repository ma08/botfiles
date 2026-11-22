import React, {useMemo} from 'react';
import {useCurrentFrame} from 'remotion';
import {fonts} from '../theme';
import type {SceneTiming, Word} from '../lib/timeline';

type Chunk = {text: string; start: number; end: number};

const WEAK = new Set(['the', 'a', 'an', 'of', 'and', 'to', 'in', 'on', 'that', 'his', 'her', 'its', 'for', 'with', 'by', 'at', 'is', 'from', 'into', 'than', 'but', 'or', 'as', 'he', 'she', 'it']);
const textOf = (ws: Word[]) => ws.map((w) => w.text).join(' ');

/**
 * Group words into caption chunks of <= maxChars. Breaks after sentence punctuation, prefers commas,
 * never ends a chunk on a weak word, and merges orphan fragments (a lone "one.") into the previous chunk.
 * scripts/make_srt.py implements the same rules so the SRT matches the burned-in captions.
 */
export const chunkWords = (words: Word[], maxChars = 52): Chunk[] => {
  const chunks: Chunk[] = [];
  let cur: Word[] = [];
  const emit = (ws: Word[]) => {
    if (ws.length) chunks.push({text: textOf(ws), start: ws[0].start, end: ws[ws.length - 1].end});
  };
  for (const w of words) {
    if (cur.length && textOf([...cur, w]).length > maxChars) {
      let cut = -1;
      for (let i = cur.length - 1; i >= 1; i--)
        if (/[,;]$/.test(cur[i].text) && textOf(cur.slice(0, i + 1)).length >= 20) {
          cut = i;
          break;
        }
      if (cut === -1) {
        cut = cur.length - 1;
        while (cut > 1 && WEAK.has(cur[cut].text.toLowerCase())) cut--;
      }
      emit(cur.slice(0, cut + 1));
      cur = cur.slice(cut + 1);
    }
    cur.push(w);
    if (/[.?!:]$/.test(w.text)) {
      const prev = chunks[chunks.length - 1];
      if (textOf(cur).length > 14) {
        emit(cur);
        cur = [];
      } else if (prev && !/[.?!:]$/.test(prev.text) && (prev.text + ' ' + textOf(cur)).length <= 64) {
        // a short sentence tail ("new.") joins the caption it finishes instead of leading the next one
        prev.text = prev.text + ' ' + textOf(cur);
        prev.end = cur[cur.length - 1].end;
        cur = [];
      }
    }
  }
  emit(cur);
  for (let i = chunks.length - 1; i > 0; i--) {
    const c = chunks[i];
    const p = chunks[i - 1];
    if (c.text.length <= 8 && !/[.?!:]$/.test(p.text) && (p.text + ' ' + c.text).length <= 64) {
      chunks.splice(i - 1, 2, {text: p.text + ' ' + c.text, start: p.start, end: c.end});
    }
  }
  for (let i = 0; i < chunks.length; i++) {
    const next = chunks[i + 1];
    chunks[i].end = next ? Math.min(next.start, chunks[i].end + 0.6) : chunks[i].end + 0.6;
  }
  return chunks;
};

export const Captions: React.FC<{scene: SceneTiming; fps: number}> = ({scene, fps}) => {
  const frame = useCurrentFrame();
  const chunks = useMemo(() => chunkWords(scene.words), [scene]);
  const t = frame / fps - scene.leadIn;
  const c = chunks.find((x) => t >= x.start - 0.05 && t < x.end);
  if (!c) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: '50%',
        bottom: 58,
        transform: 'translateX(-50%)',
        padding: '12px 26px',
        borderRadius: 10,
        background: 'rgba(0,0,0,0.68)',
        color: '#fff',
        fontFamily: fonts.body,
        fontSize: 36,
        fontWeight: 400,
        whiteSpace: 'nowrap',
      }}
    >
      {c.text}
    </div>
  );
};
