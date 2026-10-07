# BCF camera verification, 2026-10-07

Camera review now supports explicit per-viewpoint reference, coordinate and FOV
choices before persistence. See [operator instructions](bcf-21-compatibility.md#camera-review-and-corrections).
This record separates synthetic rendering from the unresolved ACC report.

## Runtime and fixture

The measured runtime was Kit `110.2.0+feature.342835.698af100.gl`, Python
`3.12.13`, OpenUSD `0.25.11`. Verification uses a separate visible Kit process,
the ordinary-copy dependency snapshot and generated scenes/archives.

`tests/test_bcf_camera_workflow.py` contains three selected checks:

- `test_bcf_camera_preview_and_corrected_import` uses a referenced model with a
  translated IFCSITE and a parent rotated 90 degrees. A source-world camera and
  reference-local camera frame the same red cube, green sphere and blue cube.
- `test_bcf_camera_centimetres_y_up` repeats the workflow with centimetres and
  Y-up, exercising axis/unit conversion before the rotated reference placement.
- `test_bcf_camera_preview_releases_native_navigation` switches to another
  camera while preview is open, then checks product/camera cleanup and an
  unrelated parent-layer edit.

The two rendering cases use a 60-degree horizontal BCF 2.1 FOV and an 800 x 600
snapshot. An independently authored USD camera supplies the synthetic source
render. The imported camera must match its world transform within `1e-5`, put
all landmark centers inside the frustum and produce more than 80 pixels of each
landmark color. Normalized pixel centroids must lie within `0.025` of the source
render and within `0.045` of the projected geometric centers. These are framing
checks, not a claim of pixel-identical rendering.

The fixture opens the native file picker, sets its directory/filename and calls
its registered apply handler. It changes real ComboBox value models and invokes
the actual Recalculate, Preview and Apply callbacks. It verifies source snapshot
provider construction, dirty-option gating and empty callback errors. It does
not simulate physical mouse/keyboard input or measure dialog layout.

Cancel must leave issue records and the parent layer unchanged. A default import
is then corrected on reimport; issue/comment/viewpoint identities and original
snapshots survive. Repeating the same corrected import changes no parent-layer
bytes. Exporting and reopening the generated parent USD retains the saved views.
Source USD and BCF bytes remain unchanged.

## Evidence and commands

Run from the isolated development checkout with no other Kit verification
process active:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:OPTIX_CACHE_PATH = Join-Path (Get-Location) 'verification/optix-cache'
./run-verify-kit.ps1 -Case bcf_camera_workflow -DependencyRoot 'C:/Users/StevenGomba/.codex/worktrees/issues-tag-improvements/verification-dependencies' -Visible
```

Add `-TestName test_bcf_camera_preview_and_corrected_import` or
`-TestName test_bcf_camera_preview_releases_native_navigation` to isolate a
failure. The runner writes `verification/results.json`, `progress.json`,
`kit.log`, `stdout.log` and `loaded-extensions.json`. Per-run copies and six
rendered PNGs are retained under `verification/bcf-camera/`.

The successful SDK probe in `verification/bcf-camera/run-22/` reported one pass,
zero failures and no error log lines. It proved session camera binding, exact
prior relationship restoration, root preservation and rendered independent
navigation. The final product-based run in `verification/bcf-camera/run-23/` passed all
three cases, with zero error log lines and natural runner exit 0. Earlier run-10 reported three passes
but had renderer errors, so it does not establish final acceptance.
The inspected final run-23 images are:

- `rotated-metres-z-up-expected.png`
- `rotated-metres-z-up-local-preview.png`
- `rotated-metres-z-up-world-preview.png`
- `rotated-centimetres-y-up-expected.png`
- `rotated-centimetres-y-up-local-preview.png`
- `rotated-centimetres-y-up-world-preview.png`

All six final framing images show the red cube at lower left, green sphere at lower right and blue cube
above them. The orange selection outline on the red cube remains in the preview,
which deliberately preserves selection. The metre and centimetre scenes have
slightly different sphere tessellation, but their landmark framing agrees.

Focused offline commands use real USD with UI/viewport boundary doubles:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = 'verification/python'
& C:/kit-app-template/_build/windows-x86_64/release/kit/python/python.exe tests/test_import_camera_preview.py -v
& C:/kit-app-template/_build/windows-x86_64/release/kit/python/python.exe tests/test_import_camera_review.py -v
& C:/kit-app-template/_build/windows-x86_64/release/kit/python/python.exe tests/test_import_reference.py -v
& C:/kit-app-template/_build/windows-x86_64/release/kit/python/python.exe -m unittest discover -s tests -p test_acc_controller.py -v
```

The latest focused results are 12 preview checks, seven camera-review checks,
eight import-reference checks and 30 controller checks passing. No broad standalone suite was
rerun to avoid unrelated known baseline failures.

## Preview ownership found by native testing

The Kit renderer writes render-product camera relationships and camera exposure
settings after activation. A temporary camera alone therefore polluted the
parent layer even when its creation used a session edit context.

The final preview keeps the viewport's existing RenderProduct. It creates a
unique session camera, copies only audited exposure/autoExposure schemas and
values, and authors that product's camera relationship in session before calling
the camera setter inside the same short edit context. Imported pose, projection
and lens values remain authoritative. User model edits retain their edit target.

Close is synchronous. It restores the prior session relationship only while its
own target opinion remains, preserves independent camera/product navigation and
removes its temporary camera and otherwise empty session specs. Preexisting
relationship list operations are restored exactly when the preview still owns
the camera. A newer navigation choice takes precedence over the old camera
binding; relationship metadata is preserved. Root and model layers are untouched.

The discarded temporary-product approach produced renderer lifecycle errors
that neither drawable notifications nor context frame-completion fences fixed.
A separate viewport also authored a root render product. Those investigations
remain archived; their temporary products, deferred tasks, timeout, and controller
drain changes are absent from the final implementation.

Runs 01-11 had completed Kit reports but hung PowerShell wrappers, which were
interrupted after Kit exited. Later runs returned naturally. The managed sandbox
initially denied OptiX's default AppData cache writes. Necessary runs from run-15
set process-local `OPTIX_CACHE_PATH` to the isolated checkout's
`verification/optix-cache`, as documented by NVIDIA's
[OptiX device-context API](https://raytracing-docs.nvidia.com/optix9/api/group__optix__host__api__device__context.html).
This removed cache errors without changing user settings. Shader compilation
still took roughly three minutes. No GPU fault or abnormal Kit crash occurred. Run-23 still has SDK/environment
warnings: OmniHub retries, AppData lookup, optional MaterialX, skipped Intel GPU,
toolbar root-frame warning before the fixture, and RTX interface acquisition
performance warnings. Zero error lines does not mean a warning-free log.
## ACC limits

Read-only sample inspection found 108 cameras: 21 perspective and 87
orthographic. Ninety-eight have survey-sized positions near X=579,000 and
Y=6,633,000; ten have both horizontal coordinates below 10,000 in magnitude.
These ranges do not establish that the topics belong to one model or identify
their coordinate convention. Four perspective snapshots are nonsquare, so the
explicit horizontal FOV option can change framing without moving the eye.
See [the source investigation](that-open-bcf-camera-research.md).

The affected ACC topic and matching model remain unidentified. The synthetic
fixture verifies explicit correction behavior and visible landmark framing; it
does not reproduce the user's actual ACC snapshot or prove that the reported
location problem is fixed. Camera-only preview also leaves BCF visibility and
clipping unapplied. Export remains BCF 3.0.
