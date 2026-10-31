/**
 * Privacy-preserving GitHub profile metrics.
 * Reads repository metadata and the user's aggregate contribution calendar.
 * NEVER reads repository code, commit messages, customer names, or private paths.
 * NEVER serializes private repository names into public SVGs or logs.
 *
 * node scripts/update-stats.mjs --snapshot   Generate a verified 2026-10-28 baseline
 * GH_STATS_TOKEN=... node scripts/update-stats.mjs   Refresh authenticated metrics
 */
import fs from 'node:fs/promises';
import path from 'node:path';

const outDir = path.resolve('assets');
const USERNAME = 'christo-zero-john';
const snapshot = process.argv.includes('--snapshot');
const verified = { public: 89, private: 32, collaborators: 4, owned: 121 };

function fmt(number) { return new Intl.NumberFormat('en-US').format(number); }
function safe(text) {return String(text).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&apos;');}
function nowDate() { return new Date().toISOString().slice(0,10); }
async function graphql(query, variables={}) {
  if (!process.env.GH_STATS_TOKEN) throw new Error('GH_STATS_TOKEN is required; default GITHUB_TOKEN cannot read all private repositories.');
  const response = await fetch('https://api.github.com/graphql',{
    method:'POST',
    headers:{ 'Authorization':`Bearer ${process.env.GH_STATS_TOKEN}`, 'Accept':'application/vnd.github+json','Content-Type':'application/json','User-Agent':'github-profile-private-safe-stats' },
    body:JSON.stringify({query,variables})
  });
  if (!response.ok) throw new Error(`GitHub GraphQL request failed (HTTP ${response.status}); verify token scopes and access.`);
  const payload = await response.json();
  if(payload.errors?.length) throw new Error(`GitHub GraphQL rejected query: ${payload.errors.map(e=>e.message).join('; ').slice(0,250)}`);
  return payload.data;
}

const REPOS_QUERY = `query RepoFootprint($cursor: String) {
  viewer { login repositories(first: 100, after: $cursor, affiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER]) {
    nodes { nameWithOwner isPrivate }
    pageInfo { hasNextPage endCursor }
  } }
}`;
const CONTRIBUTIONS_QUERY = `query ContributorActivity($from: DateTime!, $to: DateTime!) {
  viewer { contributionsCollection(from: $from, to: $to) {
    contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    totalCommitContributions totalPullRequestContributions totalPullRequestReviewContributions
  } }
}`;

async function loadAccount() {
  let cursor = null, pages=0;
  const discovered = new Map();
  while(true) {
    const response=await graphql(REPOS_QUERY,{cursor});
    if(response.viewer.login.toLowerCase()!==USERNAME) throw new Error('Token belongs to a different GitHub account.');
    const repositories=response.viewer.repositories;
    for(const repo of repositories.nodes) discovered.set(repo.nameWithOwner.toLowerCase(), {owner:repo.nameWithOwner.split('/')[0].toLowerCase(),isPrivate:repo.isPrivate});
    pages++;
    if(!repositories.pageInfo.hasNextPage) break;
    cursor=repositories.pageInfo.endCursor;
    if(pages>100) throw new Error('Pagination guard exceeded');
  }
  const repos=[...discovered.values()];
  const own=repos.filter(r=>r.owner===USERNAME);
  const counts={owned:own.length,private:own.filter(r=>r.isPrivate).length,public:own.filter(r=>!r.isPrivate).length,collaborators:repos.filter(r=>r.owner!==USERNAME).length};
  const minimum = Number(process.env.MIN_EXPECTED_PRIVATE_REPOS ?? '32');
  if (!Number.isSafeInteger(minimum) || minimum < 1) throw new Error('Invalid minimum-private-repo guard.');
  if(counts.private < minimum) throw new Error(`Private access incomplete (${counts.private} < ${minimum}); refusing to overwrite current stats.`);

  const to = new Date();
  const from = new Date(to.getTime() - 365*24*60*60*1000);
  const contributions=(await graphql(CONTRIBUTIONS_QUERY,{from:from.toISOString(),to:to.toISOString()})).viewer.contributionsCollection;
  return {counts, contributions, date:nowDate()};
}

function surface(width, height) {
  return `<defs>
    <linearGradient id="dark" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0B1013"/><stop offset="1" stop-color="#182022"/></linearGradient>
    <linearGradient id="lime" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#CAF36D"/><stop offset="1" stop-color="#A6D958"/></linearGradient>
    <pattern id="texture" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#D8E7D3" stroke-opacity=".035"/></pattern>
    <style>
      .base { font-family: Inter, 'Segoe UI', Arial, sans-serif; }
      .mono { font-family: 'SFMono-Regular', Consolas, monospace; }
      .sub { font-size: 13px; font-weight: 600; letter-spacing: 2.6px; fill: #CAF36D; }
      .figure { font-size: 76px; font-weight: 750; fill: #F3F5EF; letter-spacing: -3.8px; }
      .desc { font-size: 15px; font-weight: 600; letter-spacing: 1.5px; fill: #A2B3AA; }
      .note { font-size: 13px; fill: #92A79B; }
      @keyframes pulse { 0%,100%{opacity:.55}50%{opacity:1} }
      .animate-glow {animation:pulse 4s ease-in-out infinite}
      @media(prefers-reduced-motion:reduce){*{animation:none!important}}
    </style>
  </defs>
  <rect width="${width}" height="${height}" rx="12" fill="url(#dark)"/>
  <rect width="${width}" height="${height}" rx="12" fill="url(#texture)"/>
  <rect x="1" y="1" width="${width-2}" height="${height-2}" rx="11" fill="none" stroke="#405149" stroke-opacity=".75"/>`;
}

function repoCard(counts,date) {
  const metrics = [
    {value:counts.owned,label:'OWNED REPOSITORIES'},
    {value:counts.public,label:'PUBLIC'},
    {value:counts.private,label:'PRIVATE'},
    {value:counts.collaborators,label:'COLLABORATIONS'}
  ];
  const cells = metrics.map((m,i) => {
    const x = 57 + i * 294;
    const highlight = i===2 ? '#CAF36D' : '#F3F5EF';
    return `<g class="base">
      <text x="${x}" y="155" class="figure" fill="${highlight}" style="fill:${highlight}">${fmt(m.value)}</text>
      <text x="${x+2}" y="190" class="desc">${safe(m.label)}</text>
      ${i<3?`<line x1="${x+255}" y1="98" x2="${x+255}" y2="192" stroke="#52625B" stroke-opacity=".52"/>`:''}
    </g>`;
  }).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 225" role="img" aria-label="${counts.owned} owned repositories, ${counts.public} public, ${counts.private} private, and ${counts.collaborators} collaborations">
    ${surface(1200,225)}
    <rect x="56" y="26" width="9" height="9" rx="2" fill="#CAF36D" class="animate-glow"/>
    <text x="77" y="35" class="sub mono">THE BUILD LOG</text>
    <text x="1144" y="35" text-anchor="end" class="note mono">UPDATED ${safe(date)}</text>
    ${cells}
    <rect x="56" y="207" width="1088" height="1" fill="#4D5B54" opacity=".55"/>
    <rect x="56" y="206" width="120" height="3" fill="#CAF36D"/>
  </svg>`;
}

function contributionCard(record,date) {
  const {contributions}=record;
  if(!contributions) {
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 244" role="img" aria-label="Private-safe contribution chart activates after authenticated GitHub Actions setup">
    ${surface(1200,244)}
    <text class="sub mono" x="44" y="48">GITHUB / CONTRIBUTION SIGNAL</text>
    <text class="base" x="44" y="116" fill="#F3F5EF" font-weight="650" font-size="27">Private-inclusive activity, without exposing private work.</text>
    <text class="base" x="44" y="157" fill="#ACBCB0" font-size="18">Connect the read-only GitHub statistics token and run the included workflow.</text>
    <rect x="44" y="185" width="1094" height="5" rx="2.5" fill="#415048"/>
    <rect x="44" y="185" width="270" height="5" rx="2.5" fill="url(#lime)" class="animate-glow"/>
    </svg>`;
  }
  const coll=contributions.contributionCalendar;
  const days=coll.weeks.flatMap(w=>w.contributionDays);
  const arr=coll.weeks.slice(-53);
  const sizes=[0,1,3,7];
  let cells='';
  for(let w=0;w<arr.length;w++) {
    for(let d=0;d<7;d++) {
      const day=arr[w].contributionDays[d];
      const count=day?.contributionCount??0;
      const tone=count===0?'#27332C':count<=2?'#45683B':count<=6?'#739C49':count<=12?'#A0C956':'#CEF17C';
      const x=43+w*16.8, y=91+d*17.5;
      cells+=`<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="13.5" height="13.5" rx="3" fill="${tone}"><title>${count} contributions</title></rect>`;
    }
  }
  const total=coll.totalContributions;
  const stats=`<text class="figure" x="1003" y="123" font-size="62" text-anchor="middle">${fmt(total)}</text>
    <text class="desc" x="1003" y="151" font-size="15" text-anchor="middle">CONTRIBUTIONS / 12 MONTHS</text>
    <text class="note mono" x="1003" y="182" text-anchor="middle">${fmt(contributions.totalCommitContributions)} commits · ${fmt(contributions.totalPullRequestContributions)} PRs</text>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 256" role="img" aria-label="${total} GitHub contributions during the last 12 months; private contributions included when eligible">
    ${surface(1200,256)}
    <text class="sub mono" x="44" y="50">GITHUB / LAST 12 MONTHS</text>
    <text class="note mono" x="1144" y="50" text-anchor="end">UPDATED ${safe(date)}</text>
    ${cells}
    <line x1="956" y1="85" x2="956" y2="216" stroke="#53645B"/>
    ${stats}
    <text class="note" x="44" y="237">GitHub contribution calendar · 12 months</text>
  </svg>`;
}

async function main(){
  const record=snapshot?{counts:verified,contributions:null,date:'2026-10-31'}:await loadAccount();
  await fs.mkdir(outDir,{recursive:true});
  await Promise.all([
    fs.writeFile(path.join(outDir,'engineering-stats.svg'), repoCard(record.counts,record.date)),
    fs.writeFile(path.join(outDir,'contribution-grid.svg'), contributionCard(record,record.date))
  ]);
  // Only coarse aggregates are logged. Never expose repository names or API payloads.
  process.stdout.write(`SVG cards refreshed: ${record.counts.owned} owned, ${record.counts.private} private, ${record.counts.collaborators} collaborations.\n`);
}
main().catch(e=>{ console.error(`Statistics update failed: ${e.message}`); process.exitCode=1; });
