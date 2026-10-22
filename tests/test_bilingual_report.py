"""Translation assets must remain available in a portable report."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import standalone


class TestBilingualReport(unittest.TestCase):
    def test_report_contains_translations_without_external_scripts(self):
        data={'note':'</script><script>unexpected()</script>', 'path':'/tmp/中文视频.avi'}
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'report.html'
            standalone(data,target)
            html=target.read_text()
        self.assertIn('id="languageToggle"',html)
        self.assertIn('window.FringeI18n',html)
        self.assertNotIn('<script src=',html)
        self.assertNotIn('<link rel="stylesheet"',html)
        self.assertNotIn('<script>unexpected()',html)
        payload=html.split('window.FIXED_REPORT=',1)[1].split(';</script>',1)[0]
        self.assertEqual(json.loads(payload),data)


if __name__=='__main__':unittest.main()
