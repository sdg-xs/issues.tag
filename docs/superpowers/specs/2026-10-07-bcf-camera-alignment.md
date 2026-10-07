# BCF camera alignment

## Intent

Make ACC BCF camera imports diagnosable and correctable before persistence. The current importer has one mapping per document; the existing sample contains both near-origin and survey-sized camera positions. This does not prove that they belong to the same model. Preserve the existing mapping by default and require an explicit choice to interpret a camera relative to a model reference.

## Required behavior

- Preserve the original standard BCF camera values and version separately from the converted USD camera. Native Omniverse viewpoints retain their recorded frame.
- Provide a read-only offline camera report and import-review diagnostics. Reports identify topic/viewpoint, original and converted position, projection, reference path, coordinate mode and field-of-view interpretation. Omit image bytes and descriptions from diagnostic output.
- Support per-viewpoint options: original source-world coordinates or reference-local coordinates, an optional reference path, and file-compatible or horizontal legacy perspective FOV. Defaults preserve existing import behavior. Never choose an origin based on coordinate magnitude alone.
- A source-world camera uses the existing original-to-composed reference delta. A reference-local camera uses the selected reference's composed world transform after BCF axis/unit conversion. Transform position, direction, up and clipping planes consistently. Reject nonuniform scale, shear, reflection, invalid options and unresolved reference selections.
- Horizontal FOV correction is explicit and limited to standard BCF 2.1 perspective cameras. BCF 3.0 is vertical. Existing legacy vertical behavior remains the default until exporter-specific evidence establishes otherwise. Orthographic scale is not guessed.
- Reimport with corrected options updates camera/clipping data without duplicating issues, comments or viewpoints or replacing stored snapshots. Native editable Markup blocks a camera/frame change. Unchanged repeated imports are idempotent. Export remains BCF 3.0.
- Import preview shows the source snapshot and can open a camera-only preview in the active viewport before applying. Preview uses a temporary session-layer camera, leaves issue records, source models, selection, visibility and clipping unchanged, and restores the prior camera on close/cancel/apply only while it still owns the preview. Stage replacement, viewport navigation to another camera and extension shutdown must not restore stale state.
- Per-viewpoint options can be changed and the plan rebuilt without reading the archive again. Preserve field-conflict choices that remain valid. Cancel persists nothing; Apply revalidates every chosen coordinate frame and issue baseline before any mutation.
- A selected Kit fixture verifies actual viewport camera placement and visible model landmarks for synthetic world/local, rotated and unit-converted cases. The real ACC sample is inspected read-only; no claim of ACC visual correctness without a matching affected issue and model.

## Global constraints

- Target Kit 110.2.0, Python 3.12.13 and OpenUSD 0.25.11; add no product dependency.
- Issue mutations belong to the parent root layer; referenced model layers remain untouched.
- No source archive or user scene is written, and no user application is closed or operated.
- Keep all development in the isolated feature worktree; do not merge, push or deploy.
- Run only one Kit verification process at a time using the existing ordinary-copy dependency snapshot; never mutate the shared NVIDIA SDK.
- Preserve the original checkout's preexisting changes. Use focused regression checks and independent task reviews.

## Acceptance limits

Numerical identity, internal round trips and schema validity are separate from rendered snapshot alignment. The source-world default is a compatibility choice, not an assertion about all ACC files. Expose ambiguity and retain original evidence rather than guessing. A camera-only preview evaluates placement/framing; it does not reproduce BCF visibility or clipping.
