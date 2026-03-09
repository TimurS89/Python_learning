# Python_learning

## Premium FFmpeg Thin-Wave Visualizer

`wave_visualizer.py` now ships with **3 significantly different visual directions**:

1. **Wire Ribbon Infinity** (`wire_ribbon`)  
   Deep blue flowing ribbons with dense dotted wire mesh and cinematic glow.
2. **Prism Spectrum Pulse** (`prism_spectrum`)  
   Radial neon spectrum burst with orbit rings and pulse spokes.
3. **Lattice Dream Waves** (`lattice_dream`)  
   Folded lattice curtains + crossing wave sheets in an elegant abstract look.

These were redesigned to be much richer and more publication-ready for YouTube/social platforms.

## Requirements

- Python 3.9+
- FFmpeg available in `PATH` for final MP4 rendering

## Generate previews (no video render)

```bash
python wave_visualizer.py --render-previews --width 1280 --height 720 --preview-dir previews
```

This creates 2 preview SVG images for each style (6 total).

## Render video

```bash
python wave_visualizer.py --style wire_ribbon --audio your_song.mp3 --output output/wire_ribbon.mp4 --width 1920 --height 1080 --fps 30
```

Switch style via `--style prism_spectrum` or `--style lattice_dream`.

## Generated preview files

- `previews/wire_ribbon_preview_1.svg`
- `previews/wire_ribbon_preview_2.svg`
- `previews/prism_spectrum_preview_1.svg`
- `previews/prism_spectrum_preview_2.svg`
- `previews/lattice_dream_preview_1.svg`
- `previews/lattice_dream_preview_2.svg`
