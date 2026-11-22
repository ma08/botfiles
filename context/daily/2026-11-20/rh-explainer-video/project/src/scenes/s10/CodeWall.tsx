import React, {useMemo} from 'react';
import {random} from 'remotion';
import {colors} from '../../theme';

/**
 * A zoomed-out "wall" of code: columns of minimap-style grey bars, procedurally generated
 * (deterministic via remotion's random(seed)). `scroll` is a pixel offset that drives the
 * vertical drift; each column drifts at its own speed.
 */
export const CodeWall: React.FC<{
  width: number;
  height: number;
  cols?: number;
  gap?: number;
  rowH?: number;
  rows?: number;
  scroll?: number;
  seed?: string;
  dim?: string;
  bright?: string;
  brightShare?: number;
}> = ({
  width,
  height,
  cols = 14,
  gap = 22,
  rowH = 9,
  rows = 140,
  scroll = 0,
  seed = 'wall',
  dim = colors.line,
  bright = colors.faint,
  brightShare = 0.18,
}) => {
  const colW = (width - gap * (cols - 1)) / cols;
  const patternH = rows * rowH;
  const columns = useMemo(() => {
    const out: {dimD: string; brightD: string; speed: number; phase: number}[] = [];
    for (let c = 0; c < cols; c++) {
      let dimD = '';
      let brightD = '';
      let indent = 0;
      for (let r = 0; r < rows; r++) {
        const k = `${seed}-${c}-${r}`;
        const blank = random(`${k}-b`) < 0.16;
        if (blank) {
          indent = 0;
          continue;
        }
        const step = random(`${k}-i`);
        if (step < 0.25) indent = Math.min(4, indent + 1);
        else if (step < 0.42) indent = Math.max(0, indent - 1);
        let x = indent * colW * 0.07;
        const segs = 1 + Math.floor(random(`${k}-n`) * 3.2);
        const y = r * rowH;
        const h = rowH * 0.48;
        for (let j = 0; j < segs; j++) {
          const w = colW * (0.06 + random(`${k}-w${j}`) * 0.3);
          if (x + w > colW) break;
          const d = `M${x.toFixed(1)},${y.toFixed(1)}h${w.toFixed(1)}v${h.toFixed(1)}h${(-w).toFixed(1)}Z`;
          if (random(`${k}-c${j}`) < brightShare) brightD += d;
          else dimD += d;
          x += w + colW * 0.025;
        }
      }
      out.push({dimD, brightD, speed: 0.6 + random(`${seed}-s${c}`) * 0.8, phase: random(`${seed}-p${c}`) * patternH});
    }
    return out;
  }, [cols, rows, rowH, colW, seed, brightShare, patternH]);

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{display: 'block', overflow: 'hidden'}}>
      {columns.map((col, c) => {
        const off = (((scroll * col.speed + col.phase) % patternH) + patternH) % patternH;
        const reps = Math.ceil(height / patternH) + 1;
        return (
          <g key={c} transform={`translate(${(c * (colW + gap)).toFixed(1)}, ${(-off).toFixed(1)})`}>
            {Array.from({length: reps}).map((_, i) => (
              <g key={i} transform={`translate(0, ${i * patternH})`}>
                <path d={col.dimD} fill={dim} />
                <path d={col.brightD} fill={bright} />
              </g>
            ))}
          </g>
        );
      })}
    </svg>
  );
};
