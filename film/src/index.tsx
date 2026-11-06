import '@fontsource-variable/instrument-sans/index.css';
import '@fontsource/ibm-plex-mono/500.css';
import { Composition, registerRoot } from 'remotion';
import { BuildLogFilm, BuildLogCover } from './Film';
import { TOTAL_FRAMES } from './content';

const Root = () => (
  <>
    <Composition id="BuildLogFilm" component={BuildLogFilm} durationInFrames={TOTAL_FRAMES} fps={30} width={1080} height={1920} defaultProps={{ bgm: true }} />
    <Composition id="BuildLogCover" component={BuildLogCover} durationInFrames={1} fps={30} width={1080} height={1350} />
  </>
);

registerRoot(Root);
