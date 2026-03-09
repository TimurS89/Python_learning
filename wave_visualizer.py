#!/usr/bin/env python3
"""Wire-focused premium visualizer with 3 distinct variants.

This revision intentionally keeps only wire-style directions and removes older non-wire concepts.
- Generate static SVG previews for fast human review.
- Render MP4 output with FFmpeg showwaves pipelines.
"""

from __future__ import annotations

import argparse
import math
import random
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent


@dataclass(frozen=True)
class Variant:
    key: str
    title: str
    bg_top: str
    bg_bottom: str
    palette: tuple[str, ...]
    mode: str


VARIANTS: dict[str, Variant] = {
    "wire_flux": Variant(
        key="wire_flux",
        title="Wire Ribbon Flux",
        bg_top="#021839",
        bg_bottom="#010713",
        palette=("#19D9FF", "#61EDFF", "#9AF8FF", "#2A8FFF"),
        mode="flux",
    ),
    "wire_helix": Variant(
        key="wire_helix",
        title="Wire Ribbon Helix",
        bg_top="#071032",
        bg_bottom="#01040E",
        palette=("#32B5FF", "#86D7FF", "#4CF0FF", "#8D7BFF"),
        mode="helix",
    ),
    "wire_silk": Variant(
        key="wire_silk",
        title="Wire Ribbon Silk",
        bg_top="#021E2E",
        bg_bottom="#00080D",
        palette=("#5FFFD5", "#83F7FF", "#D2FFF4", "#5BC5FF"),
        mode="silk",
    ),
}


def _path(points: list[tuple[float, float]]) -> str:
    return " ".join(("M" if i == 0 else "L") + f"{x:.2f},{y:.2f}" for i, (x, y) in enumerate(points))


def _wave(w: int, h: int, phase: float, amp: float, f1: float, f2: float, center: float = 0.53) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(640):
        xn = i / 639
        x = xn * w
        y = center + amp * math.sin(xn * math.pi * 2.8 * f1 + phase)
        y += amp * 0.45 * math.sin(xn * math.pi * 7.5 * f2 - phase * 1.35)
        pts.append((x, y * h))
    return pts


def _flux_svg(v: Variant, w: int, h: int, phase: float, rng: random.Random) -> str:
    parts: list[str] = []
    # Dense background wire field
    for sheet in range(38):
        pts = _wave(w, h, phase + sheet * 0.09, 0.036 + 0.0019 * sheet, 0.9, 0.95 + sheet * 0.018)
        d = _path(pts)
        yoff = (sheet - 19) * 4.8
        color = v.palette[sheet % len(v.palette)]
        parts.append(f'<path d="{d}" transform="translate(0,{yoff:.2f})" stroke="{color}" stroke-width="0.85" opacity="0.24" fill="none"/>')

    # Bright hero wave trio
    for k in range(3):
        pts = _wave(w, h, phase + k * 0.58, 0.106, 0.88 + k * 0.08, 1.0 + k * 0.14)
        d = _path(pts)
        c = v.palette[k]
        parts.append(f'<path d="{d}" stroke="{c}" stroke-width="19" opacity="0.11" fill="none"/>')
        parts.append(f'<path d="{d}" stroke="{c}" stroke-width="3.5" opacity="0.96" fill="none"/>')

    # Mesh dots
    for i in range(320):
        xn = i / 319
        x = xn * w
        base = h * (0.53 + 0.17 * math.sin(xn * math.pi * 4.8 + phase))
        for z in range(11):
            y = base + (z - 5) * 9.8 + 3.2 * math.sin(xn * 35 + phase + z)
            op = 0.06 + z * 0.028
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="0.95" fill="{v.palette[2]}" opacity="{op:.3f}"/>')

    for _ in range(240):
        x = rng.uniform(0, w)
        y = rng.uniform(0, h)
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="0.9" fill="#BEEFFF" opacity="0.16"/>')

    return "".join(parts)


def _helix_svg(v: Variant, w: int, h: int, phase: float, rng: random.Random) -> str:
    parts: list[str] = []
    cx, cy = w * 0.5, h * 0.52

    # Twisted dual helix rails crossing the canvas
    for strand in range(2):
        pts_top = []
        pts_bottom = []
        for i in range(520):
            xn = i / 519
            x = xn * w
            ang = xn * math.pi * 8 + phase * 2.5 + strand * math.pi
            y0 = cy + math.sin(xn * math.pi * 2.2 + strand * 0.9) * h * 0.13
            offset = 36 * math.sin(ang)
            pts_top.append((x, y0 + offset))
            pts_bottom.append((x, y0 - offset))
            if i % 7 == 0:
                c = v.palette[(i // 20 + strand) % len(v.palette)]
                parts.append(f'<line x1="{x:.2f}" y1="{y0+offset:.2f}" x2="{x:.2f}" y2="{y0-offset:.2f}" stroke="{c}" stroke-width="0.8" opacity="0.20"/>')
        for idx, pts in enumerate((pts_top, pts_bottom)):
            d = _path(pts)
            c = v.palette[(strand + idx) % len(v.palette)]
            parts.append(f'<path d="{d}" stroke="{c}" stroke-width="12" opacity="0.08" fill="none"/>')
            parts.append(f'<path d="{d}" stroke="{c}" stroke-width="2.2" opacity="0.88" fill="none"/>')

    # Secondary wire canopy
    for layer in range(22):
        pts = _wave(w, h, phase + layer * 0.16, 0.046 + layer * 0.0018, 0.75 + layer * 0.03, 0.96)
        d = _path(pts)
        yoff = (layer - 11) * 6.2
        c = v.palette[(layer + 1) % len(v.palette)]
        parts.append(f'<path d="{d}" transform="translate(0,{yoff:.2f})" stroke="{c}" stroke-width="0.9" opacity="0.18" fill="none"/>')

    for _ in range(250):
        x = rng.uniform(0, w)
        y = rng.uniform(0, h)
        r = rng.uniform(0.6, 1.6)
        c = v.palette[rng.randrange(0, len(v.palette))]
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{c}" opacity="0.13"/>')

    return "".join(parts)


def _silk_svg(v: Variant, w: int, h: int, phase: float, rng: random.Random) -> str:
    parts: list[str] = []

    # Smooth silk sheets built from many close thin curves
    for band in range(28):
        band_center = 0.36 + band * 0.011
        for layer in range(6):
            pts = _wave(
                w,
                h,
                phase + band * 0.13 + layer * 0.09,
                amp=0.034 + layer * 0.003,
                f1=0.62 + band * 0.018,
                f2=1.05 + layer * 0.05,
                center=band_center,
            )
            d = _path(pts)
            c = v.palette[(band + layer) % len(v.palette)]
            op = 0.09 + layer * 0.04
            parts.append(f'<path d="{d}" stroke="{c}" stroke-width="1.0" opacity="{op:.3f}" fill="none"/>')

    # Three elegant main ribbons
    for k, center in enumerate((0.40, 0.54, 0.68)):
        pts = _wave(w, h, phase + k * 0.8, 0.078, 0.74 + k * 0.09, 1.1, center=center)
        d = _path(pts)
        c = v.palette[k]
        parts.append(f'<path d="{d}" stroke="{c}" stroke-width="17" opacity="0.09" fill="none"/>')
        parts.append(f'<path d="{d}" stroke="{c}" stroke-width="2.8" opacity="0.9" fill="none"/>')

    # Soft glitter
    for _ in range(360):
        x = rng.uniform(0, w)
        y = rng.uniform(h * 0.2, h * 0.85)
        r = rng.uniform(0.5, 1.8)
        c = v.palette[rng.randrange(0, len(v.palette))]
        op = rng.uniform(0.05, 0.22)
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{c}" opacity="{op:.3f}"/>')

    return "".join(parts)


def _preview_content(v: Variant, w: int, h: int, phase: float, rng: random.Random) -> str:
    if v.mode == "flux":
        return _flux_svg(v, w, h, phase, rng)
    if v.mode == "helix":
        return _helix_svg(v, w, h, phase, rng)
    return _silk_svg(v, w, h, phase, rng)


def write_preview(v: Variant, w: int, h: int, phase: float, out_file: Path, seed: int) -> None:
    content = _preview_content(v, w, h, phase, random.Random(seed))
    svg = dedent(
        f"""\
        <svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
          <defs>
            <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="{v.bg_top}"/>
              <stop offset="100%" stop-color="{v.bg_bottom}"/>
            </linearGradient>
            <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="8" result="b"/>
              <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
          </defs>
          <rect width="100%" height="100%" fill="url(#bg)"/>
          <g filter="url(#glow)">{content}</g>
          <text x="36" y="58" fill="#E6F7FF" opacity="0.83" font-size="27" font-family="Arial, sans-serif">{v.title}</text>
        </svg>
        """
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(svg, encoding="utf-8")


def generate_previews(preview_dir: Path, width: int, height: int) -> list[Path]:
    files: list[Path] = []
    for i, v in enumerate(VARIANTS.values()):
        path = preview_dir / f"{v.key}_preview_1.svg"
        write_preview(v, width, height, phase=0.0 + i * 0.38, out_file=path, seed=800 + i)
        files.append(path)
    return files


def ffmpeg_filter(v: Variant, w: int, h: int, fps: int) -> str:
    if v.mode == "flux":
        return ";".join([
            f"color=c={v.bg_top}:s={w}x{h}:r={fps}[bg]",
            f"[0:a]showwaves=s={w}x{h}:mode=cline:colors={v.palette[0]}:rate={fps},gblur=sigma=7[w0]",
            f"[0:a]showwaves=s={w}x{h}:mode=line:colors={v.palette[1]}:rate={fps},gblur=sigma=3[w1]",
            f"[0:a]showwaves=s={w}x{h}:mode=p2p:colors={v.palette[2]}:rate={fps},gblur=sigma=5[w2]",
            "[bg][w0]overlay=0:0[t1]",
            "[t1][w1]overlay=0:0[t2]",
            "[t2][w2]overlay=0:0,eq=saturation=1.35:contrast=1.08,format=yuv420p[v]",
        ])
    if v.mode == "helix":
        return ";".join([
            f"color=c={v.bg_top}:s={w}x{h}:r={fps}[bg]",
            f"[0:a]showwaves=s={w}x{h}:mode=point:colors={v.palette[2]}:rate={fps},gblur=sigma=2[p]",
            f"[0:a]showwaves=s={w}x{h}:mode=cline:colors={v.palette[0]}:rate={fps},gblur=sigma=8[c]",
            "[bg][p]overlay=0:0[t1]",
            "[t1][c]overlay=0:0,curves=all='0/0 0.45/0.52 1/1',eq=saturation=1.48:gamma=1.06,format=yuv420p[v]",
        ])
    return ";".join([
        f"color=c={v.bg_top}:s={w}x{h}:r={fps}[bg]",
        f"[0:a]showwaves=s={w}x{h}:mode=cline:colors={v.palette[1]}:rate={fps}[a]",
        f"[0:a]showwaves=s={w}x{h}:mode=line:colors={v.palette[0]}:rate={fps}[b]",
        "[a]gblur=sigma=4[ab]",
        "[b]gblur=sigma=6[bb]",
        "[bg][ab]overlay=0:0[t1]",
        "[t1][bb]overlay=0:0,unsharp=7:7:0.9:7:7:0.0,eq=saturation=1.25,format=yuv420p[v]",
    ])


def render_video(variant_key: str, audio: Path, output: Path, width: int, height: int, fps: int) -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is required but not found in PATH.")
    v = VARIANTS[variant_key]
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(audio),
        "-filter_complex",
        ffmpeg_filter(v, width, height, fps),
        "-map",
        "[v]",
        "-map",
        "0:a",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "16",
        "-c:a",
        "aac",
        "-b:a",
        "320k",
        "-shortest",
        str(output),
    ]
    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Wire-focused premium FFmpeg visualizer")
    p.add_argument("--style", choices=VARIANTS.keys(), default="wire_flux")
    p.add_argument("--audio", type=Path, help="Input audio path")
    p.add_argument("--output", type=Path, default=Path("output/visualizer.mp4"))
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--render-previews", action="store_true")
    p.add_argument("--preview-dir", type=Path, default=Path("previews"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.render_previews:
        files = generate_previews(args.preview_dir, args.width, args.height)
        print("Generated previews:")
        for f in files:
            print(f"- {f}")
        return
    if args.audio is None:
        raise SystemExit("--audio is required unless --render-previews is used.")
    render_video(args.style, args.audio, args.output, args.width, args.height, args.fps)
    print(f"Video rendered: {args.output}")


if __name__ == "__main__":
    main()
