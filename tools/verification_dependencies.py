"""Prepare ordinary dependency copies for verification, without starting Kit."""
import argparse
import json
import os
from pathlib import Path
import shutil
import stat

FOLDERS = ('extscache', 'extscore', 'exts', 'project-exts')


def _reject_link(path):
    info = path.lstat()
    reparse = getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)
    if path.is_symlink() or reparse or (path.is_file() and info.st_nlink != 1):
        raise ValueError(f'Dependency snapshot contains a shared link: {path}')


def validate_snapshot(destination):
    destination = Path(destination).absolute()
    _reject_link(destination)
    manifest_path = destination / 'snapshot.json'
    if not manifest_path.is_file():
        raise ValueError('Dependency snapshot manifest is missing; prepare private copies first.')
    _reject_link(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('version') != 1 or set(manifest.get('folders', {})) != set(FOLDERS):
        raise ValueError('Dependency snapshot manifest is unsupported or incomplete.')
    for name in FOLDERS:
        folder = destination / name
        _reject_link(folder)
        count = 0
        for current, dirs, files in os.walk(folder, followlinks=False):
            for entry in dirs + files:
                _reject_link(Path(current) / entry)
            if '__pycache__' not in Path(current).relative_to(folder).parts:
                count += len(files)
        if (not count and name != 'exts') or count != manifest['folders'][name]['file_count']:
            raise ValueError(f'Dependency snapshot file count changed or folder is empty: {name}')
    return manifest


def prepare_snapshot(destination, sources):
    destination = Path(destination).absolute()
    if destination.exists():
        return validate_snapshot(destination)
    if set(sources) != set(FOLDERS):
        raise ValueError('Supply all four dependency source folders.')
    sources = {name: Path(path).absolute() for name, path in sources.items()}
    for source in sources.values():
        if not source.is_dir():
            raise ValueError(f'Dependency source is missing: {source}')
        if destination == source or source in destination.parents:
            raise ValueError('Dependency destination must be outside its source folders.')
    destination.mkdir(parents=True)
    manifest = {'version': 1, 'folders': {}}
    for name, source in sources.items():
        target = destination / name
        if name == 'project-exts' and (source / 'config' / 'extension.toml').is_file():
            target.mkdir()
            target = target / source.name
        shutil.copytree(source, target, symlinks=False, ignore=shutil.ignore_patterns('__pycache__'))
        count = sum(len(files) for _, _, files in os.walk(destination / name))
        manifest['folders'][name] = {'source': str(source), 'file_count': count}
        print(f'Copied {name}: {count} files', flush=True)
    (destination / 'snapshot.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return validate_snapshot(destination)


def qualify_extension_paths(extension_paths, dependency_root, project_root):
    allowed = (Path(dependency_root).resolve(), Path(project_root).resolve())
    if allowed[0] == allowed[1] or allowed[0] in allowed[1].parents or allowed[1] in allowed[0].parents:
        raise ValueError('Dependency and extension roots overlap; Kit would unload copied SDK modules with Issues.')
    qualified = []
    for extension_id, value in extension_paths:
        if not value:
            raise ValueError(f'Loaded extension has no resolved path: {extension_id}')
        path = Path(value).resolve()
        if not any(path == root or root in path.parents for root in allowed):
            raise ValueError(f'Loaded extension is outside private verification folders: {extension_id}: {path}')
        qualified.append({'id': extension_id, 'path': str(path)})
    return qualified


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'validate'))
    parser.add_argument('destination', type=Path)
    parser.add_argument('--kit-root', type=Path)
    parser.add_argument('--project-exts', type=Path)
    parser.add_argument('--project-root', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        if args.kit_root is None or args.project_exts is None:
            parser.error('prepare requires --kit-root and --project-exts')
        sources = {'extscache': args.kit_root.parent / 'extscache',
                   'extscore': args.kit_root / 'extscore', 'exts': args.kit_root / 'exts',
                   'project-exts': args.project_exts}
        prepare_snapshot(args.destination, sources)
    else:
        if args.project_root is not None:
            qualify_extension_paths([], args.destination, args.project_root)
        validate_snapshot(args.destination)
    print('Private dependency snapshot validated.', flush=True)


if __name__ == '__main__':
    main()
