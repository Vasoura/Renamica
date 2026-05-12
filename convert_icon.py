#!/usr/bin/env python3
"""Generate Renamica app icon - 1024x1024 PNG and .icns"""

import os
import subprocess
import math
from PIL import Image, ImageDraw, ImageFont


SIZE = 1024
OUT_PNG = "renamica_icon.png"
OUT_ICNS = "renamica.icns"
ICONSET = "renamica.iconset"

FONT_SIZES = {
    1024: 420,
}


def create_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = 80
    radius = 180
    box = (margin, margin, SIZE - margin, SIZE - margin)

    for y in range(SIZE):
        for x in range(SIZE):
            px, py = x, y
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            rx, ry = (box[2] - box[0]) / 2, (box[3] - box[1]) / 2

            if rx <= 0 or ry <= 0:
                continue

            dx, dy = abs(px - cx), abs(py - cy)
            if dx > rx - radius and dy > ry - radius:
                corner_dist = math.sqrt((dx - (rx - radius)) ** 2 + (dy - (ry - radius)) ** 2)
                if corner_dist > radius:
                    continue

            t = (py / SIZE)
            r = int((0x00 + (0x58 - 0x00) * t))
            g = int((0x7A + (0x56 - 0x7A) * t))
            b = int((0xFF + (0xD6 - 0xFF) * t))
            draw.point((px, py), fill=(r, g, b, 255))

    try:
        font = ImageFont.truetype("/System/Library/Fonts/SFNSDisplay.ttf", FONT_SIZES[SIZE])
    except (IOError, OSError):
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", FONT_SIZES[SIZE])
        except (IOError, OSError):
            font = ImageFont.load_default()

    text = "R"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (SIZE - tw) / 2 - bbox[0]
    ty = (SIZE - th) / 2 - bbox[1] - 20

    draw.text((tx, ty), text, fill=(255, 255, 255, 255), font=font)

    arrow_size = 140
    arrow_x = SIZE - margin - arrow_size - 30
    arrow_y = SIZE - margin - arrow_size - 20

    draw_rename_arrow(draw, arrow_x, arrow_y, arrow_size)

    img.save(OUT_PNG, "PNG")
    print(f"  Created {OUT_PNG} ({SIZE}x{SIZE})")


def draw_rename_arrow(draw, x, y, size):
    cx = x + size / 2
    cy = y + size / 2
    r = size * 0.4
    color = (255, 255, 255, 200)
    width = max(int(size * 0.1), 6)

    angle_start = -math.pi * 0.3
    angle_end = math.pi * 1.6
    steps = 60
    points = []

    for i in range(steps + 1):
        a = angle_start + (angle_end - angle_start) * i / steps
        px = cx + r * math.cos(a)
        py = cy + r * math.sin(a)
        points.append((px, py))

    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=color, width=width)

    tip_angle = angle_end
    tip_len = size * 0.15
    tip_x = cx + (r + tip_len) * math.cos(tip_angle)
    tip_y = cy + (r + tip_len) * math.sin(tip_angle)
    draw.line([(cx + r * math.cos(tip_angle), cy + r * math.sin(tip_angle)),
               (tip_x, tip_y)], fill=color, width=width + 2)

    t = 0.85
    mid_angle = angle_start * (1 - t) + angle_end * t
    mid_x_outer = cx + (r + 5) * math.cos(mid_angle)
    mid_y_outer = cy + (r + 5) * math.sin(mid_angle)

    handle_len = size * 0.15
    handle_angle = mid_angle + math.pi * 0.5
    end_x = mid_x_outer + handle_len * math.cos(handle_angle)
    end_y = mid_y_outer + handle_len * math.sin(handle_angle)
    draw.line([(mid_x_outer, mid_y_outer), (end_x, end_y)], fill=color, width=width)


def generate_iconset():
    if os.path.exists(ICONSET):
        for f in os.listdir(ICONSET):
            os.remove(os.path.join(ICONSET, f))
        os.rmdir(ICONSET)
    os.makedirs(ICONSET, exist_ok=True)

    img = Image.open(OUT_PNG)
    sizes = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }

    for name, s in sizes.items():
        resized = img.resize((s, s), Image.LANCZOS)
        path = os.path.join(ICONSET, name)
        resized.save(path, "PNG")
        print(f"  Created {path} ({s}x{s})")


def create_icns():
    if os.path.exists(OUT_ICNS):
        os.remove(OUT_ICNS)
    result = subprocess.run(
        ["iconutil", "-c", "icns", ICONSET, "-o", OUT_ICNS],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        size = os.path.getsize(OUT_ICNS)
        print(f"  Created {OUT_ICNS} ({size / 1024:.1f} KB)")
    else:
        print(f"  iconutil error: {result.stderr}")
        return False
    return True


def cleanup():
    if os.path.exists(ICONSET):
        for f in os.listdir(ICONSET):
            os.remove(os.path.join(ICONSET, f))
        os.rmdir(ICONSET)


if __name__ == "__main__":
    print("Generating Renamica icon...")
    create_icon()
    print("Generating .iconset...")
    generate_iconset()
    print("Creating .icns...")
    if create_icns():
        cleanup()
        print(f"\nDone! Generated:")
        print(f"  - {OUT_PNG} ({SIZE}x{SIZE})")
        print(f"  - {OUT_ICNS}")
    else:
        print("\niconutil failed. Keeping .iconset for debugging.")
