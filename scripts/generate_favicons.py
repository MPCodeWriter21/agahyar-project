"""Generate favicon icons for Agahyar project.

Outputs favicons for both the main site and the admin panel.
Main: #1a5f7a (teal)
Admin: #0f3d52 (darker teal)

Usage:
    uv run --extra scripts scripts/generate_favicons.py
"""

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SIZE = 512
LETTER = "\u0622"


def _find_font() -> str:
    candidates = [
        "C:/Windows/Fonts/Vazirmatn-Bold.ttf",
        "/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Bold.ttf",
        "/usr/share/fonts/vazirmatn-ttf/Vazirmatn-Bold.ttf",
        str(Path.home() / ".fonts" / "Vazirmatn-Bold.ttf"),
    ]
    for path in candidates:
        if Path(path).exists():
            return path
    print("Error: Vazirmatn-Bold.ttf not found. Searched:", file=sys.stderr)
    for c in candidates:
        print(f"  {c}", file=sys.stderr)
    sys.exit(1)


FONT = _find_font()
HEXAGON_CORNER_RADIUS = 40
HEXAGON_SCALE = 0.88
CROP_PAD = 10

SITES = {
    "main": {
        "accent": "#1a5f7a",
        "output": ROOT / "static" / "services" / "img",
    },
    "admin": {
        "accent": "#0f3d52",
        "output": ROOT / "static" / "services" / "img" / "admin",
    },
}

FAVICON_SIZES = {
    "favicon-16x16.png": 16,
    "favicon-32x32.png": 32,
    "favicon-48x48.png": 48,
    "apple-touch-icon.png": 180,
    "favicon.png": 192,
}


def hex_color_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def make_hexagon_mask(size: int, corner_radius: int) -> Image.Image:
    cx, cy = size // 2, size // 2
    r = size // 2 - 30

    pts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    small_pts = [
        (cx + (x - cx) * HEXAGON_SCALE, cy + (y - cy) * HEXAGON_SCALE) for x, y in pts
    ]
    md.polygon(small_pts, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=corner_radius))
    mask = mask.point(lambda p: 255 if p > 128 else 0)
    return mask


def generate_hexagon_icon(accent: str) -> Image.Image:
    rgb = hex_color_to_rgb(accent)
    mask = make_hexagon_mask(SIZE, HEXAGON_CORNER_RADIUS)

    bg = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    bg.paste(Image.new("RGBA", (SIZE, SIZE), rgb), mask=mask)

    font = ImageFont.truetype(FONT, 220)
    d = ImageDraw.Draw(bg)
    bbox = d.textbbox((0, 0), LETTER, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (SIZE - tw) / 2 - bbox[0]
    y = (SIZE - th) / 2 - bbox[1]
    d.text((x, y), LETTER, fill="#ffffff", font=font)

    # Auto-crop
    crop_box = bg.getbbox()
    cropped = bg.crop(
        (
            crop_box[0] - CROP_PAD,
            crop_box[1] - CROP_PAD,
            crop_box[2] + CROP_PAD,
            crop_box[3] + CROP_PAD,
        )
    )

    # Make square
    w, h = cropped.size
    max_dim = max(w, h)
    result = Image.new("RGBA", (max_dim, max_dim), (0, 0, 0, 0))
    result.paste(cropped, ((max_dim - w) // 2, (max_dim - h) // 2))
    return result


def save_favicons(icon: Image.Image, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, size in FAVICON_SIZES.items():
        resized = icon.resize((size, size), Image.LANCZOS)
        resized.save(output_dir / name)

    icon.save(
        output_dir / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
    )
    icon.save(output_dir / "favicon-hires.png")

    print(f"  Saved to {output_dir.relative_to(ROOT)}/")


def main() -> None:
    print("Generating favicons...\n")

    for site_name, cfg in SITES.items():
        print(f"[{site_name}] accent={cfg['accent']}")
        icon = generate_hexagon_icon(cfg["accent"])
        print(f"  Icon: {icon.size[0]}x{icon.size[1]}")
        save_favicons(icon, cfg["output"])

    print("\nDone!")


if __name__ == "__main__":
    main()
