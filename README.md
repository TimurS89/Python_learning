# Python_learning

## FFmpeg Thin-Wave Visualizer

I added `wave_visualizer.py`, a script that creates high-quality thin-wave music visualizers in three styles:

1. **Vivid Wave Of Colors Wave Sound Effect** (`vivid`)
2. **Animated Wave Wave Music Wave Wave And Sound Background** (`animated`)
3. **Abstract Sound Equalizer Background Shining Music Wave Design Equalizer** (`equalizer`)

### What it does

- Uses **FFmpeg** to render audio visualizer videos.
- Uses Python `math`-based wave construction for style geometry.
- Generates **preview images** (SVG) so you can choose a style before rendering.

### Requirements

- Python 3.9+
- FFmpeg installed and available in `PATH`

### Generate style previews (no video render)

```bash
python wave_visualizer.py --render-previews --width 1280 --height 720 --preview-dir previews
```

### Render a visualizer video

```bash
python wave_visualizer.py --style vivid --audio your_song.mp3 --output output/vivid_visualizer.mp4 --width 1920 --height 1080 --fps 30
```

You can switch styles with `--style animated` or `--style equalizer`.

### Preview files created

- `previews/vivid_preview_1.svg`
- `previews/vivid_preview_2.svg`
- `previews/animated_preview_1.svg`
- `previews/animated_preview_2.svg`
- `previews/equalizer_preview_1.svg`
- `previews/equalizer_preview_2.svg`
