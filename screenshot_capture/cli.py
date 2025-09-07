from __future__ import annotations

import argparse
import os
import sys
from typing import Iterable, List, Optional, Set

from .ffmpeg import FFmpegNotFoundError, capture_frame, probe_duration
from .timeutil import parse_many, parse_time_to_seconds, seconds_to_name


def _read_timestamps_file(path: str) -> List[str]:
    out: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            out.append(s)
    return out


def _collect_times(
    input_path: str,
    timestamps: List[str],
    timestamps_file: Optional[str],
    interval: Optional[float],
    start: Optional[float],
    end: Optional[float],
) -> List[float]:
    # Explicit timestamps
    times: List[float] = []
    if timestamps:
        times.extend(parse_many(timestamps))
    if timestamps_file:
        times.extend(parse_many(_read_timestamps_file(timestamps_file)))

    # Interval-based times
    if interval is not None:
        if start is None:
            start = 0.0
        if end is None:
            # Probe duration only if needed
            end = probe_duration(input_path)
        if end <= start:
            raise ValueError("--end must be greater than --start for interval generation")
        t = float(start)
        # Generate up to but not including end (avoid near-EoS issues)
        # Add a tiny epsilon to account for floating point rounding when comparing
        eps = 1e-9
        while t + eps < end:
            times.append(t)
            t += interval

    # Deduplicate with millisecond rounding to avoid near-duplicates
    rounded: Set[float] = set()
    unique_sorted = []
    for t in sorted(times):
        key = round(t, 3)
        if key not in rounded:
            rounded.add(key)
            unique_sorted.append(float(key))
    return unique_sorted


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Capture screenshots from a video at timestamps and/or intervals (ffmpeg-based)."
    )
    p.add_argument("input", help="Path to input video file (mp4, mkv, etc.)")
    p.add_argument("--out-dir", default="frames", help="Output directory for screenshots (default: frames)")
    p.add_argument("-t", "--timestamps", action="append", default=[], help="Timestamps (comma-separated or repeat flag). Accepts seconds or HH:MM:SS[.ms]")
    p.add_argument("--timestamps-file", help="Path to a file with one timestamp per line")
    p.add_argument("-i", "--interval", type=float, help="Interval in seconds for automatic captures")
    p.add_argument("--start", type=str, help="Start time bound (seconds or HH:MM:SS[.ms])")
    p.add_argument("--end", type=str, help="End time bound (seconds or HH:MM:SS[.ms])")
    p.add_argument("--format", default="jpg", choices=["jpg", "jpeg", "png", "webp"], help="Output image format (default: jpg)")
    p.add_argument("--width", type=int, help="Output width (height auto if not set)")
    p.add_argument("--height", type=int, help="Output height (width auto if not set)")
    p.add_argument("--prefix", default="frame", help="Output filename prefix (default: frame)")
    p.add_argument("--quality", type=int, help="Quality for jpg/webp (ffmpeg -q:v). Lower means higher quality. Default 2 for jpg, 80 for webp")
    p.add_argument("--fast-seek", action="store_true", help="Use fast but less-accurate seek (-ss before -i)")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing screenshots")
    p.add_argument("--dry-run", action="store_true", help="Print actions without writing files")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = args.input
    if not os.path.isfile(input_path):
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    try:
        start_s = parse_time_to_seconds(args.start) if args.start else None
        end_s = parse_time_to_seconds(args.end) if args.end else None
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    if not args.timestamps and not args.timestamps_file and args.interval is None:
        parser.error("Provide at least one of: --timestamps, --timestamps-file, or --interval")

    # Sensible defaults for quality
    quality = args.quality
    if quality is None:
        if args.format.lower() in ("jpg", "jpeg"):
            quality = 2
        elif args.format.lower() == "webp":
            quality = 80

    try:
        times = _collect_times(
            input_path=input_path,
            timestamps=args.timestamps or [],
            timestamps_file=args.timestamps_file,
            interval=args.interval,
            start=start_s,
            end=end_s,
        )
    except (ValueError, FFmpegNotFoundError, RuntimeError) as e:
        print(str(e), file=sys.stderr)
        return 2

    if not times:
        print("No times to capture (after de-duplication and bounds).", file=sys.stderr)
        return 1

    # Prepare output dir
    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)

    # Perform captures
    total = len(times)
    failures = 0
    for idx, t in enumerate(times, start=1):
        name = seconds_to_name(t)
        ext = args.format.lower()
        if ext == "jpeg":
            ext = "jpg"
        out_path = os.path.join(out_dir, f"{args.prefix}_{name}.{ext}")

        if args.dry_run:
            print(f"[{idx}/{total}] {t:.3f}s -> {out_path}")
            continue

        if os.path.exists(out_path) and not args.overwrite:
            print(f"[{idx}/{total}] Skipping existing: {out_path}")
            continue

        try:
            capture_frame(
                input_path,
                t,
                out_path,
                width=args.width,
                height=args.height,
                img_format=ext,
                quality=quality,
                overwrite=args.overwrite,
                fast_seek=args.fast_seek,
            )
            print(f"[{idx}/{total}] Saved {out_path}")
        except (RuntimeError, FFmpegNotFoundError) as e:
            print(f"[{idx}/{total}] FAILED at {t:.3f}s: {e}", file=sys.stderr)
            failures += 1

    if failures:
        print(f"Completed with {failures} failures out of {total} captures.", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

