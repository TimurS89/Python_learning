#!/usr/bin/env python3
"""Create cinematic audio visualizers inspired by three reference wave looks.

Styles:
1) aurora_mist  - layered translucent aqua wave fog + particles.
2) neon_pulse   - centered cyan/magenta glow band with pulse/equalizer accents.
3) wire_ribbon  - luminous blue ribbon waves with dotted wireframe guides.

The script can:
- Generate static SVG previews (2 per style) so you can pick a look quickly.
- Render MP4 with FFmpeg `showwaves` composition for each style.
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
    colors: tuple[str, ...]
    mode: str


STYLES: dict[str, Style] = {
    "aurora_mist": Style(
        key="aurora_mist",
        title="Aurora Mist Wave",
        bg_top="#020612",
        bg_bottom="#000000",
        colors=("#95fff5", "#66f2ea", "#d7fff8", "#49ced6"),
        mode="mist",
    ),
    "neon_pulse": Style(
        key="neon_pulse",
        title="Neon Pulse Spectrum",
        bg_top="#060019",
        bg_bottom="#000008",
        colors=("#2ab7ff", "#00e9ff", "#ff4ca0", "#ff6cab"),
        mode="pulse",
    ),
    "wire_ribbon": Style(
        key="wire_ribbon",
        title="Wire Ribbon Wave",
        bg_top="#03143a",
        bg_bottom="#000713",
        colors=("#1ac8ff", "#47deff", "#84ebff", "#0ca0ff"),
        mode="wire",
    ),
}


def _path_from_points(points: list[tuple[float, float]]) -> str:
    return " ".join([("M" if i == 0 else "L") + f"{x:.2f},{y:.2f}" for i, (x, y) in enumerate(points)])


def _wave_points(width: int, height: int, phase: float, f1: float, f2: float, amp: float) -> list[tuple[float, float]]:
    pts = []
    for i in range(460):
        xn = i / 459
        x = xn * width
        y = (
            0.52
            + amp * math.sin(xn * math.pi * 2.4 * f1 + phase)
            + (amp * 0.45) * math.sin(xn * math.pi * 8.0 * f2 + phase * 1.9)
        )
        pts.append((x, y * height))
    return pts


def _mist_svg(style: Style, width: int, height: int, phase: float, rng: random.Random) -> str:
    layers = []
    for i in range(10):
        pts = _wave_points(width, height, phase + i * 0.28, 0.75 + i * 0.05, 0.85 + i * 0.03, amp=0.09 + i * 0.004)
        path = _path_from_points(pts)
        color = style.colors[i % len(style.colors)]
        dy = (i - 5) * 8
        layers.append(
            f'<path d="{path}" transform="translate(0,{dy})" stroke="{color}" stroke-width="{16 - i}" opacity="{0.04 + i*0.015:.3f}" fill="none"/>'
        )
        layers.append(
            f'<path d="{path}" transform="translate(0,{dy})" stroke="{color}" stroke-width="1.2" opacity="0.34" fill="none"/>'
        )

    particles = []
    for _ in range(420):
        x = rng.uniform(0, width)
        y = rng.uniform(height * 0.18, height * 0.9)
        r = rng.uniform(0.4, 2.1)
        op = rng.uniform(0.05, 0.35)
        c = style.colors[rng.randrange(0, len(style.colors))]
        particles.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{c}" opacity="{op:.3f}"/>')

    return "".join(layers + particles)


def _pulse_svg(style: Style, width: int, height: int, phase: float, rng: random.Random) -> str:
    center_y = height * 0.5
    elems = []
    # Core flare
    for i in range(28):
        r = (i + 1) * 22
        op = max(0.0, 0.23 - i * 0.007)
        c = style.colors[i % len(style.colors)]
        elems.append(f'<circle cx="{width/2:.2f}" cy="{center_y:.2f}" r="{r:.2f}" fill="{c}" opacity="{op:.3f}"/>')

    # Horizontal beam
    elems.append(
        f'<rect x="0" y="{center_y - 3:.2f}" width="{width}" height="6" fill="{style.colors[1]}" opacity="0.55"/>'
    )
    elems.append(
        f'<rect x="0" y="{center_y - 1:.2f}" width="{width}" height="2" fill="#ffffff" opacity="0.35"/>'
    )

    # Equalizer spikes around center.
    bars = 160
    for i in range(bars):
        xn = i / (bars - 1)
        x = xn * width
        dist = abs(xn - 0.5)
        env = max(0.04, (1.0 - dist * 2.0) ** 2)
        h = (8 + 120 * env * abs(math.sin(i * 0.31 + phase * 4.0)))
        color = style.colors[(i // 6) % len(style.colors)]
        op = 0.12 + env * 0.45
        elems.append(f'<line x1="{x:.2f}" x2="{x:.2f}" y1="{center_y-h:.2f}" y2="{center_y+h:.2f}" stroke="{color}" stroke-width="1.1" opacity="{op:.3f}"/>')

    # Floating dust
    for _ in range(360):
        x = rng.uniform(0, width)
        y = rng.uniform(0, height)
        c = style.colors[rng.randrange(0, len(style.colors))]
        r = rng.uniform(0.5, 1.8)
        op = rng.uniform(0.06, 0.4)
        elems.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{c}" opacity="{op:.3f}"/>')
    return "".join(elems)


def _wire_svg(style: Style, width: int, height: int, phase: float, rng: random.Random) -> str:
    elems = []
    # Multiple ribbon lines
    for layer in range(22):
        pts = _wave_points(width, height, phase + layer * 0.12, 0.75, 0.95 + layer * 0.03, amp=0.05 + layer * 0.0025)
        path = _path_from_points(pts)
        yoff = (layer - 11) * 5.5
        color = style.colors[layer % len(style.colors)]
        elems.append(f'<path d="{path}" transform="translate(0,{yoff:.2f})" stroke="{color}" stroke-width="0.9" fill="none" opacity="0.26"/>')

    # Main bright ribbons
    for k in range(3):
        pts = _wave_points(width, height, phase + k * 0.7, 0.8 + 0.1 * k, 1.0 + 0.3 * k, amp=0.10)
        path = _path_from_points(pts)
        c = style.colors[k]
        elems.append(f'<path d="{path}" stroke="{c}" stroke-width="11" fill="none" opacity="0.12"/>')
        elems.append(f'<path d="{path}" stroke="{c}" stroke-width="3.2" fill="none" opacity="0.85"/>')

    # Dotted mesh look
    for i in range(220):
        xn = i / 219
        x = xn * width
        y = height * (0.53 + 0.15 * math.sin(xn * math.pi * 4 + phase))
        for j in range(6):
            yy = y + (j - 3) * 16 + math.sin(xn * 25 + j + phase) * 4
            op = 0.10 + (0.02 * j)
            elems.append(f'<circle cx="{x:.2f}" cy="{yy:.2f}" r="1.1" fill="{style.colors[2]}" opacity="{op:.3f}"/>')

    # subtle stars
    for _ in range(120):
        x = rng.uniform(0, width)
        y = rng.uniform(0, height)
        elems.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="0.8" fill="#b5dfff" opacity="0.15"/>')

    return "".join(elems)


def write_preview(style: Style, width: int, height: int, phase: float, out_file: Path, seed: int) -> None:
    rng = random.Random(seed)
    if style.mode == "mist":
        content = _mist_svg(style, width, height, phase, rng)
    elif style.mode == "pulse":
        content = _pulse_svg(style, width, height, phase, rng)
    else:
        content = _wire_svg(style, width, height, phase, rng)

    svg = dedent(
        f"""\
        <svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
          <defs>
            <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="{style.bg_top}"/>
              <stop offset="100%" stop-color="{style.bg_bottom}"/>
            </linearGradient>
            <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="8" result="blur"/>
              <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
          </defs>
          <rect width="100%" height="100%" fill="url(#bg)"/>
          <g filter="url(#softGlow)">{content}</g>
          <text x="34" y="58" fill="#d7f1ff" opacity="0.78" font-size="27" font-family="Arial, sans-serif">{style.title}</text>
        </svg>
        """
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(svg, encoding="utf-8")


def generate_previews(preview_dir: Path, width: int, height: int) -> list[Path]:
    generated: list[Path] = []
    for idx, style in enumerate(STYLES.values()):
        for n, phase in enumerate((0.0, 0.65), start=1):
            path = preview_dir / f"{style.key}_preview_{n}.svg"
            write_preview(style, width, height, phase, path, seed=1000 + idx * 100 + n)
            generated.append(path)
    return generated


def ffmpeg_filter(style: Style, width: int, height: int, fps: int) -> str:
    if style.mode == "mist":
        return ";".join([
            f"color=c={style.bg_top}:s={width}x{height}:r={fps}[bg]",
            f"[0:a]showwaves=s={width}x{height}:mode=line:colors={style.colors[1]}:rate={fps},gblur=sigma=10[w0]",
            f"[0:a]showwaves=s={width}x{height}:mode=cline:colors={style.colors[0]}:rate={fps},gblur=sigma=6[w1]",
            f"[0:a]showwaves=s={width}x{height}:mode=p2p:colors={style.colors[2]}:rate={fps},gblur=sigma=4[w2]",
            "[bg][w0]overlay=0:0[tmp1]",
            "[tmp1][w1]overlay=0:0[tmp2]",
            "[tmp2][w2]overlay=0:0,eq=brightness=-0.02:saturation=1.25,format=yuv420p[v]",
        ])

    if style.mode == "pulse":
        return ";".join([
            f"color=c={style.bg_bottom}:s={width}x{height}:r={fps}[bg]",
            f"[0:a]showwaves=s={width}x{height}:mode=cline:colors={style.colors[0]}:rate={fps},gblur=sigma=7[w0]",
            f"[0:a]showwaves=s={width}x{height}:mode=point:colors={style.colors[2]}:rate={fps},gblur=sigma=3[w1]",
            "[bg][w0]overlay=0:0[tmp1]",
            "[tmp1][w1]overlay=0:0,curves=all='0/0 0.5/0.62 1/1',eq=saturation=1.5:contrast=1.08,format=yuv420p[v]",
        ])

    return ";".join([
        f"color=c={style.bg_top}:s={width}x{height}:r={fps}[bg]",
        f"[0:a]showwaves=s={width}x{height}:mode=cline:colors={style.colors[0]}:rate={fps}[w0]",
        f"[0:a]showwaves=s={width}x{height}:mode=line:colors={style.colors[1]}:rate={fps}[w1]",
        "[w0]gblur=sigma=5[w0b]",
        "[w1]gblur=sigma=2[w1b]",
        "[bg][w0b]overlay=0:0[tmp1]",
        "[tmp1][w1b]overlay=0:0,unsharp=5:5:1.0:5:5:0.0,eq=saturation=1.35,format=yuv420p[v]",
    ])


def render_video(style_key: str, audio: Path, output: Path, width: int, height: int, fps: int) -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is required but not found in PATH.")
    output.parent.mkdir(parents=True, exist_ok=True)
    style = STYLES[style_key]
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(audio),
        "-filter_complex",
        ffmpeg_filter(style, width, height, fps),
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
    parser = argparse.ArgumentParser(description="Reference-inspired FFmpeg wave visualizer")
    parser.add_argument("--style", choices=STYLES.keys(), default="aurora_mist")
    parser.add_argument("--audio", type=Path, help="Input audio file")
    parser.add_argument("--output", type=Path, default=Path("output/visualizer.mp4"))
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--render-previews", action="store_true")
    parser.add_argument("--preview-dir", type=Path, default=Path("previews"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.render_previews:
        created = generate_previews(args.preview_dir, args.width, args.height)
        print("Generated previews:")
        for p in created:
            print(f"- {p}")
        return

    if args.audio is None:
        raise SystemExit("--audio is required unless --render-previews is used.")

    render_video(args.style, args.audio, args.output, args.width, args.height, args.fps)
    print(f"Video rendered: {args.output}")


if __name__ == "__main__":
    main()
