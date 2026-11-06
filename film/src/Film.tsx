import React from 'react';
import { AbsoluteFill, Audio, Easing, interpolate, Sequence, staticFile, useCurrentFrame } from 'remotion';
import { AUDIT, SHOTS } from './content';
import { MONTHLY_COMMITS } from './audit-series';

const C = { dark: '#11171A', paper: '#F3F1EA', steel: '#7C8A89', citron: '#D3EE8D', ink: '#182022' };
const SANS = '"Instrument Sans Variable", Arial, sans-serif';
const MONO = '"IBM Plex Mono", Consolas, monospace';
const clamp = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const };
const out = Easing.bezier(0.16, 1, 0.3, 1);
const inOut = Easing.bezier(0.4, 0, 0.2, 1);
const tween = (f: number, a: number, b: number, easing = out) => interpolate(f, [a, b], [0, 1], { ...clamp, easing });

const Grain: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: 'none', opacity: 0.22, mixBlendMode: 'multiply', backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 150 150\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'n\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'.8\' numOctaves=\'3\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23n)\' opacity=\'.18\'/%3E%3C/svg%3E")' }} />
);

const Chrome: React.FC<{ folio: string; section: string; light?: boolean; footer?: string }> = ({ folio, section, light = false, footer }) => {
  const color = light ? C.ink : C.paper;
  const quiet = light ? '#788683' : C.steel;
  return <>
    <div style={{ position: 'absolute', left: 96, right: 96, top: 285, display: 'flex', justifyContent: 'space-between', alignItems: 'center', font: `500 26px ${MONO}`, letterSpacing: '0.13em', color: quiet }}>
      <span>{section}</span><span>{folio} / 07</span>
    </div>
    <div style={{ position: 'absolute', left: 96, right: 96, top: 346, height: 1, background: light ? '#4B58583D' : '#B7C7C433' }} />
    <div style={{ position: 'absolute', left: 96, right: 96, bottom: 310, height: 1, background: light ? '#4B58583D' : '#B7C7C433' }} />
    {footer && <div style={{ position: 'absolute', left: 96, bottom: 266, font: `500 24px ${MONO}`, letterSpacing: '0.08em', color: quiet }}>{footer}</div>}
    <div style={{ position: 'absolute', right: 96, bottom: 267, width: 38, height: 3, background: light ? C.ink : C.citron }} />
    <Grain />
  </>;
};

const Scene: React.FC<{ children: React.ReactNode; light?: boolean }> = ({ children, light = false }) => (
  <AbsoluteFill style={{ background: light ? C.paper : C.dark, color: light ? C.ink : C.paper, overflow: 'hidden', fontFamily: SANS }}>{children}</AbsoluteFill>
);

const RevealLine: React.FC<{ text: string; frame: number; at: number; fontSize: number; color?: string; weight?: number; lineHeight?: number }> = ({ text, frame, at, fontSize, color, weight = 730, lineHeight = 1 }) => {
  const t = tween(frame, at, at + 25);
  return <div style={{ overflow: 'hidden', height: fontSize * lineHeight * 1.08 }}>
    <div style={{ fontSize, fontWeight: weight, letterSpacing: '-0.067em', lineHeight, color, transform: `translateY(${(1 - t) * 115}%)`, filter: `blur(${(1 - t) * 7}px)`, opacity: t }}>{text}</div>
  </div>;
};

export const NameScene: React.FC = () => {
  const f = useCurrentFrame();
  const rule = tween(f, 0, 35);
  const fade = interpolate(f, [119, 135], [1, 0], clamp);
  return <Scene>
    <Chrome folio="01" section="THE BUILD LOG" footer="2023 — 2026" />
    <div style={{ position: 'absolute', left: 96, top: 555, width: 95, height: 95, borderLeft: '5px solid ' + C.citron, borderTop: '5px solid ' + C.citron, clipPath: `inset(0 ${100 - rule * 100}% ${100 - rule * 100}% 0)`, opacity: 0.9 }} />
    <div style={{ position: 'absolute', left: 88, top: 700, width: 900, opacity: fade }}>
      <RevealLine text="CHRISTO" frame={f} at={18} fontSize={194} />
      <div style={{ display: 'flex', alignItems: 'baseline' }}><RevealLine text="JOHN" frame={f} at={27} fontSize={194} /><span style={{ fontSize: 195, fontWeight: 730, lineHeight: 1, color: C.citron, opacity: tween(f, 48, 58) }}>.</span></div>
    </div>
    <div style={{ position: 'absolute', left: 96, top: 1168, font: `500 27px ${MONO}`, letterSpacing: '0.115em', color: C.steel, opacity: tween(f, 54, 72) }}>ENGINEERING / DESIGN / AI</div>
  </Scene>;
};

export const TimelineScene: React.FC = () => {
  const f = useCurrentFrame();
  const travel = interpolate(f, [0, 28, 114, 140], [0, 0.06, 0.91, 1], { ...clamp, easing: inOut });
  const worldY = 700 - travel * 1260;
  return <Scene light>
    <Chrome folio="02" section="A RECORD OF BUILDING" light footer={`${AUDIT.firstDate} — ${AUDIT.lastDate}`} />
    <div style={{ position: 'absolute', left: 108, top: 445, height: 940, width: 2, background: '#5D716B55' }} />
    <div style={{ position: 'absolute', left: 107, top: 445, height: 940 * travel, width: 4, background: C.ink }} />
    <div style={{ position: 'absolute', inset: '405px 0 370px', overflow: 'hidden' }}>
    {AUDIT.years.map((year, i) => {
      const yy = worldY + i * 420;
      const distance = Math.abs(yy - 700);
      const opacity = Math.min(1, Math.max(0.06, 1 - distance / 520));
      return <div key={year} style={{ position: 'absolute', left: 76, top: yy, width: 900, opacity }}>
        <div style={{ position: 'absolute', left: 26, top: 66, width: 17, height: 17, borderRadius: '50%', background: i === 3 ? C.citron : C.ink, border: '4px solid ' + C.paper }} />
        <div style={{ marginLeft: 90, fontSize: 235, fontWeight: 760, letterSpacing: '-0.09em', lineHeight: 1 }}>{year}</div>
        <div style={{ marginLeft: 100, marginTop: 10, font: `500 27px ${MONO}`, letterSpacing: '0.08em', color: '#798481' }}>{i === 0 ? AUDIT.firstDate : i === 3 ? AUDIT.lastDate : ''}</div>
      </div>;
    })}
    </div>
  </Scene>;
};

export const ProjectsScene: React.FC = () => {
  const f = useCurrentFrame();
  const focus = Math.min(4, Math.floor(Math.max(0, f - 28) / 41));
  return <Scene>
    <Chrome folio="03" section="SELECTED WORK" footer="PUBLIC REPOSITORIES / AUDIT 2026" />
    <div style={{ position: 'absolute', left: 96, top: 420, width: 888 }}>
      {AUDIT.projects.map((p, i) => {
        const y = i * 192;
        const t = tween(f, 8 + i * 15, 27 + i * 15);
        const isFocus = i === focus;
        const titleSize = p.name.length > 34 ? 46 : p.name.length > 26 ? 51 : 58;
        return <div key={p.name} style={{ position: 'absolute', top: y, left: 0, right: 0, minHeight: 166, borderBottom: '1px solid #BAC9C32A', display: 'flex', alignItems: 'center', transform: `translateY(${(1 - t) * 45}px)`, opacity: t * (isFocus ? 1 : 0.63) }}>
          <span style={{ width: 68, alignSelf: 'flex-start', paddingTop: 31, color: isFocus ? C.citron : C.steel, font: `500 24px ${MONO}` }}>{String(i + 1).padStart(2, '0')}</span>
          <div style={{ flex: 1, paddingRight: 15, fontSize: titleSize, fontWeight: 680, lineHeight: 1.06, letterSpacing: '-0.052em', overflowWrap: 'anywhere' }}>{p.name}</div>
          <div style={{ alignSelf: 'flex-end', paddingBottom: 25, color: isFocus ? C.citron : C.steel, font: `500 27px ${MONO}`, whiteSpace: 'nowrap' }}>{p.commits}</div>
        </div>;
      })}
    </div>
    <div style={{ position: 'absolute', right: 96, top: 1422, color: C.steel, font: `500 23px ${MONO}`, letterSpacing: '0.08em', opacity: tween(f, 100, 130) }}>ATTRIBUTED COMMITS / REPOSITORY</div>
  </Scene>;
};

export const DisciplinesScene: React.FC = () => {
  const f = useCurrentFrame();
  const lines = [
    { no: '01', text: 'DESIGN THINKING', at: 9 },
    { no: '02', text: 'FULL STACK', at: 48 },
    { no: '03', text: 'PLANNING TO\nDEPLOYMENT', at: 88 },
  ];
  return <Scene light>
    <Chrome folio="04" section="THE PRACTICE" light footer="FROM IDEA TO SOFTWARE" />
    <div style={{ position: 'absolute', left: 95, top: 470, right: 95 }}>
      {lines.map((line, i) => <div key={line.no} style={{ height: i === 2 ? 298 : 255, borderBottom: '1px solid #29373433', paddingTop: 28, display: 'flex', gap: 22 }}>
        <span style={{ paddingTop: 17, width: 62, font: `500 27px ${MONO}`, color: '#87918D', opacity: tween(f, line.at, line.at + 12) }}>{line.no}</span>
        <div style={{ fontSize: i === 2 ? 83 : 104, lineHeight: 0.96, letterSpacing: '-0.068em', fontWeight: 735, whiteSpace: 'pre-line', transform: `translateY(${(1 - tween(f, line.at, line.at + 25)) * 42}px)`, opacity: tween(f, line.at, line.at + 25) }}>{line.text}</div>
      </div>)}
    </div>
  </Scene>;
};

export const ToolsScene: React.FC = () => {
  const f = useCurrentFrame();
  const tools = ['FIGMA', 'NEXT.JS', 'SUPABASE', 'VS CODE', 'CLAUDE', 'CODEX'];
  return <Scene>
    <Chrome folio="05" section="TOOLS OF THE WORK" footer="DESIGN / BUILD / REVIEW" />
    <div style={{ position: 'absolute', left: 96, top: 492, width: 888, display: 'grid', gridTemplateColumns: '1fr 1fr', columnGap: 38 }}>
      {tools.map((tool, i) => {
        const t = tween(f, 9 + i * 11, 28 + i * 11);
        return <div key={tool} style={{ height: 242, borderTop: '1px solid #C8D7D033', position: 'relative', transform: `translateY(${(1 - t) * 35}px)`, opacity: t }}>
          <div style={{ position: 'absolute', left: 0, top: 29, font: `500 24px ${MONO}`, color: C.citron }}>{String(i + 1).padStart(2, '0')}</div>
          <div style={{ position: 'absolute', left: 0, top: 77, fontSize: tool.length > 7 ? 62 : 76, fontWeight: 700, letterSpacing: '-0.06em' }}>{tool}</div>
        </div>;
      })}
    </div>
  </Scene>;
};

export const NumberScene: React.FC = () => {
  const f = useCurrentFrame();
  const compress = tween(f, 8, 54, inOut);
  const reveal = tween(f, 58, 93);
  return <Scene>
    <Chrome folio="06" section="THE WORK, IN NUMBERS" footer="CHRISTO JOHN / NOV 2026" />
    <div style={{ position: 'absolute', left: 96, top: 444, font: `500 23px ${MONO}`, letterSpacing: '0.1em', color: C.steel, opacity: tween(f, 0, 24) }}>MONTHLY ACTIVITY / 2023—2026</div>
    <div style={{ position: 'absolute', left: 96, top: 535, width: 888, height: 92, display: 'flex', alignItems: 'flex-end', gap: 4 }}>
      {MONTHLY_COMMITS.map((item, i) => {
        const progress = tween(f, 5 + i * 1.15, 24 + i * 1.15);
        const height = 7 + Math.sqrt(item.commits / 4979) * 82;
        return <div key={item.month} style={{ flex: 1, height: height * progress, background: i >= 35 ? C.citron : '#759088', opacity: i >= 35 ? 0.92 : 0.55 }} />;
      })}
    </div>
    <div style={{ position: 'absolute', left: 96, right: 96, top: 664, height: 2, background: C.steel, transform: `scaleX(${1 - compress * 0.75})`, transformOrigin: 'left center', opacity: 1 - reveal }} />
    <div style={{ position: 'absolute', left: 89, right: 89, top: 676, fontSize: 213, lineHeight: 1, fontWeight: 760, letterSpacing: '-0.095em', fontVariantNumeric: 'tabular-nums', overflow: 'hidden' }}>
      <div style={{ transform: `translateY(${(1 - reveal) * 105}%)`, filter: `blur(${(1 - reveal) * 11}px)`, opacity: reveal, whiteSpace: 'nowrap' }}>{AUDIT.uniqueCommits}<span style={{ color: C.citron }}>.</span></div>
    </div>
    <div style={{ position: 'absolute', left: 97, top: 933, fontSize: 49, lineHeight: 1.12, letterSpacing: '0.02em', fontWeight: 680, opacity: tween(f, 86, 110) }}>UNIQUE ATTRIBUTED<br />COMMITS</div>
    <div style={{ position: 'absolute', left: 97, top: 1175, width: 875, height: 1, background: '#B3C9BA55', transform: `scaleX(${tween(f, 102, 130)})`, transformOrigin: 'left center' }} />
    <div style={{ position: 'absolute', left: 97, top: 1225, font: `500 31px ${MONO}`, letterSpacing: '0.05em', color: C.steel, opacity: tween(f, 92, 116) }}>{AUDIT.repositoriesScanned} REPOSITORIES SCANNED</div>
  </Scene>;
};

export const OutroScene: React.FC = () => {
  const f = useCurrentFrame();
  const line = tween(f, 0, 35);
  const title = tween(f, 24, 58);
  const sub = tween(f, 61, 96);
  return <Scene>
    <Chrome folio="07" section="THE BUILD LOG" footer="05 APR 2023 — 06 NOV 2026" />
    <div style={{ position: 'absolute', left: 96, top: 586, width: 6, height: 560 * line, background: C.citron }} />
    <div style={{ position: 'absolute', left: 139, top: 670, fontSize: 150, fontWeight: 750, letterSpacing: '-0.075em', lineHeight: 0.99, opacity: title, transform: `translateY(${(1 - title) * 70}px)` }}>CHRISTO<br />JOHN<span style={{ color: C.citron }}>.</span></div>
    <div style={{ position: 'absolute', left: 141, top: 1110, width: 680, fontSize: 55, fontWeight: 610, lineHeight: 1.06, letterSpacing: '-0.03em', color: '#D3DCD3', opacity: sub, transform: `translateY(${(1 - sub) * 25}px)` }}>ASPIRING AI<br />PRODUCT ENGINEER</div>
  </Scene>;
};

const shotComponents: Record<string, React.FC> = {
  name: NameScene, timeline: TimelineScene, projects: ProjectsScene, disciplines: DisciplinesScene,
  tools: ToolsScene, number: NumberScene, outro: OutroScene,
};

export const soundCues = [
  { at: SHOTS[0].from + 32, file: 'fs-319809.mp3', volume: 0.16 },
  ...[27, 67, 106, 145].map(offset => ({ at: SHOTS[1].from + offset, file: 'fs-830459.mp3', volume: 0.3 })),
  ...[35, 76, 117].map(offset => ({ at: SHOTS[2].from + offset - 4, file: 'fs-470189.mp3', volume: 4 })),
  { at: SHOTS[5].from + 76, file: 'fs-319809.mp3', volume: 0.2 },
] as const;

export const BuildLogFilm: React.FC<{ bgm: boolean }> = ({ bgm }) => (
  <AbsoluteFill style={{ backgroundColor: C.dark }}>
    {SHOTS.map(s => {
      const Component = shotComponents[s.id];
      return <Sequence key={s.id} from={s.from} durationInFrames={s.duration} name={s.label}><Component /></Sequence>;
    })}
    {bgm && <Audio src={staticFile('audio/sonor-01-film-mix.mp3')} volume={1} />}
    {soundCues.map((cue, i) => <Sequence key={i} from={Math.max(0, cue.at - 1)} durationInFrames={24} name={`SFX ${i + 1}`}><Audio src={staticFile(`audio/sfx/${cue.file}`)} volume={cue.volume} /></Sequence>)}
  </AbsoluteFill>
);

export const BuildLogCover: React.FC = () => (
  <AbsoluteFill style={{ background: C.dark, color: C.paper, fontFamily: SANS, overflow: 'hidden' }}>
    <div style={{ position: 'absolute', top: 160, left: 96, font: `500 28px ${MONO}`, letterSpacing: '0.13em', color: C.steel }}>THE BUILD LOG</div>
    <div style={{ position: 'absolute', top: 236, left: 96, right: 96, height: 1, background: '#B7C7C433' }} />
    <div style={{ position: 'absolute', top: 428, left: 96, width: 78, height: 78, borderTop: '5px solid ' + C.citron, borderLeft: '5px solid ' + C.citron }} />
    <div style={{ position: 'absolute', left: 89, top: 575, fontSize: 193, fontWeight: 750, letterSpacing: '-0.074em', lineHeight: 0.88 }}>CHRISTO<br />JOHN<span style={{ color: C.citron }}>.</span></div>
    <div style={{ position: 'absolute', left: 96, bottom: 143, font: `500 27px ${MONO}`, letterSpacing: '0.11em', color: C.steel }}>2023 — 2026</div>
    <Grain />
  </AbsoluteFill>
);
