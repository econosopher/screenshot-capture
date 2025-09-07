from __future__ import annotations

import os
import shutil
import subprocess
from typing import Optional, Sequence


class FFmpegNotFoundError(RuntimeError):
    pass


def _require_binaries() -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        raise FFmpegNotFoundError(
            f"Missing required binaries: {', '.join(missing)}. Install ffmpeg/ffprobe and ensure they are on PATH."
        )


def probe_duration(path: str) -> float:
    _require_binaries()
    try:
        # Returns only the duration number in seconds
        out = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nokey=1:noprint_wrappers=1",
                path,
            ],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        msg = e.output.decode("utf-8", errors="ignore")
        raise RuntimeError(f"ffprobe failed for {path!r}: {msg}")
    try:
        return float(out.decode("utf-8").strip())
    except Exception as exc:
        raise RuntimeError(f"Unable to parse duration from ffprobe output: {out!r}") from exc


def capture_frame(
    input_path: str,
    time_seconds: float,
    output_path: str,
    *,
    width: Optional[int] = None,
    height: Optional[int] = None,
    img_format: str = "jpg",
    quality: Optional[int] = None,
    overwrite: bool = False,
    fast_seek: bool = False,
) -> None:
    """Capture a single frame using ffmpeg.

    If fast_seek is False, uses accurate seek by placing -ss after -i (slower, more accurate).
    If fast_seek is True, places -ss before -i (faster, less accurate).
    """
    _require_binaries()
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Build video filters
    vf_parts = []
    if width or height:
        w = width if width and width > 0 else -1
        h = height if height and height > 0 else -1
        vf_parts.append(f"scale={w}:{h}")
    vf = None
    if vf_parts:
        vf = ",".join(vf_parts)

    args: list[str] = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    if fast_seek:
        args += ["-ss", f"{time_seconds:.6f}", "-i", input_path]
    else:
        args += ["-i", input_path, "-ss", f"{time_seconds:.6f}"]

    if vf:
        args += ["-vf", vf]

    # Select format-specific options
    fmt = img_format.lower()
    if fmt in ("jpg", "jpeg", "webp") and quality is not None:
        args += ["-q:v", str(quality)]
    elif fmt == "png":
        # Optional: mild compression for smaller files without being too slow
        args += ["-compression_level", "3"]

    args += ["-frames:v", "1"]
    args += ["-y" if overwrite else "-n"]
    args += [output_path]

    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"ffmpeg failed extracting frame at {time_seconds:.3f}s to {output_path!r}"
        ) from e

