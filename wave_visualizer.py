#!/usr/bin/env python3
"""Premium audio visualizer generator with 3 highly distinct art directions.

Focus: thin-wave / elegant line aesthetics with richer composition than the previous version.
- Generates 2 SVG previews per style for quick visual selection.
- Renders MP4 via FFmpeg with style-specific `showwaves` pipelines.
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
class Style:
    key: str
    title: str
    bg_top: str
    bg_bottom: str
    palette: tuple[str, ...]
    mode: str


STYLES: dict[str, Style] = {
    "wire_ribbon": Style(
        key="wire_ribbon",
        title="Wire Ribbon Infinity",
        bg_top="#021636",
        bg_bottom="#010612",
        palette=("#1DD3FF", "#64ECFF", "#A0F8FF", "#2C8DFF"),
        mode="mesh_ribbon",
    ),
    "prism_spectrum": Style(
        key="prism_spectrum",
        title="Prism Spectrum Pulse",
        bg_top="#0B0426",
        bg_bottom="#02010A",
        palette=("#2EE6FF", "#8A7DFF", "#FF4AB8", "#FF8E42"),
        mode="radial_prism",
    ),
    "lattice_dream": Style(
        key="lattice_dream",
        title="Lattice Dream Waves",
        bg_top="#041A1E",
        bg_bottom="#010506",
        palette=("#57FFD3", "#7EF9FF", "#FFD56A", "#C7FFF2"),
        mode="lattice_fold",
    ),
}


def _path(points: list[tuple[float, float]]) -> str:
    return " ".join(("M" if i == 0 else "L") + f"{x:.2f},{y:.2f}" for i, (x, y) in enumerate(points))


def _wave(width: int, height: int, phase: float, amp: float, f1: float, f2: float) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(560):
        xn = i / 559
        x = xn * width
        y = 0.53 + amp * math.sin(xn * math.pi * 2.5 * f1 + phase)
        y += amp * 0.43 * math.sin(xn * math.pi * 7.0 * f2 - phase * 1.4)
        pts.append((x, y * height))
    return pts


def _mesh_ribbon_svg(style: Style, w: int, h: int, phase: float, rng: random.Random) -> str:
    layers: list[str] = []

    # Deep wire sheets
    for sheet in range(30):
        pts = _wave(w, h, phase + sheet * 0.10, amp=0.040 + 0.002 * sheet, f1=0.9, f2=0.92 + 0.02 * sheet)
        d = _path(pts)
        yoff = (sheet - 15) * 5.1
        c = style.palette[sheet % len(style.palette)]
        layers.append(f'<path d="{d}" transform="translate(0,{yoff:.2f})" stroke="{c}" stroke-width="0.8" opacity="0.24" fill="none"/>')

    # Hero ribbons
    for k in range(4):
        pts = _wave(w, h, phase + k * 0.62, amp=0.102, f1=0.86 + k * 0.06, f2=1.0 + k * 0.12)
        d = _path(pts)
        c = style.palette[k % len(style.palette)]
        layers.append(f'<path d="{d}" stroke="{c}" stroke-width="16" opacity="0.11" fill="none"/>')
        layers.append(f'<path d="{d}" stroke="{c}" stroke-width="3.3" opacity="0.95" fill="none"/>')

    # Dotted links between sheets
    for ix in range(280):
        xn = ix / 279
        x = xn * w
        base = h * (0.53 + 0.15 * math.sin(xn * math.pi * 4.8 + phase))
        for k in range(10):
            y = base + (k - 5) * 10.5 + 3.5 * math.sin(xn * 30 + phase + k)
            op = 0.07 + 0.03 * k
            layers.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.0" fill="{style.palette[2]}" opacity="{op:.3f}"/>')

    for _ in range(220):
        x = rng.uniform(0, w)
        y = rng.uniform(0, h)
        layers.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="0.9" fill="#c9f6ff" opacity="0.16"/>')

    return "".join(layers)


def _radial_prism_svg(style: Style, w: int, h: int, phase: float, rng: random.Random) -> str:
    cx, cy = w / 2, h / 2
    elems: list[str] = []

    # Color bloom core.
    for i in range(50):
        r = 14 + i * 15
        op = max(0.0, 0.19 - i * 0.0032)
        color = style.palette[i % len(style.palette)]
        elems.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{color}" opacity="{op:.3f}"/>')

    # Radial spokes with modulation.
    for i in range(280):
        angle = (i / 280) * math.tau
        amp = 0.35 + 0.65 * abs(math.sin(i * 0.17 + phase * 2.4))
        r1 = 45
        r2 = 130 + 290 * amp
        x1 = cx + r1 * math.cos(angle)
        y1 = cy + r1 * math.sin(angle)
        x2 = cx + r2 * math.cos(angle)
        y2 = cy + r2 * math.sin(angle)
        c = style.palette[(i // 18) % len(style.palette)]
        op = 0.12 + 0.36 * amp
        elems.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{c}" stroke-width="1.1" opacity="{op:.3f}"/>')

    # Orbiting curve rings.
    for ring in range(5):
        pts = []
        for i in range(260):
            a = (i / 259) * math.tau
            r = 160 + ring * 54 + 18 * math.sin(a * (4 + ring) + phase * 2.0)
            x = cx + r * math.cos(a)
            y = cy + 0.65 * r * math.sin(a)
            pts.append((x, y))
        c = style.palette[ring % len(style.palette)]
        d = _path(pts)
        elems.append(f'<path d="{d}" stroke="{c}" stroke-width="8" opacity="0.06" fill="none"/>')
        elems.append(f'<path d="{d}" stroke="{c}" stroke-width="1.2" opacity="0.45" fill="none"/>')

    for _ in range(350):
        x = rng.uniform(0, w)
        y = rng.uniform(0, h)
        r = rng.uniform(0.5, 2.3)
        c = style.palette[rng.randrange(0, len(style.palette))]
        op = rng.uniform(0.06, 0.35)
        elems.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{c}" opacity="{op:.3f}"/>')

    return "".join(elems)


def _lattice_fold_svg(style: Style, w: int, h: int, phase: float, rng: random.Random) -> str:
    elems: list[str] = []

    # Faceted vertical curtains.
    columns = 42
    for col in range(columns):
        xn = col / (columns - 1)
        x = xn * w
        env = 0.35 + 0.65 * (1 - abs(xn - 0.5) * 1.8)
        for seg in range(22):
            y1 = h * (seg / 22)
            y2 = h * ((seg + 1) / 22)
            bend = 38 * env * math.sin(seg * 0.42 + xn * 9 + phase * 2)
            x2 = x + bend
            c = style.palette[(seg + col) % len(style.palette)]
            op = 0.03 + 0.02 * seg
            elems.append(f'<line x1="{x:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{c}" stroke-width="0.9" opacity="{op:.3f}"/>')

    # Crossing sine folds.
    for layer in range(14):
        pts = _wave(w, h, phase + layer * 0.27, amp=0.062 + layer * 0.003, f1=0.7 + layer * 0.05, f2=1.2)
        d = _path(pts)
        yoff = (layer - 7) * 7.5
        c = style.palette[layer % len(style.palette)]
        elems.append(f'<path d="{d}" transform="translate(0,{yoff:.2f})" stroke="{c}" stroke-width="11" opacity="0.07" fill="none"/>')
        elems.append(f'<path d="{d}" transform="translate(0,{yoff:.2f})" stroke="{c}" stroke-width="1.6" opacity="0.55" fill="none"/>')

    for _ in range(180):
        x = rng.uniform(0, w)
        y = rng.uniform(0, h)
        c = style.palette[rng.randrange(0, len(style.palette))]
        elems.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.0" fill="{c}" opacity="0.14"/>')

    return "".join(elems)


def _preview_content(style: Style, w: int, h: int, phase: float, rng: random.Random) -> str:
    if style.mode == "mesh_ribbon":
        return _mesh_ribbon_svg(style, w, h, phase, rng)
    if style.mode == "radial_prism":
        return _radial_prism_svg(style, w, h, phase, rng)
    return _lattice_fold_svg(style, w, h, phase, rng)


def write_preview(style: Style, w: int, h: int, phase: float, out_file: Path, seed: int) -> None:
    rng = random.Random(seed)
    content = _preview_content(style, w, h, phase, rng)
    svg = dedent(
        f"""\
        <svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
          <defs>
            <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="{style.bg_top}"/>
              <stop offset="100%" stop-color="{style.bg_bottom}"/>
            </linearGradient>
            <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="8" result="b"/>
              <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
          </defs>
          <rect width="100%" height="100%" fill="url(#bg)"/>
          <g filter="url(#glow)">{content}</g>
          <text x="36" y="58" fill="#E7F8FF" opacity="0.82" font-size="28" font-family="Arial, sans-serif">{style.title}</text>
        </svg>
        """
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(svg, encoding="utf-8")


def generate_previews(preview_dir: Path, width: int, height: int) -> list[Path]:
    files: list[Path] = []
    for style_index, style in enumerate(STYLES.values()):
        for num, phase in enumerate((0.0, 0.8), start=1):
            path = preview_dir / f"{style.key}_preview_{num}.svg"
            write_preview(style, width, height, phase, path, seed=700 + style_index * 100 + num)
            files.append(path)
    return files


def ffmpeg_filter(style: Style, w: int, h: int, fps: int) -> str:
    if style.mode == "mesh_ribbon":
        return ";".join([
            f"color=c={style.bg_top}:s={w}x{h}:r={fps}[bg]",
            f"[0:a]showwaves=s={w}x{h}:mode=cline:colors={style.palette[0]}:rate={fps},gblur=sigma=7[w0]",
            f"[0:a]showwaves=s={w}x{h}:mode=line:colors={style.palette[1]}:rate={fps},gblur=sigma=3[w1]",
            f"[0:a]showwaves=s={w}x{h}:mode=p2p:colors={style.palette[2]}:rate={fps},gblur=sigma=5[w2]",
            "[bg][w0]overlay=0:0[t1]",
            "[t1][w1]overlay=0:0[t2]",
            "[t2][w2]overlay=0:0,eq=saturation=1.35:contrast=1.08,format=yuv420p[v]",
        ])
    if style.mode == "radial_prism":
        return ";".join([
            f"color=c={style.bg_bottom}:s={w}x{h}:r={fps}[bg]",
            f"[0:a]showwaves=s={w}x{h}:mode=point:colors={style.palette[2]}:rate={fps},gblur=sigma=2[p]",
            f"[0:a]showwaves=s={w}x{h}:mode=cline:colors={style.palette[0]}:rate={fps},gblur=sigma=8[c]",
            "[bg][p]overlay=0:0[t1]",
            "[t1][c]overlay=0:0,curves=all='0/0 0.4/0.5 1/1',eq=saturation=1.55:gamma=1.05,format=yuv420p[v]",
        ])
    return ";".join([
        f"color=c={style.bg_top}:s={w}x{h}:r={fps}[bg]",
        f"[0:a]showwaves=s={w}x{h}:mode=cline:colors={style.palette[1]}:rate={fps}[a]",
        f"[0:a]showwaves=s={w}x{h}:mode=line:colors={style.palette[0]}:rate={fps}[b]",
        "[a]gblur=sigma=4[ab]",
        "[b]gblur=sigma=6[bb]",
        "[bg][ab]overlay=0:0[t1]",
        "[t1][bb]overlay=0:0,unsharp=7:7:0.9:7:7:0.0,eq=saturation=1.3,format=yuv420p[v]",
    ])


def render_video(style_key: str, audio: Path, output: Path, width: int, height: int, fps: int) -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is required but not found in PATH.")
    style = STYLES[style_key]
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(audio), "-filter_complex", ffmpeg_filter(style, width, height, fps),
        "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-c:a", "aac", "-b:a", "320k", "-shortest", str(output),
    ]
    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Premium FFmpeg visualizer with 3 distinct styles")
    p.add_argument("--style", choices=STYLES.keys(), default="wire_ribbon")
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
        for file in files:
            print(f"- {file}")
        return
    if args.audio is None:
        raise SystemExit("--audio is required unless --render-previews is used.")
    render_video(args.style, args.audio, args.output, args.width, args.height, args.fps)
    print(f"Video rendered: {args.output}")


if __name__ == "__main__":
    main()
