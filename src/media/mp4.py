import subprocess
from shutil import which
from pathlib import Path

from src.core.cache_manager import CacheManager
from src.utils.utils import download_file


def download_mp4(url: str, out_path: Path):
    return download_file(url, out_path)


def extract_frames(mp4_path: Path, frames_dir: Path, fps: int = 1, max_frames: int = 4):
    frames_dir.mkdir(parents=True, exist_ok=True)

    pattern = str(frames_dir / "frame_%04d.png")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", str(mp4_path),
            "-vf", f"fps={fps}",
            "-frames:v", str(max_frames),
            pattern,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    return sorted(frames_dir.glob("frame_*.png"))


def extract_mp4(video_url: str, cache: CacheManager, fps: int = 1, max_frames: int = 4):
    video_id = cache.hash_key(video_url)

    mp4_dir = cache.mp4_dir(video_id)
    frames_dir = mp4_dir / "frames"
    video_file = mp4_dir / "video.mp4"

    if not video_file.exists():
        try:
            download_mp4(video_url, video_file)
        except Exception:
            return {
                "provider": "mp4",
                "id": video_id,
                "url": video_url,
                "video_path": "",
                "frames_dir": str(frames_dir),
                "frames": [],
            }

    frames = sorted(frames_dir.glob("frame_*.png"))
    if not frames and which("ffmpeg"):
        try:
            frames = extract_frames(video_file, frames_dir, fps=fps, max_frames=max_frames)
        except Exception:
            frames = []

    return {
        "provider": "mp4",
        "id": video_id,
        "url": video_url,
        "video_path": str(video_file),
        "frames_dir": str(frames_dir),
        "frames": [str(f) for f in frames],
    }
