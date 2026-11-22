import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {SceneFrame} from '../components/SceneFrame';
import {StatusStamp} from '../components/StatusStamp';
import {colors, fonts} from '../theme';
import {clamp, enter, ramp} from '../lib/anim';
import {lineEndFrame, lineStartFrame, sceneById} from '../lib/timeline';
import statusJson from '../data/status.json';
import noteTimeline from '../data/notetimeline.json';
import {wordIn} from './s10/sync';
import {StateIcon, stateColor} from './s11/Icons';

const S = sceneById('s11_checks');

type Check = {label: string; value: string; state: string};
type Status = typeof statusJson & {checks: Check[]};
const status = statusJson as Status;

const F = {
  L1: lineStartFrame(S, 1),
  independent: wordIn(S, 1, 'independent', 0, 0.25),
  compiles: wordIn(S, 1, 'compiles', 0, 0.42),
  L2: lineStartFrame(S, 2),
  L2end: lineEndFrame(S, 2),
  L3: lineStartFrame(S, 3),
  timeline: wordIn(S, 3, 'timeline', 0, 0.08),
  october: wordIn(S, 3, 'october', 0, 0.18),
  sixteenth: wordIn(S, 3, '16th', 0, 0.35),
  alpoge: wordIn(S, 3, 'alpöge', 0, 0.44),
  supplied: wordIn(S, 3, 'supplied', 0, 0.58),
  claude: wordIn(S, 3, 'claude', 0, 0.79),
};

/**
 * When each check resolves. Label keywords refine the timing against the narration clauses;
 * anything unmatched falls back to its state (pending/missing -> line 2) or is interpolated
 * by row order between matched neighbours. Never depends on exact label text.
 */
const resolveFrames = (checks: Check[]): number[] => {
  const rules: [RegExp, () => number][] = [
    [/compil/i, () => wordIn(S, 1, 'compiles', 0, 0.42)],
    [/axiom/i, () => wordIn(S, 1, 'axioms', 0, 0.66)],
    [/independent|nanoda|second checker/i, () => wordIn(S, 1, 'checkers', 0, 0.88)],
    [/comparat|end.to.end/i, () => wordIn(S, 2, 'comparison', 0, 0.28)],
    [/human|readable/i, () => wordIn(S, 2, 'weekend', 0, 0.62)],
  ];
  const byState = (st: string) =>
    st === 'pending' ? wordIn(S, 2, 'comparison', 0, 0.28) : st === 'pass' ? null : wordIn(S, 2, 'weekend', 0, 0.62);
  const f: (number | null)[] = checks.map((c) => {
    const r = rules.find(([re]) => re.test(c.label));
    return r ? r[1]() : byState(c.state);
  });
  // interpolate the unmatched ones by order
  const lo = wordIn(S, 1, 'compiles', 0, 0.42);
  const hi = wordIn(S, 1, 'checkers', 0, 0.88);
  return f.map((v, i) => {
    if (v !== null) return v;
    let p = i - 1;
    while (p >= 0 && f[p] === null) p--;
    let n = i + 1;
    while (n < f.length && f[n] === null) n++;
    const pf = p >= 0 ? (f[p] as number) : lo - 30;
    const nf = n < f.length ? (f[n] as number) : Math.max(pf + 30, hi);
    return Math.round(pf + ((nf - pf) * (i - p)) / (n - p));
  });
};

const ChecksList: React.FC<{frame: number; checks: Check[]; pendingDetail?: string}> = ({frame, checks, pendingDetail}) => {
  const at = resolveFrames(checks);
  const firstPending = checks.findIndex((c) => c.state === 'pending');
  const detailH = 36;
  const avail = 470 - (firstPending >= 0 && pendingDetail ? detailH : 0);
  const rowH = Math.max(52, Math.min(72, avail / Math.max(1, checks.length)));
  const left = 120;
  const width = 1680;
  return (
    <div style={{position: 'absolute', left, top: 262, width}}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontFamily: fonts.mono,
          fontSize: 17,
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
          color: colors.faint,
          paddingBottom: 10,
          borderBottom: `1px solid ${colors.line}`,
          ...enter(frame, 10, 14, 6),
        }}
      >
        <span style={{paddingLeft: 66}}>Check</span>
        <span>Reported result</span>
      </div>
      {checks.map((c, i) => {
        const appear = enter(frame, 14 + i * 5, 14, 10);
        const t = ramp(frame, at[i], 16, Easing.out(Easing.back(1.4)));
        const tLin = ramp(frame, at[i], 12);
        const showDetail = i === firstPending && !!pendingDetail;
        // a soft scanning shimmer while queued
        const sweep = ((frame * 14 + i * 260) % 2600) - 400;
        const queued = 1 - tLin;
        return (
          <div
            key={`${c.label}-${i}`}
            style={{
              position: 'relative',
              height: rowH + (showDetail ? detailH : 0),
              borderBottom: `1px solid ${colors.line}`,
              overflow: 'hidden',
              ...appear,
            }}
          >
            {queued > 0 && (
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  left: sweep,
                  width: 400,
                  opacity: queued * 0.9,
                  background: 'linear-gradient(90deg, rgba(242,237,228,0) 0%, rgba(242,237,228,0.035) 50%, rgba(242,237,228,0) 100%)',
                }}
              />
            )}
            {tLin > 0 && (
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  opacity: tLin * (1 - ramp(frame, at[i] + 10, 30)) * 0.9,
                  background: `linear-gradient(90deg, ${c.state === 'pass' ? 'rgba(159,211,138,0.10)' : c.state === 'pending' ? 'rgba(232,196,106,0.10)' : 'rgba(201,131,122,0.10)'} 0%, rgba(0,0,0,0) 60%)`,
                }}
              />
            )}
            <div style={{position: 'absolute', left: 6, top: (rowH - 38) / 2}}>
              <StateIcon state={c.state} t={t} frame={frame} />
            </div>
            <div
              style={{
                position: 'absolute',
                left: 66,
                top: 0,
                height: rowH,
                display: 'flex',
                alignItems: 'center',
                fontFamily: fonts.body,
                fontWeight: 400,
                fontSize: 33,
                color: c.state === 'pass' || queued > 0.5 ? colors.fg : c.state === 'pending' ? colors.fg : colors.muted,
                opacity: 0.42 + 0.58 * tLin,
              }}
            >
              {c.label}
            </div>
            <div
              style={{
                position: 'absolute',
                right: 6,
                top: 0,
                height: rowH,
                display: 'flex',
                alignItems: 'center',
                fontFamily: fonts.mono,
                fontSize: 25,
                color: c.state === 'pass' ? colors.muted : stateColor(c.state),
                opacity: tLin,
                transform: `translateX(${(1 - tLin) * 14}px)`,
              }}
            >
              {c.value}
            </div>
            {showDetail && (
              <div
                style={{
                  position: 'absolute',
                  left: 66,
                  top: rowH - 10,
                  fontFamily: fonts.mono,
                  fontSize: 20,
                  color: colors.pending,
                  opacity: 0.8 * ramp(frame, at[i] + 10, 16),
                }}
              >
                pending: {pendingDetail}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

// ---------- timeline ----------
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const dayNum = (iso: string) => {
  const [y, m, d] = iso.split('-').map(Number);
  return Date.UTC(y, m - 1, d) / 86400000;
};
const dayLabel = (n: number) => {
  const dt = new Date(n * 86400000);
  return `${MONTHS[dt.getUTCMonth()]} ${dt.getUTCDate()}`;
};
type Item = {date: string; label: string; cluster?: number};
const items = (noteTimeline.items as Item[]).map((it) => ({...it, day: dayNum(it.date)}));
const d0 = items[0].day;
const d1 = items[items.length - 1].day;
const spanDays = d1 - d0;

const Timeline: React.FC<{frame: number}> = ({frame}) => {
  const x0 = 200;
  const x1 = 1640;
  const axisY = 560;
  const dx = (d: number) => x0 + ((d - d0) / spanDays) * (x1 - x0);
  const p = interpolate(frame, [F.october - 4, F.sixteenth + 4], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const head = x0 + p * (x1 - x0);
  const passAt = (x: number) => F.october - 4 + ((x - x0) / (x1 - x0)) * (F.sixteenth + 8 - F.october);
  const title = enter(frame, F.timeline + 10, 20, 16);
  const end = items[items.length - 1];
  const tag = enter(frame, F.alpoge, 16, 8);
  const cA = enter(frame, F.supplied, 18, 12);
  const cB = enter(frame, F.claude, 18, 12);
  const days: number[] = [];
  for (let d = d0; d <= d1; d++) days.push(d);
  return (
    <>
      <div style={{position: 'absolute', left: 120, top: 150, display: 'flex', alignItems: 'baseline', gap: 26, ...title}}>
        <span style={{fontFamily: fonts.display, fontStyle: 'italic', fontSize: 104, lineHeight: 1, color: colors.fg, letterSpacing: '-0.02em'}}>
          {dayLabel(d0)} → {dayLabel(d1)}
        </span>
        <span style={{fontFamily: fonts.mono, fontSize: 22, color: colors.muted}}>
          the note's timeline (Claude-compiled, per the note)
        </span>
      </div>
      <svg style={{position: 'absolute', left: 0, top: 0}} width={1920} height={1080}>
        {/* faint track */}
        <line x1={x0} y1={axisY} x2={x1} y2={axisY} stroke={colors.line} strokeWidth={1.5} opacity={ramp(frame, F.timeline + 6, 16)} />
        {/* drawn axis */}
        <line x1={x0} y1={axisY} x2={head} y2={axisY} stroke={colors.muted} strokeWidth={2} />
        {days.map((d) => {
          const x = dx(d);
          const on = ramp(frame, passAt(x), 6);
          const first = new Date(d * 86400000).getUTCDate() === 1;
          return <line key={d} x1={x} x2={x} y1={axisY + 6} y2={axisY + (first ? 22 : 12)} stroke={first ? colors.muted : colors.faint} strokeWidth={1.4} opacity={on} />;
        })}
        {p > 0 && p < 1 && <circle cx={head} cy={axisY} r={4} fill={colors.fg} style={{filter: 'drop-shadow(0 0 6px rgba(242,237,228,0.8))'}} />}
        {items.map((it, i) => {
          const x = dx(it.day);
          const isEnd = i === items.length - 1;
          const n = it.cluster ?? 1;
          const t0 = passAt(x);
          return (
            <g key={i}>
              {Array.from({length: n}).map((_, k) => {
                const t = ramp(frame, t0 + k * 3, 10, Easing.out(Easing.back(2)));
                if (t <= 0) return null;
                return (
                  <circle
                    key={k}
                    cx={x}
                    cy={axisY - k * 20}
                    r={(isEnd ? 11 : 7) * t}
                    fill={isEnd ? colors.accent : colors.fg}
                    style={{filter: isEnd ? 'drop-shadow(0 0 12px rgba(255,110,40,0.9))' : 'drop-shadow(0 0 5px rgba(242,237,228,0.45))'}}
                  />
                );
              })}
            </g>
          );
        })}
      </svg>
      {/* date labels */}
      {[d0, d1].map((d, i) => (
        <div
          key={d}
          style={{
            position: 'absolute',
            left: dx(d) - 100,
            width: 200,
            top: axisY + 28,
            textAlign: 'center',
            fontFamily: fonts.mono,
            fontSize: 24,
            color: colors.fg,
            opacity: ramp(frame, i === 0 ? F.october - 4 : F.sixteenth, 12),
          }}
        >
          {dayLabel(d)}
        </div>
      ))}
      {days
        .filter((d) => new Date(d * 86400000).getUTCDate() === 1)
        .map((d) => (
          <div
            key={d}
            style={{
              position: 'absolute',
              left: dx(d) - 60,
              width: 120,
              top: axisY + 30,
              textAlign: 'center',
              fontFamily: fonts.mono,
              fontSize: 18,
              color: colors.muted,
              opacity: ramp(frame, passAt(dx(d)), 10),
            }}
          >
            {dayLabel(d)}
          </div>
        ))}
      {/* cluster count + end label */}
      {items
        .filter((it) => (it.cluster ?? 1) > 1)
        .map((it) => (
          <div
            key={it.date}
            style={{
              position: 'absolute',
              left: dx(it.day) - 160,
              width: 140,
              top: axisY - ((it.cluster ?? 1) - 1) * 20 - 14,
              textAlign: 'right',
              fontFamily: fonts.mono,
              fontSize: 18,
              lineHeight: 1.3,
              color: colors.muted,
              opacity: ramp(frame, passAt(dx(it.day)) + (it.cluster ?? 1) * 3, 12),
            }}
          >
            {it.cluster} of 20 entries
            <br />
            {dayLabel(it.day)}
          </div>
        ))}
      <div
        style={{
          position: 'absolute',
          left: dx(end.day) + 24,
          top: axisY - 44,
          fontFamily: fonts.display,
          fontStyle: 'italic',
          fontSize: 68,
          lineHeight: 1,
          color: colors.fg,
          textShadow: '0 0 24px rgba(255,110,40,0.35)',
          ...enter(frame, passAt(x1) + 2, 14, 8),
        }}
      >
        {end.label}
      </div>
      {/* credit split */}
      <div style={{position: 'absolute', left: 0, right: 0, top: 668, textAlign: 'center', ...tag}}>
        <span
          style={{
            display: 'inline-block',
            fontFamily: fonts.mono,
            fontSize: 19,
            color: colors.muted,
            border: `1px solid ${colors.line}`,
            borderRadius: 999,
            padding: '6px 14px',
          }}
        >
          per Alpöge's note
        </span>
      </div>
      <div style={{position: 'absolute', left: 200, top: 740, display: 'flex', alignItems: 'baseline', gap: 14, ...cA}}>
        <span style={{fontFamily: fonts.body, fontWeight: 500, fontSize: 30, color: colors.fg}}>Alpöge:</span>
        <span style={{fontFamily: fonts.display, fontStyle: 'italic', fontSize: 50, color: colors.fg}}>guiding idea</span>
      </div>
      <div
        style={{
          position: 'absolute',
          right: 1920 - (x1 + 22),
          top: 740,
          display: 'flex',
          alignItems: 'baseline',
          gap: 14,
          ...cB,
        }}
      >
        <span style={{fontFamily: fonts.body, fontWeight: 500, fontSize: 30, color: colors.fg}}>Claude:</span>
        <span style={{fontFamily: fonts.display, fontStyle: 'italic', fontSize: 50, color: colors.fg}}>far outpaced him near the finish</span>
      </div>
    </>
  );
};

export const S11Checks: React.FC<{checks?: Check[]}> = ({checks = status.checks}) => {
  const frame = useCurrentFrame();
  const statusOut = 1 - ramp(frame, F.timeline - 6, 18);
  const titleIn = enter(frame, 6, 20, 18);
  return (
    <SceneFrame index={11} kicker="The checks, and the note's timeline">
      {statusOut > 0 && (
        <AbsoluteFill style={{opacity: statusOut}}>
          {/* opacity-only wrapper: StatusStamp keeps its own absolute position */}
          <StatusStamp start={10} />
          <div
            style={{
              position: 'absolute',
              left: 120,
              top: 150,
              fontFamily: fonts.display,
              fontStyle: 'italic',
              fontSize: 80,
              lineHeight: 1,
              letterSpacing: '-0.02em',
              color: colors.fg,
              ...titleIn,
            }}
          >
            Independent checks
          </div>
          <ChecksList frame={frame} checks={checks} pendingDetail={checks.some((c) => c.state === 'pending') ? status.pending_detail : undefined} />
          <div
            style={{
              position: 'absolute',
              left: 120,
              width: 1680,
              top: 790,
              fontFamily: fonts.body,
              fontWeight: 300,
              fontSize: 22,
              lineHeight: 1.5,
              color: colors.muted,
            }}
          >
            <div style={enter(frame, F.L1, 16, 6)}>{status.onscreen_footnote}</div>
            <div style={enter(frame, F.L1 + 12, 16, 6)}>{status.onscreen_footnote_2}</div>
          </div>
        </AbsoluteFill>
      )}
      {frame >= F.timeline && <Timeline frame={frame} />}
    </SceneFrame>
  );
};
