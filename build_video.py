#!/usr/bin/env python3
"""Build a benchmark task grid from a JSON layout and video clips."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


HEADER_HEIGHT = 120
BACKGROUND = "0xf7f7f5"


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="合成 benchmark 任务视频网格")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parent / "layout.json",
        help="配置文件路径；视频路径相对于该文件所在目录",
    )
    args = parser.parse_args()
    config_path = args.config.resolve()
    work_dir = config_path.parent
    output_dir = work_dir / "dist"
    output_video = output_dir / "benchmark_tasks.mp4"
    poster = output_dir / "benchmark_tasks_poster.jpg"
    contact_sheet = output_dir / "contact_sheet.jpg"

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        try:
            import imageio_ffmpeg
        except ImportError as error:
            raise RuntimeError("未找到 FFmpeg，请先安装依赖：python3 -m pip install -r requirements.txt") from error
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    config = json.loads(config_path.read_text(encoding="utf-8"))
    rows = int(config["rows"])
    columns = int(config["columns"])
    duration = float(config["duration_seconds"])
    playback_speed = float(config["playback_speed"])
    width = int(config["width"])
    height = int(config["height"])
    fps = int(config["fps"])
    slots = config["slots"]

    if len(slots) != rows * columns:
        raise ValueError(f"需要 {rows * columns} 个视频位置，配置中有 {len(slots)} 个")
    if duration <= 0 or playback_speed <= 0:
        raise ValueError("视频时长和播放倍速必须大于零")
    if height <= HEADER_HEIGHT or width % columns or (height - HEADER_HEIGHT) % rows:
        raise ValueError("输出尺寸必须能被网格均分，并为标题区留出空间")

    tile_width = width // columns
    tile_height = (height - HEADER_HEIGHT) // rows
    paths = [(work_dir / slot).resolve() for slot in slots]
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"找不到视频文件：{path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    command: list[str] = [ffmpeg, "-hide_banner", "-y", "-loglevel", "error"]
    for path in paths:
        command.extend(["-stream_loop", "-1", "-threads:v", "1", "-i", str(path)])

    filters: list[str] = []
    for index in range(len(paths)):
        filters.append(
            f"[{index}:v]setpts=(PTS-STARTPTS)/{playback_speed:.12f},"
            f"scale={tile_width}:{tile_height}:force_original_aspect_ratio=increase,"
            f"crop={tile_width}:{tile_height},setsar=1,fps={fps},"
            f"trim=duration={duration},setpts=PTS-STARTPTS[v{index}]"
        )

    layout = "|".join(
        f"{column * tile_width}_{row * tile_height}"
        for row in range(rows)
        for column in range(columns)
    )
    streams = "".join(f"[v{index}]" for index in range(len(paths)))
    filters.append(
        f"{streams}xstack=inputs={len(paths)}:layout={layout}:fill={BACKGROUND}:shortest=1,"
        f"pad={width}:{height}:0:{HEADER_HEIGHT}:{BACKGROUND},"
        f"drawtext=text='{config['title']}':x=48:y=38:fontsize=40:"
        "fontcolor=0x222222:font=Sans[outv]"
    )

    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[outv]",
            "-an",
            "-t",
            str(duration),
            "-r",
            str(fps),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_video),
        ]
    )

    print(
        f"正在合成 {len(paths)} 个视频格（{rows}×{columns}，{duration:g} 秒，{playback_speed:g} 倍速），请稍候……",
        flush=True,
    )
    run(command)

    for target, timestamp in ((poster, min(1, duration / 2)), (contact_sheet, duration / 2)):
        run(
            [
                ffmpeg,
                "-hide_banner",
                "-y",
                "-loglevel",
                "error",
                "-ss",
                str(timestamp),
                "-i",
                str(output_video),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(target),
            ]
        )

    print(f"视频：{output_video}")
    print(f"封面：{poster}")
    print(f"总览图：{contact_sheet}")
    print("已完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
