#!/usr/bin/env python3
"""Check Gathering 32 bytes, records, scope and offline gallery structure."""
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess

from check_delivery import Gallery, jpeg_dimensions, png_dimensions


def main():
    wall_path = Path('artifacts/gathering/wall-v12.png')
    wall = wall_path.read_bytes()
    assert wall == Path('artifacts/gathering/wall.png').read_bytes()
    assert png_dimensions(wall) == (1254, 1254)
    assert wall[24:26] == bytes((8, 2)), 'need 8-bit RGB PNG'
    digest = hashlib.sha256(wall).hexdigest()
    jpeg = Path('dist/gathering/32.jpg').read_bytes()
    assert jpeg_dimensions(jpeg) == (512, 512) and len(jpeg) < 100000
    record = json.loads(Path('dist/gathering/32.json').read_text())
    assert set(record) == {'name', 'image', 'attributes'}
    assert record['image'] == 'https://api.imd.fun/artifacts/' + digest
    attributes = {item['trait_type']: item['value'] for item in record['attributes']}
    assert len(attributes) == len(record['attributes']) == 6
    assert set(attributes) == {'Cave', 'Wall', 'Number', 'Left behind', 'Meaning', 'One thing'}
    assert attributes['Cave'] == 'Ice' and attributes['Wall'] == 'Gathering'
    assert type(attributes['Number']) is int and attributes['Number'] == 32
    assert attributes['One thing'] == 'Gathering'
    goals = [{'line': n, 'goal': Path(f'line-{n}/GOAL.md').read_text().strip()}
             for n in range(1, 5)]
    assert json.loads(Path('dist/goals.json').read_text()) == goals

    content = Path('dist/index.html').read_text()
    gallery = Gallery(content)
    sources = sorted(Path('dist').glob('*/[0-9][0-9].json'))
    expected = {p.relative_to('dist').as_posix() for p in sources}
    assert len(content.encode()) < 100000
    assert len(gallery.records) == len(expected) == 160
    assert set(gallery.records) == expected
    assert len(gallery.images) == 60
    assert all(re.fullmatch(r'data:image/jpeg;base64,[A-Za-z0-9+/=]+', src)
               for src in gallery.images)
    assert not set(gallery.tags) & {'script', 'iframe', 'link'}
    assert len(base64.b64decode(gallery.images[0].split(',', 1)[1])) > 100
    for href in gallery.links:
        if href.startswith('#'):
            assert f'id="{href[1:]}"' in content
        elif not href.startswith('https://'):
            assert (Path('dist') / href).is_file(), href
    for wall_name in ('gathering', 'line-1', 'line-2', 'line-3', 'line-4'):
        keys = [key for key in gallery.records if key.startswith(wall_name + '/')]
        for unpainted in (False, True):
            subset = [key for key in keys if
                      (json.loads(Path('dist', key).read_text())['name'] == 'Not painted yet') == unpainted]
            assert subset == sorted(subset, reverse=True)
        for number in range(2, 22):
            source = Path('dist', wall_name, f'{number:02}.json')
            assert json.loads(source.read_text()) == {
                'name': 'Not painted yet',
                'image': 'https://api.imd.fun/artifacts/b5e794cb2c70bd232230e389707698c69c2080786d606a13b39f9315c9a90799',
                'attributes': [{'trait_type': 'Cave', 'value': 'Ice'}]}
            assert not source.with_suffix('.jpg').exists()

    assert Path('line-1/tools/payload-lens/payload_lens.py').read_bytes() == \
           Path('shared/http-evidence/payload_lens.py').read_bytes()
    adapted = Path('line-2/tools/csv-duplicates/duplicates.py').read_text().replace(
        "Path(__file__).resolve().parents[1] / 'csv-reconcile' / 'reconcile.py'",
        "Path(__file__).resolve().parent / 'reconcile.py'")
    assert adapted == Path('shared/http-evidence/duplicates.py').read_text()

    image = json.loads(Path('gathering/image-checks32.json').read_text())
    assert image['png']['sha256'] == digest
    assert image['png']['format'] == 'PNG' and image['png']['dimensions'] == [1254, 1254]
    assert image['jpeg']['format'] == 'JPEG' and image['jpeg']['dimensions'] == [512, 512]
    assert image['preservation']['changed_pixels'] > 0
    assert image['preservation']['outside_rectangle_changed_pixels'] == 0
    assert image['visual_review_completed'] and image['unmet_visual_requirements'] == []
    tests = json.loads(Path('gathering/test-runs32.json').read_text())
    assert tests['ok'] and tests['line_tests'] == 452 and tests['shared_tests'] == 83
    assert tests['gathering_tests'] == 8
    for name in ('integration-checks32', 'inherited-new-tool-checks32', 'new-tool-checks32'):
        assert json.loads(Path(f'gathering/{name}.json').read_text())['ok']
    changed = subprocess.run(['git', 'status', '--porcelain', '--',
                              'line-1', 'line-2', 'line-3', 'line-4',
                              'dist/line-1', 'dist/line-2', 'dist/line-3', 'dist/line-4'],
                             capture_output=True, text=True, check=True)
    assert not changed.stdout, 'line folder or record changed'
    changed_all = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=all'],
                                 capture_output=True, text=True, check=True)
    for row in changed_all.stdout.splitlines():
        path = Path(row[3:])
        if path.is_file() and not path.as_posix().startswith('artifacts/'):
            assert path.stat().st_size < 100000, path
    result = {'ok': True, 'png': {'format': 'PNG', 'mode': 'RGB',
              'dimensions': [1254, 1254], 'bytes': len(wall), 'sha256': digest},
              'jpeg': {'format': 'JPEG', 'dimensions': [512, 512], 'bytes': len(jpeg)},
              'gallery_records': 160, 'painted_previews': 60,
              'placeholders': 100, 'gallery_bytes': len(content.encode()),
              'line_paths_unchanged': True, 'unmet_visual_requirements': []}
    Path('gathering/delivery-checks32.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
