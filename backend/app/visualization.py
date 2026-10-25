"""Server-side conceptual architectural visualization.

The LLM supplies the concept description; this module renders a deterministic SVG
front elevation + plot footprint so the UI always has a visual preview, with no
image-generation API required."""
from __future__ import annotations

from xml.sax.saxutils import escape


def render_concept_svg(plot_length_ft: float, plot_width_ft: float, floors: int,
                       construction_type: str, style: str) -> str:
    floors = max(1, min(int(floors), 12))
    w, h = 640, 360
    # ---- elevation (left) ----
    el_x, el_w = 40, 340
    ground_y = 300
    floor_h = min(60, 220 // floors)
    bld_h = floor_h * floors
    top_y = ground_y - bld_h
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" '
        f'font-family="Segoe UI, Arial, sans-serif" font-size="12">',
        f'<rect width="{w}" height="{h}" fill="#f4f6f8"/>',
        f'<rect x="0" y="{ground_y}" width="{w}" height="{h - ground_y}" fill="#d9dee3"/>',
        f'<text x="{el_x}" y="26" font-size="14" font-weight="600" fill="#1f2a37">'
        f'Front elevation - {escape(construction_type.title())} ({escape(style)})</text>',
        f'<rect x="{el_x}" y="{top_y}" width="{el_w}" height="{bld_h}" fill="#e8e1d5" stroke="#5b6b7a" stroke-width="2"/>',
    ]
    for i in range(floors):
        fy = ground_y - (i + 1) * floor_h
        parts.append(f'<line x1="{el_x}" y1="{fy}" x2="{el_x + el_w}" y2="{fy}" stroke="#9aa7b3" stroke-width="1"/>')
        for wx in range(el_x + 30, el_x + el_w - 40, 70):
            wy = fy + floor_h * 0.25
            parts.append(f'<rect x="{wx}" y="{wy:.0f}" width="34" height="{floor_h * 0.45:.0f}" '
                         f'fill="#8fb8d8" stroke="#39546b" stroke-width="1.5"/>')
        if i > 0:
            parts.append(f'<rect x="{el_x + el_w - 110}" y="{fy + floor_h * 0.55:.0f}" width="80" height="{floor_h * 0.3:.0f}" '
                         f'fill="none" stroke="#39546b" stroke-width="1.5"/>')
    # door
    parts.append(f'<rect x="{el_x + el_w / 2 - 18:.0f}" y="{ground_y - floor_h * 0.75:.0f}" width="36" '
                 f'height="{floor_h * 0.75:.0f}" fill="#6d4c41" stroke="#39546b" stroke-width="1.5"/>')
    # parapet
    parts.append(f'<rect x="{el_x - 6}" y="{top_y - 10}" width="{el_w + 12}" height="10" fill="#5b6b7a"/>')
    parts.append(f'<text x="{el_x}" y="{ground_y + 36}" fill="#1f2a37">{floors} floor(s), ~{floors * 10} ft height</text>')

    # ---- plot footprint (right) ----
    px, py, pw, ph = 420, 60, 190, 220
    ratio = plot_width_ft / plot_length_ft if plot_length_ft else 1
    if ratio > 1:
        fw, fh = pw / ratio, ph
    else:
        fw, fh = pw, ph * ratio
    fw, fh = max(60, min(pw, fw)), max(60, min(ph, fh))
    ox, oy = px + (pw - fw) / 2, py + (ph - fh) / 2
    sb = 0.12
    parts += [
        f'<text x="{px}" y="26" font-size="14" font-weight="600" fill="#1f2a37">Plot footprint</text>',
        f'<rect x="{ox:.0f}" y="{oy:.0f}" width="{fw:.0f}" height="{fh:.0f}" fill="#dfe8d4" stroke="#4b6b3c" stroke-width="2"/>',
        f'<rect x="{ox + fw * sb:.0f}" y="{oy + fh * sb:.0f}" width="{fw * (1 - 2 * sb):.0f}" height="{fh * (1 - 2 * sb):.0f}" '
        f'fill="#e8e1d5" stroke="#5b6b7a" stroke-width="2"/>',
        f'<text x="{ox + fw / 2:.0f}" y="{oy + fh / 2:.0f}" text-anchor="middle" fill="#1f2a37">Built-up</text>',
        f'<text x="{ox + fw / 2:.0f}" y="{oy + fh + 18:.0f}" text-anchor="middle" fill="#1f2a37">{plot_length_ft:g} ft</text>',
        f'<text x="{ox - 8:.0f}" y="{oy + fh / 2:.0f}" text-anchor="end" fill="#1f2a37">{plot_width_ft:g} ft</text>',
        f'<text x="{px}" y="{h - 20}" fill="#4a5a68">Conceptual sketch - not to scale, not for construction.</text>',
        '</svg>',
    ]
    return "".join(parts)
