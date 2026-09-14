#!/usr/bin/env python3
"""Transcribe one local media file and preserve source and timestamps."""
import argparse
import importlib.metadata
import json
import math
import os
from pathlib import Path
import tempfile
import time


def timestamp(seconds, srt=False):
    value = round(seconds * 1000)
    hours, value = divmod(value, 3600000)
    minutes, value = divmod(value, 60000)
    seconds, millis = divmod(value, 1000)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}{"," if srt else "."}{millis:03d}'


def prepare_cache(root):
    root = root.expanduser().resolve()
    paths = {'XDG_CACHE_HOME': root, 'HF_HOME': root / 'huggingface',
             'HF_HUB_CACHE': root / 'huggingface/hub',
             'HF_XET_CACHE': root / 'huggingface/xet',
             'HF_ASSETS_CACHE': root / 'huggingface/assets'}
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=path) as probe:
            probe.write(b'toddle cache check')
            probe.flush()
    # Hugging Face reads environment variables at import time. Keep this before
    # either engine import, including Xet's auxiliary cache and logs.
    os.environ.update({key: str(path) for key, path in paths.items()})
    return str(root)


def bounded_segments(segments, duration):
    """Keep model text beyond decoded audio out of the usable transcript."""
    if duration is None or not math.isfinite(duration) or duration <= 0:
        raise ValueError('Decoded audio duration must be finite and positive')
    verified, unverified = [], []
    previous_start = -1.0
    for segment in segments:
        if not all(math.isfinite(segment[k]) for k in ['start', 'end']):
            raise ValueError('Non-finite timestamp returned by engine')
        if segment['start'] < 0 or segment['end'] < segment['start'] or segment['start'] < previous_start:
            raise ValueError('Invalid or out-of-order segment timestamps')
        previous_start = segment['start']
        if segment['end'] > duration:
            unverified.append({**segment, 'reason': 'outside_decoded_audio'})
        else:
            verified.append(segment)
    return verified, unverified


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--engine', choices=['faster-whisper', 'mlx-whisper'], default='faster-whisper')
    p.add_argument('--model', help='Engine model name/repository or local model directory')
    p.add_argument('--language', help='Language code; omitted means automatic detection')
    p.add_argument('--title', default='')
    p.add_argument('--source-url', default='')
    p.add_argument('--model-root', help='Optional faster-whisper download/cache directory')
    p.add_argument('--cache-root', type=Path,
                   help='Keep Hugging Face, Xet and XDG caches inside this directory for this process')
    args = p.parse_args()
    if not args.input.is_file():
        p.error('Input must be an existing local file')
    targets = [args.output_dir / f'transcript.{ext}' for ext in ['md', 'srt', 'json']]
    if any(x.exists() for x in targets):
        p.error('Transcript outputs already exist; choose a new output directory')
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=args.output_dir) as probe:
            probe.write(b'toddle output check')
            probe.flush()
        cache_root = prepare_cache(args.cache_root) if args.cache_root else None
    except OSError as exc:
        p.error(f'Output or cache directory is not writable: {exc}. Choose workspace-local paths.')
    started = time.perf_counter()
    if args.engine == 'faster-whisper':
        from faster_whisper import WhisperModel
        model_id = args.model or 'base'
        model = WhisperModel(model_id, device='cpu', compute_type='int8', cpu_threads=4,
                             download_root=args.model_root)
        iterator, info = model.transcribe(str(args.input), language=args.language,
                                         beam_size=5, vad_filter=True)
        segments = [{'start':s.start, 'end':s.end, 'text':s.text.strip()} for s in iterator]
        language, duration = info.language, info.duration
    else:
        import mlx_whisper
        from mlx_whisper.audio import SAMPLE_RATE, load_audio
        model_id = args.model or 'mlx-community/whisper-base-mlx'
        waveform = load_audio(str(args.input))
        duration = waveform.shape[0] / SAMPLE_RATE
        raw = mlx_whisper.transcribe(waveform, path_or_hf_repo=model_id,
                                    language=args.language, condition_on_previous_text=False,
                                    word_timestamps=False, verbose=None)
        segments = [{'start':s['start'], 'end':s['end'], 'text':s['text'].strip()}
                    for s in raw['segments']]
        language = raw.get('language')
    segments = [s for s in segments if s['text']]
    if not segments:
        raise RuntimeError('No speech text returned; no successful transcript was written')
    segments, unverified = bounded_segments(segments, duration)
    if not segments:
        raise RuntimeError('No speech segments within decoded audio; no successful transcript was written')
    meta = {'title': args.title or args.input.stem, 'source_url': args.source_url,
            'input_file': str(args.input.resolve()), 'source_type': 'local_asr',
            'engine': args.engine, 'engine_version': importlib.metadata.version(args.engine),
            'model': model_id, 'language': language, 'audio_duration_seconds': duration,
            'cache_root': cache_root,
            'unverified_segments': unverified,
            'last_segment_end_seconds': max(s['end'] for s in segments),
            'human_reviewed': False, 'elapsed_seconds': round(time.perf_counter()-started, 2)}
    title = ' '.join(meta['title'].splitlines())
    markdown = (f'# {title}\n\n来源：{args.source_url or args.input.name}\n\n'
                f'本地自动转写，未经人工校对。引擎：{args.engine}；模型：{model_id}。\n\n')
    if unverified:
        markdown += f'{len(unverified)} 段超出已解码音频范围，未纳入正文或 SRT；原始段落保留在 JSON 的 unverified_segments 中。\n\n'
    markdown += '\n\n'.join(f"**[{timestamp(s['start'])} – {timestamp(s['end'])}]**\n\n{s['text']}"
                            for s in segments)
    srt = '\n\n'.join(f"{i}\n{timestamp(s['start'],True)} --> {timestamp(s['end'],True)}\n{s['text']}"
                        for i,s in enumerate(segments,1))
    targets[0].write_text(markdown + '\n', encoding='utf-8')
    targets[1].write_text(srt + '\n', encoding='utf-8')
    targets[2].write_text(json.dumps({**meta, 'segments':segments}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status':'completed_with_unverified_segments' if unverified else 'completed',
                      'engine':args.engine, 'segments':len(segments), 'unverified_segments':len(unverified),
                      'elapsed_seconds':meta['elapsed_seconds'],
                      'outputs':[str(x.resolve()) for x in targets]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
