const fs = require('fs');
const path = 'api/openapi.json';

// Read as raw bytes
const buf = fs.readFileSync(path);
console.log('File size:', buf.length, 'bytes');

// The bad byte sequence: C3 A2 E2 82 AC 22 (mojibake em-dash with literal ASCII quote)
const bad = Buffer.from([0xC3, 0xA2, 0xE2, 0x82, 0xAC, 0x22]);
// Replacement: -- followed by the quote that was part of the bad sequence  
// Actually the 0x22 is the closing quote of the JSON string - we need to keep it
// No wait - the 0x22 is embedded IN the mojibake. Let me think...
// The text shows: â€" where the " at end is byte 0x22
// We want to replace the whole bad sequence with just -- (two dashes)
// But the 0x22 might be the start of the next JSON key

// Let's just do text-level replacement. Read as latin1 to preserve all bytes
const latin1 = buf.toString('latin1');

// In latin1, the bad sequence C3 A2 E2 82 AC 22 becomes: Ã¢â‚¬"
// Let's find it by converting bad bytes to latin1
const badStr = bad.toString('latin1');
console.log('Bad string (latin1 repr):', JSON.stringify(badStr));
console.log('Occurrences:', latin1.split(badStr).length - 1);

// Replace with -- and keep the quote (0x22) since it's part of JSON structure
// Actually, looking at the rendered output "â€"", the 0x22 is the trailing "
// In the JSON: ...Claw AI â€" a multi... the " terminates the string early
// We need to replace C3 A2 E2 82 AC with -- (remove the bad bytes, the 22 stays as the next char)
const bad5 = Buffer.from([0xC3, 0xA2, 0xE2, 0x82, 0xAC]);
const badStr5 = bad5.toString('latin1');
console.log('5-byte bad string occurrences:', latin1.split(badStr5).length - 1);

// Replace the 5-byte sequence (without the quote) with --
const fixed = latin1.split(badStr5).join('--');
console.log('After fix, remaining bad sequences:', fixed.split(badStr5).length - 1);

// Write back as latin1 (preserves all byte values)
fs.writeFileSync(path, Buffer.from(fixed, 'latin1'));
console.log('Written fixed file');

// Verify JSON parse
try {
  JSON.parse(fs.readFileSync(path, 'utf8'));
  console.log('JSON VALID!');
} catch (e) {
  console.log('JSON still invalid:', e.message);
  // Show context around error
  const text = fs.readFileSync(path, 'utf8');
  const pos = e.message.match(/position (\d+)/);
  if (pos) {
    const p = parseInt(pos[1]);
    console.log('Around error:', JSON.stringify(text.substring(p-30, p+30)));
  }
}
