// All film metrics and repository names are transcribed from docs/github-audit/
// as generated on 2026-11-06 14:59 UTC. Keep this file audit-derived.
export const AUDIT = {
  firstDate: '05 APR 2023',
  lastDate: '06 NOV 2026',
  uniqueCommits: '15,882',
  repositoriesScanned: '125',
  years: ['2023', '2024', '2025', '2026'],
  projects: [
    { name: 'complaint-management-system', commits: '5,139' },
    { name: 'movie-watch-history-tracker-webapp', commits: '1,148' },
    { name: 'pbl-academy', commits: '907' },
    { name: 'mu-companion-webapp', commits: '622' },
    { name: 'virtual-background-photobooth', commits: '218' },
  ],
} as const;

export const SHOTS = [
  { id: 'name', from: 0, duration: 135, label: '01 Name' },
  { id: 'timeline', from: 135, duration: 180, label: '02 Timeline' },
  { id: 'projects', from: 315, duration: 240, label: '03 Selected work' },
  { id: 'disciplines', from: 555, duration: 180, label: '04 Disciplines' },
  { id: 'tools', from: 735, duration: 135, label: '05 Tools' },
  { id: 'number', from: 870, duration: 210, label: '06 The number' },
  { id: 'outro', from: 1080, duration: 180, label: '07 Christo John' },
] as const;

export const TOTAL_FRAMES = 1260;
