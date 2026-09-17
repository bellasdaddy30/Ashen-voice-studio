import { cp, mkdir, readdir, rm, access, readFile, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';

const root = resolve(process.cwd());
const out = join(root, 'ios-native', 'Resources', 'Web');
const nodeModules = join(root, 'node_modules');

const skipNames = new Set([
  '.git', '.github', '.tauri-dist', 'node_modules', 'src-tauri', 'scripts',
  'ios-native', 'package.json', 'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock'
]);

async function exists(path){try{await access(path);return true}catch{return false}}

await rm(out, { recursive: true, force: true });
await mkdir(out, { recursive: true });

for (const entry of await readdir(root, { withFileTypes: true })) {
  if (skipNames.has(entry.name) || entry.name.startsWith('.')) continue;
  await cp(join(root, entry.name), join(out, entry.name), { recursive: true });
}

const vendor = join(out, 'vendor');
await mkdir(vendor, { recursive: true });
const jszip = join(nodeModules, 'jszip', 'dist', 'jszip.min.js');
if (!(await exists(jszip))) throw new Error('JSZip is missing. Run npm install first.');
await cp(jszip, join(vendor, 'jszip.min.js'));

// WKWebView loads the UI from a file URL, so root-relative /foo.js paths would point
// at the filesystem root. Make all bundled web references relative for iOS only.
const indexPath = join(out, 'index.html');
let html = await readFile(indexPath, 'utf8');
html = html
  .replaceAll('src="/', 'src="')
  .replaceAll("src='/", "src='")
  .replaceAll('href="/', 'href="')
  .replaceAll("href='/", "href='");
await writeFile(indexPath, html);

console.log('Prepared Ashen Voice Studio iOS web assets in ios-native/Resources/Web');
