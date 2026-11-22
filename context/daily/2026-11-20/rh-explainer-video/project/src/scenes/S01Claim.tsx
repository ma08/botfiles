import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {SceneFrame} from '../components/SceneFrame';
import {colors, fonts} from '../theme';
import {clamp, enter, ramp} from '../lib/anim';
import {lineStartFrame, sceneById, wordFrame} from '../lib/timeline';

const s = sceneById('s01_claim');

const B = {
  november: wordFrame(s, 'November'),
  number: wordFrame(s, 'number'),
  levent: wordFrame(s, 'Levent'),
  anthropic: wordFrame(s, 'Anthropic'),
  posted: wordFrame(s, 'posted'),
  heSays: lineStartFrame(s, 1),
  believes: wordFrame(s, 'believes'),
  proved: wordFrame(s, 'proved'),
  riemann: wordFrame(s, 'Riemann'),
  broader: wordFrame(s, 'broader'),
  version: wordFrame(s, 'version'),
  released: wordFrame(s, 'released'),
  lean: wordFrame(s, 'Lean'),
  computers: wordFrame(s, 'computers'),
  check: wordFrame(s, 'check'),
  heres: wordFrame(s, "Here's"),
};

// ---- the note, page 1 (public/img/remark-1.png is 935 x 1210) ----
const IMG_W = 935;
const IMG_H = 1210;
const PW = 600;
const K = PW / IMG_W; // image px -> paper px
const PH = IMG_H * K;
const PX = 1180;
const PY = 112;
const PROT = -2.4; // degrees

/** Image pixel on the note -> screen pixel (accounts for the paper's rotation). */
const paperToScreen = (ix: number, iy: number): [number, number] => {
  const lx = ix * K - PW / 2;
  const ly = iy * K - PH / 2;
  const a = (PROT * Math.PI) / 180;
  return [PX + PW / 2 + lx * Math.cos(a) - ly * Math.sin(a), PY + PH / 2 + lx * Math.sin(a) + ly * Math.cos(a)];
};

// "I believe I have, working with Claude, discovered a proof¹" (page rendered with annotations hidden; footnote mark ends ~x 621)
const Q = {x0: 221, x1: 624, y0: 143, y1: 167};
// footnote 1: links to lean.tar.gz.part01 ... part14
const FN = {x0: 216, x1: 688, y0: 1011, y1: 1033};

// ---- pulled-out clipping of the quote ----
const CLIP_INNER_W = 860;
const M = CLIP_INNER_W / (Q.x1 - Q.x0); // magnification vs image px
const CLIP_PAD_X = 20;
const CLIP_PAD_Y = 14;
const CLIP_W = CLIP_INNER_W + CLIP_PAD_X * 2;
const CLIP_H = (Q.y1 - Q.y0) * M + CLIP_PAD_Y * 2;
const CLIP_LEFT = 930;
const CLIP_TOP = 408;

// ---- left column ----
const COL = 120;
const CARD_TOP = 300;
const CHIP_TOP = [482, 556, 630];
const LEAN_CHIP_RIGHT = COL + 506; // approx right edge of the Lean chip (for the leader)

const Chip: React.FC<{start: number; frame: number; children: React.ReactNode; top: number}> = ({start, frame, children, top}) => {
  const t = ramp(frame, start, 16);
  return (
    <div
      style={{
        position: 'absolute',
        left: COL,
        top,
        height: 56,
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        padding: '0 24px 0 20px',
        borderRadius: 999,
        border: `1px solid ${colors.line}`,
        background: 'rgba(26,23,20,0.85)',
        fontFamily: fonts.body,
        fontSize: 26,
        color: colors.fg,
        whiteSpace: 'nowrap',
        opacity: t,
        transform: `translateX(${(1 - t) * -16}px)`,
      }}
    >
      <span style={{width: 8, height: 8, borderRadius: 4, background: colors.accent, opacity: 0.9}} />
      {children}
    </div>
  );
};

export const S01Claim: React.FC = () => {
  const frame = useCurrentFrame();

  // rack focus onto the note on "posted a short note"
  const focus = ramp(frame, B.posted - 2, 30, Easing.inOut(Easing.cubic));
  const paperIn = 1; // on screen from frame 0 (poster frame)

  // quote: lift a clipping off the page, then highlight it
  const lift = ramp(frame, B.heSays + 2, 28, Easing.inOut(Easing.cubic));
  const clipOut = ramp(frame, B.version + 12, 20, Easing.in(Easing.cubic));
  const sweep = interpolate(frame, [B.believes - 12, B.proved + 6], [0, 1], {...clamp, easing: Easing.inOut(Easing.sin)});
  const [srcX, srcY] = paperToScreen((Q.x0 + Q.x1) / 2, (Q.y0 + Q.y1) / 2);
  const dstX = CLIP_LEFT + CLIP_W / 2;
  const dstY = CLIP_TOP + CLIP_H / 2;
  const clipScale = interpolate(lift, [0, 1], [K / M, 1]);
  const clipX = interpolate(lift, [0, 1], [srcX, dstX]);
  const clipY = interpolate(lift, [0, 1], [srcY, dstY]) - Math.sin(lift * Math.PI) * 40;
  const clipRot = interpolate(lift, [0, 1], [PROT, 0.8]);

  // footnote + leader to the Lean chip
  const fnIn = ramp(frame, B.released - 2, 22);
  const leader = ramp(frame, B.released + 8, 26, Easing.inOut(Easing.cubic));
  const leaderOut = ramp(frame, B.computers - 10, 16);
  const [fnX, fnY] = paperToScreen(FN.x0 - 6, (FN.y0 + FN.y1) / 2);
  const ldX = LEAN_CHIP_RIGHT + 14;
  const ldY = CHIP_TOP[2] + 28;

  // check motif on "computers can check"
  const chkIn = ramp(frame, B.computers - 2, 14);
  const chkDraw = ramp(frame, B.computers + 8, 18, Easing.inOut(Easing.cubic));

  // pull focus to the title on "Here's what that means"
  const pull = ramp(frame, B.heres - 4, 24, Easing.inOut(Easing.cubic));

  return (
    <SceneFrame index={1} kicker={s.title} instant>
      <AbsoluteFill
        style={{
          filter: `blur(${pull * 9}px)`,
          opacity: 1 - pull * 0.82,
          transform: `scale(${1 - pull * 0.025})`,
        }}
      >
        {/* ---------------- the note ---------------- */}
        <div
          style={{
            position: 'absolute',
            left: PX,
            top: PY,
            width: PW,
            height: PH,
            transform: `translateY(${(1 - focus) * 26}px) rotate(${PROT - (1 - focus) * 1.6}deg) scale(${0.95 + 0.05 * focus})`,
            transformOrigin: '50% 50%',
            opacity: paperIn * (0.32 + 0.68 * focus),
            filter: `blur(${(1 - focus) * 7}px)`,
          }}
        >
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: '#fbfaf7',
              borderRadius: 3,
              boxShadow: '0 40px 80px rgba(0,0,0,0.55), 0 8px 22px rgba(0,0,0,0.35)',
              overflow: 'hidden',
            }}
          >
            <Img src={staticFile('img/remark-1.png')} style={{width: PW, height: PH, display: 'block'}} />
            {/* highlight on the page itself */}
            <div
              style={{
                position: 'absolute',
                left: Q.x0 * K,
                top: (Q.y0 + 2) * K,
                width: (Q.x1 - Q.x0) * K * sweep,
                height: (Q.y1 - Q.y0 - 2) * K,
                background: 'rgba(255,122,40,0.6)',
                mixBlendMode: 'multiply',
                borderRadius: 2,
              }}
            />
            {/* footnote marker + footnote */}
            <div
              style={{
                position: 'absolute',
                left: FN.x0 * K - 4,
                top: FN.y0 * K - 3,
                width: (FN.x1 - FN.x0) * K + 8,
                height: (FN.y1 - FN.y0) * K + 6,
                border: `2px solid ${colors.accent}`,
                borderRadius: 4,
                opacity: fnIn,
                clipPath: `inset(0 ${100 - fnIn * 100}% 0 0)`,
              }}
            />
            <div
              style={{
                position: 'absolute',
                left: 611 * K,
                top: 143 * K,
                width: 15 * K,
                height: 25 * K,
                background: 'rgba(255,122,40,0.55)',
                mixBlendMode: 'multiply',
                opacity: fnIn,
              }}
            />
            {/* soft paper vignette */}
            <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(0,0,0,0) 70%, rgba(0,0,0,0.06) 100%)'}} />
          </div>
        </div>

        {/* ---------------- lifted clipping of the quote ---------------- */}
        {lift > 0 && clipOut < 1 && (
          <div
            style={{
              position: 'absolute',
              left: clipX - CLIP_W / 2,
              top: clipY - CLIP_H / 2,
              width: CLIP_W,
              height: CLIP_H,
              transform: `rotate(${clipRot}deg) scale(${clipScale * (1 - clipOut * 0.04)})`,
              transformOrigin: '50% 50%',
              background: '#fbfaf7',
              borderRadius: 4,
              boxShadow: `0 ${10 + 30 * lift}px ${20 + 50 * lift}px rgba(0,0,0,${0.3 + 0.35 * lift})`,
              opacity: Math.min(1, lift * 4) * (1 - clipOut),
              overflow: 'hidden',
            }}
          >
            <div style={{position: 'absolute', left: CLIP_PAD_X, top: CLIP_PAD_Y, width: CLIP_INNER_W, height: (Q.y1 - Q.y0) * M, overflow: 'hidden'}}>
              <Img
                src={staticFile('img/remark-1.png')}
                style={{
                  position: 'absolute',
                  left: -Q.x0 * M,
                  top: -Q.y0 * M,
                  width: IMG_W * M,
                  height: IMG_H * M,
                  maxWidth: 'none',
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  left: -6,
                  top: 3 * M,
                  width: (CLIP_INNER_W + 10) * sweep,
                  height: (Q.y1 - Q.y0 - 4) * M,
                  background: 'rgba(255,122,40,0.62)',
                  mixBlendMode: 'multiply',
                  borderRadius: 4,
                }}
              />
            </div>
          </div>
        )}
        {/* attribution under the clipping */}
        <div
          style={{
            position: 'absolute',
            left: CLIP_LEFT + 4,
            top: CLIP_TOP + CLIP_H + 16,
            fontFamily: fonts.mono,
            fontSize: 19,
            color: colors.muted,
            zIndex: 20,
            opacity: ramp(frame, B.heSays + 26, 14) * (1 - clipOut),
          }}
        >
          Alpöge's note · p. 1
        </div>

        {/* ---------------- left column ---------------- */}
        <div
          style={{
            position: 'absolute',
            left: COL,
            top: 150,
            fontFamily: fonts.display,
            fontStyle: 'italic',
            fontSize: 96,
            lineHeight: 1,
            letterSpacing: '-0.02em',
            color: colors.fg,
            whiteSpace: 'nowrap',
            ...enter(frame, -40, 22, 20), // date visible from frame 0 (poster frame)
          }}
        >
          November 20, 2026
        </div>

        {/* name card: "Levent Alpöge · number theorist · Anthropic" */}
        <div
          style={{
            position: 'absolute',
            left: COL,
            top: CARD_TOP,
            display: 'flex',
            alignItems: 'baseline',
            padding: '20px 30px 22px 28px',
            borderRadius: 16,
            border: `1px solid ${colors.line}`,
            background: colors.bgRaised,
            whiteSpace: 'nowrap',
            ...enter(frame, B.levent - 12, 18, 12),
          }}
        >
          <span style={{fontFamily: fonts.display, fontStyle: 'italic', fontSize: 60, lineHeight: 1, color: colors.fg}}>Levent Alpöge</span>
          <span style={{fontFamily: fonts.body, fontWeight: 300, fontSize: 28, color: colors.muted, ...enter(frame, B.levent - 4, 14, 6)}}>
            <span style={{margin: '0 14px', color: colors.faint}}>·</span>number theorist
          </span>
          <span style={{fontFamily: fonts.body, fontWeight: 300, fontSize: 28, color: colors.fg, ...enter(frame, B.anthropic - 4, 14, 6)}}>
            <span style={{margin: '0 14px', color: colors.faint}}>·</span>Anthropic
          </span>
        </div>

        {/* tag chips */}
        <Chip frame={frame} start={B.riemann - 2} top={CHIP_TOP[0]}>
          Riemann Hypothesis
        </Chip>
        <Chip frame={frame} start={B.broader - 2} top={CHIP_TOP[1]}>
          Generalized Riemann Hypothesis, for Dirichlet L-functions
        </Chip>
        <Chip frame={frame} start={B.lean - 4} top={CHIP_TOP[2]}>
          <span>Lean</span>
          <span style={{fontFamily: fonts.mono, fontSize: 19, color: colors.muted}}>lean.tar.gz · part01 … part14</span>
        </Chip>

        {/* small "machine-checkable" motif next to the Lean chip only (neutral color, no claim of a result) */}
        {chkIn > 0 && (
          <div style={{position: 'absolute', left: LEAN_CHIP_RIGHT + 18, top: CHIP_TOP[2] + 4, opacity: chkIn, transform: `scale(${0.85 + 0.15 * chkIn})`}}>
            <svg width={48} height={48} viewBox="0 0 48 48">
              <rect x={1} y={1} width={46} height={46} rx={11} fill="none" stroke={colors.muted} strokeWidth={1.5} />
              <line x1={11} y1={14} x2={24} y2={14} stroke={colors.faint} strokeWidth={2.5} strokeLinecap="round" />
              <line x1={11} y1={22} x2={20} y2={22} stroke={colors.faint} strokeWidth={2.5} strokeLinecap="round" />
              <line x1={11} y1={30} x2={17} y2={30} stroke={colors.faint} strokeWidth={2.5} strokeLinecap="round" />
              <path
                d="M22 30 L28 36 L39 19"
                fill="none"
                stroke={colors.fg}
                strokeWidth={3}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeDasharray={32}
                strokeDashoffset={32 * (1 - chkDraw)}
              />
            </svg>
          </div>
        )}

        {/* leader: footnote links on the page -> Lean chip */}
        {leader > 0 && leaderOut < 1 && (
          <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
            <path
              d={`M${fnX},${fnY} C${fnX - 220},${fnY} ${ldX + 260},${ldY} ${ldX},${ldY}`}
              fill="none"
              stroke={colors.accent}
              strokeWidth={1.6}
              strokeDasharray="1200"
              strokeDashoffset={1200 * (1 - leader)}
              opacity={0.75 * (1 - leaderOut)}
            />
            <circle cx={ldX} cy={ldY} r={4} fill={colors.accent} opacity={leader > 0.95 ? 1 - leaderOut : 0} />
          </svg>
        )}
      </AbsoluteFill>

      {/* ---------------- title ---------------- */}
      {pull > 0 && (
        <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
          <div style={{textAlign: 'center', marginTop: -60}}>
            <div
              style={{
                fontFamily: fonts.display,
                fontStyle: 'italic',
                fontSize: 150,
                lineHeight: 1,
                letterSpacing: '-0.02em',
                color: colors.fg,
                ...enter(frame, B.heres + 2, 24, 18),
              }}
            >
              The Riemann Hypothesis
            </div>
            <div
              style={{
                marginTop: 36,
                fontFamily: fonts.mono,
                fontSize: 24,
                letterSpacing: '0.2em',
                color: colors.muted,
                ...enter(frame, B.heres + 14, 20, 10),
              }}
            >
              WHAT IT SAYS · WHAT HAS BEEN CHECKED
            </div>
          </div>
        </AbsoluteFill>
      )}
    </SceneFrame>
  );
};
