"""Generate PNG icons for the Claw Agent Chrome extension."""
import struct
import zlib
import os

def create_png(width, height, rgba_data):
    """Create a minimal PNG from RGBA pixel data."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    # PNG signature
    sig = b"\x89PNG\r\n\x1a\n"
    # IHDR
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    # IDAT — filter type 0 (None) for each row
    raw = b""
    for y in range(height):
        raw += b"\x00"  # filter byte
        raw += rgba_data[y * width * 4 : (y + 1) * width * 4]
    idat = chunk(b"IDAT", zlib.compress(raw))
    # IEND
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


def draw_icon(size):
    """Draw a ⚡ lightning bolt icon on dark background."""
    pixels = bytearray(size * size * 4)
    cx, cy = size / 2, size / 2
    r = size / 2 - 1

    for y in range(size):
        for x in range(size):
            idx = (y * size + x) * 4
            dx, dy = x - cx, y - cy
            dist = (dx * dx + dy * dy) ** 0.5

            if dist <= r:
                # Dark background circle
                bg_r, bg_g, bg_b = 30, 30, 30
                # Lightning bolt shape
                fx, fy = x / size, y / size

                # Define lightning bolt polygon (normalized 0-1 coords)
                in_bolt = False

                # Upper part: triangle pointing right
                if 0.25 <= fy <= 0.52:
                    t = (fy - 0.25) / 0.27
                    left = 0.30 + t * 0.05
                    right = 0.70 - t * 0.25
                    if left <= fx <= right:
                        in_bolt = True

                # Middle bar going left
                if 0.45 <= fy <= 0.58:
                    left = 0.28
                    right = 0.65 - (fy - 0.45) / 0.13 * 0.10
                    if left <= fx <= right:
                        in_bolt = True

                # Lower part: triangle pointing down
                if 0.50 <= fy <= 0.78:
                    t = (fy - 0.50) / 0.28
                    left = 0.30 + t * 0.12
                    right = 0.60 - t * 0.15
                    if left <= fx <= right:
                        in_bolt = True

                if in_bolt:
                    # Gold/amber color like the accent
                    pixels[idx] = 212      # R
                    pixels[idx + 1] = 165  # G
                    pixels[idx + 2] = 116  # B
                    pixels[idx + 3] = 255  # A
                else:
                    # Edge glow
                    edge = max(0, 1.0 - abs(dist - r) / 2)
                    pixels[idx] = int(bg_r + edge * 20)
                    pixels[idx + 1] = int(bg_g + edge * 15)
                    pixels[idx + 2] = int(bg_b + edge * 10)
                    pixels[idx + 3] = 255
            else:
                # Transparent outside circle
                pixels[idx] = 0
                pixels[idx + 1] = 0
                pixels[idx + 2] = 0
                pixels[idx + 3] = 0

    return bytes(pixels)


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "icons")
    os.makedirs(out_dir, exist_ok=True)

    for size in [16, 32, 48, 128]:
        data = draw_icon(size)
        png = create_png(size, size, data)
        path = os.path.join(out_dir, f"icon{size}.png")
        with open(path, "wb") as f:
            f.write(png)
        print(f"Created {path} ({len(png)} bytes)")
