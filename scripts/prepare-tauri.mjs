import { cp, mkdir, readdir, rm } from 'node:fs/promises';
import { resolve, join } from 'node:path';

const root = resolve(process.cwd());
const out = join(root, '.tauri-dist');

const skipNames = new Set([
  '.git',
  '.github',
  '.tauri-dist',
  'node_modules',
  'src-tauri',
  'scripts',
  'package.json',
  'package-lock.json',
  'pnpm-lock.yaml',
  'yarn.lock'
]);

await rm(out, { recursive: true, force: true });
await mkdir(out, { recursive: true });

for (const entry of await readdir(root, { withFileTypes: true })) {
  if (skipNames.has(entry.name)) continue;
  if (entry.name.startsWith('.')) continue;

  const src = join(root, entry.name);
  const dst = join(out, entry.name);
  await cp(src, dst, { recursive: true });
}

console.log('Prepared Ashen Voice Studio web assets in .tauri-dist');
