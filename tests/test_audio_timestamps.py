import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('audio_to_text', Path(__file__).parents[1] / 'scripts/audio_to_text.py')
audio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio)


class AudioTimestampTests(unittest.TestCase):
    def run_engine(self, engine, segments, duration=45):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        source = root / 'input.wav'
        source.touch()
        output = root / 'out'
        waveform = types.SimpleNamespace(shape=(int(duration * 16000),))
        mlx = types.ModuleType('mlx_whisper')
        mlx.transcribe = Mock(return_value={'language': 'en', 'segments': segments})
        mlx_audio = types.ModuleType('mlx_whisper.audio')
        mlx_audio.SAMPLE_RATE = 16000
        mlx_audio.load_audio = Mock(return_value=waveform)
        faster = types.ModuleType('faster_whisper')
        model = Mock()
        model.transcribe.return_value = (
            iter(types.SimpleNamespace(**s) for s in segments),
            types.SimpleNamespace(language='en', duration=duration))
        faster.WhisperModel = Mock(return_value=model)
        modules = {'mlx_whisper': mlx, 'mlx_whisper.audio': mlx_audio, 'faster_whisper': faster}
        argv = ['audio_to_text.py', str(source), '--output-dir', str(output), '--engine', engine]
        with patch.dict(sys.modules, modules), patch.object(sys, 'argv', argv), \
             patch.object(audio.importlib.metadata, 'version', return_value='test'), \
             contextlib.redirect_stdout(io.StringIO()):
            audio.main()
        return output, mlx, waveform

    def test_mlx_measures_decoded_waveform_and_excludes_padded_tail(self):
        output, mlx, waveform = self.run_engine('mlx-whisper', [
            {'start': 0.0, 'end': 11.36, 'text': 'Actual speech'},
            {'start': 30.0, 'end': 59.98, 'text': 'Unverified credit'},
        ])
        result = json.loads((output / 'transcript.json').read_text())
        self.assertIs(mlx.transcribe.call_args.args[0], waveform)
        self.assertEqual(result['audio_duration_seconds'], 45)
        self.assertEqual(result['last_segment_end_seconds'], 11.36)
        self.assertEqual(len(result['segments']), 1)
        self.assertEqual(result['unverified_segments'][0]['end'], 59.98)
        self.assertNotIn('Unverified credit', (output / 'transcript.md').read_text())
        self.assertNotIn('Unverified credit', (output / 'transcript.srt').read_text())

    def test_faster_whisper_also_checks_actual_duration(self):
        output, _, _ = self.run_engine('faster-whisper', [
            {'start': 0.0, 'end': 1.0, 'text': 'Actual speech'},
            {'start': 39.36, 'end': 52.8, 'text': 'Unverified ending'},
        ])
        result = json.loads((output / 'transcript.json').read_text())
        self.assertEqual(len(result['segments']), 1)
        self.assertEqual(result['unverified_segments'][0]['reason'], 'outside_decoded_audio')

    def test_only_out_of_range_text_is_not_successful_speech(self):
        with self.assertRaisesRegex(RuntimeError, 'No speech segments within'):
            self.run_engine('mlx-whisper', [
                {'start': 30.0, 'end': 59.98, 'text': 'Unverified credit'},
            ])


if __name__ == '__main__':
    unittest.main()
