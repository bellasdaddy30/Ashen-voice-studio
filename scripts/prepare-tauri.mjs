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
async function firstExisting(paths,label){
  for(const p of paths) if(await exists(p)) return p;
  throw new Error(`${label} is missing. Checked:\n${paths.map(p=>'  '+p).join('\n')}\nRun npm install once in ${root}, then retry.`);
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
const kokoroVoices = join(nodeModules, 'kokoro-js', 'voices');
const ortWasm = await firstExisting([
  join(nodeModules, 'onnxruntime-web', 'dist', 'ort-wasm-simd-threaded.jsep.wasm'),
  join(nodeModules, '@huggingface', 'transformers', 'node_modules', 'onnxruntime-web', 'dist', 'ort-wasm-simd-threaded.jsep.wasm')
], 'ONNX Runtime WASM binary');

await mustExist(jszipSource, 'JSZip');
await mustExist(kokoroDist, 'kokoro-js');
await mustExist(kokoroVoices, 'Kokoro voice files');

const vendor = join(out, 'vendor');
const kokoroVendor = join(vendor, 'kokoro-js');
const ortVendor = join(vendor, 'ort');
await mkdir(kokoroVendor, { recursive: true });
await mkdir(ortVendor, { recursive: true });

await cp(jszipSource, join(vendor, 'jszip.min.js'));
await cp(kokoroDist, join(kokoroVendor, 'dist'), { recursive: true });
await cp(kokoroVoices, join(kokoroVendor, 'voices'), { recursive: true });
await cp(ortWasm, join(ortVendor, 'ort-wasm-simd-threaded.jsep.wasm'));

console.log('Prepared Ashen Voice Studio native assets in .tauri-dist');
console.log('  Kokoro browser runtime: bundled');
console.log('  Kokoro voice embeddings: bundled');
console.log('  ONNX WASM backend: bundled locally (no jsDelivr backend import)');
