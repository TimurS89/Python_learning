# Python_learning

## Reference-Inspired FFmpeg Wave Visualizer

`wave_visualizer.py` now provides **three clearly different visualizer styles** inspired by your attached references:

1. **Aurora Mist Wave** (`aurora_mist`)  
   Layered translucent aqua wave fog + floating particles.
2. **Neon Pulse Spectrum** (`neon_pulse`)  
   Cyan/magenta center glow, beam core, and pulse/equalizer accents.
3. **Wire Ribbon Wave** (`wire_ribbon`)  
   Bright blue ribbon waves with dotted wireframe texture.

## Requirements

- Python 3.9+
- FFmpeg available in `PATH` (for final MP4 rendering)

## Generate style previews only

```bash
python wave_visualizer.py --render-previews --width 1280 --height 720 --preview-dir previews
```

This creates 2 previews for each of the 3 styles.

## Render final video

```bash
python wave_visualizer.py --style aurora_mist --audio your_song.mp3 --output output/aurora_mist.mp4 --width 1920 --height 1080 --fps 30
```

Use `--style neon_pulse` or `--style wire_ribbon` for the other looks.

## Preview files

- `previews/aurora_mist_preview_1.svg`
- `previews/aurora_mist_preview_2.svg`
- `previews/neon_pulse_preview_1.svg`
- `previews/neon_pulse_preview_2.svg`
- `previews/wire_ribbon_preview_1.svg`
- `previews/wire_ribbon_preview_2.svg`
