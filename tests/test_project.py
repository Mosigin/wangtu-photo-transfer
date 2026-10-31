import json
from pathlib import Path
import plistlib
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ProjectTests(unittest.TestCase):
    def test_source_catalogs_have_both_languages(self):
        for name in ['Localizable', 'InfoPlist']:
            catalog = json.loads((ROOT / 'ios' / (name + '.xcstrings')).read_text(encoding='utf-8'))
            for key, entry in catalog['strings'].items():
                values = [entry['localizations'][language]['stringUnit']['value'] for language in ['zh-Hans', 'en']]
                self.assertTrue(all(values), key)
                self.assertEqual(values[0].count('%@'), values[1].count('%@'), key)

    def test_project_is_self_contained_and_has_icon(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)/'project'
            subprocess.run([sys.executable, str(ROOT/'tools/build.py'), '--platform', 'simulator', '--output', str(out)], check=True, stdout=subprocess.DEVNULL)
            project = plistlib.loads((out/'WangtuPhotoTransfer.xcodeproj/project.pbxproj').read_bytes())
            self.assertEqual(project['objects']['000000000000000000000017']['buildSettings']['PRODUCT_BUNDLE_IDENTIFIER'], 'io.github.mosigin.wangtu-photo-transfer')
            self.assertTrue((out/'Assets.xcassets/AppIcon.appiconset/AppIcon.png').is_file())
            for language in ['en','zh-Hans']:
                self.assertTrue((out/'Resources'/f'{language}.lproj/Localizable.strings').is_file())
                self.assertTrue((out/'Resources'/f'{language}.lproj/InfoPlist.strings').is_file())
            self.assertFalse((out/'DerivedData').exists())

    def test_no_device_or_personal_signing_defaults(self):
        build = (ROOT/'tools/build.py').read_text(encoding='utf-8')
        sender = (ROOT/'tools/transfer.py').read_text(encoding='utf-8')
        self.assertIn("parser.add_argument('--team',", build)
        self.assertNotRegex(build, r"--team'.*default=")
        self.assertIn("parser.add_argument('--device', help=", sender)
        self.assertNotRegex(sender, r"--device'.*default=")

    def test_no_photos_deletion_api(self):
        app = (ROOT/'ios/WangtuPhotoTransfer.swift').read_text(encoding='utf-8')
        self.assertNotIn('deleteAssets', app)
        self.assertIn('isNetworkAccessAllowed = false', app)
        self.assertIn('ImportPolicy.idleState(state)', app)

    def test_png_icon_is_1024_square(self):
        data=(ROOT/'assets/logo.png').read_bytes()
        self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
        self.assertEqual(int.from_bytes(data[16:20],'big'),1024)
        self.assertEqual(int.from_bytes(data[20:24],'big'),1024)
        self.assertEqual(data,(ROOT/'ios/Assets.xcassets/AppIcon.appiconset/AppIcon.png').read_bytes())

    def test_document_local_links_exist(self):
        for document in ROOT.rglob('*.md'):
            for value in re.findall(r'\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
                if '://' in value or value.startswith('#'):continue
                path=value.split('#')[0]
                if path:self.assertTrue((document.parent/path).exists(),f'{document.name}: {value}')


if __name__=='__main__':unittest.main()
