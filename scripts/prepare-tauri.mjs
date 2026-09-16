import { cp, mkdir, readdir, rm, access } from 'node:fs/promises';
import { resolve, join } from 'node:path';

const root = resolve(process.cwd());
const out = join(root, '.tauri-dist');
const nodeModules = join(root, 'node_modules');

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

async function mustExist(path, label) {
  try { await access(path); }
  catch { throw new Error(`${label} is missing. Run npm install once in ${root}, then retry.`); }
}

await rm(out, { recursive: true, force: true });
await mkdir(out, { recursive: true });

for (const entry of await readdir(root, { withFileTypes: true })) {
  if (skipNames.has(entry.name)) continue;
  if (entry.name.startsWith('.')) continue;

  const src = join(root, entry.name);
  const dst = join(out, entry.name);
  await cp(src, dst, { recursive: true });
}

const jszipSource = join(nodeModules, 'jszip', 'dist', 'jszip.min.js');
const kokoroDist = join(nodeModules, 'kokoro-js', 'dist');
await mustExist(jszipSource, 'JSZip');
await mustExist(kokoroDist, 'kokoro-js');

const vendor = join(out, 'vendor');
await mkdir(vendor, { recursive: true });
await cp(jszipSource, join(vendor, 'jszip.min.js'));
await cp(kokoroDist, join(vendor, 'kokoro-js'), { recursive: true });

console.log('Prepared Ashen Voice Studio native assets in .tauri-dist');
