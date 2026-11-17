import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from lxml import etree
from test_converter import XML
from converter import NS_ANALYTICAL

SCRIPT = Path(__file__).resolve().parents[1] / 'konvi.py'

class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True)

    def test_paths_with_spaces_default_output_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'reki (3).xml'
            source.write_text(XML, encoding='utf-8')
            result = self.run_cli(source)
            self.assertEqual(result.returncode, 0, result.stderr)
            output = source.with_name('reki (3)_REK_O.xml')
            root = etree.fromstring(output.read_bytes())
            self.assertEqual(root.findtext(f'.//{{{NS_ANALYTICAL}}}A086O'), '7.72')
            self.assertIsNone(root.find(f'.//{{{NS_ANALYTICAL}}}A086P'))
            previous = output.read_bytes()
            self.assertEqual(self.run_cli(source).returncode, 1)
            self.assertEqual(output.read_bytes(), previous)
            self.assertEqual(source.read_text(encoding='utf-8'), XML)

    def test_custom_output_same_path_and_invalid_input(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'vhod.xml'
            output = Path(folder) / 'izhod.xml'
            source.write_text(XML, encoding='utf-8')
            self.assertEqual(self.run_cli(source, source).returncode, 1)
            self.assertEqual(self.run_cli(source, output).returncode, 0)
            source.write_text('<bad', encoding='utf-8')
            bad_output = Path(folder) / 'bad.xml'
            self.assertEqual(self.run_cli(source, bad_output).returncode, 1)
            self.assertFalse(bad_output.exists())
            self.assertEqual(self.run_cli(Path(folder) / 'missing.xml').returncode, 1)

    def test_help_and_missing_arguments(self):
        self.assertEqual(self.run_cli('--help').returncode, 0)
        self.assertEqual(self.run_cli().returncode, 2)
