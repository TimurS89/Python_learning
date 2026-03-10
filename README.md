# Python_learning

## Cinematic Wire-Wave Visualizer

This version focuses on premium-looking wire-wave visuals similar to high-end sound-wave artwork.

## wire_flux preview variants (small-scale friendly)

Per latest request, I created 3 enhanced alternatives focused on `wire_flux`, tuned for readability and appeal even at small sizes (~120-180 px):

- `previews/wire_flux_preview_1_variant_a.svg`
- `previews/wire_flux_preview_1_variant_b.svg`
- `previews/wire_flux_preview_1_variant_c.svg`

These use stronger contrast, bolder silhouette ribbons, and controlled glow/spark accents for better downscaled clarity.

## Generate previews

```bash
python wave_visualizer.py --render-previews --width 1280 --height 720 --preview-dir previews
```

## Render video

```bash
python wave_visualizer.py --style wire_flux --audio your_song.mp3 --output output/wire_flux.mp4 --width 1920 --height 1080 --fps 30
```
