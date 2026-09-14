#!/usr/bin/env python3
"""Inspect existing video tools without installing packages or loading models."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PROBE = '''import importlib.util as u, importlib.metadata as m, json
result = {}
for module, dist in [('yt_dlp','yt-dlp'),('av','av'),('PIL','Pillow'),('faster_whisper','faster-whisper'),('mlx_whisper','mlx-whisper')]:
 try: result[module] = m.version(dist) if u.find_spec(module) else None
 except (ImportError, m.PackageNotFoundError): result[module] = None
print(json.dumps(result))'''


def writable_root(root, fallback_root=None):
    failures = []
    candidates = [root]
    if fallback_root is not None:
        candidates.append(Path(fallback_root).expanduser().resolve())
    for candidate in dict.fromkeys(candidates):
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryFile(dir=candidate) as probe:
                probe.write(b'toddle write check')
                probe.flush()
            return candidate, failures
        except OSError as exc:
            failures.append({'path': str(candidate), 'error': type(exc).__name__,
                             'errno': exc.errno})
    raise OSError('No writable data directory: ' +
                  '; '.join(f"{f['path']} ({f['error']}, errno {f['errno']})" for f in failures))


def inspect(root, python_paths=(), mlx_model=None, config_path=None, *,
            check_write=False, fallback_root=None):
    root = Path(root).expanduser().resolve()
    requested_root = root
    failures = []
    if fallback_root is not None and not check_write:
        raise ValueError('--fallback-root requires --check-write')
    if check_write:
        root, failures = writable_root(root, fallback_root)
    config_path = Path(config_path).expanduser() if config_path else root / 'runtime.json'
    config = json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}
    if not isinstance(config, dict):
        raise ValueError('runtime.json must contain an object')
    configured = config.get('python', [])
    if not isinstance(configured, list) or not all(isinstance(p, str) and p for p in configured):
        raise ValueError('runtime.json python must be a list of interpreter paths')
    selected_model = mlx_model or config.get('mlx_model')
    if selected_model is not None and not isinstance(selected_model, str):
        raise ValueError('mlx_model must be a directory path')
    managed = root / 'runtime' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    candidates = [sys.executable, str(managed), *configured, *python_paths]
    # Resolving interpreter symlinks would lose the virtual environment.
    candidates = list(dict.fromkeys(str(Path(p).expanduser().absolute()) for p in candidates))
    runtimes = []
    for executable in candidates:
        if not Path(executable).is_file():
            continue
        try:
            result = subprocess.run([executable, '-I', '-c', PROBE], capture_output=True,
                                    text=True, timeout=10)
            packages = json.loads(result.stdout) if result.returncode == 0 else None
            if not isinstance(packages, dict):
                packages = None
            runtimes.append({'python': executable, 'packages': packages})
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
            runtimes.append({'python': executable, 'packages': None})
    model = Path(selected_model).expanduser() if selected_model else None
    ready = model and (model / 'config.json').is_file() and any(model.glob('*.safetensors'))
    return {'state_root': str(root), 'runtimes': runtimes,
            'storage': {'requested_root': str(requested_root),
                        'write_checked': check_write,
                        'fallback_used': root != requested_root,
                        'failed_candidates': failures},
            'commands': {name: shutil.which(name) for name in
                         ('yt-dlp', 'ffmpeg', 'ffprobe', 'agent-browser', 'playwright-cli', 'browser-use', 'node', 'npm')},
            'ffmpeg': shutil.which('ffmpeg'), 'ffprobe': shutil.which('ffprobe'),
            'mlx_model': str(model.resolve()) if ready else None,
            'audio_understanding': 'ASR availability does not establish music, timbre or sound-effect understanding.',
            'note': 'PATH presence is not a successful browser launch. Check native tools or use a permitted browser CLI; see references/browser.md. No installs, model loads, network calls or browser permissions. Writes occur only with --check-write.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path,
                        default=Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'toddle-skill')
    parser.add_argument('--python', action='append', default=[], help='Existing trusted Python interpreter; repeatable')
    parser.add_argument('--mlx-model', help='Existing MLX model directory')
    parser.add_argument('--config', type=Path, help='Local runtime.json (defaults to <root>/runtime.json)')
    parser.add_argument('--check-write', action='store_true',
                        help='Create the data directory if needed and test writing a temporary file')
    parser.add_argument('--fallback-root', type=Path,
                        help='Explicit alternate data directory if the write check fails; requires --check-write')
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.root, args.python, args.mlx_model, args.config,
                                 check_write=args.check_write, fallback_root=args.fallback_root),
                         ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(2, f'{type(exc).__name__}: {exc}\n')


if __name__ == '__main__':
    main()
