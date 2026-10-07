# Graph Report - issues.tag  (2026-10-07)

## Corpus Check
- 86 files · ~75,603 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .xsd 6, (none) 1, .toml 1)

## Summary
- 1372 nodes · 3125 edges · 66 communities (48 shown, 18 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 212 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `310457ba`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_lifecycle.py
- bcf.py
- Omniverse issue management specification
- test_acc_workflow.py
- test_bcf_camera_workflow.py
- MarkupAdapter
- IssueService
- Omniverse issue management implementation plan
- test_window_cleanup.py
- commands.py
- Issues for Omniverse
- graphify
- DraftMarkupTests
- IssuesWindow
- Issue viewport design
- IssuesToolbarButton
- IssueStore
- Issues panel design
- BcfCompatibilityTests
- test_markup.py
- ACC issue workflow recovery implementation plan
- ComboModel
- pathlib
- session_api
- ._exercise_native_delivery
- RecallTests
- Pin creation and Markup verification
- ViewportAdapter
- DependencySnapshotTests
- ._operation
- test_acc_ui.py
- verify_kit.py
- controller_sdk
- ACCUITests
- Stability and saved view recall
- test_capture_probe.py
- unittest
- test_issue_editor.py
- Widget
- Recovered ACC issue creation and editing requirements
- ACC workflow verification, 2026-10-01
- Details
- verification_dependencies.py
- Ownership and shared interfaces
- IssuesController
- CameraOptionsTests
- pxr
- BCF camera alignment
- BCF camera verification, 2026-10-07
- viewport.py
- ImportWindow
- logging
- _PlacementClick
- enable_extension
- Implementation verification record
- extension.py
- ._dispatch
- DirtyDetailsDialog
- ImportCameraReviewTests
- frames
- test_creation.py
- test_viewpoints.py
- ImportCameraPreviewTests
- AccBcfTests
- Markup ownership and USD edit targets
- collect

## God Nodes (most connected - your core abstractions)
1. `frames()` - 68 edges
2. `IssuesController` - 57 edges
3. `ACCUITests` - 51 edges
4. `ViewportAdapter` - 50 edges
5. `controller_sdk()` - 43 edges
6. `IssueService` - 39 edges
7. `Omniverse issue management implementation plan` - 39 edges
8. `Status` - 36 edges
9. `enable_extension()` - 33 edges
10. `read_bcf()` - 32 edges

## Surprising Connections (you probably didn't know these)
- `Creation and editing` --references--> `IssueEditSession`  [INFERRED]
  docs/superpowers/specs/2026-10-01-acc-issue-workflow-recovered.md → issues_tag/edit_session.py
- `ACC issue workflow recovery implementation plan` --references--> `IssueEditSession`  [INFERRED]
  docs/superpowers/plans/2026-10-01-acc-issue-workflow-recovery.md → issues_tag/edit_session.py
- `Task 3: Wire creation, editing, and evidence ownership` --references--> `IssueEditSession`  [INFERRED]
  docs/superpowers/plans/2026-10-01-acc-issue-workflow-recovery.md → issues_tag/edit_session.py
- `Ownership and shared interfaces` --references--> `IssuesExtension`  [INFERRED]
  docs/superpowers/plans/2026-10-01-acc-issue-workflow-recovery.md → issues_tag/extension.py
- `Task 3: Import-review controls and temporary camera preview` --references--> `ImportWindow`  [INFERRED]
  docs/superpowers/plans/2026-10-07-bcf-camera-alignment.md → issues_tag/import_window.py

## Import Cycles
- None detected.

## Communities (66 total, 18 thin omitted)

### Community 0 - "test_lifecycle.py"
Cohesion: 0.06
Nodes (21): gc, finish(), EvidenceCaptureTests, window(), Settings, _failure(), lifecycle_sdk(), destroy() (+13 more)

### Community 1 - "bcf.py"
Cohesion: 0.06
Nodes (81): base64, carb_settings, datetime, apply_import(), BcfDocument, _component(), Conflict, export_view() (+73 more)

### Community 2 - "Omniverse issue management specification"
Cohesion: 0.11
Nodes (18): Acceptance criteria, BCF file exchange, Core workflow, Delivery and review, Omniverse issue management specification, Further Notes, Implementation Decisions, Issue interactions and lifecycle (+10 more)

### Community 3 - "test_acc_workflow.py"
Cohesion: 0.19
Nodes (28): _action(), _arrow(), _button(), _close(), _comment_evidence_trace(), _create(), _discard(), _dock_primary_viewport() (+20 more)

### Community 4 - "test_bcf_camera_workflow.py"
Cohesion: 0.06
Nodes (45): difflib, Runtime and fixture, BCF camera alignment Implementation Plan, File responsibilities, Global Constraints, Plan self-review, Review Focus, Task 1: Retain source camera provenance and provide offline diagnostics (+37 more)

### Community 5 - "MarkupAdapter"
Cohesion: 0.11
Nodes (11): clean_evidence_ui(), overlapping_windows(), Temporarily suppress viewport overlays without changing the application's UI., MarkupAdapter, _native_camera_matches(), Recall an existing native camera without entering Markup review or editing., Evaluate the vendor's attribute-copy result without changing the live scene., Delete this adapter's unsaved native draft in its originating scene. (+3 more)

### Community 6 - "IssueService"
Cohesion: 0.07
Nodes (9): IssueService, operation(), operation(), operation(), migrated_operation(), setter, setter, record() (+1 more)

### Community 7 - "Omniverse issue management implementation plan"
Cohesion: 0.13
Nodes (15): Omniverse issue management implementation plan, File structure, Global Constraints, Local evidence and prerequisites, Plan review and execution handoff, Review Focus, Shared interfaces, Task 1: Isolated runtime and extension activation (+7 more)

### Community 8 - "test_window_cleanup.py"
Cohesion: 0.19
Nodes (8): inspect, leaf_errors(), make_window(), Standalone destructor checks using SDK boundary stubs, without Kit imports., Resource, Service, window_type(), WindowCleanupTests

### Community 9 - "commands.py"
Cohesion: 0.31
Nodes (5): copy_issues(), Undo only issue records, preserving unrelated root-layer opinions., restore_issues(), UpdateIssuesCommand, omni_kit_commands

### Community 10 - "Issues for Omniverse"
Cohesion: 0.17
Nodes (8): Section Box acceptance verification, BCF exchange, Current boundaries, Issues for Omniverse, Install and use, Normal scene Save, Verification, Parent USD ownership

### Community 13 - "IssuesWindow"
Cohesion: 0.08
Nodes (6): _dock_when_ready(), IssueDetailsWindow, IssuesWindow, IssueTypesWindow, test_panel_manage_types_create_delete_and_undo(), test_panel_reports_unsupported_scene_schema()

### Community 14 - "Issue viewport design"
Cohesion: 0.25
Nodes (8): Issue viewport design, Pin eligibility, Scoped source identity, Session-layer restoration, Stage-safe picking, Unresolved component retention, Independent pin anchors, Saved review context

### Community 16 - "IssueStore"
Cohesion: 0.26
Nodes (3): encode(), IssueStore, Materialize derived legacy fields once, inside the caller's undo command.

### Community 17 - "Issues panel design"
Cohesion: 0.14
Nodes (14): BCF XML 3.0, Bounded ZIP parsing, Supported BCF file profile, Native viewpoint metadata, Three-way import baseline, Behavior and accessibility, Issues panel design, Explicit import preview (+6 more)

### Community 19 - "test_markup.py"
Cohesion: 0.08
Nodes (33): Cleanup-wave comparison checkpoint, Crash investigation, 2026-09-30, Delivered-frame gate verification, Focused recurrence at 13:47:30 UTC, Isolated follow-up verification, Preserved work and evidence, Private rendered run at 13:34:10 UTC, Recurrence after delivered-frame gate at 14:40 UTC (+25 more)

### Community 20 - "ACC issue workflow recovery implementation plan"
Cohesion: 0.29
Nodes (5): ACC issue workflow recovery implementation plan, Global constraints, Recovery record, Review focus, Self-review and handoff

### Community 22 - "pathlib"
Cohesion: 0.12
Nodes (20): argparse, contextlib, io, Editable evidence through NVIDIA's supported Markup Core API., json, math, os, pathlib (+12 more)

### Community 23 - "session_api"
Cohesion: 0.13
Nodes (4): AccPersistenceTests, persistence_sdk(), session_api(), EditSessionTests

### Community 26 - "Pin creation and Markup verification"
Cohesion: 0.50
Nodes (3): Limits, Pin creation and Markup verification, Results

### Community 27 - "ViewportAdapter"
Cohesion: 0.09
Nodes (8): Live viewport remains impaired, Reopened scene with stale cyan pins, Verification state, ViewportAdapter, test_imported_metadata_does_not_invalidate_coordinate_frame(), test_placement_cancel_clears_prompt_without_creating_issue(), test_restore_clipping_and_viewport_camera_isolation(), test_surface_pick_and_placement_lifecycle()

### Community 29 - "._operation"
Cohesion: 0.11
Nodes (6): add(), add(), annotate(), focus(), open_view(), reattach()

### Community 30 - "test_acc_ui.py"
Cohesion: 0.08
Nodes (18): ast, Combo, FillPolicy, ImageWithProvider, IwpFillPolicy, panel_types(), Enum, str (+10 more)

### Community 31 - "verify_kit.py"
Cohesion: 0.14
Nodes (16): get_runtime_service(), service_for_new_scene(), test_failed_issue_transaction_has_no_partial_records(), test_issue_comment_status_survive_reopen(), test_issue_undo_preserves_unrelated_scene_edits(), test_listeners_observe_complete_records(), test_root_layer_ownership_and_read_only(), test_unsaved_state_and_next_reviewer() (+8 more)

### Community 32 - "controller_sdk"
Cohesion: 0.06
Nodes (9): controller_sdk(), capture(), finish(), ControllerTests, place(), fail(), NativeCallbackDispatchTests, start() (+1 more)

### Community 33 - "ACCUITests"
Cohesion: 0.06
Nodes (3): ACCUITests, find(), dispatch()

### Community 34 - "Stability and saved view recall"
Cohesion: 0.40
Nodes (4): Progress, Sequence and evidence, Shared interfaces and ownership, Stability and saved view recall

### Community 35 - "test_capture_probe.py"
Cohesion: 0.20
Nodes (19): _cancel_native_capture(), caller(), _markup_prelude_then_native_cancel(), _milestone(), _native_capture(), _native_probe(), _new_scene(), _prepare_camera() (+11 more)

### Community 36 - "unittest"
Cohesion: 0.15
Nodes (20): asyncio, dataclasses, importlib, importlib_util, Title/type exchange and repeat imports through real project records., Controller transitions with real USD transactions and controlled native…, Offline staged Save and migration checks using real USD and issue commands., Explicit camera corrections against real BCF parsing and USD composition. (+12 more)

### Community 37 - "test_issue_editor.py"
Cohesion: 0.27
Nodes (4): editor_type(), IssueEditorTests, Offline native-editor behavior checks without importing or replacing Kit…, StringModel

### Community 39 - "Recovered ACC issue creation and editing requirements"
Cohesion: 0.20
Nodes (10): Acceptance workflow, Confirmed intent, Creation and editing, Integration policy for completing the recovered work, Issue list, Recovered ACC issue creation and editing requirements, Recovery status and evidence, Requirements inferred from the unfinished implementation (+2 more)

### Community 40 - "ACC workflow verification, 2026-10-01"
Cohesion: 0.22
Nodes (7): ACC workflow execution decisions, 2026-10-01, Decision record, ACC workflow verification, 2026-10-01, Actual results, Artifacts and inspection, Authored coverage, Lead-run commands

### Community 42 - "verification_dependencies.py"
Cohesion: 0.36
Nodes (8): shutil, stat, main(), prepare_snapshot(), qualify_extension_paths(), Prepare ordinary dependency copies for verification, without starting Kit., _reject_link(), validate_snapshot()

### Community 43 - "Ownership and shared interfaces"
Cohesion: 0.27
Nodes (5): Ownership and shared interfaces, Task 1: Recover staged records, USD migration, and BCF fields, Task 2: Recover separate issue list and details panels, Task 3: Wire creation, editing, and evidence ownership, Task 4: Independent review and complete Composer verification

### Community 45 - "CameraOptionsTests"
Cohesion: 0.21
Nodes (4): CameraOptionsTests, CopyEvidenceTests, capture(), discard()

### Community 46 - "pxr"
Cohesion: 0.21
Nodes (16): hashlib, attachment_state(), geometry_digest(), Match source identities within a reference instance, never by proximity., Resolution, resolve_element(), Separate dockable issue list and staged details panels., omni_kit_app (+8 more)

### Community 47 - "BCF camera alignment"
Cohesion: 0.33
Nodes (5): Acceptance limits, BCF camera alignment, Global constraints, Intent, Required behavior

### Community 48 - "BCF camera verification, 2026-10-07"
Cohesion: 0.14
Nodes (11): Camera review and corrections, Initial BCF import sample, ACC limits, BCF camera verification, 2026-10-07, Evidence and commands, Preview ownership found by native testing, Implications for issues.tag and ACC, Local sample evidence (+3 more)

### Community 49 - "viewport.py"
Cohesion: 0.24
Nodes (5): world_anchor(), matrix(), pin_is_visible(), Review camera state and surface anchors for one native viewport., _ViewportItem

### Community 50 - "ImportWindow"
Cohesion: 0.09
Nodes (12): copy, ViewpointImportOptions, camera_diagnostics(), Read-only camera evidence for BCF import review and offline reports., Pair retained source evidence with converted cameras by viewpoint UUID., ImportWindow, Review imported BCF field conflicts before applying the import plan., Resolve staged changes before closing details or switching issues. (+4 more)

### Community 52 - "_PlacementClick"
Cohesion: 0.25
Nodes (5): _PinManipulator, on_build(), _PlacementClick, on_ended(), Build a native scene gesture without requiring a global input hook.

### Community 53 - "enable_extension"
Cohesion: 0.17
Nodes (15): flatten(), omni_kit_viewport_utility, omni_usd, test_destroy_during_creation_callback_releases_capture(), cancel_and_destroy(), test_extension_activation_and_shutdown(), test_markup_compatibility(), test_native_pin_registry_cleanup_across_reload_and_reopen() (+7 more)

### Community 54 - "Implementation verification record"
Cohesion: 0.29
Nodes (7): Crash investigation, Decisions and costs, Follow-up development and review, Implementation verification record, Independent review, Open acceptance gates, Runtime evidence

### Community 55 - "extension.py"
Cohesion: 0.13
Nodes (8): ReferenceSelectionRequired, IssuesExtension, Lifecycle and the Issues menu entry., Manager-owned registration; pending work belongs to the detached controller., ReferenceSelectionWindow, omni_ext, omni_kit_menu_utils, ValueError

### Community 59 - "frames"
Cohesion: 0.27
Nodes (11): _disable_runtime(), exercise_mouse_navigation(), navigate(), exercise_saved_view(), preview_native_saved_view_allows_mouse_navigation(), Native saved Markup camera recall without rendering a thumbnail., saved_scene_content(), test_saved_native_issue_view_recalls_camera_without_annotation() (+3 more)

### Community 60 - "test_creation.py"
Cohesion: 0.28
Nodes (7): test_acc_create_cancel_removes_native_draft(), test_acc_create_save_clean_native_evidence(), exercise_creation(), edit_draft(), Lead-controlled rendered pin, native Markup, save and cancel workflow., test_cancel_pin_markup_draft_leaves_no_issue(), test_pin_opens_markup_and_saves_annotated_initial_view()

### Community 61 - "test_viewpoints.py"
Cohesion: 0.33
Nodes (11): make_anchor(), reference_for_prim(), preview_issue_pins(), require_viewport(), test_completed_pick_cannot_cross_scene_close(), test_overlay_tracks_scene_and_stage_scope(), test_pin_cache_tracks_camera_parent_geometry(), test_pin_filtering_and_issue_access() (+3 more)

### Community 68 - "Markup ownership and USD edit targets"
Cohesion: 0.40
Nodes (5): Markup ownership and USD edit targets, Runtime coverage, Selecting saved evidence without entering annotation, Why the root target remains selected during drawing, thumbnail()

## Knowledge Gaps
- **94 isolated node(s):** `Decision record`, `Authored coverage`, `Lead-run commands`, `Artifacts and inspection`, `Actual results` (+89 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 421 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Omniverse issue management implementation plan` connect `Omniverse issue management implementation plan` to `bcf.py`, `Omniverse issue management specification`, `commands.py`, `Issues for Omniverse`, `pxr`, `viewport.py`, `ImportWindow`, `test_markup.py`, `enable_extension`, `pathlib`, `extension.py`, `test_viewpoints.py`, `verify_kit.py`?**
  _High betweenness centrality (0.154) - this node is a cross-community bridge._
- **Why does `Omniverse issue management specification` connect `Omniverse issue management specification` to `Stability and saved view recall`, `Omniverse issue management implementation plan`, `ACC workflow verification, 2026-10-01`, `Issues for Omniverse`, `Issue viewport design`, `Issues panel design`, `ACC issue workflow recovery implementation plan`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `IssuesController` connect `IssuesController` to `test_lifecycle.py`, `bcf.py`, `test_bcf_camera_workflow.py`, `MarkupAdapter`, `IssueService`, `Ownership and shared interfaces`, `IssuesWindow`, `IssuesToolbarButton`, `ImportWindow`, `extension.py`, `._dispatch`, `DirtyDetailsDialog`, `ViewportAdapter`, `._operation`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `IssuesController` (e.g. with `ReferenceSelectionRequired` and `IssueEditSession`) actually correct?**
  _`IssuesController` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `ViewportAdapter` (e.g. with `Reopened scene with stale cyan pins` and `IssuesController`) actually correct?**
  _`ViewportAdapter` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `controller_sdk()` (e.g. with `begin()` and `capture()`) actually correct?**
  _`controller_sdk()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Decision record`, `Authored coverage`, `Lead-run commands` to the rest of the system?**
  _94 weakly-connected nodes found - possible documentation gaps or missing edges._