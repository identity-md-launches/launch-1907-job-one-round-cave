#!/usr/bin/env python3
"""Rebuild the offline gallery from records, retaining its embedded old previews.

Python standard library; Node + the vendored encoder only for missing previews.
Run from the repository root. No network, temporary pictures, or outside inputs.
"""
import base64
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess


class Previews(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.record = None
        self.images = {}
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'article':
            self.record = attrs.get('data-record')
        if tag == 'img' and self.record:
            source = attrs.get('src', '')
            if re.fullmatch(r'data:image/jpeg;base64,[A-Za-z0-9+/=]+', source):
                self.images[self.record] = source

    def handle_endtag(self, tag):
        if tag == 'article':
            self.record = None


def main():
    target = Path('dist/index.html')
    previews = Previews(target.read_text()).images if target.exists() else {}
    previews = json.loads(subprocess.run(['node', 'gathering/compact_previews.js'],
        input=json.dumps(previews), text=True, capture_output=True, check=True).stdout)
    goals = json.loads(Path('dist/goals.json').read_text())
    esc = html.escape
    chunks = ['''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<meta name="description" content="Four lines of worker tools, tested and connected at the Ice gathering. Every cave painting and its record."><title>Pepeolithic · Ice</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#1b160f;color:#f2e2c6;font:16px/1.6 system-ui,sans-serif}header,main,footer{max-width:1100px;margin:auto;padding:24px}h1{font-size:clamp(2.5rem,7vw,4rem);line-height:1.1}h2{font-size:1.8rem}a{color:#efbb72}a:focus-visible,summary:focus-visible{outline:3px solid #efbb72;outline-offset:4px}nav{display:flex;flex-wrap:wrap;gap:18px}section{margin:28px 0 60px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:16px}article{background:#2b2319;border:1px solid #695236;border-radius:8px;padding:20px}article img{float:right;width:96px;height:96px;image-rendering:auto;margin:0 0 12px 12px}details{margin-top:22px}summary{cursor:pointer}.future{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px}.future i{font-size:.85rem;padding:8px}.note{max-width:75ch;color:#cbbb9d}footer{border-top:1px solid #695236}
</style></head><body><header><p>Pepeolithic / Ice</p><h1>Four trails.<br>One shared bowl.</h1>
<p class="note">Four lines build worker tools. The gathering tests and connects them. Paintings appear newest first.</p><nav aria-label="Walls">''']
    walls = [('gathering', 'Gathering')] + [(f'line-{i}', f'Line {i}') for i in range(1, 5)]
    chunks += [f'<a href="#{wall}">{label}</a>' for wall, label in walls]
    chunks.append('</nav></header><main>')
    count = painted = 0
    for wall, label in walls:
        goal = 'Test the four lines and share useful pieces.' if wall == 'gathering' else goals[int(wall[-1])-1]['goal']
        chunks.append(f'<section id="{wall}"><h2>{label}</h2><p class="note">{esc(goal)}</p><div class="grid">')
        records = [(p, json.loads(p.read_text())) for p in sorted(Path('dist', wall).glob('[0-9][0-9].json'), reverse=True)]
        future = []
        for path, record in records:
            count += 1
            key = path.relative_to('dist').as_posix()
            image = record['image']
            if not re.fullmatch(r'https://api\.imd\.fun/artifacts/[a-f0-9]{64}', image):
                raise ValueError(f'invalid artifact URL: {key}')
            if record['name'] == 'Not painted yet':
                future.append(f'<i data-record={key}>{path.stem}</i>')
                continue
            painted += 1
            if key not in previews:
                # Adjacent record JPEGs are delivered in source, so a rebuild
                # also works offline without the daemon's artifact mount.
                source = path.with_suffix('.jpg')
                if not source.is_file():
                    raise ValueError(f'missing record preview: {key}')
                preview = 'data:image/jpeg;base64,' + base64.b64encode(source.read_bytes()).decode('ascii')
                previews[key] = json.loads(subprocess.run(
                    ['node', 'gathering/compact_previews.js'],
                    input=json.dumps({key: preview}), text=True,
                    capture_output=True, check=True).stdout)[key]
            attrs = {a['trait_type']: a['value'] for a in record['attributes']}
            title = esc(record['name'])
            chunks.append(f'<article data-record="{key}"><a href="{image}"><img src="{previews[key]}" width="96" height="96" alt="{title}"></a><a href="{key}">{path.stem} · {title}</a></article>')
        chunks.append(f'</div><details><summary>Unpainted records · {len(future)}</summary><div class="future">' + ''.join(future) + '</div></details></section>')
    chunks.append(f'</main><footer><p>{count} records · {painted} paintings · {count-painted} reserved slots.</p><p>Embedded previews work offline. Full walls open the artifact service. Records link to metadata; adjacent JPEGs are 512 px.</p><p><a href="../gathering/REPORT.md">Gathering report</a> · <a href="goals.json">Four goals</a> · <a href="../shared/http-evidence/README.md">Shared HTTP evidence tools</a></p></footer></body></html>')
    result = '\n'.join(chunks)
    if len(result.encode()) > 100000:
        raise ValueError(f'gallery exceeds 100 KB: {len(result.encode())} bytes')
    target.write_text(result, encoding='utf-8')
    print(json.dumps({'records': count, 'paintings': painted, 'bytes': len(result.encode())}))


if __name__ == '__main__':
    main()
