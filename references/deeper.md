# Use media tools when closer inspection is needed

Ordinary browsing starts with browser control, page reading and screenshots. Use the capabilities below as needed, not as prerequisites for opening the feed.

For a video with speech, checking language is part of ordinary watching. Read reliable captions covering the observed interval; when captions are absent or insufficient, use the audio route below. A silent screenshot does not establish that the video has no narration. Preserve the transcript's source interval and align it with frames before drawing conclusions. Record an unavailable speech track explicitly instead of reporting visual sampling as complete audiovisual understanding.

Run this skill's `scripts/doctor.py` when a tooling check is needed. By default it only reads the current Python interpreter, the managed runtime, explicitly configured Python environments, PATH commands and local model candidates. `commands["yt-dlp"]` reports the standalone executable separately from `runtimes[*].packages.yt_dlp`; a missing module does not mean the PATH command is missing. Use that executable directly if appropriate. Detection runs package queries through trusted interpreters, without installing packages, loading models, accessing the network or reading cookies. It cannot establish whether the agent has browser-control tools.

## Writable data and cache directories

Choose the data root described in `SKILL.md` before writing records or preparing media tools. In a known workspace-only sandbox, use an ignored directory such as `$PWD/work/toddle-skill` directly. Otherwise, this optional check tests the normal root and an explicit fallback:

```bash
python3 "$SKILL/scripts/doctor.py" --check-write \
  --fallback-root "$PWD/work/toddle-skill"
```

`$SKILL` is the installed skill directory. Unlike the default read-only mode, `--check-write` creates candidate directories if needed and writes a temporary probe file, which it removes. The JSON `state_root` is the chosen writable directory; `storage` records whether a fallback was used and which probes failed. Both paths failing produces a nonzero exit. Set `TODDLE_DATA` to that returned path for subsequent commands. When resuming a known local root, pass `--root "$TODDLE_DATA" --check-write`. An explicitly requested user path should not be changed without agreement; omit the fallback in that case.

Keep `history.jsonl`, `interests.json`, `runtime.json`, notes and media under the chosen root. A successful probe does not guarantee that an existing individual file is writable: check each save and report failures. Do not use `mkdir -p` or `os.access` alone as proof of sandbox write permission, or let `tail`, `echo`, or a pipeline hide a failed command's exit status. Use `&&` or propagate the original status, then check expected outputs. Verify that workspace-local private files are ignored and untracked; `.gitignore` does not protect files already committed or force-added.

For ASR in a restricted workspace, pass `--cache-root "$TODDLE_DATA/cache"` to `audio_to_text.py`. It checks the output/cache paths before loading an engine and sets `XDG_CACHE_HOME`, `HF_HOME`, `HF_HUB_CACHE`, `HF_XET_CACHE` and `HF_ASSETS_CACHE` inside that root before either engine imports. This applies only to the helper process. Without the flag, existing cache settings are preserved. `--model-root` controls faster-whisper's model location but does not redirect every auxiliary cache or Xet log.

For other Python processes that access Hugging Face, set the equivalent environment before launch, using absolute paths:

```bash
export XDG_CACHE_HOME="$TODDLE_DATA/cache"
export HF_HOME="$XDG_CACHE_HOME/huggingface"
export HF_HUB_CACHE="$HF_HOME/hub"
export HF_XET_CACHE="$HF_HOME/xet"
export HF_ASSETS_CACHE="$HF_HOME/assets"
```

These are task-local settings, not edits to shell startup files. Reuse a readable cached model through `--model /path/to/model` when available. Hugging Face reads these variables at import time; see its [environment-variable reference](https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables). If installing dependencies also needs a writable cache, use a task-local `PIP_CACHE_DIR` or `npm_config_cache` within the same permitted root. This does not grant missing browser tools or additional execution permissions.

## Existing media capabilities

Reused capabilities and historical validation, 2026-09-13–14:

- `scripts/sample_frames.py` comes from video-analyze. It supports frame sampling, dense local sampling, actual presentation timestamps (PTS), contact sheets, variable frame rates and final-frame coverage. Open the resulting images before claiming visual observation.
- `scripts/audio_to_text.py` comes from video-transcribe. It uses local faster-whisper or MLX Whisper and preserves timestamps and sources. Prefer captions, use audio as a fallback, and retain the original transcript separately.
- Sample checks passed on Apple Silicon with yt-dlp 2026.08.19, PyAV/Pillow and local faster-whisper / MLX Whisper. These historical results do not establish compatibility with other environments; inspect the current setup before use.
- Bilibili media, two Douyin short-link downloads and existing YouTube captions were tested. Other videos, regions, login states and machines may differ. A signed-in Chrome session does not guarantee that command-line tools can decrypt its cookies; public audio may still be accessible.

If a component is missing, continue with available browser frames and visible captions and state the coverage. Install missing components in an isolated virtual environment only when the current question needs them. Do not reinstall the full MediaBrief/BiliNote applications or redownload cached models. A first large-v3-turbo download is about 1.6 GB; prepare it only when needed and no suitable cached model exists.

When aligning frames and text, check that they come from the same video version and share the same starting point. Cropping or different intros can offset video PTS and ASR timestamps. Label human captions, platform auto-captions, visible subtitles and local ASR separately. Descriptions, comments and on-screen viewer messages are not speech transcripts. Discard garbled or apparently hallucinated output and record the uncertainty.

If ASR returns only lyric-like or incoherent text, mark speech as uncertain. That result cannot establish the absence of narration, confirm singing or identify a soundtrack. Keep those limits when updating interest notes.

The transcription helper checks segment times against decoded audio duration. Segments extending beyond it are retained in JSON as `unverified_segments` and excluded from the usable Markdown/SRT text; they are not silently clamped to the clip boundary. A run with retained uncertainty reports `completed_with_unverified_segments`. If no in-range speech remains, the helper fails instead of reporting a successful transcript. Review uncertain words even when every timestamp is valid.

The audio-input tool used in prior local testing returned an unsupported-input result, so music, voice quality, effects and rhythm were not reliably heard. Report sound only when the current tool supports and successfully receives audio. First determine whether that route uploads audio, incurs charges or downloads a model, and follow the user's authorization. An installed ASR package is not proof of broader audio understanding.

To reuse existing environments, pass `--python /path/to/venv/bin/python`; repeat it for separate module environments. Supply a local MLX model with `--mlx-model /path/to/model`. Alternatively, save a private `runtime.json` in the data directory containing `{"python": ["/path/to/venv/bin/python"], "mlx_model": "/path/to/model"}`. Use actual local paths; the model field is optional. Do not commit this machine-specific configuration.

## Minimal setup without an existing environment

The agent performs these steps when needed; users do not have to configure the toolchain before browsing. The helpers require Python 3.10+. `TODDLE_DATA` below does not replace the system's HOME variable. Inspect doctor output first and reuse a suitable interpreter instead of installing again. If no suitable Python exists, use an available trusted package manager or uv to prepare Python 3.12. Explain concrete platform or network blockers.

```bash
# TODDLE_DATA is the writable root already chosen for this task.
python3 -m venv "$TODDLE_DATA/runtime"
"$TODDLE_DATA/runtime/bin/python" -m pip install yt-dlp av Pillow
```

On Windows, use the virtual environment's `Scripts/python.exe`. Do not recreate an existing runtime. Add `faster-whisper` only when speech transcription is needed; on Apple Silicon, reuse an existing mlx-whisper installation and model. The bundled helper defaults to `base` on CPU with int8 when using faster-whisper, with a model download on first use. It can misrecognize speech, so check names and key statements; prefer a better cached model when available. If installation fails, retain the specific error and return to usable frames or captions rather than retrying indefinitely.

## Essential commands

`$PY` is a suitable interpreter, `$SKILL` is this skill's directory, `$URL` is a verified public video URL, and `$OUT` is a new output directory for that video. Different modules may use different existing interpreters. Use fixed filenames or video IDs; do not interpolate third-party prose into shell commands.

```bash
"$PY" -m yt_dlp --ignore-config --no-playlist --socket-timeout 20 --retries 1 --skip-download --list-subs "$URL"
"$PY" -m yt_dlp --ignore-config --no-playlist --socket-timeout 20 --retries 1 -f 'bv*[height<=720]/b[height<=720]/bv*/best' -o "$OUT/source.%(ext)s" "$URL"
"$PY" "$SKILL/scripts/sample_frames.py" "$OUT/source.mp4" --output-dir "$OUT/frames"
```

Replace `source.mp4` with the actual downloaded extension. This downloads a single stream containing video, which may omit audio; frame extraction does not require merging first. Obtain audio separately when speech matters. Merge audio and video if a complete playable file is needed and FFmpeg is available. The default sampling cap is 72 frames; an overview of a long video is not a full watch. Open original frames if captions are too small. For fast action, sample a specific interval more densely, for example `--start 6.8 --end 8.8 --interval 0.1`.

When platform captions exist, select the actual language track with `--skip-download --write-subs --write-auto-subs --sub-langs 'actual-language-code'`. Exclude Bilibili danmaku. Obtain audio only when usable captions are unavailable:

```bash
"$PY" -m yt_dlp --ignore-config --no-playlist --socket-timeout 20 --retries 1 -f 'bestaudio/best' -o "$OUT/audio.%(ext)s" "$URL"
"$PY" "$SKILL/scripts/audio_to_text.py" "$OUT/audio.m4a" --output-dir "$OUT/transcript" --source-url "$URL" --cache-root "$TODDLE_DATA/cache"
```

Replace `audio.m4a` with the actual audio extension. For MLX, use `--engine mlx-whisper --model '/path/to/cached/model'`; FFmpeg is required. faster-whisper also accepts a local model directory to avoid another download. Do not force transcription of music or audio without reliable speech.

## When platform downloads fail

Treat failures as observations about a particular request, tool version and environment. Metadata access does not prove media access. Record the HTTP status and stage, avoid printing signed media URLs, cookies or tokens, and choose at most one evidence-based alternative after a failure.

For audio extraction, compare the formats already returned for that work. Two bitrates can use the same failing CDN route while another format uses a different host or port. Choose the alternative using the observed failure and returned URLs; do not guess or rewrite CDN hostnames. A lower-bitrate track may be sufficient for speech transcription. Verify decoded audio and the resulting text instead of always maximizing bitrate, or claiming all formats failed after testing only two. Keep failed partial files separate from the next attempt and retain the source interval.

- **Bilibili HTTP 412:** A sandboxed session returned 412 while earlier anonymous public-video checks succeeded. The status alone does not establish the cause or prove that every video requires cookies. Use an available authorized browser session, supplied local media, or report the acquisition blocker. Browser sign-in does not guarantee command-line access; do not export credentials as a routine workaround.
- **YouTube HTTP 403:** Check the installed yt-dlp version and the reported client/format failure. In one local session, `--extractor-args "youtube:player_client=android"` succeeded for short clips after default requests failed. This is a conditional alternative, not a default or guaranteed fix. Client and PO-token requirements change; consult the [yt-dlp YouTube guidance](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#youtube) before choosing a route.
- **Only a segment is needed:** `--download-sections` reduces the requested scope and needs FFmpeg. It does not remove authorization or rate limits, and a successful segment does not establish that the whole video can be downloaded. For a selected, accessible interval:

```bash
"$PY" -m yt_dlp --ignore-config --no-playlist --socket-timeout 20 --retries 1 \
  --download-sections '*100-170' -f 'bv*[height<=720]/b[height<=720]/bv*/best' \
  -o "$OUT/clip.%(ext)s" "$URL"
```

Record the source interval and offset when downloading or trimming a clip. Frame and ASR times usually start from the local clip; add the verified offset when citing the original video, and check alignment against an actual frame. For example, clip time `00:06.7` from an audio segment starting at 100 seconds corresponds to source time `01:46.7`.

- **Captions HTTP 429:** Stop repeated caption requests. Respect a provided retry delay, use already acquired media for local ASR if suitable, or report that captions are unavailable. Do not describe rate limiting as an absence of speech or captions.

## Tool selection rationale, reviewed 2026-09-14

Keep [yt-dlp](https://github.com/yt-dlp/yt-dlp), PyAV/Pillow and local Whisper as the default. The downloader obtains media, the agent interprets frames, and Whisper supplies speech text. Discover homepage content through the actual browser page. Replace a component when evidence shows it makes the current task easier, not because it has more stars.

The following observations describe the source and project documentation reviewed on that date:

- [F2](https://github.com/Johnserf-Seed/f2/blob/main/f2/apps/douyin/dl.py) supports Douyin downloads, but its downloader initialization required cookies. It had not been shown to simplify the working anonymous path, so it remained an alternative rather than a default dependency.
- [DouK-Downloader](https://github.com/JoeanAmier/TikTokDownloader) supports Douyin/TikTok downloads. Its README stated that the encrypted-parameter algorithm was no longer maintained, and initialization required cookie configuration. It could not support a promise of configuration-free startup.
- The default repository pages for [bilibili-api](https://github.com/Nemo2011/bilibili-api) and [BBDown](https://github.com/nilaoda/BBDown) indicated archival or discontinued maintenance at review time, so they were not added as core dependencies. Old branch READMEs may remain accessible; check the current repository state when reconsidering them.

These alternatives were inspected through source and documentation, not installed or individually tested. Reuse the working, sample-validated toolchain without repeating the earlier six-tool comparison unless new evidence warrants it.
