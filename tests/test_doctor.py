import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('doctor', Path(__file__).parents[1] / 'scripts/doctor.py')
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)


class DoctorTests(unittest.TestCase):
    def test_missing_environment_does_not_create_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'state'
            result = doctor.inspect(root, [str(root / 'missing-python')])
            self.assertFalse(root.exists())
            self.assertIsNone(result['mlx_model'])
            self.assertTrue(any(r['python'] == str(Path(sys.executable).absolute()) for r in result['runtimes']))

    def test_configured_venv_keeps_its_path_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable = root / 'venv/bin/python'
            executable.parent.mkdir(parents=True)
            executable.touch()
            (root / 'runtime.json').write_text(json.dumps({'python': [str(executable)]}))
            response = subprocess.CompletedProcess([], 0, '{"av":"test-version"}', '')
            with patch.object(doctor.subprocess, 'run', return_value=response) as run:
                result = doctor.inspect(root, [str(executable)])
            matching = [r for r in result['runtimes'] if r['python'] == str(executable)]
            self.assertEqual(len(matching), 1)
            self.assertEqual(matching[0]['packages']['av'], 'test-version')
            self.assertTrue(all(c.args[0][1] == '-I' for c in run.call_args_list))

    def test_bad_configuration_is_rejected_before_running_interpreters(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for config in ([], {'python': 'not-a-list'}, {'mlx_model': 4}):
                (root / 'runtime.json').write_text(json.dumps(config))
                with patch.object(doctor.subprocess, 'run') as run, self.assertRaises(ValueError):
                    doctor.inspect(root)
                run.assert_not_called()

    def test_timeout_and_invalid_probe_output_are_unavailable(self):
        for effect in (subprocess.TimeoutExpired('python', 10),
                       subprocess.CompletedProcess([], 0, 'not-json', '')):
            with tempfile.TemporaryDirectory() as temp:
                kwargs = {'side_effect': effect} if isinstance(effect, Exception) else {'return_value': effect}
                with patch.object(doctor.subprocess, 'run', **kwargs):
                    result = doctor.inspect(Path(temp))
                self.assertTrue(result['runtimes'])
                self.assertTrue(all(r['packages'] is None for r in result['runtimes']))

    def test_model_candidate_needs_config_and_weights(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            model = root / 'model'
            model.mkdir()
            (model / 'config.json').write_text('{}')
            with patch.object(doctor.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '{}', '')):
                self.assertIsNone(doctor.inspect(root, mlx_model=str(model))['mlx_model'])
                (model / 'weights.safetensors').touch()
                self.assertEqual(doctor.inspect(root, mlx_model=str(model))['mlx_model'], str(model.resolve()))


if __name__ == '__main__':
    unittest.main()
