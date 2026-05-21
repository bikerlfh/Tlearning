import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const HERE =
  typeof import.meta.dirname === "string"
    ? import.meta.dirname
    : dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
const SRC = resolve(ROOT, "public/icon.svg");
const SIZES = [192, 512] as const;

async function main() {
  const svg = readFileSync(SRC);
  for (const size of SIZES) {
    const out = resolve(ROOT, `public/icon-${size}.png`);
    await sharp(svg)
      .resize(size, size, {
        fit: "contain",
        background: { r: 99, g: 102, b: 241, alpha: 1 },
      })
      .png({ compressionLevel: 9 })
      .toFile(out);
    console.log(`Wrote ${out}`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
