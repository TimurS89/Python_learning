# Python_learning

## Premium Wire Visualizer (3 Distinct Variants)

Per your request, this version focuses only on enhanced wire-style aesthetics inspired by top sound-wave visuals.

### Variants

1. **Wire Ribbon Flux** (`wire_flux`)  
   Dense wave sheets + strong hero ribbon curves + luminous point mesh.
2. **Wire Ribbon Helix** (`wire_helix`)  
   Twisted dual-helix wire structure with crossing links and canopy waves.
3. **Wire Ribbon Silk** (`wire_silk`)  
   Elegant layered silk-like wave curtains with refined glow lines.

## Requirements

- Python 3.9+
- FFmpeg in `PATH` for MP4 rendering

## Generate review previews

```bash
python wave_visualizer.py --render-previews --width 1280 --height 720 --preview-dir previews
```

This generates exactly 3 previews (one for each variant) for quick review.

## Render video

```bash
python wave_visualizer.py --style wire_flux --audio your_song.mp3 --output output/wire_flux.mp4 --width 1920 --height 1080 --fps 30
```

Use `--style wire_helix` or `--style wire_silk` for the other variants.

## Preview files

- `previews/wire_flux_preview_1.svg`
- `previews/wire_helix_preview_1.svg`
- `previews/wire_silk_preview_1.svg`
