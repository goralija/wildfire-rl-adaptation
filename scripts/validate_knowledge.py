"""Check repository Markdown against OKF 0.2 and optional project navigation rules.

Requires requirements/knowledge.txt. No network, content execution or LLM calls.
--strict adds repository quality rules; these are not universal OKF requirements.
"""

import argparse
from datetime import date, datetime
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

import yaml


def markdown_files(root):
    if (root / '.git').exists():
        output = subprocess.check_output(
            ['git', '-C', str(root), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'])
        return sorted({root / p for p in output.decode().split('\0')
                       if p.endswith('.md') and (root / p).is_file()})
    return sorted(root.rglob('*.md'))


def without_fences(text):
    visible, fence = [], None
    for line in text.splitlines():
        if fence:
            character, length = fence
            if re.fullmatch(r' {0,3}' + re.escape(character) + '{%d,}[ \t]*' % length, line):
                fence = None
            continue
        opening = re.match(r' {0,3}(`{3,}|~{3,})(.*)$', line)
        if opening and not (opening[1][0] == '`' and '`' in opening[2]):
            fence = (opening[1][0], len(opening[1]))
        else:
            visible.append(line)
    return '\n'.join(visible)


def frontmatter(text):
    if not text.startswith('---\n'):
        return None, text
    parts = text.split('\n---', 1)
    if len(parts) != 2 or (parts[1] and not parts[1].startswith('\n')):
        raise ValueError('unterminated frontmatter')
    metadata = yaml.safe_load(parts[0][4:])
    if not isinstance(metadata, dict):
        raise ValueError('frontmatter must be a YAML mapping')
    return metadata, parts[1].lstrip('\n')


def timestamp(value):
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError('provenance datetime requires an explicit UTC offset')


def metadata_checks(metadata):
    for key in ('generated', 'verified'):
        events = metadata.get(key, [])
        if isinstance(events, dict):
            events = [events]
        if not isinstance(events, list):
            raise ValueError(key + ' must contain actor events')
        for event in events:
            if not isinstance(event, dict) or not isinstance(event.get('by'), str) or not event['by'].strip():
                raise ValueError(key + ' requires a by actor')
            if 'at' in event:
                timestamp(event['at'])
    if 'stale_after' in metadata:
        timestamp(metadata['stale_after'])
    if 'sources' in metadata:
        if not isinstance(metadata['sources'], list):
            raise ValueError('sources must be a list')
        for source in metadata['sources']:
            if not isinstance(source, dict) or not isinstance(source.get('resource'), str) or not source['resource'].strip():
                raise ValueError('each source needs a resource')
            if 'last_modified' in source:
                timestamp(source['last_modified'])
    if 'tags' in metadata and (not isinstance(metadata['tags'], list)
                              or any(not isinstance(tag, str) for tag in metadata['tags'])):
        raise ValueError('tags must be a list of strings')


def validate(root, strict=False):
    root = root.resolve()
    paths = markdown_files(root)
    errors, edges = [], {}
    for path in paths:
        name = path.relative_to(root).as_posix()
        try:
            if not path.resolve().is_relative_to(root):
                raise ValueError('document is outside bundle')
            metadata, body = frontmatter(path.read_text(encoding='utf-8'))
            visible = without_fences(body)
            if path.name.lower() in ('index.md', 'log.md') and path.name != path.name.lower():
                raise ValueError('reserved filename must be lowercase')
            if path.name == 'index.md':
                if metadata is not None:
                    if path != root / 'index.md' or metadata != {'okf_version': '0.2'}:
                        raise ValueError('only root index may declare quoted okf_version: "0.2"')
                for line in visible.splitlines():
                    if line.strip() and not re.match(r'^#{1,6} |^[-*] \[[^\]]+\]\([^)]+\)', line):
                        raise ValueError('index body must contain headings and link bullets')
            elif path.name == 'log.md':
                if metadata is not None:
                    raise ValueError('reserved log has no frontmatter')
                dates = []
                for line in visible.splitlines():
                    if line.startswith('## '):
                        match = re.fullmatch(r'## (\d{4}-\d\d-\d\d)(?:: .+)?', line)
                        if not match:
                            raise ValueError('log entry heading needs ISO date')
                        dates.append(date.fromisoformat(match[1]))
                if dates != sorted(dates, reverse=True):
                    raise ValueError('log dates must be newest first')
            else:
                if metadata is None or not isinstance(metadata.get('type'), str) or not metadata['type'].strip():
                    raise ValueError('concept needs YAML frontmatter with nonempty string type')
                metadata_checks(metadata)
            links = re.findall(r'\[[^\]\n]*\]\(\s*(<[^>\n]*>|[^\s)\n]+)', visible)
            if metadata:
                links += [s['resource'] for s in metadata.get('sources', [])
                          if s['resource'].startswith(('/', './', '../'))]
            edges[path] = set()
            if strict:
                for link in links:
                    uri = urlsplit(link.strip('<>'))
                    if uri.scheme or not uri.path:
                        continue
                    target = (root / unquote(uri.path).lstrip('/') if uri.path.startswith('/')
                              else path.parent / unquote(uri.path)).resolve()
                    if not target.is_relative_to(root) or not target.exists():
                        errors.append(name + ': broken/outside local link ' + link)
                    elif target.is_dir():
                        edges[path].add(target / 'index.md')
                    else:
                        edges[path].add(target)
        except (ValueError, yaml.YAMLError, OSError) as exc:
            errors.append(name + ': ' + str(exc))
    if strict:
        index = root / 'index.md'
        if not index.exists():
            errors.append('project profile requires root index.md')
        reached, pending = set(), [index]
        while pending:
            path = pending.pop()
            if path not in reached:
                reached.add(path)
                pending.extend(edges.get(path, set()) - reached)
        errors.extend(str(p.relative_to(root)) + ': unreachable from index.md'
                      for p in paths if p not in reached)
    return paths, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--strict', action='store_true')
    args = parser.parse_args()
    paths, errors = validate(args.root, args.strict)
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('OKF 0.2: %d Markdown files pass%s.' % (len(paths), ' with project link/reachability checks' if args.strict else ''))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
