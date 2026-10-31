import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import transfer
from media_plan import candidates, select_batch, RESERVE, OVERHEAD


def entry(identity, size, live=False, video=False):
    return {'id': identity, 'resources': [{'bytes': size, 'kind': 'video' if video else 'photo'}]
            + ([{'bytes': size, 'kind': 'pairedVideo'}] if live else [])}


class PlanningTests(unittest.TestCase):
    def test_reserve_boundary(self):
        for free in [0, -1, RESERVE, RESERVE + OVERHEAD]:
            self.assertEqual(select_batch([entry('a', 1)], {}, free), [])

    def test_large_video_can_travel_alone(self):
        video = entry('movie', 2_000_000_000, video=True)
        self.assertEqual(select_batch([video], {}, 8_000_000_000), [video])

    def test_large_video_must_fit_double_copy_budget(self):
        self.assertEqual(select_batch([entry('movie', 2_000_000_000, video=True)], {}, 4_000_000_000), [])

    def test_large_blocked_item_does_not_block_small_item(self):
        rows = [entry('large', 100), entry('small', 3)]
        self.assertEqual(select_batch(rows, {}, RESERVE + OVERHEAD + 10), [rows[1]])

    def test_live_pair_is_indivisible(self):
        self.assertEqual(select_batch([entry('live', 8, True)], {}, RESERVE + OVERHEAD + 30), [])

    def test_completed_and_failed_not_repeated(self):
        for state in ['verified', 'failed']:
            self.assertEqual(select_batch([entry('a', 5)], {'a': state}, 2_000_000_000), [])

    def test_batch_count_limit(self):
        self.assertEqual(len(select_batch([entry(str(i), 1) for i in range(100)], {}, 2_000_000_000)), 20)

    def test_custom_reserve(self):
        self.assertEqual(select_batch([entry('a', 1)], {}, 3_000_000_000, reserve=3_000_000_000), [])

    def test_nested_same_name_keeps_separate_id_and_filename(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for relative in ['one/image.jpg', 'two/image.jpg', '影片.mp4']:
                path = root / relative; path.parent.mkdir(exist_ok=True); path.write_bytes(b'fixture')
            rows = candidates(root)
            self.assertEqual(len(rows), 3)
            self.assertEqual(len({r['id'] for r in rows}), 3)
            files = [r['resources'][0] for r in rows]
            self.assertEqual(len({r['file'] for r in files}), 3)
            self.assertEqual(sum(r['originalFilename'] == 'image.jpg' for r in files), 2)

    def test_no_automatic_live_guess_and_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ['A.heic', 'A.mov', 'A.aae', '.hidden.jpg']:
                (root / name).write_bytes(b'fixture')
            self.assertEqual(len(candidates(root)), 2)
            self.assertTrue(all(len(e['resources']) == 1 for e in candidates(root)))
            self.assertEqual(len(candidates(root, media='photos')), 1)
            self.assertEqual(len(candidates(root, media='videos')), 1)

    def test_explicit_live_pair(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ['A.heic', 'A.mov']: (root / name).write_bytes(b'fixture')
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'schema': 1, 'entries': [{'photo': 'A.heic', 'pairedVideo': 'A.mov'}]}))
            rows = candidates(root, manifest, 'photos')
            self.assertEqual(len(rows), 1); self.assertEqual(len(rows[0]['resources']), 2)

    def test_path_escape_and_invalid_roles_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); manifest = root / 'manifest.json'
            for item in [{'photo': '../other.jpg'}, {'pairedVideo': 'A.mov'},
                         {'video': 'A.mov', 'photo': 'A.jpg'}]:
                manifest.write_text(json.dumps({'schema': 1, 'entries': [item]}))
                with self.assertRaises(ValueError): candidates(root, manifest)

    def test_creation_date_needs_timezone(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root/'A.jpg').write_bytes(b'fixture'); manifest=root/'manifest.json'
            manifest.write_text(json.dumps({'schema':1,'entries':[{'photo':'A.jpg','creationDate':'2020-01-01T00:00:00'}]}))
            with self.assertRaises(ValueError): candidates(root, manifest)

    def test_duplicate_source_in_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/'A.jpg').write_bytes(b'fixture'); manifest=root/'manifest.json'
            manifest.write_text(json.dumps({'schema':1,'entries':[{'photo':'A.jpg'}, {'photo':'A.jpg'}]}))
            with self.assertRaises(ValueError): candidates(root, manifest)


class ReceiptTests(unittest.TestCase):
    def test_reject_wrong_batch_identity_and_incomplete_success(self):
        batch={'id':'one','entries':[{'id':'a'}]}
        for status in [{'batch':'other','state':'batchDone','results':{'a':'verified'}},
                       {'batch':'one','state':'batchDone','results':{'b':'verified'}},
                       {'batch':'one','state':'batchDone','results':{}},
                       {'batch':'one','state':'batchDone','results':{'a':'pending'}}]:
            with self.assertRaises(ValueError): transfer.verify_receipt(batch,status)

    def test_partial_only_at_reserve_stop(self):
        transfer.verify_receipt({'id':'one','entries':[{'id':'a'},{'id':'b'}]},
                                {'batch':'one','state':'space','results':{'a':'verified'}})

    def test_unicode_private_plan_is_utf8(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'plan.json'
            transfer.atomic_json(path, {'file': '影片.mp4'})
            self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['file'], '影片.mp4')

    def test_atomic_ledger(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'ledger.json';transfer.atomic_json(path, {'pending':{'id':'one'}})
            self.assertEqual(json.loads(path.read_text())['pending']['id'],'one')
            self.assertFalse(path.with_suffix('.json.tmp').exists())

    def test_socket_retry_removes_incomplete_local_observation(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'status.json';calls=[]
            def command(*args):
                calls.append(args)
                if len(calls)==1:
                    target.write_text('partial');raise subprocess.CalledProcessError(1,'devicectl')
                self.assertFalse(target.exists());target.write_text('{"state":"batchDone"}')
            with patch.object(transfer,'run_device',command),patch.object(transfer.time,'sleep'):
                self.assertEqual(transfer.copy_from('chosen-device','Documents/status.json',target)['state'],'batchDone')
            self.assertTrue(all(args[1:4]==('device','copy','from') for args in calls))

    def test_bounded_read_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(transfer,'run_device',side_effect=subprocess.CalledProcessError(1,'devicectl')) as run:
                with patch.object(transfer.time,'sleep'):
                    with self.assertRaises(subprocess.CalledProcessError):
                        transfer.copy_from('chosen-device','Documents/status.json',Path(temp)/'status.json')
                self.assertEqual(run.call_count,6)

    def test_windows_execution_reports_unsupported(self):
        from types import SimpleNamespace
        with patch.object(transfer.sys,'platform','win32'):
            with self.assertRaisesRegex(RuntimeError,'Windows supports planning only'):
                transfer.execute(SimpleNamespace(), [])


if __name__=='__main__': unittest.main()
