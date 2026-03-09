# Python_learning

## Cinematic Wire-Wave Visualizer

This version heavily upgrades the visual language to match premium flowing sound-wave artwork (translucent ribbons + spark particles + glowing layers), with 3 distinct variants:

1. **Wire Flux Aurora** (`wire_flux`)  
   Bright arcing ribbon canopy with strong central woven mesh and spark trails.
2. **Wire Helix Photon** (`wire_helix`)  
   More twisted and energetic ribbon flow with tighter wave crossing behavior.
3. **Wire Silk Dream** (`wire_silk`)  
   Softer satin-like layered ribbons with elegant bright highlights.

## Requirements

- Python 3.9+
- FFmpeg in `PATH` for MP4 rendering

## Generate preview images for review

```bash
python wave_visualizer.py --render-previews --width 1280 --height 720 --preview-dir previews
```

This outputs 3 SVG previews (1 per variant):

- `previews/wire_flux_preview_1.svg`
- `previews/wire_helix_preview_1.svg`
- `previews/wire_silk_preview_1.svg`

## Render a video

```bash
python wave_visualizer.py --style wire_flux --audio your_song.mp3 --output output/wire_flux.mp4 --width 1920 --height 1080 --fps 30
```

Switch with `--style wire_helix` or `--style wire_silk`.
