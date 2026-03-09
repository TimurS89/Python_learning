#!/usr/bin/env python3
"""Ultra-detailed wire-wave visualizer with 3 cinematic variants.

Goal: emulate premium flowing light-ribbon backgrounds similar to stock "sound wave" art.
- Rich translucent ribbons
- Layered wire curves
- Spark fields and glowing trails
- FFmpeg render mode per variant
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
    cool: tuple[str, ...]
    warm: tuple[str, ...]
    mode: str


VARIANTS: dict[str, Variant] = {
    "wire_flux": Variant(
        key="wire_flux",
        title="Wire Flux Aurora",
        bg_top="#081B57",
        bg_bottom="#030713",
        cool=("#A5D7FF", "#BEEBFF", "#A7BEFF", "#D7F7FF"),
        warm=("#FF63D1", "#FF8CE4", "#FFC76D"),
        mode="aurora",
    ),
    "wire_helix": Variant(
        key="wire_helix",
        title="Wire Helix Photon",
        bg_top="#0A1450",
        bg_bottom="#02050F",
        cool=("#96CCFF", "#84E9FF", "#B9B4FF", "#D4F8FF"),
        warm=("#FF66C8", "#FF9AF0", "#FFAA73"),
        mode="helix",
    ),
    "wire_silk": Variant(
        key="wire_silk",
        title="Wire Silk Dream",
        bg_top="#0A2C67",
        bg_bottom="#030816",
        cool=("#C8E2FF", "#C8F3FF", "#B7D2FF", "#ECF7FF"),
        warm=("#FF5BB5", "#FF88E0", "#FFD17A"),
        mode="silk",
    ),
}


def _path(points: list[tuple[float, float]]) -> str:
    return " ".join(("M" if i == 0 else "L") + f"{x:.2f},{y:.2f}" for i, (x, y) in enumerate(points))


def _ribbon_wave(w: int, h: int, phase: float, center: float, amp: float, f1: float, f2: float) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(820):
        xn = i / 819
        x = xn * w
        y = center + amp * math.sin(xn * math.pi * 2.35 * f1 + phase)
        y += amp * 0.52 * math.sin(xn * math.pi * 7.4 * f2 - phase * 1.28)
        y += amp * 0.18 * math.sin(xn * math.pi * 15.0 + phase * 0.7)
        pts.append((x, y * h))
    return pts


def _spark_trail(parts: list[str], v: Variant, w: int, h: int, phase: float, y_bias: float, rng: random.Random) -> None:
    for lane in range(3):
        col = v.warm[lane % len(v.warm)]
        for i in range(140):
            xn = i / 139
            x = xn * w
            y = h * (y_bias + 0.10 * math.sin(xn * math.pi * (4.8 + lane * 0.8) + phase * 1.8 + lane))
            y += math.sin(xn * 40 + lane + phase) * 5
            r = 0.9 + 1.5 * abs(math.sin(i * 0.37 + lane))
            op = 0.18 + 0.45 * (1 - abs(xn - 0.5) * 1.4)
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{col}" opacity="{max(0.05, op):.3f}"/>')

    for _ in range(260):
        x = rng.uniform(0, w)
        y = rng.uniform(h * 0.16, h * 0.92)
        col = v.cool[rng.randrange(0, len(v.cool))]
        r = rng.uniform(0.5, 1.5)
        op = rng.uniform(0.08, 0.25)
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{col}" opacity="{op:.3f}"/>')


def _draw_wire_ribbons(v: Variant, w: int, h: int, phase: float, rng: random.Random, intensity: float, twist: float) -> str:
    parts: list[str] = []

    # soft luminous canopy curves (large transparent ribbons)
    for layer in range(14):
        center = 0.30 + layer * 0.030
        pts = _ribbon_wave(w, h, phase + layer * 0.22, center, 0.080 + layer * 0.0015 * intensity, 0.74 + layer * 0.04, 0.95)
        d = _path(pts)
        c = v.cool[layer % len(v.cool)]
        parts.append(f'<path d="{d}" stroke="{c}" stroke-width="{26 - layer * 1.2:.1f}" opacity="{0.035 + layer * 0.010:.3f}" fill="none"/>')
        parts.append(f'<path d="{d}" stroke="{c}" stroke-width="1.15" opacity="0.43" fill="none"/>')

    # middle energetic wire matrix
    for lane in range(34):
        center = 0.45 + math.sin(lane * 0.21 + phase) * 0.12
        pts = _ribbon_wave(w, h, phase + lane * 0.12 * twist, center, 0.052 + lane * 0.0016, 0.80 + lane * 0.03, 1.04)
        d = _path(pts)
        c = v.cool[(lane + 1) % len(v.cool)]
        yoff = (lane - 17) * 2.2
        parts.append(f'<path d="{d}" transform="translate(0,{yoff:.2f})" stroke="{c}" stroke-width="0.85" opacity="0.24" fill="none"/>')

    # highlighted foreground ribbons
    for k in range(6):
        center = 0.52 + (k - 2.5) * 0.043
        pts = _ribbon_wave(w, h, phase + k * 0.52, center, 0.10, 0.9 + k * 0.08, 1.2)
        d = _path(pts)
        c = v.cool[k % len(v.cool)]
        parts.append(f'<path d="{d}" stroke="{c}" stroke-width="18" opacity="0.10" fill="none"/>')
        parts.append(f'<path d="{d}" stroke="{c}" stroke-width="3.4" opacity="0.94" fill="none"/>')

    # tiny bridge dots giving woven mesh look
    for i in range(400):
        xn = i / 399
        x = xn * w
        y0 = h * (0.54 + 0.09 * math.sin(xn * math.pi * 5.2 + phase * 1.3))
        for row in range(12):
            y = y0 + (row - 6) * 7.6 + math.sin(xn * 35 + row + phase) * 2.8
            op = 0.035 + row * 0.020
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="0.86" fill="{v.cool[2]}" opacity="{op:.3f}"/>')

    _spark_trail(parts, v, w, h, phase, y_bias=0.77, rng=rng)
    return "".join(parts)


def _variant_svg(v: Variant, w: int, h: int, phase: float, rng: random.Random) -> str:
    if v.mode == "aurora":
        return _draw_wire_ribbons(v, w, h, phase, rng, intensity=1.0, twist=1.0)
    if v.mode == "helix":
        return _draw_wire_ribbons(v, w, h, phase + 0.5, rng, intensity=1.2, twist=1.35)
    return _draw_wire_ribbons(v, w, h, phase + 1.1, rng, intensity=0.88, twist=0.75)


def write_preview(v: Variant, w: int, h: int, phase: float, out_file: Path, seed: int) -> None:
    content = _variant_svg(v, w, h, phase, random.Random(seed))
    svg = dedent(
        f"""\
        <svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
          <defs>
            <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="{v.bg_top}"/>
              <stop offset="100%" stop-color="{v.bg_bottom}"/>
            </linearGradient>
            <radialGradient id="centerGlow" cx="50%" cy="42%" r="52%">
              <stop offset="0%" stop-color="#B8ECFF" stop-opacity="0.85"/>
              <stop offset="45%" stop-color="#8CC3FF" stop-opacity="0.35"/>
              <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
            </radialGradient>
            <filter id="glow" x="-35%" y="-35%" width="170%" height="170%">
              <feGaussianBlur stdDeviation="7" result="blur"/>
              <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
          </defs>
          <rect width="100%" height="100%" fill="url(#bg)"/>
          <rect width="100%" height="100%" fill="url(#centerGlow)" opacity="0.72"/>
          <g filter="url(#glow)">{content}</g>
          <text x="34" y="60" fill="#EAF6FF" opacity="0.82" font-size="28" font-family="Arial, sans-serif">{v.title}</text>
        </svg>
        """
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(svg, encoding="utf-8")


def generate_previews(preview_dir: Path, width: int, height: int) -> list[Path]:
    files: list[Path] = []
    for i, v in enumerate(VARIANTS.values()):
        target = preview_dir / f"{v.key}_preview_1.svg"
        write_preview(v, width, height, phase=i * 0.45, out_file=target, seed=900 + i)
        files.append(target)
    return files


def ffmpeg_filter(v: Variant, w: int, h: int, fps: int) -> str:
    # video pipeline is style-aware, while static previews carry the full detailed art direction.
    if v.mode == "aurora":
        return ";".join([
            f"color=c={v.bg_top}:s={w}x{h}:r={fps}[bg]",
            f"[0:a]showwaves=s={w}x{h}:mode=cline:colors={v.cool[0]}:rate={fps},gblur=sigma=8[a0]",
            f"[0:a]showwaves=s={w}x{h}:mode=line:colors={v.cool[1]}:rate={fps},gblur=sigma=4[a1]",
            f"[0:a]showwaves=s={w}x{h}:mode=point:colors={v.warm[0]}:rate={fps},gblur=sigma=3[a2]",
            "[bg][a0]overlay=0:0[t1]",
            "[t1][a1]overlay=0:0[t2]",
            "[t2][a2]overlay=0:0,eq=saturation=1.45:contrast=1.08:gamma=1.04,format=yuv420p[v]",
        ])
    if v.mode == "helix":
        return ";".join([
            f"color=c={v.bg_top}:s={w}x{h}:r={fps}[bg]",
            f"[0:a]showwaves=s={w}x{h}:mode=p2p:colors={v.cool[2]}:rate={fps},gblur=sigma=5[h0]",
            f"[0:a]showwaves=s={w}x{h}:mode=cline:colors={v.cool[0]}:rate={fps},gblur=sigma=7[h1]",
            f"[0:a]showwaves=s={w}x{h}:mode=point:colors={v.warm[1]}:rate={fps},gblur=sigma=2[h2]",
            "[bg][h0]overlay=0:0[t1]",
            "[t1][h1]overlay=0:0[t2]",
            "[t2][h2]overlay=0:0,curves=all='0/0 0.45/0.54 1/1',eq=saturation=1.52,format=yuv420p[v]",
        ])
    return ";".join([
        f"color=c={v.bg_top}:s={w}x{h}:r={fps}[bg]",
        f"[0:a]showwaves=s={w}x{h}:mode=line:colors={v.cool[3]}:rate={fps},gblur=sigma=6[s0]",
        f"[0:a]showwaves=s={w}x{h}:mode=cline:colors={v.cool[1]}:rate={fps},gblur=sigma=3[s1]",
        f"[0:a]showwaves=s={w}x{h}:mode=point:colors={v.warm[2]}:rate={fps},gblur=sigma=2[s2]",
        "[bg][s0]overlay=0:0[t1]",
        "[t1][s1]overlay=0:0[t2]",
        "[t2][s2]overlay=0:0,eq=saturation=1.34:gamma=1.03,unsharp=7:7:0.8:7:7:0.0,format=yuv420p[v]",
    ])


def render_video(style: str, audio: Path, output: Path, width: int, height: int, fps: int) -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is required but not found in PATH.")
    v = VARIANTS[style]
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(audio), "-filter_complex", ffmpeg_filter(v, width, height, fps),
        "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-c:a", "aac", "-b:a", "320k", "-shortest", str(output),
    ]
    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Cinematic wire-wave visualizer")
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
