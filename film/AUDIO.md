# Audio sources and mix

The film uses the first 42 seconds of **Sonor 01** by Eugenio Mininni, from [Mixkit](https://mixkit.co/free-stock-music/). Source file: `https://assets.mixkit.co/music/558/558.mp3`. The selected file was trimmed and set to 82% base gain, with a smoothly tapering lift of the first 22 seconds for phone playback. It fades in over 0.35 seconds and fades out from 36.5 to 42 seconds. The processed file is `public/audio/sonor-01-film-mix.mp3`. Mixkit's [free music license](https://mixkit.co/license/modal/musicFree/) permits social media video use. The music must remain part of the video, not distributed as a standalone track.

Music selection compared Sonor 01, Vastness (Andrew Ev), and Jungle Voices (Diego Nava). Source metadata and 1-second RMS analysis showed Sonor 01's first 42 seconds rising naturally toward the numerical reveal. Selection was based on that measured energy shape and in-video context; no claim of a human listening audition is made.

Three CC0 Freesound recordings provide the physical cues: a book close, a paper slide, and a mechanical switch. Their individual pages, exact license URLs, SHA-256 hashes, and measured peaks are in [`public/audio/sfx/audio-manifest.json`](public/audio/sfx/audio-manifest.json). [`FREESOUND-CREDITS.md`](public/audio/sfx/FREESOUND-CREDITS.md) is kept with the project. The files are high-quality MP3 previews, not uploader originals.

The no-music render uses the same composition and retains these SFX. The encoded files should be checked for duration, sample peak, integrated loudness, and the absence of clipped samples. An objective audio check does not replace listening on headphones and a phone speaker before posting.
