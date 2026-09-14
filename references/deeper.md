# 只在需要细看时使用

普通浏览只需要能操作浏览器、读页面和看截图。下面的能力按需使用，不是开始刷视频的前置步骤。

运行本 skill 的 `scripts/doctor.py` 可只读检测当前 Python、托管 runtime、明确配置的 Python 环境、FFmpeg 和本地模型候选；不联网、不安装、不加载模型、不读取 Cookie。输出 `runtimes` 给出实际可复用路径。检测会执行这些可信 Python 的包查询，不扫描全部磁盘或浏览器账户。

已复用的能力与历史验证（2026-09-13—14）：

- 随包 `scripts/sample_frames.py` 来自 `video-analyze`：连续取帧、局部加密、真实 PTS、联系表、变帧率与末帧完整性；实际打开图片才算观察画面。
- 随包 `scripts/audio_to_text.py` 来自 `video-transcribe`：本地 faster-whisper / MLX Whisper，保留时间戳与来源。字幕优先，音轨兜底；原稿单独保留。
- Apple Silicon 上用 yt-dlp 2026.08.19、PyAV/Pillow、本地 faster-whisper / MLX Whisper 跑通过样本。这些历史结果不意味着其他环境已经验证；使用前检查当前环境。
- 实测过 B 站媒体、两条抖音短链下载和 YouTube 既有字幕读取；不保证其他视频、地区、登录内容或其他机器可用。Chrome 登录不保证命令行能解密 Cookie，公开音轨可能仍可访问。

缺组件时仍可用浏览器画面和可见字幕继续浏览，明确范围。只有当前问题确实需要时才在独立 venv 安装所缺组件。不重装完整 MediaBrief/BiliNote 应用，不重复下载模型。large-v3-turbo 首次下载约 1.6 GB，只在需要且没有合适缓存模型时准备。

对齐帧与文字时核对同一视频版本和音画起点；视频 PTS 与 ASR 时间可能因裁剪/片头不同而错位。平台人工字幕、自动字幕、画面字幕、本地 ASR 分开标注；简介/评论/弹幕不当口述。疑似乱码或幻觉直接弃用，保留未确认说明。

本机此前的音频输入工具返回不支持，配乐、音色、音效、节拍尚未可靠听辨。只有当前工具明确支持并实际成功接收音频，才报告该次听到的声音；先确认是否上传音频、收费或下载模型，并遵循用户授权。不能用 ASR 包存在代替声音理解能力验证。

已有独立环境时，可传 `--python /path/to/venv/bin/python`，多次传入以复用不同模块的环境；本地 MLX 模型用 `--mlx-model /path/to/model`。也可以在数据目录保存私有 `runtime.json`，内容为 `{"python": ["/path/to/venv/bin/python"], "mlx_model": "/path/to/model"}`。路径按实际情况填写，模型字段可省略；不要提交这个本机配置。

## 无旧环境时的最小准备

以下由 Codex 执行，不是让用户手动填配置的前置流程。需要 Python 3.10+；命令里的 `TODDLE_DATA` 不改写系统 HOME。先看 doctor 输出，有可用环境就直接用其 Python 跳过安装。没有合适 Python 时用现有可信包管理器或 uv 准备 Python 3.12，平台/网络阻塞如实说明。

```bash
TODDLE_DATA="${XDG_DATA_HOME:-$HOME/.local/share}/toddle-skill"
python3 -m venv "$TODDLE_DATA/runtime"
"$TODDLE_DATA/runtime/bin/python" -m pip install yt-dlp av Pillow
```

Windows 使用 venv 的 `Scripts/python.exe`。不要重复创建已有 runtime。只有缺语音文字时再在该环境安装 `faster-whisper`；Apple Silicon 已有 mlx-whisper 和模型时直接复用。faster-whisper 默认 base、CPU/int8，首次需下载模型；base 会误识别，专名/关键句需要校对，已缓存较好模型时优先使用。安装失败保留一次具体错误，转到可用的画面/字幕路径，不无限重试。

## 最少命令

`$PY` 是上述可用 Python，`$SKILL` 是当前 toddle-skill 目录，`$URL` 是已核对的公开作品 URL，`$OUT` 是新的该视频产物目录。不同模块可使用不同的既有 Python。文件名用固定名称/视频 ID，第三方文案不要拼进 shell 命令。

```bash
"$PY" -m yt_dlp --ignore-config --no-playlist --socket-timeout 20 --retries 1 --skip-download --list-subs "$URL"
"$PY" -m yt_dlp --ignore-config --no-playlist --socket-timeout 20 --retries 1 -f 'bv*[height<=720]/b[height<=720]/bv*/best' -o "$OUT/source.%(ext)s" "$URL"
"$PY" "$SKILL/scripts/sample_frames.py" "$OUT/source.mp4" --output-dir "$OUT/frames"
```

以实际下载扩展名替换 `source.mp4`；这里取单个含视频的流，可能没有音轨，但可直接取帧而不强制先合并。需要语音时另取音轨；需要完整可播放媒体且有 FFmpeg 时再合并音视频。默认采样最多 72 帧，长片概览不等于完整观看；字幕看不清就打开原帧，动作太快就对具体区间用 `--start 6.8 --end 8.8 --interval 0.1` 加密。

有平台字幕则按实际语言轨下载：`--skip-download --write-subs --write-auto-subs --sub-langs '实际语言代码'`；排除 B 站 danmaku。无字幕才取音轨：

```bash
"$PY" -m yt_dlp --ignore-config --no-playlist --socket-timeout 20 --retries 1 -f 'bestaudio/best' -o "$OUT/audio.%(ext)s" "$URL"
"$PY" "$SKILL/scripts/audio_to_text.py" "$OUT/audio.m4a" --output-dir "$OUT/transcript" --source-url "$URL"
```

以实际音轨扩展名替换 `audio.m4a`。MLX 使用 `--engine mlx-whisper --model '已缓存模型目录'`，并需要 FFmpeg；faster-whisper 可直接使用本地模型目录，避免重复下载。纯音乐/无可靠语音不强行转写。

## 选型依据（2026-09-14 核查）

默认保留 [yt-dlp](https://github.com/yt-dlp/yt-dlp) + PyAV/Pillow + 本地 Whisper，下载器负责取得媒体，Codex 负责解释画面，Whisper 负责语音文字。主页发现仍优先实际浏览器页面；替换组件需证明当前任务更容易完成，不按星数盲换。

- [F2](https://github.com/Johnserf-Seed/f2/blob/main/f2/apps/douyin/dl.py) 提供抖音下载，但当前下载器构造过程要求 Cookie，未证明能简化本机已可用的匿名路径；列为备选，不默认安装。
- [DouK-Downloader](https://github.com/JoeanAmier/TikTokDownloader) 可下载抖音/TikTok；当前 README 明示加密参数算法不再维护，初始化需配置 Cookie，不能作为无配置启动保证。
- [bilibili-api](https://github.com/Nemo2011/bilibili-api) 和 [BBDown](https://github.com/nilaoda/BBDown) 当前默认仓库页已归档/停止维护，不新增为核心依赖。旧分支 README 可能仍可访问，选型以当前仓库状态为准。

以上备选只核查源码/项目说明，没有安装或宣称逐个实测。保留已通过样本的主链，不重复六工具评测。
