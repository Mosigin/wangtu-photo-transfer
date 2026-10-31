"""Portable, offline media planning. No device access or third-party packages."""
import hashlib
import json
from pathlib import Path

PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.heic', '.heif', '.png', '.gif', '.bmp', '.tif', '.tiff', '.dng'}
VIDEO_EXTENSIONS = {'.mov', '.mp4', '.m4v'}
RESERVE = 1_000_000_000
OVERHEAD = 150_000_000
BATCH_LIMIT = 32_000_000


def checked_source(root, relative):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Manifest paths must be relative and remain inside --source')
    path = root / relative
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root) or path.is_symlink() or not resolved.is_file():
        raise ValueError('Only regular files inside --source are accepted')
    if resolved.stat().st_size <= 0:
        raise ValueError('Empty media file')
    return resolved


def candidates(source, manifest=None, media='all'):
    source = source.resolve(strict=True)
    if not source.is_dir():
        raise ValueError('--source must be a directory')
    selected = []
    if manifest:
        document = json.loads(manifest.read_text(encoding='utf-8'))
        if document.get('schema') != 1 or not isinstance(document.get('entries'), list):
            raise ValueError('Expected manifest schema 1 and entries array')
        for item in document['entries']:
            keys = {key for key in ('photo', 'video', 'pairedVideo') if key in item}
            if keys not in ({'photo'}, {'video'}, {'photo', 'pairedVideo'}):
                raise ValueError('Each manifest entry is one photo, one video, or an explicit Live pair')
            selected.append(([(key, item[key]) for key in ('photo', 'video', 'pairedVideo') if key in item],
                             item.get('creationDate')))
    else:
        for path in sorted(source.rglob('*')):
            relative = path.relative_to(source)
            if any(part.startswith('.') for part in relative.parts) or not path.is_file():
                continue
            extension = path.suffix.lower()
            if extension in PHOTO_EXTENSIONS:
                selected.append(([('photo', str(relative))], None))
            elif extension in VIDEO_EXTENSIONS:
                # A matching basename is not proof of a Live Photo pair.
                selected.append(([('video', str(relative))], None))
    entries = []
    seen_paths = set()
    for paths, creation_date in selected:
        is_video = paths[0][0] == 'video'
        if media == 'photos' and is_video or media == 'videos' and not is_video:
            continue
        if creation_date is not None:
            from datetime import datetime
            try:
                date = datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
                if date.tzinfo is None: raise ValueError('Timezone required')
                creation_date = date.isoformat()
            except (ValueError, TypeError, AttributeError):
                raise ValueError('creationDate must be ISO-8601 with a timezone') from None
        identifier = hashlib.sha256(json.dumps(paths, ensure_ascii=False).encode()).hexdigest()[:24]
        resources = []
        for role, relative in paths:
            path = checked_source(source, relative)
            extension = path.suffix.lower()
            expected = PHOTO_EXTENSIONS if role == 'photo' else VIDEO_EXTENSIONS
            if extension not in expected:
                raise ValueError('Media extension does not match manifest role')
            if path in seen_paths: raise ValueError('A source resource appears in multiple entries')
            seen_paths.add(path)
            resources.append({'file': identifier + '-' + role + extension, 'kind': role,
                              'originalFilename': path.name, 'bytes': path.stat().st_size,
                              'source': str(path), 'mtime_ns': path.stat().st_mtime_ns})
        entries.append({'id': 'wt-' + identifier, 'resources': resources, 'creationDate': creation_date})
    if not entries: raise ValueError('No supported media found for the selected scope')
    return entries


def select_batch(entries, completed, free, reserve=RESERVE):
    available = max(0, (free - reserve - OVERHEAD) // 2)
    budget = min(BATCH_LIMIT, available)
    chosen = []
    size = 0
    for entry in entries:
        if entry['id'] in completed: continue
        amount = sum(r['bytes'] for r in entry['resources'])
        if amount > budget - size:
            if not chosen and amount <= available:
                return [entry]  # A large photo/video may travel alone, never split its resources.
            continue
        chosen.append(entry); size += amount
        if len(chosen) == 20: break
    return chosen
