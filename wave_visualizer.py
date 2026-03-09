#!/usr/bin/env python3
"""FFmpeg thin-wave visualizer generator with built-in style previews.

- Uses FFmpeg for final render.
- Uses only Python stdlib math functions for style geometry.
- Exports static SVG preview images (1-2 per style) so you can choose without rendering video.
"""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent


@dataclass(frozen=True)
class WaveStyle:
    key: str
    title: str
    background: str
    colors: tuple[str, ...]
    glow: float
    thickness: int
    harmonics: tuple[tuple[float, float, float], ...]  # amplitude, freq, phase


STYLES: dict[str, WaveStyle] = {
    "vivid": WaveStyle(
        key="vivid",
        title="Vivid Wave Of Colors Wave Sound Effect",
        background="#020010",
        colors=("#00E5FF", "#FF41F2", "#FFE66D", "#00FF9C"),
        glow=0.35,
        thickness=2,
        harmonics=((1.0, 1.0, 0.0), (0.42, 2.5, 1.0), (0.18, 4.2, 2.2)),
    ),
    "animated": WaveStyle(
        key="animated",
        title="Animated Wave Wave Music Wave Wave And Sound Background",
        background="#041521",
        colors=("#4CC9F0", "#4895EF", "#3F37C9", "#80FFDB"),
        glow=0.26,
        thickness=2,
        harmonics=((1.0, 0.8, 0.0), (0.30, 2.2, 1.4), (0.14, 3.7, 2.0)),
    ),
    "equalizer": WaveStyle(
        key="equalizer",
        title="Abstract Sound Equalizer Background Shining Music Wave Design Equalizer",
        background="#0B0714",
        colors=("#FF8A00", "#FF0058", "#7A00FF", "#00D4FF"),
        glow=0.30,
        thickness=2,
        harmonics=((1.0, 1.2, 0.0), (0.35, 2.8, 0.5), (0.15, 5.0, 1.1)),
    ),
}


def make_wave_points(style: WaveStyle, phase: float, width: int, samples: int = 360) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    center = 0.5
    amp = 0.11
    for i in range(samples):
        x_norm = i / (samples - 1)
        x = x_norm * width
        y = 0.0
        for a, f, p in style.harmonics:
            y += a * math.sin((x_norm * math.pi * 6.0 * f) + phase + p)
        y_norm = center + amp * y / 1.6
        points.append((x, y_norm))
    return points


def points_to_path(points: list[tuple[float, float]], height: int) -> str:
    cmds = []
    for idx, (x, y_norm) in enumerate(points):
        y = y_norm * height
        prefix = "M" if idx == 0 else "L"
        cmds.append(f"{prefix}{x:.2f},{y:.2f}")
    return " ".join(cmds)


def write_preview_svg(style: WaveStyle, width: int, height: int, phase: float, out_file: Path) -> None:
    lines = []
    for idx, color in enumerate(style.colors):
        pts = make_wave_points(style, phase + idx * 0.4, width)
        path = points_to_path(pts, height)
        y_offset = (idx - (len(style.colors) - 1) / 2) * 12
        lines.append(
            f'<path d="{path}" transform="translate(0,{y_offset:.1f})" '
            f'stroke="{color}" stroke-width="{style.thickness * 3}" stroke-linecap="round" '
            f'fill="none" opacity="{style.glow:.2f}"/>'
        )
        lines.append(
            f'<path d="{path}" transform="translate(0,{y_offset:.1f})" '
            f'stroke="{color}" stroke-width="{style.thickness}" stroke-linecap="round" '
            f'fill="none" opacity="0.98"/>'
        )

    svg = dedent(
        f"""\
        <svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
          <defs>
            <linearGradient id="bg" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="{style.background}"/>
              <stop offset="100%" stop-color="#000000"/>
            </linearGradient>
          </defs>
          <rect width="100%" height="100%" fill="url(#bg)"/>
          <line x1="0" x2="{width}" y1="{height/2:.2f}" y2="{height/2:.2f}" stroke="#FFFFFF" stroke-opacity="0.07"/>
          {''.join(lines)}
          <text x="40" y="60" fill="#FFFFFF" fill-opacity="0.85" font-size="28" font-family="Arial, sans-serif">{style.title}</text>
        </svg>
        """
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(svg, encoding="utf-8")


def generate_previews(preview_dir: Path, width: int, height: int) -> list[Path]:
    out: list[Path] = []
    for style in STYLES.values():
        for i, phase in enumerate((0.0, 0.55), start=1):
            target = preview_dir / f"{style.key}_preview_{i}.svg"
            write_preview_svg(style, width=width, height=height, phase=phase, out_file=target)
            out.append(target)
    return out


def ffmpeg_filter(style: WaveStyle, width: int, height: int, fps: int) -> str:
    # Build multi-layer thin showwaves composition for premium look.
    parts = [
        f"[0:a]aformat=channel_layouts=stereo,showwaves=s={width}x{height}:mode=line:colors={style.colors[0]}:rate={fps}[w0]",
        f"[0:a]aformat=channel_layouts=stereo,showwaves=s={width}x{height}:mode=line:colors={style.colors[1]}:rate={fps}[w1]",
        f"[0:a]aformat=channel_layouts=stereo,showwaves=s={width}x{height}:mode=line:colors={style.colors[2]}:rate={fps}[w2]",
        f"[0:a]aformat=channel_layouts=stereo,showwaves=s={width}x{height}:mode=line:colors={style.colors[3]}:rate={fps}[w3]",
        f"color=c={style.background}:s={width}x{height}:r={fps}[bg]",
        "[w0]gblur=sigma=6:steps=1[w0g]",
        "[w1]gblur=sigma=5:steps=1[w1g]",
        "[w2]gblur=sigma=6:steps=1[w2g]",
        "[w3]gblur=sigma=5:steps=1[w3g]",
        "[bg][w0g]overlay=0:0[tmp1]",
        "[tmp1][w1g]overlay=0:0[tmp2]",
        "[tmp2][w2g]overlay=0:0[tmp3]",
        "[tmp3][w3g]overlay=0:0[tmp4]",
        "[tmp4][w0]overlay=0:0[tmp5]",
        "[tmp5][w1]overlay=0:0[tmp6]",
        "[tmp6][w2]overlay=0:0[tmp7]",
        "[tmp7][w3]overlay=0:0,format=yuv420p[v]",
    ]
    return ";".join(parts)


def render_video(style_key: str, audio: Path, output: Path, width: int, height: int, fps: int) -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is required but not found in PATH.")
    style = STYLES[style_key]
    output.parent.mkdir(parents=True, exist_ok=True)
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
    p = argparse.ArgumentParser(description="Thin-wave visualizer (FFmpeg + math)")
    p.add_argument("--style", choices=STYLES.keys(), default="vivid")
    p.add_argument("--audio", type=Path, help="Audio input file")
    p.add_argument("--output", type=Path, default=Path("output/visualizer.mp4"))
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--render-previews", action="store_true", help="Generate SVG preview images only")
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
