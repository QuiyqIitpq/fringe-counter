"""Check that live pages and portable reports carry their own translations."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class BilingualPageTests(unittest.TestCase):
    def test_live_template_embeds_localization(self):
        page = app.page_template()
        self.assertIn('id="languageToggle"', page)
        self.assertIn('window.FringeI18n', page)
        self.assertNotIn('<script src="i18n.js">', page)
        self.assertEqual(page.count('<!--BOOTSTRAP-->'), 1)

    def test_offline_report_embeds_data_and_translations(self):
        data = {"folder": "/tmp/中文路径", "note": "</script><script>unexpected()</script>"}
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(app, 'report_data', return_value=data.copy()):
                app.save_html_report(folder)
            page = (Path(folder) / 'report.html').read_text(encoding='utf-8')
        self.assertIn('window.FringeI18n', page)
        self.assertNotIn('<script src=', page)
        self.assertNotIn('<!--BOOTSTRAP-->', page)
        self.assertNotIn('<script>unexpected()', page)
        payload = page.split('window.FIXED_REPORT=', 1)[1].split(';</script>', 1)[0]
        result = json.loads(payload)
        self.assertEqual(result['folder'], data['folder'])
        self.assertEqual(result['note'], data['note'])
        self.assertEqual(result['preview_url'], 'selected_regions.png')


if __name__ == '__main__':
    unittest.main()
