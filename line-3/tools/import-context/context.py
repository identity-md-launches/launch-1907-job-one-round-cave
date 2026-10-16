#!/usr/bin/env python3
"""Show syntactic surroundings of explicit imports, without executing project code."""
import argparse
import ast
from collections import defaultdict, deque
import importlib.util
import json
from pathlib import Path
import sys

SCOPE = ('Contexts describe syntax, not whether an import runs. TYPE_CHECKING labels '
         'recognize only literal spellings TYPE_CHECKING and typing.TYPE_CHECKING; '
         'aliases, rebinding, negation and truth values are not inferred. No imports '
         'are removed from the map. Function/class bodies, conditions, handlers, '
         'loops and other compound statement branches are retained outermost first. '
         'Dynamic calls and implicit package initialization are not resolved. '
         'Review collection skips, parse issues, collisions and source hashes.')


def load_budget():
    path = Path(__file__).resolve().parents[1] / 'import-budget' / 'budget.py'
    spec = importlib.util.spec_from_file_location('line3_context_budget', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def branch(node, field, mapper):
    """Describe compound statement child fields; never evaluate their expressions."""
    kind = type(node).__name__
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {'kind': kind, 'branch': field, 'line': node.lineno, 'name': node.name}
    if isinstance(node, ast.If):
        test = node.test
        spelling = ('TYPE_CHECKING' if isinstance(test, ast.Name) and test.id == 'TYPE_CHECKING'
                    else 'typing.TYPE_CHECKING' if isinstance(test, ast.Attribute)
                    and test.attr == 'TYPE_CHECKING' and isinstance(test.value, ast.Name)
                    and test.value.id == 'typing' else None)
        result = {'kind': kind, 'branch': field, 'line': node.lineno,
                  'guard': 'main_guard' if mapper.is_main_guard(node) else
                           'type_checking_spelling' if spelling else 'condition'}
        if spelling:
            result['spelling'] = spelling
        return result
    # A generic AST kind/field pair also covers try*, match, async loops and with.
    if isinstance(node, (ast.stmt, ast.ExceptHandler, ast.match_case)):
        line = getattr(node, 'lineno', None)
        if line is None and isinstance(node, ast.match_case):
            line = node.pattern.lineno
        return {'kind': kind, 'branch': field, 'line': line}
    return None


def import_contexts(tree, mapper):
    """Match mapper's breadth-first import order, including duplicate same-line sites."""
    surroundings = {}
    pending = [(tree, ())]
    while pending:
        node, parents = pending.pop()
        surroundings[id(node)] = parents
        for field, value in ast.iter_fields(node):
            children = value if isinstance(value, list) else [value]
            children = [child for child in children if isinstance(child, ast.AST)]
            for child in reversed(children):
                context = branch(node, field, mapper)
                pending.append((child, parents + (context,) if context else parents))
    sites = defaultdict(deque)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            prefix = '.' * node.level + (node.module or '')
            targets = [prefix + ' import ' + alias.name for alias in node.names]
        else:
            continue
        for target in targets:
            sites[node.lineno, target].append({'column': node.col_offset,
                                               'contexts': list(surroundings[id(node)])})
    return sites


def analyze(root, limits=None):
    budget = load_budget()
    mapper = budget.load_mapper()
    limits = dict(budget.DEFAULTS if limits is None else limits)
    sources, inventory = budget.collect(root, limits, mapper.SKIP_DIRS)
    report = mapper.inspect(Path(root), source_bytes=sources)
    parse_errors = {issue['path'] for issue in report['issues'] if issue['type'] == 'parse_error'}
    nested = total = 0
    for module in report['modules']:
        if module['path'] in parse_errors:
            continue
        tree = ast.parse(sources[module['path']], filename=module['path'])
        sites = import_contexts(tree, mapper)
        for item in module['imports']:
            candidates = sites[item['line'], item['target']]
            if not candidates:
                raise ValueError('missing import context evidence')
            item.update(candidates.popleft())
            total += 1
            nested += bool(item['contexts'])
        if any(sites.values()):
            raise ValueError('unmatched import context evidence')
    return {'status': 'complete', 'limits': limits, 'inventory': inventory,
            'map': report, 'context_summary': {'import_sites': total,
            'nested_sites': nested, 'module_body_sites': total - nested},
            'scope': SCOPE, 'collection_scope': budget.SCOPE}


def format_text(result):
    lines = []
    for module in result['map']['modules']:
        lines.append(module['module'] + ' (' + module['path'] + ')')
        for item in module['imports']:
            contexts = ' / '.join(c['kind'] + '.' + c['branch'] + '@' + str(c['line'])
                                  + (' [' + c['guard'] + ']' if 'guard' in c else '')
                                  for c in item['contexts']) or 'module body'
            lines.append(f"  {item['line']}:{item['column']}: {item['target']} ({item['kind']}) — {contexts}")
    report = result['map']
    for issue in report['issues']:
        lines.append('Issue: ' + json.dumps(issue, ensure_ascii=False))
    for module in report['modules']:
        for line in module['dynamic_import_lines']:
            lines.append(f"Dynamic call: {module['path']}:{line}")
    for cycle in report['cycles']:
        lines.append('Cycle: ' + ', '.join(cycle))
    lines.extend([json.dumps(result['context_summary'], sort_keys=True), SCOPE])
    return '\n'.join(lines)


def main(argv=None):
    budget = load_budget()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path, help='explicit import root within current workspace')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--strict', action='store_true', help='exit 1 on map warnings or cycles')
    for name, value in budget.DEFAULTS.items():
        parser.add_argument('--max-' + name.replace('_', '-'), type=int, default=value, dest=name)
    args = parser.parse_args(argv)
    try:
        result = analyze(args.root, {name: getattr(args, name) for name in budget.DEFAULTS})
    except (OSError, ValueError, RuntimeError, RecursionError) as exc:
        # Each analyze call loads its own collector class; use its structured evidence.
        error = getattr(exc, 'evidence', {'type': 'scan_error', 'detail': str(exc)})
        if args.json:
            print(json.dumps({'status': 'refused', 'error': error}, indent=2))
        else:
            print('import-context: ' + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else format_text(result))
    report = result['map']
    warnings = report['issues'] or report['cycles'] or any(
        module['dynamic_import_lines'] for module in report['modules'])
    return int(bool(args.strict and warnings))


if __name__ == '__main__':
    sys.exit(main())
