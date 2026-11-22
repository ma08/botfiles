// Render one still at the midpoint of every narration line (captions on), plus each scene's last frame.
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const outDir = path.join(root, 'out/lines');
fs.rmSync(outDir, {recursive: true, force: true});
fs.mkdirSync(outDir, {recursive: true});
const tl = JSON.parse(fs.readFileSync(path.join(root, 'src/data/timeline.json'), 'utf8'));
const only = process.argv[2] ? process.argv[2].split(',') : null;
const serveUrl = await bundle({entryPoint: path.join(root, 'src/index.ts'), publicDir: path.join(root, 'public')});
const index = [];
for (const s of tl.scenes) {
  if (only && !only.includes(s.id)) continue;
  const comp = await selectComposition({serveUrl, id: `Scene-${s.id.replace(/_/g, '-')}`});
  const frames = s.lines.map((l, i) => ({tag: `L${i}`, frame: Math.round((s.leadIn + (l.start + l.end) / 2) * tl.fps), caption: l.caption}));
  frames.push({tag: 'end', frame: comp.durationInFrames - 8, caption: '(last frames)'});
  for (const f of frames) {
    const output = path.join(outDir, `${s.id}-${f.tag}-f${String(f.frame).padStart(4, '0')}.jpg`);
    await renderStill({composition: comp, serveUrl, output, frame: f.frame, imageFormat: 'jpeg', jpegQuality: 82, scale: 0.6});
    index.push({scene: s.id, ...f, file: path.basename(output)});
  }
  console.log('done', s.id);
}
fs.writeFileSync(path.join(outDir, 'index.json'), JSON.stringify(index, null, 1));
