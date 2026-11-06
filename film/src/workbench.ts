import React from 'react';
import { SHOTS, TOTAL_FRAMES } from './content';
import { BuildLogFilm, DisciplinesScene, NameScene, NumberScene, OutroScene, ProjectsScene, TimelineScene, ToolsScene, soundCues } from './Film';

const components = {
  name: NameScene,
  timeline: TimelineScene,
  projects: ProjectsScene,
  disciplines: DisciplinesScene,
  tools: ToolsScene,
  number: NumberScene,
  outro: OutroScene,
};

export const WORKBENCH = {
  name: 'Christo John · The Build Log',
  fps: 30,
  width: 1080,
  height: 1920,
  total: TOTAL_FRAMES,
  background: '#11171A',
  shots: SHOTS.map(shot => ({ id: shot.id, label: shot.label, from: shot.from, duration: shot.duration, component: components[shot.id] })),
  sfx: soundCues.map((cue, index) => ({ id: `sfx-${index + 1}`, from: Math.max(0, cue.at - 1), duration: 24, src: `audio/sfx/${cue.file}`, volume: cue.volume })),
  bgm: [{ from: 0, duration: TOTAL_FRAMES, src: 'audio/sonor-01-film-mix.mp3', volume: 1 }],
  original: () => React.createElement(BuildLogFilm, { bgm: true }),
};
