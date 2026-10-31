#!/usr/bin/env python3
"""Wangtu Photo Transfer: an offline macOS USB sender for the iPhone companion app.

Dry-run planning is the default. --execute uses devicectl, never Finder photo sync, AirDrop, or an app-level cloud service.
The original media is only read; all state stays outside the repository.
"""
import argparse
import hashlib
import sys
import contextlib
import json
import os
from pathlib import Path
import subprocess
import time

from media_plan import candidates, select_batch, RESERVE, OVERHEAD, BATCH_LIMIT

BUNDLE = 'io.github.mosigin.wangtu-photo-transfer'
DEVICE_TIMEOUT = 600


def atomic_json(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def run_device(device, *arguments):
    subprocess.run(['xcrun', 'devicectl', *arguments, '--device', device,
                    '--timeout', str(DEVICE_TIMEOUT)], check=True, stdout=subprocess.DEVNULL)


def copy_from(device, remote, local):
    for attempt in range(6):
        if local.exists():
            local.unlink()  # Task-owned local observation file only.
        try:
            run_device(device, 'device', 'copy', 'from', '--domain-type', 'appDataContainer',
                       '--domain-identifier', BUNDLE, '--source', remote, '--destination', str(local))
            return json.loads(local.read_text(encoding='utf-8'))
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            # The phone replaces its status atomically; CoreDevice can also close
            # a USB file-service socket transiently. This is a read-only retry.
            if attempt == 5:
                raise
            time.sleep(attempt + 1)


def copy_to(device, source, remote):
    run_device(device, 'device', 'copy', 'to', '--domain-type', 'appDataContainer',
               '--domain-identifier', BUNDLE, '--source', str(source), '--destination', remote)


def verify_receipt(batch, status):
    expected = {e['id'] for e in batch['entries']}
    if status.get('batch') != batch['id'] or not set(status['results']).issubset(expected):
        raise ValueError('Unexpected receipt identities')
    if any(v not in ('verified', 'failed') for v in status['results'].values()):
        raise ValueError('Unknown receipt state')
    if status['state'] == 'batchDone' and set(status['results']) != expected:
        raise ValueError('Incomplete batch receipt')


def execute(args, entries):
    if sys.platform != 'darwin':
        raise RuntimeError('USB transfer currently requires macOS + Xcode. Windows supports planning only.')
    info = args.work / 'device-info.json'
    run_device(args.device, 'device', 'info', 'details', '--json-output', str(info))
    device_info = json.loads(info.read_text(encoding='utf-8'))['result']
    connection = device_info['connectionProperties']
    if connection.get('transportType') != 'wired':
        raise ValueError('A wired device connection is required')
    ledger_path = args.work / 'ledger.json'
    fingerprint = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()
    ledger = json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else {
        'sourceFingerprint': fingerprint, 'completed': {}, 'nextBatch': 1, 'pending': None}
    if ledger['sourceFingerprint'] != fingerprint:
        raise ValueError('Source changed; do not reuse this receipt ledger')
    while True:
        if (args.work / 'STOP').exists():
            signal = args.work / 'phone-stop'; signal.touch()
            copy_to(args.device, signal, 'Documents/STOP')
            print('Stopped at user request; keep pending receipts for resume', flush=True)
            return
        status = copy_from(args.device, 'Documents/status.json', args.work / 'phone-status.json')
        atomic_json(args.work / 'progress.json', {'phone': status, 'verifiedCount':
                    sum(v == 'verified' for v in ledger['completed'].values()), 'state': 'observing'})
        if not status.get('authorized'):
            raise RuntimeError('Open Wangtu Photo Transfer and grant full Photos access on your iPhone')
        if abs(time.time() - status.get('time', 0)) > 20:
            raise RuntimeError('Phone status is stale; keep Wangtu Photo Transfer open on your iPhone')
        if status['state'] in ('error', 'paused', 'permission'):
            raise RuntimeError('Phone importer needs attention: ' + status['state'])
        if ledger['pending']:
            batch = ledger['pending']
            if status.get('batch') == batch['id']:
                # Do not re-stage a batch the phone is processing or has already committed.
                while status['state'] not in ('batchDone', 'space'):
                    if status['state'] in ('error', 'paused', 'permission'):
                        raise RuntimeError('Pending phone batch needs attention')
                    time.sleep(3)
                    status = copy_from(args.device, 'Documents/status.json', args.work / 'phone-status.json')
                    if abs(time.time() - status.get('time', 0)) > 20:
                        raise RuntimeError('Pending phone batch stopped updating')
                verify_receipt(batch, status)
                ledger['completed'].update(status['results'])
                ledger['pending'] = None; ledger['nextBatch'] += 1
                atomic_json(ledger_path, ledger)
                if status['state'] == 'space':
                    finish(args, entries, ledger, status, 'reserve_reached'); return
                continue
        else:
            if status['state'] == 'space':
                finish(args, entries, ledger, status, 'reserve_reached')
                return
            selected = select_batch(entries, ledger['completed'], status['freeBytes'], args.reserve_bytes)
            if not selected:
                atomic_json(args.work / 'progress.json', {'state': 'finished_or_reserve_reached',
                            'freeBytes': status['freeBytes'], 'completed': ledger['completed']})
                finish(args, entries, ledger, status, 'source_exhausted' if len(ledger['completed']) == len(entries) else 'no_item_fits_safe_budget')
                return
            batch = {'id': f"usb-{fingerprint[:10]}-{ledger['nextBatch']:06d}", 'schema': 1,
                     'reserveBytes': args.reserve_bytes, 'entries': []}
            for entry in selected:
                value = {'id': entry['id'], 'creationDate': entry['creationDate'], 'resources': []}
                for resource in entry['resources']:
                    path = Path(resource['source'])
                    actual = sha256(path)
                    if (path.stat().st_size != resource['bytes']
                            or path.stat().st_mtime_ns != resource['mtime_ns']):
                        raise ValueError('Source content changed; transmission stopped')
                    value['resources'].append({k: resource[k] for k in ('file', 'kind', 'bytes', 'originalFilename')}
                                             | {'sha256': actual})
                batch['entries'].append(value)
            ledger['pending'] = batch
            atomic_json(ledger_path, ledger)
        run_device(args.device, 'device', 'info', 'details', '--json-output', str(info))
        observed = json.loads(info.read_text(encoding='utf-8'))['result']['connectionProperties']
        if observed.get('transportType') != 'wired':
            raise RuntimeError('Wired connection lost; no new batch sent')
        # A prepared batch is durable before payload copying. The request is sent last.
        import shutil
        needed = sum(r['bytes'] for e in batch['entries'] for r in e['resources'])
        if shutil.disk_usage(args.work).free < needed + RESERVE:
            raise RuntimeError('Not enough computer disk space for the next temporary payload')
        payload = args.work / 'payload'
        payload.mkdir(exist_ok=True)
        for old in payload.iterdir():
            if old.is_file() or old.is_symlink(): old.unlink()
            else: raise ValueError('Unexpected staging directory')
        by_id = {e['id']: e for e in entries}
        for entry in batch['entries']:
            source_map = {r['file']: Path(r['source']) for r in by_id[entry['id']]['resources']}
            for resource in entry['resources']:
                shutil.copy2(source_map[resource['file']], payload / resource['file'])
                if sha256(payload / resource['file']) != resource['sha256']:
                    raise ValueError('Staging hash mismatch')
        copy_to(args.device, payload, 'Documents/Incoming/' + batch['id'])
        request = args.work / 'request.json'; atomic_json(request, batch)
        copy_to(args.device, request, 'Documents/request.json')
        started = time.monotonic()
        while True:
            if (args.work / 'STOP').exists():
                signal = args.work / 'phone-stop'; signal.touch()
                copy_to(args.device, signal, 'Documents/STOP')
                return
            time.sleep(3)
            status = copy_from(args.device, 'Documents/status.json', args.work / 'phone-status.json')
            atomic_json(args.work / 'progress.json', {'phone': status, 'batch': batch['id'],
                        'completedBeforeBatch': len(ledger['completed'])})
            if status['batch'] == batch['id'] and status['state'] in ('batchDone', 'space'):
                break
            if status['state'] in ('error', 'paused', 'permission'):
                raise RuntimeError('Phone importer stopped: ' + status['state'])
            if time.monotonic() - started > args.timeout + 120:
                raise TimeoutError('No terminal batch receipt; resume from saved pending batch')
        verify_receipt(batch, status)
        ledger['completed'].update(status['results'])
        ledger['pending'] = None; ledger['nextBatch'] += 1
        atomic_json(ledger_path, ledger)
        print(json.dumps({'batch': batch['id'], 'processed': len(ledger['completed']),
                          'phoneFreeGB': round(status['freeBytes'] / 1e9, 3)}), flush=True)
        if status['state'] == 'space':
            finish(args, entries, ledger, status, 'reserve_reached'); return


def finish(args, entries, ledger, status, reason):
    by_id = {entry['id']: entry for entry in entries}
    verified = [identity for identity, state in ledger['completed'].items() if state == 'verified']
    summary = {'reason': reason, 'verified': len(verified),
               'failed': sum(v == 'failed' for v in ledger['completed'].values()),
               'remaining': len(entries) - len(ledger['completed']),
               'originalBytesVerified': sum(r['bytes'] for identity in verified for r in by_id[identity]['resources']),
               'freeBytes': status['freeBytes'], 'reserveBytes': args.reserve_bytes,
               'existingMediaDeleted': False, 'pending': ledger['pending'] is not None}
    atomic_json(args.work / 'summary.json', summary)
    if status['state'] != 'space':
        signal = args.work / 'phone-stop'; signal.touch()
        copy_to(args.device, signal, 'Documents/STOP')
    print(json.dumps(summary), flush=True)


@contextlib.contextmanager
def sender_lock(path):
    with path.open('a+b') as lock:
        if sys.platform == 'win32':
            import msvcrt
            lock.seek(0); lock.write(b'0'); lock.flush(); lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def main():
    global BUNDLE, DEVICE_TIMEOUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--manifest', type=Path, help='Explicit photo/video/Live-pair manifest, schema 1')
    parser.add_argument('--media', choices=['all', 'photos', 'videos'], default='all')
    parser.add_argument('--work', type=Path)
    parser.add_argument('--device', help='Exact identifier of the user-selected physical device')
    parser.add_argument('--bundle-id', default=BUNDLE)
    parser.add_argument('--reserve-gb', type=float, default=1.0)
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--list-devices', action='store_true')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if args.list_devices:
        if sys.platform != 'darwin': parser.error('Device listing currently requires macOS + Xcode')
        subprocess.run(['xcrun', 'devicectl', 'list', 'devices'], check=True)
        return
    if not args.source or not args.work: parser.error('--source and --work are required')
    if not 1 <= args.reserve_gb <= 1000: parser.error('--reserve-gb must be between 1 and 1000')
    if not 10 <= args.timeout <= 3600: parser.error('--timeout must be between 10 and 3600 seconds')
    import re
    if not re.fullmatch(r'[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+', args.bundle_id): parser.error('Invalid bundle ID')
    BUNDLE = args.bundle_id; DEVICE_TIMEOUT = args.timeout
    args.reserve_bytes = int(args.reserve_gb * 1_000_000_000)
    args.source = args.source.resolve(strict=True)
    args.work = args.work.resolve()
    repository = Path(__file__).resolve().parents[1]
    if args.work == args.source or args.work.is_relative_to(args.source) or args.work.is_relative_to(repository):
        parser.error('Keep private transfer state outside the source and the repository')
    args.work.mkdir(parents=True, exist_ok=True)
    entries = candidates(args.source, args.manifest, args.media)
    atomic_json(args.work / 'plan.json', {'schema': 1, 'entries': entries})
    if not args.execute:
        print(json.dumps({'media': len(entries),
                          'photos': sum(e['resources'][0]['kind'] == 'photo' for e in entries),
                          'videos': sum(e['resources'][0]['kind'] == 'video' for e in entries),
                          'livePairs': sum(len(e['resources']) == 2 for e in entries),
                          'originalBytes': sum(r['bytes'] for e in entries for r in e['resources']),
                          'reserveBytes': args.reserve_bytes, 'execute': False}))
        return
    if not args.device: parser.error('--execute requires an explicit --device; never guess the phone')
    import tempfile
    lock_folder = Path(tempfile.gettempdir()) / 'wangtu-photo-transfer-device-locks'
    lock_folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_name = hashlib.sha256((args.device + '|' + BUNDLE).encode()).hexdigest() + '.lock'
    with sender_lock(args.work / 'sender.lock'), sender_lock(lock_folder / lock_name):
        execute(args, entries)


if __name__ == '__main__': main()
