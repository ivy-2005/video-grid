# Benchmark Video Grid

把任务视频合成为一个适合网页展示的 5×6 视频墙。每个输入视频占一格，不区分单视角或双视角。不同画幅会等比放大并居中裁剪，不留白；片段不足时循环播放。

默认生成 1920×1080、40 秒、30 fps 的 MP4，所有任务以 3 倍速播放，输出无音轨。另附封面图和中间时刻的总览图。合成需要一定时间和内存，实际耗时取决于电脑和源视频。

## 准备

需要 Python 3.10+。脚本优先使用系统中的 FFmpeg；如果没有，会使用 `imageio-ffmpeg` 提供的版本。

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Windows 用户把激活命令换成 `.venv\\Scripts\\activate`。

## 使用

如果已有 `layout.json` 和任务视频（例如桌面的 `exhibition_final`），直接指定配置文件，无需移动视频：

```bash
python3 build_video.py --config /path/to/exhibition_final/layout.json
```

配置中的视频路径以 `layout.json` 所在目录为基准。产物保存在同目录的 `dist/`：

- `benchmark_tasks.mp4`：可用于网站的成片；
- `benchmark_tasks_poster.jpg`：封面图；
- `contact_sheet.jpg`：中间时刻的整墙截图。

如果从零开始，在任意素材目录复制 `layout.example.json` 为 `layout.json`，再把 `slots` 改成实际视频路径。`slots` 按从左到右、从上到下的顺序排列，默认必须有 30 项。同一个路径可以重复填写，用作尚未补齐任务的占位。更新素材后重新执行同一命令，已有产物会被覆盖。

```bash
python3 build_video.py --config /path/to/materials/layout.json
```

`duration_seconds` 控制成片时长，`playback_speed` 控制每格的播放倍速；例如默认 40 秒、3 倍速相当于每格需要 120 秒的源片段时间，不足部分从头循环。`width`、`height`、`rows`、`columns` 和 `fps` 也可在配置中调整；高度需预留 120 像素标题区，剩余高度与宽度要能被网格均分。

## 放到网站

将 MP4 和封面图上传到网站，使用 HTML 视频标签，例如：

```html
<video controls playsinline preload="metadata" poster="benchmark_tasks_poster.jpg" width="100%">
  <source src="benchmark_tasks.mp4" type="video/mp4">
</video>
```

仓库只包含工具和示例配置，不包含任务原视频或合成产物。
