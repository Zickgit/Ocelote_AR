// Genera el código QR que abre la página web del AR.
// Uso: node tools/make-qr.mjs [URL]
import QRCode from 'qrcode';
import { fileURLToPath } from 'url';
import path from 'path';

const url = process.argv[2] || 'https://zickgit.github.io/Ocelote_AR/';
const outDir = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'qr');
const opts = { errorCorrectionLevel: 'H', margin: 2, color: { dark: '#0f2660', light: '#ffffff' } };

await QRCode.toFile(path.join(outDir, 'ocelote-qr.png'), url, { ...opts, width: 1024 });
await QRCode.toFile(path.join(outDir, 'ocelote-qr.svg'), url, { ...opts, type: 'svg' });
console.log('QR generado para', url);
