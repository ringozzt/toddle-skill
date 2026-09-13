#!/usr/bin/env python3
"""Inspect existing video tools without installing packages or loading models."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PROBE = '''import importlib.util as u, importlib.metadata as m, json
result = {}
for module, dist in [('yt_dlp','yt-dlp'),('av','av'),('PIL','Pillow'),('faster_whisper','faster-whisper'),('mlx_whisper','mlx-whisper')]:
 try: result[module] = m.version(dist) if u.find_spec(module) else None
 except (ImportError, m.PackageNotFoundError): result[module] = None
print(json.dumps(result))'''


def inspect(root, python_paths=(), mlx_model=None, config_path=None):
    root = Path(root).expanduser().resolve()
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
            'ffmpeg': shutil.which('ffmpeg'), 'ffprobe': shutil.which('ffprobe'),
            'mlx_model': str(model.resolve()) if ready else None,
            'audio_understanding': 'ASR availability does not establish music, timbre or sound-effect understanding.',
            'note': 'Package/file detection only; no installs, model loads, network calls or browser permissions. See references/deeper.md.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path,
                        default=Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'toddle-skill')
    parser.add_argument('--python', action='append', default=[], help='Existing trusted Python interpreter; repeatable')
    parser.add_argument('--mlx-model', help='Existing MLX model directory')
    parser.add_argument('--config', type=Path, help='Local runtime.json (defaults to <root>/runtime.json)')
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.root, args.python, args.mlx_model, args.config), ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(2, f'{type(exc).__name__}: cannot read runtime configuration; check its path and format.\n')


if __name__ == '__main__':
    main()
