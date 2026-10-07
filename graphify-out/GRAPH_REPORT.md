# Graph Report - issues.tag  (2026-10-07)

## Corpus Check
- 86 files · ~76,007 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .xsd 6, (none) 1, .toml 1)

## Summary
- 1378 nodes · 3139 edges · 68 communities (49 shown, 19 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 212 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4159ea78`
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
- Status
- Issues for Omniverse
- graphify
- DraftMarkupTests
- IssuesWindow
- Issue viewport design
- .on_startup
- IssueStore
- Issues panel design
- BcfCompatibilityTests
- test_markup.py
- plan_import
- ComboModel
- verification_dependencies.py
- session_api
- ._exercise_native_delivery
- RecallTests
- Pin creation and Markup verification
- frames
- DependencySnapshotTests
- IssuesController
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
- pathlib
- IssueEditSession
- ._finish_annotation
- CameraOptionsTests
- make_anchor
- BCF camera alignment
- BCF camera verification, 2026-10-07
- viewport.py
- ImportWindow
- logging
- Crash investigation, 2026-09-30
- enable_extension
- Implementation verification record
- extension.py
- ._dispatch
- DirtyDetailsDialog
- ImportCameraReviewTests
- test_native_recall.py
- test_ui.py
- replace_progress
- ImportCameraPreviewTests
- IssuesExtension
- markup-lifecycle.md
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
- `Reopened scene with stale cyan pins` --references--> `ViewportAdapter`  [INFERRED]
  docs/crash-investigation-2026-09-30.md → issues_tag/viewport.py
- `Ownership and shared interfaces` --references--> `IssuesExtension`  [INFERRED]
  docs/superpowers/plans/2026-10-01-acc-issue-workflow-recovery.md → issues_tag/extension.py
- `Task 3: Import-review controls and temporary camera preview` --references--> `ImportWindow`  [INFERRED]
  docs/superpowers/plans/2026-10-07-bcf-camera-alignment.md → issues_tag/import_window.py
- `Focused recurrence at 13:47:30 UTC` --references--> `test_creation_cancellation_then_scene_replacement_repeated()`  [INFERRED]
  docs/crash-investigation-2026-09-30.md → tests/test_markup.py

## Import Cycles
- None detected.

## Communities (68 total, 19 thin omitted)

### Community 0 - "test_lifecycle.py"
Cohesion: 0.06
Nodes (21): gc, finish(), EvidenceCaptureTests, window(), Settings, _failure(), lifecycle_sdk(), destroy() (+13 more)

### Community 1 - "bcf.py"
Cohesion: 0.18
Nodes (24): datetime, _component(), _date(), _finite(), _guid(), _import_date(), _import_status(), _native_view() (+16 more)

### Community 2 - "Omniverse issue management specification"
Cohesion: 0.11
Nodes (18): Acceptance criteria, BCF file exchange, Core workflow, Delivery and review, Omniverse issue management specification, Further Notes, Implementation Decisions, Issue interactions and lifecycle (+10 more)

### Community 3 - "test_acc_workflow.py"
Cohesion: 0.17
Nodes (29): _action(), _arrow(), _button(), _close(), _comment_evidence_trace(), _create(), _disable_runtime(), _discard() (+21 more)

### Community 4 - "test_bcf_camera_workflow.py"
Cohesion: 0.08
Nodes (29): difflib, Runtime and fixture, BCF camera alignment Implementation Plan, File responsibilities, Global Constraints, Plan self-review, Review Focus, Task 1: Retain source camera provenance and provide offline diagnostics (+21 more)

### Community 5 - "MarkupAdapter"
Cohesion: 0.11
Nodes (11): clean_evidence_ui(), overlapping_windows(), Temporarily suppress viewport overlays without changing the application's UI., MarkupAdapter, _native_camera_matches(), Recall an existing native camera without entering Markup review or editing., Evaluate the vendor's attribute-copy result without changing the live scene., Delete this adapter's unsaved native draft in its originating scene. (+3 more)

### Community 6 - "IssueService"
Cohesion: 0.07
Nodes (9): IssueService, operation(), operation(), operation(), migrated_operation(), setter, setter, record() (+1 more)

### Community 7 - "Omniverse issue management implementation plan"
Cohesion: 0.12
Nodes (15): Omniverse issue management implementation plan, File structure, Global Constraints, Local evidence and prerequisites, Plan review and execution handoff, Review Focus, Shared interfaces, Task 1: Isolated runtime and extension activation (+7 more)

### Community 8 - "test_window_cleanup.py"
Cohesion: 0.19
Nodes (8): inspect, leaf_errors(), make_window(), Standalone destructor checks using SDK boundary stubs, without Kit imports., Resource, Service, window_type(), WindowCleanupTests

### Community 9 - "Status"
Cohesion: 0.22
Nodes (17): base64, BcfDocument, A scene-bound issue draft. Nothing in this object writes USD., Anchor, CommentRecord, IssueRecord, Enum, str (+9 more)

### Community 10 - "Issues for Omniverse"
Cohesion: 0.25
Nodes (7): BCF exchange, Current boundaries, Issues for Omniverse, Install and use, Normal scene Save, Verification, Parent USD ownership

### Community 13 - "IssuesWindow"
Cohesion: 0.08
Nodes (7): Task 2: Recover separate issue list and details panels, _dock_when_ready(), IssueDetailsWindow, IssuesWindow, IssueTypesWindow, test_panel_manage_types_create_delete_and_undo(), test_panel_reports_unsupported_scene_schema()

### Community 14 - "Issue viewport design"
Cohesion: 0.25
Nodes (8): Issue viewport design, Pin eligibility, Scoped source identity, Session-layer restoration, Stage-safe picking, Unresolved component retention, Independent pin anchors, Saved review context

### Community 16 - "IssueStore"
Cohesion: 0.12
Nodes (11): carb_settings, copy_issues(), Undo only issue records, preserving unrelated root-layer opinions., restore_issues(), UpdateIssuesCommand, Scene-scoped issue actions and notifications., encode(), IssueStore (+3 more)

### Community 17 - "Issues panel design"
Cohesion: 0.14
Nodes (14): BCF XML 3.0, Bounded ZIP parsing, Supported BCF file profile, Native viewpoint metadata, Three-way import baseline, Behavior and accessibility, Issues panel design, Explicit import preview (+6 more)

### Community 19 - "test_markup.py"
Cohesion: 0.16
Nodes (20): Focused recurrence at 13:47:30 UTC, Timeline, adapter_for(), _capture_cycle_phase(), test_annotated_comment_reopens_editably(), test_annotation_rejects_overlapping_ownership(), test_annotation_releases_navigation(), test_capture_camera_matches_view_after_markup_activation() (+12 more)

### Community 20 - "plan_import"
Cohesion: 0.21
Nodes (14): Conflict, export_view(), import_view(), Map standard BCF world coordinates through a composed USD reference., Rebuild the standard projection and pose from retained archive values., ReferenceSelectionRequired, source_view(), stage_mapping() (+6 more)

### Community 22 - "verification_dependencies.py"
Cohesion: 0.15
Nodes (14): argparse, json, os, shutil, stat, tempfile, Portable recall reuses the primary perspective camera without changing saved…, Report source BCF cameras and optional default USD mapping without saving… (+6 more)

### Community 23 - "session_api"
Cohesion: 0.10
Nodes (6): AccBcfTests, AccPersistenceTests, persistence_sdk(), session_api(), EditSessionTests, Draft changes preserve saved records and evidence until details Save.

### Community 26 - "Pin creation and Markup verification"
Cohesion: 0.50
Nodes (3): Limits, Pin creation and Markup verification, Results

### Community 27 - "frames"
Cohesion: 0.11
Nodes (16): ViewportAdapter, preview_issue_pins(), preview_native_gesture_placement(), Visible acceptance: a native mouse event must complete surface placement., require_viewport(), test_completed_pick_cannot_cross_scene_close(), test_imported_metadata_does_not_invalidate_coordinate_frame(), test_overlay_tracks_scene_and_stage_scope() (+8 more)

### Community 29 - "IssuesController"
Cohesion: 0.19
Nodes (3): IssuesController, add(), add()

### Community 30 - "test_acc_ui.py"
Cohesion: 0.08
Nodes (17): Combo, FillPolicy, ImageWithProvider, IwpFillPolicy, panel_types(), Enum, str, Native UI boundary doubles exercise real panel code without a Kit process. (+9 more)

### Community 31 - "verify_kit.py"
Cohesion: 0.19
Nodes (12): service_for_new_scene(), test_failed_issue_transaction_has_no_partial_records(), test_issue_comment_status_survive_reopen(), test_issue_undo_preserves_unrelated_scene_edits(), test_listeners_observe_complete_records(), test_root_layer_ownership_and_read_only(), test_unsaved_state_and_next_reviewer(), test_viewpoint_lookup_does_not_walk_building_geometry() (+4 more)

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
Cohesion: 0.19
Nodes (20): _cancel_native_capture(), caller(), _markup_prelude_then_native_cancel(), _milestone(), _native_capture(), _native_probe(), _new_scene(), _prepare_camera() (+12 more)

### Community 36 - "unittest"
Cohesion: 0.13
Nodes (25): contextlib, dataclasses, importlib, io, Temporary viewport camera for reviewing an import without recalling evidence…, pil, subprocess, sys (+17 more)

### Community 37 - "test_issue_editor.py"
Cohesion: 0.24
Nodes (5): ast, editor_type(), IssueEditorTests, Offline native-editor behavior checks without importing or replacing Kit…, StringModel

### Community 39 - "Recovered ACC issue creation and editing requirements"
Cohesion: 0.20
Nodes (10): Acceptance workflow, Confirmed intent, Creation and editing, Integration policy for completing the recovered work, Issue list, Recovered ACC issue creation and editing requirements, Recovery status and evidence, Requirements inferred from the unfinished implementation (+2 more)

### Community 40 - "ACC workflow verification, 2026-10-01"
Cohesion: 0.22
Nodes (7): ACC workflow execution decisions, 2026-10-01, Decision record, ACC workflow verification, 2026-10-01, Actual results, Artifacts and inspection, Authored coverage, Lead-run commands

### Community 42 - "pathlib"
Cohesion: 0.20
Nodes (10): asyncio, importlib_util, Editable evidence through NVIDIA's supported Markup Core API., math, pathlib, pxr, Offline ownership regression; framework events stand in for native render…, Evidence keeps render/Markup content and restores controls on every exit. (+2 more)

### Community 43 - "IssueEditSession"
Cohesion: 0.16
Nodes (10): ACC issue workflow recovery implementation plan, Global constraints, Ownership and shared interfaces, Recovery record, Review focus, Self-review and handoff, Task 1: Recover staged records, USD migration, and BCF fields, Task 3: Wire creation, editing, and evidence ownership (+2 more)

### Community 44 - "._finish_annotation"
Cohesion: 0.21
Nodes (5): annotate(), capture(), focus(), open_view(), reattach()

### Community 45 - "CameraOptionsTests"
Cohesion: 0.21
Nodes (4): CameraOptionsTests, CopyEvidenceTests, capture(), discard()

### Community 46 - "make_anchor"
Cohesion: 0.23
Nodes (17): hashlib, attachment_state(), geometry_digest(), make_anchor(), Match source identities within a reference instance, never by proximity., Resolution, resolve_element(), world_anchor() (+9 more)

### Community 47 - "BCF camera alignment"
Cohesion: 0.33
Nodes (5): Acceptance limits, BCF camera alignment, Global constraints, Intent, Required behavior

### Community 48 - "BCF camera verification, 2026-10-07"
Cohesion: 0.14
Nodes (11): Camera review and corrections, Initial BCF import sample, ACC limits, BCF camera verification, 2026-10-07, Evidence and commands, Preview ownership found by native testing, Implications for issues.tag and ACC, Local sample evidence (+3 more)

### Community 49 - "viewport.py"
Cohesion: 0.11
Nodes (11): matrix(), _PinManipulator, on_build(), _PlacementClick, on_ended(), Review camera state and surface anchors for one native viewport., Build a native scene gesture without requiring a global input hook., _ViewportItem (+3 more)

### Community 50 - "ImportWindow"
Cohesion: 0.05
Nodes (21): copy, ViewpointImportOptions, camera_diagnostics(), Read-only camera evidence for BCF import review and offline reports., Pair retained source evidence with converted cameras by viewpoint UUID., check_scene(), preview_import(), apply() (+13 more)

### Community 52 - "Crash investigation, 2026-09-30"
Cohesion: 0.18
Nodes (11): Cleanup-wave comparison checkpoint, Crash investigation, 2026-09-30, Delivered-frame gate verification, Isolated follow-up verification, Live viewport remains impaired, Preserved work and evidence, Private rendered run at 13:34:10 UTC, Recurrence after delivered-frame gate at 14:40 UTC (+3 more)

### Community 53 - "enable_extension"
Cohesion: 0.18
Nodes (14): get_runtime_service(), flatten(), test_destroy_during_creation_callback_releases_capture(), cancel_and_destroy(), test_extension_activation_and_shutdown(), test_markup_compatibility(), test_native_pin_registry_cleanup_across_reload_and_reopen(), _close_values() (+6 more)

### Community 54 - "Implementation verification record"
Cohesion: 0.20
Nodes (8): Section Box acceptance verification, Crash investigation, Decisions and costs, Follow-up development and review, Implementation verification record, Independent review, Open acceptance gates, Runtime evidence

### Community 55 - "extension.py"
Cohesion: 0.18
Nodes (22): apply_import(), export_document(), ImportSummary, write_bcf(), reference_for_prim(), selected(), Lifecycle and the Issues menu entry., omni_ext (+14 more)

### Community 59 - "test_native_recall.py"
Cohesion: 0.33
Nodes (9): exercise_mouse_navigation(), navigate(), exercise_saved_view(), preview_native_saved_view_allows_mouse_navigation(), Native saved Markup camera recall without rendering a thumbnail., saved_scene_content(), test_saved_native_issue_view_recalls_camera_without_annotation(), test_saved_native_parent_camera_uses_portable_world_pose() (+1 more)

### Community 60 - "test_ui.py"
Cohesion: 0.15
Nodes (23): test_acc_create_cancel_removes_native_draft(), test_acc_create_save_clean_native_evidence(), exercise_creation(), edit_draft(), Lead-controlled rendered pin, native Markup, save and cancel workflow., test_cancel_pin_markup_draft_leaves_no_issue(), test_pin_opens_markup_and_saves_annotated_initial_view(), close_controller() (+15 more)

### Community 61 - "replace_progress"
Cohesion: 0.33
Nodes (5): patch, ProgressReportTests, time, Bounded Windows sharing-lock recovery for durable verification progress., replace_progress()

### Community 68 - "markup-lifecycle.md"
Cohesion: 0.29
Nodes (5): Markup ownership and USD edit targets, Runtime coverage, Selecting saved evidence without entering annotation, Why the root target remains selected during drawing, thumbnail()

## Knowledge Gaps
- **94 isolated node(s):** `Decision record`, `Authored coverage`, `Lead-run commands`, `Artifacts and inspection`, `Actual results` (+89 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 421 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Omniverse issue management implementation plan` connect `Omniverse issue management implementation plan` to `bcf.py`, `Omniverse issue management specification`, `Status`, `pathlib`, `Issues for Omniverse`, `make_anchor`, `IssueStore`, `viewport.py`, `ImportWindow`, `test_markup.py`, `enable_extension`, `Implementation verification record`, `extension.py`, `frames`, `verify_kit.py`?**
  _High betweenness centrality (0.168) - this node is a cross-community bridge._
- **Why does `Omniverse issue management specification` connect `Omniverse issue management specification` to `Stability and saved view recall`, `Omniverse issue management implementation plan`, `ACC workflow verification, 2026-10-01`, `Issues for Omniverse`, `Issue viewport design`, `Issues panel design`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Why does `IssuesController` connect `IssuesController` to `test_lifecycle.py`, `IssuesExtension`, `test_bcf_camera_workflow.py`, `MarkupAdapter`, `IssueService`, `IssueEditSession`, `._finish_annotation`, `IssuesWindow`, `.on_startup`, `ImportWindow`, `plan_import`, `extension.py`, `._dispatch`, `DirtyDetailsDialog`, `frames`, `test_ui.py`, `._open_details`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `IssuesController` (e.g. with `ReferenceSelectionRequired` and `IssueEditSession`) actually correct?**
  _`IssuesController` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `ViewportAdapter` (e.g. with `Reopened scene with stale cyan pins` and `IssuesController`) actually correct?**
  _`ViewportAdapter` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `controller_sdk()` (e.g. with `begin()` and `capture()`) actually correct?**
  _`controller_sdk()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Decision record`, `Authored coverage`, `Lead-run commands` to the rest of the system?**
  _94 weakly-connected nodes found - possible documentation gaps or missing edges._