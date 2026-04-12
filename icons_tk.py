"""
Material Design Icons for Tkinter
Loads SVG icons from public/icons/ and converts to Tkinter PhotoImage via PIL.
Requires: Pillow

Usage:
    from icons_tk import get_icon, get_icon_color
    img = get_icon('calculate', size=20, color='#1b4f72')
    button = ttk.Button(..., image=img, compound='left')
"""
import os
import re
import math
import tkinter as tk
from functools import lru_cache
from typing import Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Icon folder relative to this file
_ICON_DIR = os.path.join(os.path.dirname(__file__), 'public', 'icons')

# Cache: (name, size, color) → PhotoImage
_cache: dict = {}


def _hex_to_rgb(color: str) -> Tuple[int, int, int]:
    """Convert #rrggbb or #rgb to (r, g, b)."""
    c = color.lstrip('#')
    if len(c) == 3:
        c = ''.join(ch * 2 for ch in c)
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def _parse_svg_path(svg_path: str) -> list:
    """
    Very simplified SVG path parser — extracts approximate polygon points
    for PIL rendering. Handles M, L, H, V, Z commands only (for simple shapes).
    Full curves (C, Q, A) are approximated as line segments to their end points.
    """
    tokens = re.findall(r'[MLHVCSQTAZmlhvcsqtaz]|[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?', svg_path)
    points = []
    poly = []
    cx, cy = 0.0, 0.0
    cmd = 'M'
    idx = 0

    def pop():
        nonlocal idx
        if idx < len(tokens):
            val = tokens[idx]; idx += 1
            try:
                return float(val)
            except ValueError:
                return None
        return None

    while idx < len(tokens):
        t = tokens[idx]
        if t.isalpha():
            cmd = t; idx += 1
            continue
        # Try to parse numeric args
        if cmd in ('M', 'm'):
            x = float(t); idx += 1; y = pop()
            if cmd == 'm':
                cx += x; cy += (y or 0)
            else:
                cx, cy = x, (y or 0)
            if poly:
                points.append(poly[:])
            poly = [(cx, cy)]
            cmd = 'L' if cmd == 'M' else 'l'

        elif cmd in ('L', 'l'):
            x = float(t); idx += 1; y = pop()
            if cmd == 'l':
                cx += x; cy += (y or 0)
            else:
                cx, cy = x, (y or 0)
            poly.append((cx, cy))

        elif cmd in ('H', 'h'):
            x = float(t); idx += 1
            cx = x if cmd == 'H' else cx + x
            poly.append((cx, cy))

        elif cmd in ('V', 'v'):
            y = float(t); idx += 1
            cy = y if cmd == 'V' else cy + y
            poly.append((cx, cy))

        elif cmd in ('Z', 'z'):
            if poly:
                poly.append(poly[0])
                points.append(poly[:])
            poly = []
            idx += 1

        elif cmd in ('C', 'c'):
            # Cubic bezier: skip control points, take end point
            x1 = float(t); idx += 1
            y1 = pop(); x2 = pop(); y2 = pop(); x = pop(); y = pop()
            if cmd == 'c':
                cx += (x or 0); cy += (y or 0)
            else:
                cx, cy = (x or cx), (y or cy)
            poly.append((cx, cy))

        elif cmd in ('Q', 'q'):
            x1 = float(t); idx += 1
            y1 = pop(); x = pop(); y = pop()
            if cmd == 'q':
                cx += (x or 0); cy += (y or 0)
            else:
                cx, cy = (x or cx), (y or cy)
            poly.append((cx, cy))

        elif cmd in ('A', 'a'):
            # Arc: rx ry rotation large-arc sweep x y
            for _ in range(6):
                pop()
            x = pop(); y = pop()
            if x is None:
                break
            if cmd == 'a':
                cx += x; cy += y
            else:
                cx, cy = x, y
            poly.append((cx, cy))

        else:
            idx += 1  # skip unrecognized

    if poly and len(poly) > 1:
        points.append(poly)
    return points


def _render_svg_to_image(
    svg_text: str,
    size: int,
    color: Tuple[int, int, int],
    bg: Optional[Tuple[int, int, int, int]] = None,
) -> "Image.Image":
    """Render a Material Symbol SVG to a PIL Image."""
    # Parse viewBox
    vb_match = re.search(r'viewBox=["\']([^"\']+)["\']', svg_text)
    if vb_match:
        vb = [float(v) for v in vb_match.group(1).split()]
        vx, vy, vw, vh = vb
    else:
        vx, vy, vw, vh = 0, -960, 960, 960

    # Extract path data
    path_matches = re.findall(r'<path[^>]*\sd=["\']([^"\']+)["\']', svg_text)
    if not path_matches:
        path_matches = re.findall(r'd=["\']([^"\']+)["\']', svg_text)

    scale = size / max(vw, vh)

    # Create RGBA image
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    r, g, b = color
    fill = (r, g, b, 255)

    for path_d in path_matches:
        polys = _parse_svg_path(path_d)
        for poly in polys:
            if len(poly) < 2:
                continue
            # Transform: (x - vx) * scale, (y - vy) * scale  (y-axis flip for negative vy)
            pts = []
            for px, py in poly:
                sx = (px - vx) * scale
                sy = (py - vy) * scale
                pts.append((sx, sy))
            if len(pts) >= 3:
                draw.polygon(pts, fill=fill)
            elif len(pts) == 2:
                draw.line(pts, fill=fill, width=max(1, size // 24))

    return img


def get_icon(
    name: str,
    size: int = 20,
    color: str = '#1b4f72',
) -> Optional["ImageTk.PhotoImage"]:
    """
    Load and return a Tkinter PhotoImage for the given Material Symbol icon.

    Args:
        name:  Icon name (e.g. 'calculate', 'check_circle')
        size:  Pixel size (default 20)
        color: Hex color string (default navy blue)
    Returns:
        ImageTk.PhotoImage or None if PIL not available / file not found
    """
    if not PIL_AVAILABLE:
        return None

    key = (name, size, color)
    if key in _cache:
        return _cache[key]

    svg_path = os.path.join(_ICON_DIR, f'{name}.svg')
    if not os.path.exists(svg_path):
        return None

    try:
        with open(svg_path, encoding='utf-8') as f:
            svg_text = f.read()
        rgb = _hex_to_rgb(color)
        img = _render_svg_to_image(svg_text, size, rgb)
        photo = ImageTk.PhotoImage(img)
        _cache[key] = photo
        return photo
    except Exception:
        return None


def get_icon_white(name: str, size: int = 20) -> Optional["ImageTk.PhotoImage"]:
    """Shortcut for white icons (on dark backgrounds)."""
    return get_icon(name, size, '#ffffff')


def get_icon_blue(name: str, size: int = 20) -> Optional["ImageTk.PhotoImage"]:
    """Shortcut for navy-blue icons."""
    return get_icon(name, size, '#1b4f72')


def get_icon_pass(name: str = 'check_circle', size: int = 16) -> Optional["ImageTk.PhotoImage"]:
    """Green checkmark icon."""
    return get_icon(name, size, '#1a7a4a')


def get_icon_fail(name: str = 'cancel', size: int = 16) -> Optional["ImageTk.PhotoImage"]:
    """Red cancel icon."""
    return get_icon(name, size, '#c0392b')


def get_icon_warn(name: str = 'warning', size: int = 16) -> Optional["ImageTk.PhotoImage"]:
    """Orange warning icon."""
    return get_icon(name, size, '#d68910')


# ── Simple fallback label-image for environments without SVG support ──────────

def make_text_icon(
    text: str,
    size: int = 20,
    bg_color: str = '#1b4f72',
    fg_color: str = '#ffffff',
) -> Optional["ImageTk.PhotoImage"]:
    """Create a simple colored square with text as fallback icon."""
    if not PIL_AVAILABLE:
        return None
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r, g, b = _hex_to_rgb(bg_color)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=size // 5,
                            fill=(r, g, b, 220))
    fr, fg_, fb = _hex_to_rgb(fg_color)
    font_size = max(size - 8, 6)
    # Center text (approximate)
    tw, th = size // 2, size // 2
    draw.text(((size - tw) // 2, (size - th) // 2), text[:1].upper(),
              fill=(fr, fg_, fb, 255))
    return ImageTk.PhotoImage(img)


# ── Tab icon mapping ──────────────────────────────────────────────────────────

TAB_ICONS = {
    'purlin':     'architecture',    # แป
    'beam':       'straighten',      # คาน
    'column':     'layers',          # เสา
    'connection': 'build',           # รอยต่อ
    'baseplate':  'construction',    # แผ่นฐาน
}

SECTION_ICONS = {
    'loads':      'tune',
    'section':    'table_view',
    'results':    'bar_chart',
    'report':     'description',
    'settings':   'settings',
    'save':       'save',
    'pdf':        'picture_as_pdf',
    'calculate':  'calculate',
    'help':       'help',
}
