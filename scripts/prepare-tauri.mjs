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
  'ios-native',
  'scripts',
  'package.json',
  'package-lock.json',
  'pnpm-lock.yaml',
  'yarn.lock'
]);

async function exists(path){try{await access(path);return true}catch{return false}}
async function mustExist(path, label) {
  if(!(await exists(path))) throw new Error(`${label} is missing. Run npm install once in ${root}, then retry.`);
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

// Native v1.4+ deliberately does not bundle Kokoro/ONNX WebAssembly. Desktop TTS
// lives behind the Tauri command bridge; iOS/Android can implement that exact same
// command contract with mobile-native runtimes later. Keeping models out of the
// WebView also avoids bloating future mobile bundles with a dead browser backend.
const jszipSource = join(nodeModules, 'jszip', 'dist', 'jszip.min.js');
await mustExist(jszipSource, 'JSZip');

const vendor = join(out, 'vendor');
await mkdir(vendor, { recursive: true });
await cp(jszipSource, join(vendor, 'jszip.min.js'));

console.log('Prepared Ashen Voice Studio native assets in .tauri-dist');
console.log('  JSZip: bundled locally');
console.log('  Voice models: not bundled in WebView');
console.log('  TTS transport: Tauri native command bridge (desktop now, mobile-safe contract)');
