"""Report source BCF cameras and optional default USD mapping without saving inputs."""
import argparse
from contextlib import ExitStack
from dataclasses import replace
import importlib
import json
import os
from pathlib import Path
import sys
import types


ROOT = Path(__file__).resolve().parents[1]
VERIFICATION = Path.home() / '.codex/worktrees/issues-tag-improvements'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--scene', type=Path, help='Read this USD scene and apply the existing source-world mapping')
    parser.add_argument('--reference', help='Select an IFCSITE path in the scene')
    args = parser.parse_args()
    if args.reference and not args.scene:
        parser.error('--reference requires --scene')
    packages = VERIFICATION / 'issues.tag/verification/python'
    if packages.is_dir():
        sys.path.insert(0, str(packages))
    package = types.ModuleType('_bcf_camera_report_product')
    package.__path__ = [str(ROOT / 'issues_tag')]
    sys.modules[package.__name__] = package
    bcf = importlib.import_module(package.__name__ + '.bcf')
    diagnostics = importlib.import_module(package.__name__ + '.bcf_diagnostics')
    try:
        with ExitStack() as dependencies:
            source = bcf.read_bcf(args.archive)
            converted = None
            mapping_report = None
            if args.scene:
                try:
                    from pxr import Usd
                except ImportError:
                    libraries = sorted((VERIFICATION / 'verification-dependencies/extscache').glob('omni.usd.libs-*'))
                    if not libraries:
                        raise ImportError('Standalone USD libraries are unavailable in the verification snapshot.')
                    if hasattr(os, 'add_dll_directory'):
                        dependencies.enter_context(os.add_dll_directory(str(libraries[0] / 'bin')))
                    sys.path.insert(0, str(libraries[0]))
                    from pxr import Usd
                stage = Usd.Stage.Open(str(args.scene))
                if stage is None:
                    raise ValueError('Cannot open the USD scene.')
                coordinates = importlib.import_module(package.__name__ + '.bcf_coordinates')
                mapping = coordinates.stage_mapping(stage, reference_path=args.reference)
                converted = replace(source, viewpoints=tuple(
                    view if view.id in source.native_viewpoints else coordinates.import_view(view, mapping)
                    for view in source.viewpoints))
                mapping_report = {'matrix': list(mapping[0]), 'meters_per_unit': mapping[1],
                                  'up_axis': mapping[2], 'reference_path': mapping[3] or None}
            report = {
                'counts': {'topics': len(source.issues), 'viewpoints': len(source.viewpoints),
                           'cameras': sum(bool(view.camera) for view in source.viewpoints)},
                'warnings': list(source.warnings),
                'mapping': mapping_report,
                'cameras': diagnostics.camera_diagnostics(source, converted),
            }
            print(json.dumps(report, indent=2, allow_nan=False))
    except (ValueError, OSError, ImportError) as error:
        parser.exit(2, f'{parser.prog}: {error}\n')


if __name__ == '__main__':
    main()
