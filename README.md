<p align="center">
  <img src="assets/toddle-banner.jpg" alt="toddle — a hand-drawn mascot holding a phone, walking beside a small TV companion" width="100%">
</p>

<p align="center">
  <strong>English</strong> · <a href="README.zh-CN.md">简体中文</a>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-24443C?style=flat-square" alt="MIT license"></a>
  <a href="https://www.douyin.com/?recommend=1"><img src="https://img.shields.io/badge/Douyin-181818?style=flat-square" alt="Douyin"></a>
  <a href="https://www.bilibili.com/"><img src="https://img.shields.io/badge/Bilibili-327D9E?style=flat-square" alt="Bilibili"></a>
  <a href="https://www.youtube.com/"><img src="https://img.shields.io/badge/YouTube-C84436?style=flat-square" alt="YouTube"></a>
</p>

**Let your AI pick something interesting and see where it leads.**

toddle helps your agent browse video feeds the way you would: open Douyin or Bilibili, choose something, watch, and decide what to explore next. It connects video frames with captions or speech, follows questions that come up, and keeps notes that help it get to know your interests. You can also start with a YouTube link, a topic or a local video.

The name means taking small, unsteady steps. Start with one video.

## Start browsing

**Your agent needs browser control and image reading.** toddle uses connected browser tools or helps set up a permitted browser CLI through Shell, reusing your current browser and login. It aims to keep browsing in the background while you use other apps. Setup, permissions and playback checks are covered in [browser access across harnesses](references/browser.md).

**1. Install** with the [skills CLI](https://github.com/vercel-labs/skills), with Node.js and Git available:

```bash
npx skills add ringozzt/toddle-skill -g -a codex
```

<details>
<summary>Install through your agent or clone it manually</summary>

Ask Codex:

```text
Install toddle-skill from https://github.com/ringozzt/toddle-skill
into my global skills directory.
```

Or run this on macOS / Linux:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
git clone https://github.com/ringozzt/toddle-skill.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/toddle-skill"
```

On Windows, the default Codex location is `%USERPROFILE%\.codex\skills\toddle-skill`. Check an existing installation before replacing it so you keep local edits. Browser sessions have been exercised in Codex and in dsh on macOS through a Shell browser CLI. Other harnesses can use native tools or a CLI with image reading; verify the selected route under its actual permissions.

</details>

**2. Open a new task and give it somewhere to wander:**

```text
Use $toddle-skill to browse my Bilibili homepage.
Pick videos that spark your curiosity, look into them, and follow what you find.
Keep going until I say stop.
```

Your agent starts with the page, actual video images and readable captions. When a video has speech without usable captions, it obtains the audio and transcribes it, then connects the spoken content with the frames. It handles the required tools; you can begin browsing without first assembling a video toolchain.

The same browsing loop can take more steps or tokens in some harnesses. The priority is completing it: choose a video, inspect it, follow the feed and save useful interest notes. If the environment cannot provide a permitted browser connection, the agent explains the blocker; supplied links and local media remain a partial fallback.

> [!NOTE]
> Long sessions can consume substantial model tokens. Set a video count or time limit whenever you want.

## Make it your kind of browsing

| You want to… | Try asking… |
|---|---|
| Browse Douyin | “Use toddle-skill to browse my Douyin feed. Tell me when something catches your attention.” |
| Explore Bilibili | “Pick a few videos from my homepage and follow the questions they raise.” |
| Open a YouTube video | “Watch this with toddle-skill: [video URL]. Show me the moments behind your conclusions.” |
| Find visual ideas | “Look for camera movement and editing ideas. Examine the useful sequences.” |
| Understand your recommendations | “What themes keep appearing in my feed? Keep uncertain guesses separate.” |
| Set a stopping point | “Browse for 10 minutes,” “Look at five videos,” or “Stop here and save the notes.” |

Without a limit, the agent keeps browsing in the current task until you stop it or the environment cannot continue. It saves progress if it reaches a blocker. A request about one video ends with that video's analysis. toddle does not create a background service or scheduled job on its own.

## What happens after the click

**The agent chooses what to explore.** It can follow a recommendation, return to the homepage, skip a weak lead or stay with a question. It shares useful discoveries and its next choice without turning every video into a report.

**It looks for evidence in the video.** Your agent connects timestamps, visible events and language before making a claim. When the browser leaves a gap, it can obtain accessible media, sample frames more closely or transcribe speech. It records how much it examined and reuses existing notes and media when you return.

**You can correct its picture of your interests.** Recommendations, your own actions and your explicit feedback remain separate kinds of evidence. The agent's clicks do not count as your preferences. Your corrections guide later choices through local notes; they do not retrain the underlying model or reveal the platform's internal profile. See the [interest-recording rules](references/interests.md).

## Media tools, when needed

The skill includes three Python helpers. You do not need separate video-analysis or transcription skills.

| Helper | Purpose |
|---|---|
| [`doctor.py`](scripts/doctor.py) | Find Python packages, browser/media CLIs on PATH and local models. An optional write check selects a permitted data directory. |
| [`sample_frames.py`](scripts/sample_frames.py) | Extract frames at their actual presentation times, with contact sheets and a JSON manifest. Sample a selected interval more densely. |
| [`audio_to_text.py`](scripts/audio_to_text.py) | Produce Markdown, SRT and source-linked JSON with faster-whisper or MLX Whisper. |

The agent uses [yt-dlp](https://github.com/yt-dlp/yt-dlp), [PyAV](https://github.com/PyAV-Org/PyAV), [Pillow](https://github.com/python-pillow/Pillow) and either [faster-whisper](https://github.com/SYSTRAN/faster-whisper) or [MLX Whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper). It reuses installed tools and cached models, adding missing components as needed. See [media setup and fallback paths](references/deeper.md) for commands and runtime configuration.

<details>
<summary>Do I need to download videos and install models first?</summary>

You can start with browser images and readable captions. Closer inspection may require downloading a video or audio track. Speech without usable captions needs transcription; local Whisper is the included fallback. The agent reserves this work for selected content rather than downloading every homepage card.

In restricted sessions, `audio_to_text.py --cache-root /absolute/workspace/path` keeps Hugging Face and auxiliary caches inside that directory. `--model-root` alone does not redirect every cache. See the [sandbox setup](references/deeper.md#writable-data-and-cache-directories).

The helpers need Python 3.10+ and their relevant packages. MLX Whisper runs on Apple Silicon and needs FFmpeg. A fresh large-v3-turbo model download is about 1.6 GB, so setup time depends on your machine and network. A text-only environment can work with supplied links or local media through available tools, but cannot operate a homepage feed without browser control.

</details>

## Your notes and your controls

The default data directory is `${XDG_DATA_HOME:-~/.local/share}/toddle-skill/`. In a workspace-only sandbox, the agent can use an ignored `work/toddle-skill/` directory, tell you once, and reuse it for the task. If no permitted location is writable, it keeps notes in the conversation and reports that they were not saved. The selected directory contains:

```text
history.jsonl   Viewing history, sources, coverage and observations
interests.json  Interest hypotheses, evidence and corrections
runtime.json    Optional paths to your local Python environments and models
```

Keep models, downloaded media and private notes out of version control. Workspace-local data must be ignored and untracked; ignoring an already committed file does not remove it from Git. This project does not automatically publish those files. Page text, images and transcripts used for analysis enter your AI provider's context and follow that product's data settings.

Browsing does not automatically like, tip, follow, comment, message or share with friends. On Douyin, “Copy link” in the share panel is used to record a source. Downloads depend on the video, login state, region and tool version.

Frame sampling shows only the sampled moments. Speech recognition can mishear words or invent text; unreliable output is excluded from conclusions. Music, voice quality, sound effects and rhythm require supported audio input. Interest notes describe content preferences, not sensitive identity, personality or health diagnoses.

## Inside the repository

```text
SKILL.md             Instructions your agent follows
agents/openai.yaml   Codex display metadata
scripts/             Environment checks, frame sampling and transcription
references/          Browser access, media setup and interest-recording guidance
tests/               Environment, cache and transcript-timestamp tests
assets/              README artwork
```

Development checks on Apple Silicon covered Bilibili media, two Douyin short links, existing YouTube subtitles, timestamped transcription and frame sampling, including variable frame rates, final-frame coverage and overwrite protection. These are sample checks, not coverage of every platform state or operating system.

The dsh test covered 20 Bilibili and 21 Douyin works using the user's signed-in Chrome, background frame sampling and local speech transcription. Coverage was sampled; uncertain speech remained explicit. Browser access and audio acquisition were tested under workspace-write permissions.

To run the environment, cache and transcript-timestamp tests without downloading models:

```bash
python3 -m unittest discover -s tests -v
```

Contributions are welcome through [issues](https://github.com/ringozzt/toddle-skill/issues) and pull requests. Include tool versions, a redacted error and a public input you have permission to share. Keep cookies, private viewing history, profiles and unapproved media out of reports. Match verification to the change; unchanged media tools do not need a fresh full evaluation.

[MIT License](LICENSE). External tools, models and video content retain their own licenses and usage terms.
