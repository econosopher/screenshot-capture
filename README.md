# screenshot-capture

A small Python CLI that grabs screenshots from a video file at specific timestamps and/or at a fixed interval. It uses `ffmpeg`/`ffprobe` under the hood for accuracy and speed.

## Requirements

- Python 3.8+
- `ffmpeg` and `ffprobe` installed and available on your `PATH`

On macOS (Homebrew):

```bash
brew install ffmpeg
```

On Ubuntu/Debian:

```bash
sudo apt-get update && sudo apt-get install -y ffmpeg
```

## Install (local editable)

```bash
pip install -e .
```

This installs a console command: `screenshot-capture`.

## Usage

Basic examples:

- Take screenshots at specific timestamps:

```bash
screenshot-capture input.mp4 \
  -t 00:00:03,5.5,00:01:10.250 \
  --out-dir shots
```

- Take screenshots every 5 seconds across the whole video:

```bash
screenshot-capture input.mkv \
  -i 5 \
  --out-dir shots
```

- Combine both timestamps and interval within a range:

```bash
screenshot-capture input.mov \
  -t 12,00:00:25 \
  -i 2.5 \
  --start 00:00:10 \
  --end 00:01:00 \
  --out-dir shots
```

- Control output format and size:

```bash
screenshot-capture input.mp4 \
  -i 10 \
  --format jpg \
  --width 1280 \
  --out-dir thumbs
```

## Options

- `input` (positional): Path to the input video file.
- `-t, --timestamps`: Comma-separated timestamps or multiple flags. Accepts seconds (e.g. `12.5`) or `HH:MM:SS[.ms]` (e.g. `00:01:10.250`).
- `--timestamps-file`: File with one timestamp per line (blank lines and lines starting with `#` ignored).
- `-i, --interval`: Interval in seconds for automatic captures.
- `--start`, `--end`: Start/end time bounds for interval captures. Accept seconds or `HH:MM:SS[.ms]`. Defaults: start=0, end=video duration.
- `--out-dir`: Directory where screenshots are written (created if missing). Default: `frames`.
- `--format`: Output image format (`jpg`, `png`, or `webp`). Default: `jpg`.
- `--width`, `--height`: Optional scaling. If only one is provided, the other is auto (-1) to preserve aspect.
- `--prefix`: Filename prefix. Default: `frame`.
- `--quality`: For `jpg/webp`, lower is higher quality for `ffmpeg` (`-q:v`). Default 2 for jpg, 80 for webp.
- `--fast-seek`: Use fast (less accurate) input seeking (`-ss` before `-i`). Default is accurate (slower) seek.
- `--overwrite`: Overwrite existing images; otherwise existing files are skipped.
- `--dry-run`: Print what would happen without writing files.

## Notes

- Timestamp formats supported: plain seconds (`125.5`) or `HH:MM:SS[.ms]` (`01:02:03.250`).
- When using `--interval`, the tool computes times from `start` to just before `end` (end-exclusive) to avoid near-EoS issues.
- Accurate seek places `-ss` after `-i` and can be slower for many timestamps. Enable `--fast-seek` to speed up at the cost of possible frame offset.

## License

UNLICENSED (adjust as you wish)
