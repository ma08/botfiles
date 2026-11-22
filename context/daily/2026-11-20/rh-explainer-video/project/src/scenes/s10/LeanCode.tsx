import React from 'react';
import {colors, fonts} from '../../theme';

type Kind = 'kw' | 'name' | 'type' | 'term' | 'punct' | 'mod' | 'sym' | 'plain';
export type Tok = {t: string; k: Kind};

const tint: Record<Kind, string> = {
  kw: colors.accent,
  name: colors.fg,
  type: '#d8ccb6',
  term: '#a99f90',
  punct: '#787166',
  mod: '#a99f90',
  sym: '#c7b9a2',
  plain: '#cfc6b8',
};

/** Tiny Lean tokenizer: just enough for the verbatim lines in lean.json. Text is never altered. */
export const tokenize = (line: string): Tok[] => {
  const out: Tok[] = [];
  let m: RegExpMatchArray | null;
  if ((m = line.match(/^(import)(\s+)(.*)$/))) {
    return [
      {t: m[1], k: 'kw'},
      {t: m[2], k: 'plain'},
      {t: m[3], k: 'mod'},
    ];
  }
  if ((m = line.match(/^(theorem|def)(\s+)(\S+)(\s+:\s+)(.*?)(\s+:=\s*)(.*)$/))) {
    out.push({t: m[1], k: 'kw'}, {t: m[2], k: 'plain'}, {t: m[3], k: 'name'}, {t: m[4], k: 'punct'});
    out.push({t: m[5], k: m[5] === 'Prop' ? 'kw' : 'type'}, {t: m[6], k: 'punct'});
    if (m[7]) out.push({t: m[7], k: 'term'});
    return out;
  }
  // generic: identifiers, numbers, symbols, whitespace
  const re = /(\s+)|([A-Za-z_][A-Za-z0-9_.']*)|(\d+)|([^\sA-Za-z0-9_])/gu;
  let x: RegExpExecArray | null;
  while ((x = re.exec(line))) {
    if (x[1]) out.push({t: x[1], k: 'plain'});
    else if (x[2]) out.push({t: x[2], k: 'plain'});
    else if (x[3]) out.push({t: x[3], k: 'sym'});
    else out.push({t: x[4], k: /^[(),:]+$/.test(x[4]) ? 'punct' : 'sym'});
  }
  return out;
};

/** One line of code. `marks` maps token text -> 0..1 underline progress (accent). */
export const CodeLine: React.FC<{
  line: string;
  size: number;
  marks?: Record<string, number>;
  dimKinds?: number; // 0..1 extra dimming of non-name tokens
}> = ({line, size, marks = {}}) => {
  const toks = tokenize(line);
  return (
    <span style={{fontFamily: fonts.mono, fontSize: size, whiteSpace: 'pre'}}>
      {toks.map((tk, i) => {
        const p = marks[tk.t] ?? 0;
        return (
          <span
            key={i}
            style={{
              color: p > 0 ? colors.fg : tint[tk.k],
              position: 'relative',
              display: 'inline-block',
            }}
          >
            {tk.t}
            {p > 0 && (
              <span
                style={{
                  position: 'absolute',
                  left: 0,
                  bottom: -size * 0.12,
                  height: 2,
                  width: `${p * 100}%`,
                  background: colors.accent,
                  boxShadow: `0 0 8px ${colors.accentGlow}`,
                }}
              />
            )}
          </span>
        );
      })}
    </span>
  );
};
