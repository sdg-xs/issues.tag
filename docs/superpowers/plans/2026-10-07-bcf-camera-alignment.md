# BCF camera alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make ACC BCF camera placement diagnosable and explicitly correctable before importing records.

**Architecture:** Retain raw camera provenance alongside the normalized USD camera. Extend the existing preview plan with per-viewpoint choices and frame signatures, then expose those choices and a temporary camera-only preview in the existing import window. Keep the parser, coordinate mapping and UI responsibilities separate.

**Tech Stack:** Python dataclasses, OpenUSD, existing omni.ui and viewport APIs, unittest and the existing isolated Kit verifier.

**Spec:** `docs/superpowers/specs/2026-10-07-bcf-camera-alignment.md`

## Global Constraints

- Target Kit 110.2.0, Python 3.12.13 and OpenUSD 0.25.11; add no product dependency.
- Issue mutations belong to the parent root layer; referenced model layers remain untouched.
- No source archive or user scene is written, and no user application is closed or operated.
- Keep all development in the isolated feature worktree; do not merge, push or deploy.
- Run only one Kit verification process at a time using the existing ordinary-copy dependency snapshot; never mutate the shared NVIDIA SDK.
- Preserve the original checkout's preexisting changes. Use focused regression checks and independent task reviews.

## Review Focus

- Mixed coordinate ranges must remain observations; test that reporting never automatically changes a camera.
- A model or scene changed after preview must reject Apply atomically; test every selected viewpoint's frame.
- Corrected repeated imports must preserve existing snapshots, comments and identities; test remap, projection change and repeat.
- Native Markup and native viewpoints must not receive unsupported corrections; test rejection before mutation.
- Preview close, stage replacement and changed camera ownership must preserve current user state; test each cleanup path.

## File responsibilities

`bcf.py` owns archive parsing and atomic import planning/apply. `bcf_coordinates.py` owns reference transforms and projection choices. New `bcf_diagnostics.py` owns camera reports. New `import_camera_preview.py` owns a temporary viewport camera. `import_window.py` owns reviewer controls; `extension.py` binds them to the current scene. New offline tests cover each seam and `test_bcf_camera_workflow.py` supplies a selected Kit case.

### Task 1: Retain source camera provenance and provide offline diagnostics

**Files:** Modify `issues_tag/bcf.py`; create `issues_tag/bcf_diagnostics.py`, `tools/bcf_camera_report.py`, `tests/test_bcf_diagnostics.py`.

**Interfaces:** Produce `camera_diagnostics(source_document, converted_document=None) -> tuple[dict, ...]`. Rows use keys `viewpoint_id`, `topic_ids`, `source_position`, `converted_position`, `projection`, `source_version`, `reference_path`, `coordinate_mode`, `fov_mode`, `source_fov_degrees`, `source_aspect_ratio`. Missing camera position/FOV is null. Source metadata lives under coordinate-frame key `bcf_source_camera`, a JSON-safe dict containing `version`, `position`, `direction`, `up`, `field_of_view`, `view_to_world_scale`, `aspect_ratio`; populate only standard cameras. No new required record fields.

- [ ] **Step 1: Write failing tests.** `test_source_camera_survives_mapping_and_native_roundtrip` checks exact original vectors, version 2.1/3.0 and field-of-view metadata survive conversion/export-native-readback. `test_report_does_not_mutate_or_infer_origin` checks mixed positions `(12,-4,1)` and `(579400,6633600,180)` stay unchanged and report rows omit snapshots/descriptions. `test_snapshot_only_and_missing_snapshot_report` checks null positions and existing warning behavior.
- [ ] **Step 2: Run RED.** `& 'C:/kit-app-template/_build/windows-x86_64/release/kit/python/python.exe' tests/test_bcf_diagnostics.py -v`. Assert missing provenance/report behavior, not a dependency error.
- [ ] **Step 3: Implement provenance and reports.** Follow existing package-loading test conventions. CLI accepts archive path, optional `--scene` and `--reference`, produces JSON to stdout, reads USD scene without saving, and reports existing default mapping when requested. Use existing verification Python paths to locate Pillow/USD; do not install dependencies or import the Kit extension initializer.
- [ ] **Step 4: Verify GREEN and sample report.** Run the new tests plus `tests/test_bcf_compat.py`. Run the CLI against the existing Downloads sample and saved SOL scene. Capture counts/ranges in the task report without dumping image bytes. Document that numeric mapping does not establish visual correctness.
- [ ] **Step 5: Commit.** Commit only this task's product, tool and test files with `feat: retain BCF source cameras and add import diagnostics`.

### Task 2: Explicit per-viewpoint coordinate and legacy FOV options

**Files:** Modify `issues_tag/bcf_coordinates.py`, `issues_tag/bcf.py`, `issues_tag/store.py`; create `tests/test_bcf_camera_options.py`; extend `tests/test_bcf_compat.py` only where necessary.

**Interfaces:** Produce frozen `ViewpointImportOptions(reference_path: str | None = None, coordinate_mode: str = 'source_world', fov_mode: str = 'file')` in `bcf_coordinates.py`. Allowed coordinate modes are `source_world`, `reference_local`; allowed FOV modes are `file`, `horizontal`. Extend `stage_mapping(stage, *, reference_path=None, coordinate_mode='source_world')`; preserve its existing four-item mapping tuple. Extend `plan_import(document, store, *, reference_path=None, viewpoint_options=None)`, with a dict keyed by viewpoint ID. Retain `ImportPlan.frame_signature/reference_path` compatibility and add immutable per-viewpoint frame/options signatures and `source_document` needed for replanning/diagnostics. Persist effective options in coordinate-frame keys `bcf_coordinate_mode` and `bcf_fov_mode`. Produce `IssueStore.list_viewpoints(issue_id) -> tuple[ViewpointRecord, ...]` for per-issue saved-view enumeration; export_document retains all saved views and viewpoint_topics ownership.

- [ ] **Step 1: Write failing behavior tests.** A source site translation `(579400,6633600,100)` maps local camera `(12,-4,1)` to `(579412,6633596,101)` only with explicit reference-local mode; a source-world survey camera remains unchanged when source/composed placement agrees. Include rotated parent, centimetres/Y-up, selected reference and clipping-plane assertions. Standard 2.1 camera FOV `53.13010235415598`, aspect `1502/891`, explicit horizontal mode yields that horizontal angle; file mode retains previous behavior. Reject horizontal mode for 3.0/native/orthographic inputs and unknown keys/modes.
- [ ] **Step 2: Run RED.** Run `tests/test_bcf_camera_options.py -v` with Kit Python and prove missing options behavior.
- [ ] **Step 3: Implement mapping and atomic correction.** Use raw source metadata from Task 1, avoiding accumulated conversions. Validate options before mutation. Capture/revalidate all effective mapping signatures, with stage identity checked before traversing a replacement stage. Reimport corrections preserve existing snapshots and IDs, reject changed native editable Markup, count changed viewpoints, and remain idempotent. Support changing selected reference and FOV independently. Unspecified options preserve existing behavior.
- [ ] **Step 4: Verify GREEN.** Run the options, compatibility and diagnostics tests. Add stale-preview tests where only a nondefault selected reference moves, unknown options, native camera protection, and correction/repeat/save/reopen/export/readback assertions.
- [ ] **Step 5: Commit.** `feat: support explicit BCF camera frame and projection corrections`.

### Task 3: Import-review controls and temporary camera preview

**Files:** Modify `issues_tag/import_window.py`, `issues_tag/extension.py`; create `issues_tag/import_camera_preview.py`, `tests/test_import_camera_preview.py`, `tests/test_import_camera_review.py`; extend `tests/test_import_reference.py` if necessary.

**Interfaces:** Consume Task 1 diagnostics and Task 2 options/planning. Extend `ImportWindow` with optional callbacks for replanning, camera preview and closing preview while keeping existing callers valid. New `ImportCameraPreview(viewport, stage)` provides `show(viewpoint)` and idempotent `close()`. The controller owns it and dialog shutdown closes it. Use a unique temporary camera in the session layer; do not overwrite an existing camera or restore the entire session layer.

- [ ] **Step 1: Write failing tests.** Real USD tests assert preview leaves parent/source layers, records, selection and clipping unchanged, restores the original camera, removes its temporary prim, preserves newer camera ownership, and safely closes after stage replacement. UI boundary tests drive viewpoint selection, reference-local/source-world choice, horizontal/file choice, replan, preview, Cancel and Apply callbacks. They assert field choices survive replanning, camera-less evidence remains accessible, failed replan leaves the valid plan intact, and scene generation change blocks callbacks.
- [ ] **Step 2: Run RED.** Run `tests/test_import_camera_preview.py -v` and `tests/test_import_camera_review.py -v` with Kit Python; distinguish missing behavior from UI double limitations.
- [ ] **Step 3: Implement controls and cleanup.** Show selected topic/viewpoint identity, source snapshot using the existing ByteImageProvider pattern, original/converted position and human-readable reference/mode. Reviewer labels: `Source world`, `Relative to reference`, `File interpretation`, `Horizontal FOV (BCF 2.1)`, `Preview camera`, and `Camera only: visibility and clipping are unchanged.` Expose existing IFCSITE reference paths; do not infer origin. Replan from source_document in memory and replace a plan only on success. Preserve applicable conflict choices. Disable correction/apply after success. Close preview on cancel, apply, window close and extension shutdown. Preview errors stay visible and do not import records.
- [ ] **Step 4: Verify GREEN.** Run both new test modules, import-reference tests, relevant controller/lifecycle tests and camera-options tests. Explicitly report offline UI doubles as boundary verification, not rendered acceptance.
- [ ] **Step 5: Commit.** `feat: preview and correct BCF cameras before import`.

### Task 4: Rendered camera acceptance and operator documentation

**Files:** Create `tests/test_bcf_camera_workflow.py`, `docs/bcf-camera-verification-2026-10-07.md`; modify `docs/bcf-21-compatibility.md`, `README.md` with concise current instructions.

**Interfaces:** Consume the finished import controls and preview. Use existing `verify_kit.py` case selection `bcf_camera_workflow`, existing service/viewport fixtures and snapshot APIs; no new launcher/dependency infrastructure.

- [ ] **Step 1: Add the selected runtime fixture.** `test_bcf_camera_preview_and_corrected_import` creates a small referenced model with visible distinctive geometry, world/local BCF cameras and a rotated instance. Drive actual import controls, open the temporary preview, verify camera world pose and projected landmark visibility, capture a rendered artifact, Cancel with no saved records, then correct/apply/reimport and assert persisted pose and no duplicates. Check native UI build errors and teardown ownership. Add source-world and centimetres/Y-up cases where they exercise a distinct boundary.
- [ ] **Step 2: Run the selected case.** `./run-verify-kit.ps1 -Case bcf_camera_workflow -DependencyRoot 'C:/Users/StevenGomba/.codex/worktrees/issues-tag-improvements/verification-dependencies' -Visible`. Only run with no other Kit verification process active. If dependencies are missing, GPU fault occurs or process exits abnormally, preserve evidence, reduce to the failing selected function, and record the precise limit without broad reruns. Do not operate on the user's application.
- [ ] **Step 3: Address fixture failures and document acceptance.** Use TDD for product defects, report RED/GREEN evidence. Documentation distinguishes observed ACC coordinate ranges, explicit choices, synthetic rendered acceptance and still-unverified actual ACC snapshot alignment. Include exact offline/Kit commands and artifact paths. Do not claim the user's specific location bug is fixed without reproducing it.
- [ ] **Step 4: Commit.** `test: verify BCF camera preview and corrected import in Kit`.

## Plan self-review

The spec's provenance/reporting requirements map to Task 1, correction/idempotence/atomicity to Task 2, reviewer controls and preview ownership to Task 3, and rendered acceptance/documentation to Task 4. Interfaces preserve existing default call sites. Every review-focus failure has an owning task test. User authorization explicitly requests planning followed by execution; do not add another approval checkpoint.
