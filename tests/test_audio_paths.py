import builtins
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('audio_to_text', Path(__file__).parents[1] / 'scripts/audio_to_text.py')
audio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio)


class AudioPathTests(unittest.TestCase):
    def test_workspace_caches_are_set_before_engine_import(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            source = root / 'input.wav'
            source.touch()
            output = root / 'transcript'
            cache = root / 'cache'
            expected = {'XDG_CACHE_HOME': str(cache), 'HF_HOME': str(cache / 'huggingface'),
                        'HF_HUB_CACHE': str(cache / 'huggingface/hub'),
                        'HF_XET_CACHE': str(cache / 'huggingface/xet'),
                        'HF_ASSETS_CACHE': str(cache / 'huggingface/assets')}
            imports = []
            original_import = builtins.__import__

            class Model:
                def __init__(self, *args, **kwargs):
                    pass

                def transcribe(self, *args, **kwargs):
                    return iter([types.SimpleNamespace(start=0.0, end=1.0, text='test speech')]), \
                           types.SimpleNamespace(language='en', duration=1.0)

            def engine_import(name, *args, **kwargs):
                if name == 'faster_whisper':
                    imports.append({key: os.environ.get(key) for key in expected})
                    return types.SimpleNamespace(WhisperModel=Model)
                return original_import(name, *args, **kwargs)

            argv = ['audio_to_text.py', str(source), '--output-dir', str(output),
                    '--cache-root', str(cache)]
            with patch.dict(os.environ, {key: '/outside-workspace' for key in expected}), \
                 patch.object(sys, 'argv', argv), \
                 patch.object(builtins, '__import__', side_effect=engine_import), \
                 patch.object(audio.importlib.metadata, 'version', return_value='test'), \
                 contextlib.redirect_stdout(io.StringIO()):
                audio.main()
            self.assertEqual(imports, [expected])
            self.assertTrue(all(Path(p).is_dir() for p in expected.values()))
            result = json.loads((output / 'transcript.json').read_text())
            self.assertEqual(result['cache_root'], str(cache))
            self.assertEqual(len(result['segments']), 1)

    def test_denied_cache_fails_before_engine_import(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'input.wav'
            source.touch()
            original = audio.tempfile.TemporaryFile

            def denied_cache(*args, **kwargs):
                if Path(kwargs['dir']).name == 'cache':
                    raise PermissionError(1, 'Operation not permitted')
                return original(*args, **kwargs)

            argv = ['audio_to_text.py', str(source), '--output-dir', str(root / 'out'),
                    '--cache-root', str(root / 'cache')]
            errors = io.StringIO()
            with patch.object(sys, 'argv', argv), \
                 patch.object(audio.tempfile, 'TemporaryFile', side_effect=denied_cache), \
                 patch.object(builtins, '__import__', wraps=builtins.__import__) as imports, \
                 contextlib.redirect_stderr(errors), self.assertRaises(SystemExit) as stopped:
                audio.main()
            self.assertEqual(stopped.exception.code, 2)
            self.assertIn('workspace-local paths', errors.getvalue())
            self.assertFalse(any(c.args[0] in ('faster_whisper', 'mlx_whisper') for c in imports.call_args_list))
            self.assertFalse((root / 'out/transcript.json').exists())

    def test_unwritable_output_fails_before_cache_or_model_setup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'input.wav'
            source.touch()
            output = root / 'not-a-directory'
            output.write_text('keep this file')
            argv = ['audio_to_text.py', str(source), '--output-dir', str(output),
                    '--cache-root', str(root / 'unused-cache')]
            with patch.object(sys, 'argv', argv), patch.object(audio, 'prepare_cache') as cache, \
                 contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as stopped:
                audio.main()
            self.assertEqual(stopped.exception.code, 2)
            cache.assert_not_called()
            self.assertEqual(output.read_text(), 'keep this file')


if __name__ == '__main__':
    unittest.main()
