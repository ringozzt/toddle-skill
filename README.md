# toddle-skill

让 AI 陪你刷短视频、逛 B 站，也逐渐看懂你的兴趣。

`toddle` 是蹒跚学步。这个项目把浏览器、视频取帧和语音转写接到同一个 Codex skill：打开首页，选一条视频，理解画面与语言，记住发现，再决定下一条看什么。它也能从单条链接或一个主题开始。

> 先生/女士，这会花费不少 token。作为交换，你的 AI 可以沿着你的 feed 认识近期兴趣，发现反复出现的主题，也告诉你哪些判断还需要你来确认。

## 两句话就可以开始

**刷抖音：**

```text
用 $toddle-skill 开始刷抖音，看到有意思的内容告诉我，我叫停时再结束。
```

**逛 B 站：**

```text
用 $toddle-skill 逛我的 B 站首页，看看推荐流反映了哪些近期偏好。
```

默认使用 [抖音推荐流](https://www.douyin.com/?recommend=1) 或 [B 站首页](https://www.bilibili.com/)，优先复用你指定的浏览器和已经打开的页面。也可以说“只看 5 条”“刷 10 分钟”“重点找运镜灵感”，或直接给视频链接。不指定时长时，会在当前任务中持续浏览，直到你叫停或运行环境无法继续；不会自行创建后台定时任务。

## 它能做什么

| 场景 | 行为与产物 |
|---|---|
| 浏览推荐流 | 阅读当前页面，观察实际画面和字幕，识别作品来源，选择或跳过内容 |
| 理解一条视频 | 将时间点、画面变化、对应语言与判断联系起来，保留可回查的来源 |
| 细看动作或剪辑 | 连续取帧、局部密集采样，打开真实帧核对，避免只凭封面猜内容 |
| 没有可靠字幕 | 获取可访问的音轨，复用本地 Whisper 转写，保留时间戳与原稿 |
| 认识近期偏好 | 从多条作品和用户反馈积累兴趣假设、支持证据与反例，帮助后续选片 |
| 结束或续看 | 保存观看范围、笔记与未确认事项，再次遇到同一作品时优先复用 |

推荐流能反映平台正在给你看什么。它不等于你喜欢的全部内容，也不是平台内部用户画像的直接读数。toddle-skill 会区分推荐曝光、真实用户行为和用户明确反馈，代理自己的点击不算你的选择。所谓越来越懂你，来自本地笔记和可修订的偏好记录，不是重新训练底层模型。具体规则见 [兴趣记录](references/interests.md)。

## 安装

需要一个能操作浏览器、读取页面并查看图片的 Codex 环境。浏览器应能正常打开目标平台；skill 本身不提供浏览器连接或平台账号。只有纯文本终端、没有浏览器工具时，无法直接操作首页推荐流，仍可处理给定链接或本地媒体。

可以直接让 Codex 安装：

```text
从 https://github.com/ringozzt/toddle-skill 安装 toddle-skill 到我的全局 skills 目录。
```

也可以在 macOS / Linux 上运行：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
git clone https://github.com/ringozzt/toddle-skill.git "${CODEX_HOME:-$HOME/.codex}/skills/toddle-skill"
```

Windows 默认目录是 `%USERPROFILE%\.codex\skills\toddle-skill`。已存在同名目录时先检查旧版本，不要覆盖本机修改。安装后在新任务中调用 `$toddle-skill`。

目标是在浏览器已连接、平台可访问的环境里，五分钟内开始看第一条。首次浏览不要求建会话、配置数据库或先下载大模型。浏览器信息不够时，Codex 会主动获取媒体、取帧或转写，不会只看标题就声称理解了视频。全新机器的 Python、依赖安装、登录和模型下载耗时受环境影响，五分钟不是整套准备工作的保证。

## 工具按需准备

随包提供三个小脚本，不需要另外安装 video-analyze / video-transcribe：

- [`doctor.py`](scripts/doctor.py)：检查已有 Python 环境、包版本、FFmpeg 和本地模型候选。
- [`sample_frames.py`](scripts/sample_frames.py)：按真实帧时间生成图片、联系表和 JSON，支持局部密集采样。
- [`audio_to_text.py`](scripts/audio_to_text.py)：使用 faster-whisper 或 MLX Whisper 生成 Markdown、SRT 和带来源的 JSON。

采集使用 [yt-dlp](https://github.com/yt-dlp/yt-dlp)，取帧使用 [PyAV](https://github.com/PyAV-Org/PyAV) 与 [Pillow](https://github.com/python-pillow/Pillow)，语音使用 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 或 [MLX Whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper)。优先复用现成环境和缓存模型，缺什么再安装什么；具体命令和失败时的替代路径见 [按需工具说明](references/deeper.md)。

## 成本、记录与边界

连续浏览会消耗模型 token，密集看帧和长视频转写会增加处理成本。你可以随时限定数量、时长或让它停止。持续探索时，只对选中的内容增加处理深度，避免给每张首页卡片都下载整片。

观看记录默认写入 `${XDG_DATA_HOME:-~/.local/share}/toddle-skill/history.jsonl`，兴趣假设写入同目录的 `interests.json`。本机环境路径可放 `runtime.json`，模型和媒体也放数据目录，保持仓库干净。这些文件不会由本项目自动上传，但用于理解的页面文字、图像和转写会进入你使用的 AI 上下文，数据处理方式取决于对应产品和账户设置。

当前视觉以实际页面截图、连续取帧和局部观察为主；语音主要依赖字幕或 ASR。成功返回文字不代表识别正确，乱码和疑似幻觉不会当作台词。配乐、音色、音效、节拍没有可靠输入时不作听辨结论，也不把抽样观察称作完整实时视听。

浏览不会自动点赞、投币、关注、评论、私信或向好友分享。抖音分享面板里的“复制链接”仅用于记录来源。平台内容能否访问取决于具体作品、登录状态、地区和工具版本，不承诺所有链接可下载。

## 验证与贡献

开发过程中已在 Apple Silicon 上验证 B 站媒体、两条抖音短链、YouTube 既有字幕、带时间戳转写，以及连续取帧的局部加密、变帧率、末帧完整性和防覆盖。本机浏览器已打开过抖音推荐流和 B 站首页，并完成过画面与语言的局部对照。这些是样本验证，不覆盖每个平台状态或操作系统。

欢迎提交能复现的问题和改进：提供工具版本、脱敏错误与允许公开的输入，别上传 Cookie、观看历史、用户画像或未经允许的媒体。修改脚本时做与改动相称的验证，未改的模型与媒体处理不用重新做整套评测。

仓库的环境检测测试不需要下载模型：

```bash
python3 -m unittest discover -s tests -v
```

本项目使用 [MIT License](LICENSE)。外部工具、模型和视频内容各自遵循其许可证与使用条件。
