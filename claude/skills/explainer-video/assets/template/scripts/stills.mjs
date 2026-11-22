// Render one still at the midpoint of every narration line (captions on) plus each scene's last frames,
// then tile them into one contact sheet per scene. Bundles once, so it's fast (about 40 s for 60 stills).
//
// Usage: node scripts/stills.mjs                         # all scenes
//        node scripts/stills.mjs s01_hook,s02_proof
//        node scripts/stills.mjs s02_proof --frames 120,300,450 --scale 1   # chosen frames, full size (read small text)
// Output: out/lines/<scene>-L<n>-f<frame>.jpg, out/lines/index.json, out/linesheets/<scene>.jpg
// Look at every sheet: does each picture match its caption? Is anything clipped, overlapping the captions, or empty?
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import {execFileSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const outDir = path.join(root, 'out/lines');
const sheetDir = path.join(root, 'out/linesheets');
fs.mkdirSync(outDir, {recursive: true});
fs.mkdirSync(sheetDir, {recursive: true});
const tl = JSON.parse(fs.readFileSync(path.join(root, 'src/data/timeline.json'), 'utf8'));
const argv = process.argv.slice(2);
const opt = (k) => (argv.includes(k) ? argv[argv.indexOf(k) + 1] : null);
const positional = argv.filter((a, i) => !a.startsWith('--') && !(i > 0 && argv[i - 1].startsWith('--')));
const only = positional[0] ? positional[0].split(',') : null;
const custom = opt('--frames') ? opt('--frames').split(',').map(Number) : null;
const scale = opt('--scale') ? Number(opt('--scale')) : 0.6;
const serveUrl = await bundle({entryPoint: path.join(root, 'src/index.ts'), publicDir: path.join(root, 'public')});
const index = [];
for (const s of tl.scenes) {
  if (only && !only.includes(s.id)) continue;
  for (const f of fs.readdirSync(outDir)) if (f.startsWith(s.id + '-')) fs.rmSync(path.join(outDir, f));
  const comp = await selectComposition({serveUrl, id: `Scene-${s.id.replace(/_/g, '-')}`});
  const frames = custom
    ? custom.map((f) => ({tag: 'F', frame: Math.min(comp.durationInFrames - 1, f), caption: '(chosen frame)'}))
    : s.lines.map((l, i) => ({tag: `L${i}`, frame: Math.round((s.leadIn + (l.start + l.end) / 2) * tl.fps), caption: l.caption}));
  if (!custom) frames.push({tag: 'end', frame: comp.durationInFrames - 8, caption: '(last frames)'});
  const files = [];
  for (const f of frames) {
    const output = path.join(outDir, `${s.id}-${f.tag}-f${String(f.frame).padStart(4, '0')}.jpg`);
    await renderStill({composition: comp, serveUrl, output, frame: f.frame, imageFormat: 'jpeg', jpegQuality: 82, scale});
    files.push(output);
    index.push({scene: s.id, ...f, file: path.basename(output)});
  }
  // contact sheet: 3 columns of 640x360 tiles
  const cols = 3;
  const inputs = files.flatMap((f) => ['-i', f]);
  const layout = files.map((_, i) => `${(i % cols) * 640}_${Math.floor(i / cols) * 360}`).join('|');
  const filter = files.map((_, i) => `[${i}:v]scale=640:360[v${i}]`).join(';') + ';' + files.map((_, i) => `[v${i}]`).join('') + `xstack=inputs=${files.length}:layout=${layout}:fill=black`;
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', ...inputs, '-filter_complex', filter, path.join(sheetDir, `${s.id}.jpg`)]);
  console.log('done', s.id, `(${files.length} stills)`);
}
fs.writeFileSync(path.join(outDir, 'index.json'), JSON.stringify(index, null, 1));
