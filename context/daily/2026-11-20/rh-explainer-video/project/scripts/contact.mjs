// Bundle once, render sample stills for every scene, write a contact sheet per scene.
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const outDir = path.join(root, 'out/contact');
fs.mkdirSync(outDir, {recursive: true});
const timeline = JSON.parse(fs.readFileSync(path.join(root, 'src/data/timeline.json'), 'utf8'));
const only = process.argv[2] ? process.argv[2].split(',') : null;
const fracs = process.argv[3] ? process.argv[3].split(',').map(Number) : [0.15, 0.4, 0.65, 0.9];
const serveUrl = await bundle({entryPoint: path.join(root, 'src/index.ts'), publicDir: path.join(root, 'public')});
for (const s of timeline.scenes) {
  if (only && !only.includes(s.id)) continue;
  const id = `Scene-${s.id.replace(/_/g, '-')}`;
  const comp = await selectComposition({serveUrl, id});
  for (const f of fracs) {
    const frame = Math.min(comp.durationInFrames - 1, Math.round(comp.durationInFrames * f));
    const output = path.join(outDir, `${s.id}-f${String(frame).padStart(4, '0')}.jpg`);
    await renderStill({composition: comp, serveUrl, output, frame, imageFormat: 'jpeg', jpegQuality: 80, scale: 0.5});
    console.log(output);
  }
}
