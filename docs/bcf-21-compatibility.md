# Initial BCF import sample

The supplied `2026-09-30 11_36 106 Issues.bcf` is a BCF XML 2.1 archive.
The importer now accepts 2.1 and 3.0. Export remains BCF XML 3.0.

The compatibility path reads root-level comments and viewpoint references,
normalizes casing for the four supported statuses, and derives missing camera
aspect ratios from snapshot dimensions. Image signatures determine the format,
so JPEG snapshots named `.png` remain usable. An absent snapshot uses a warned
1:1 aspect ratio. Existing archive path, entity, duplicate, and size checks remain.

Timestamp values without timezones are interpreted as UTC with an import
warning. The archive does not establish the original timezone. One missing
comment author is retained as `Unknown author`. Assignment and due dates remain
outside the current issue model and produce an import warning.

When every viewpoint is linked to a comment, the first available camera view
also becomes the issue's initial review view. Viewpoints without cameras retain
their snapshots and comment links without inventing a camera.

Offline checks against the supplied archive verify 106 issues, 118 comments,
121 viewpoints, and 108 cameras. Checks cover BCF 3.0 export/readback, import into
a temporary parent USD, save/reopen, and duplicate-free repeat import.
No user scene or source archive is edited. Rendered navigation remains unverified.

Standard BCF cameras and clipping planes are converted from metres/Z-up into
the USD frame at import preview. For a single referenced model, the importer
uses its top-level `Default` frame when available, otherwise its reference root.
The mapping compares the original source USD world transform with the composed
world transform, including parent placement and rotation. Existing source
georeferencing is removed before applying the composed transform, so its offset
is not applied twice. Reference units and up axis are read from the source USD.
Without a reference, the scene's units and up axis define the conversion.

The saved SOL11-23 scene and all 108 sample cameras were checked read-only.
Their source and composed georeferenced frames agree within 1e-6. Regression
checks also cover parent motion, a `Default` override, centimetres/Y-up, clipping
planes, inverse BCF export, and native metadata reimport without double mapping.
Multiple model instances, multiple independent `Default` frames, nonuniform
scale, shear, and reflection produce an explicit error rather than a guessed
camera placement. A changed frame after preview requires a fresh preview.
Native Omniverse viewpoints retain their recorded frame; they are not remapped
as standard BCF source coordinates.

Run `tests/test_bcf_compat.py` with Python, Pillow, and standalone USD libraries.
Set `ISSUES_BCF_SAMPLE` to another location for the same sample archive. The sample
file itself is not stored in the repository.

Schema references: [BCF 2.1 markup](https://github.com/buildingSMART/BCF-XML/blob/release_2_1/Schemas/markup.xsd)
and [BCF 2.1 visualization](https://github.com/buildingSMART/BCF-XML/blob/release_2_1/Schemas/visinfo.xsd).
