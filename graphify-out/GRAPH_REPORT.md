# Graph Report - issues.tag  (2026-10-07)

## Corpus Check
- 84 files · ~72,303 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: .xsd 6, (none) 2, .toml 1)

## Summary
- 1334 nodes · 3011 edges · 65 communities (49 shown, 16 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 205 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f0210505`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_lifecycle.py
- bcf.py
- Omniverse issue management specification
- test_acc_workflow.py
- CameraDiagnosticsTests
- MarkupAdapter
- IssueService
- Omniverse issue management implementation plan
- test_window_cleanup.py
- Settings
- Issues for Omniverse
- graphify
- DraftMarkupTests
- IssuesWindow
- Issue viewport design
- IssuesToolbarButton
- Implementation verification record
- Issues panel design
- BcfCompatibilityTests
- test_markup.py
- bcf-21-compatibility.md
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
- service_for_new_scene
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
- elements.py
- BCF camera alignment
- That Open BCF camera research
- frames
- ImportWindow
- Crash investigation, 2026-09-30
- viewport.py
- enable_extension
- service.py
- extension.py
- ._dispatch
- DirtyDetailsDialog
- ImportCameraReviewTests
- replace_progress
- reference_for_prim
- pxr
- ACC issue workflow recovery implementation plan
- ImportCameraPreviewTests
- Markup ownership and USD edit targets

## God Nodes (most connected - your core abstractions)
1. `frames()` - 61 edges
2. `IssuesController` - 57 edges
3. `ACCUITests` - 51 edges
4. `ViewportAdapter` - 50 edges
5. `controller_sdk()` - 43 edges
6. `IssueService` - 39 edges
7. `Omniverse issue management implementation plan` - 39 edges
8. `Status` - 36 edges
9. `enable_extension()` - 33 edges
10. `ControllerTests` - 31 edges

## Surprising Connections (you probably didn't know these)
- `Creation and editing` --references--> `IssueEditSession`  [INFERRED]
  docs/superpowers/specs/2026-10-01-acc-issue-workflow-recovered.md → issues_tag/edit_session.py
- `Reopened scene with stale cyan pins` --references--> `ViewportAdapter`  [INFERRED]
  docs/crash-investigation-2026-09-30.md → issues_tag/viewport.py
- `ACC issue workflow recovery implementation plan` --references--> `IssueEditSession`  [INFERRED]
  docs/superpowers/plans/2026-10-01-acc-issue-workflow-recovery.md → issues_tag/edit_session.py
- `Task 3: Wire creation, editing, and evidence ownership` --references--> `IssueEditSession`  [INFERRED]
  docs/superpowers/plans/2026-10-01-acc-issue-workflow-recovery.md → issues_tag/edit_session.py
- `Ownership and shared interfaces` --references--> `IssuesExtension`  [INFERRED]
  docs/superpowers/plans/2026-10-01-acc-issue-workflow-recovery.md → issues_tag/extension.py

## Import Cycles
- None detected.

## Communities (65 total, 16 thin omitted)

### Community 0 - "test_lifecycle.py"
Cohesion: 0.10
Nodes (17): gc, _failure(), lifecycle_sdk(), destroy(), __init__(), ManagerShutdownTests, Run real lifecycle code with narrow SDK boundaries and injected failures. The…, Resource (+9 more)

### Community 1 - "bcf.py"
Cohesion: 0.05
Nodes (94): base64, apply_import(), BcfDocument, _component(), Conflict, export_view(), import_view(), Map standard BCF world coordinates through a composed USD reference. (+86 more)

### Community 2 - "Omniverse issue management specification"
Cohesion: 0.11
Nodes (18): Acceptance criteria, BCF file exchange, Core workflow, Delivery and review, Omniverse issue management specification, Further Notes, Implementation Decisions, Issue interactions and lifecycle (+10 more)

### Community 3 - "test_acc_workflow.py"
Cohesion: 0.08
Nodes (39): encode(), IssueStore, Materialize derived legacy fields once, inside the caller's undo command., _action(), _arrow(), _button(), _close(), _comment_evidence_trace() (+31 more)

### Community 4 - "CameraDiagnosticsTests"
Cohesion: 0.11
Nodes (12): BCF camera alignment Implementation Plan, File responsibilities, Global Constraints, Plan self-review, Review Focus, Task 1: Retain source camera provenance and provide offline diagnostics, Task 2: Explicit per-viewpoint coordinate and legacy FOV options, Task 3: Import-review controls and temporary camera preview (+4 more)

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

### Community 9 - "Settings"
Cohesion: 0.17
Nodes (4): finish(), EvidenceCaptureTests, window(), Settings

### Community 10 - "Issues for Omniverse"
Cohesion: 0.17
Nodes (8): Section Box acceptance verification, BCF exchange, Current boundaries, Issues for Omniverse, Install and use, Normal scene Save, Verification, Parent USD ownership

### Community 13 - "IssuesWindow"
Cohesion: 0.08
Nodes (7): Task 2: Recover separate issue list and details panels, _dock_when_ready(), IssueDetailsWindow, IssuesWindow, IssueTypesWindow, test_panel_manage_types_create_delete_and_undo(), test_panel_reports_unsupported_scene_schema()

### Community 14 - "Issue viewport design"
Cohesion: 0.25
Nodes (8): Issue viewport design, Pin eligibility, Scoped source identity, Session-layer restoration, Stage-safe picking, Unresolved component retention, Independent pin anchors, Saved review context

### Community 16 - "Implementation verification record"
Cohesion: 0.29
Nodes (7): Crash investigation, Decisions and costs, Follow-up development and review, Implementation verification record, Independent review, Open acceptance gates, Runtime evidence

### Community 17 - "Issues panel design"
Cohesion: 0.14
Nodes (14): BCF XML 3.0, Bounded ZIP parsing, Supported BCF file profile, Native viewpoint metadata, Three-way import baseline, Behavior and accessibility, Issues panel design, Explicit import preview (+6 more)

### Community 19 - "test_markup.py"
Cohesion: 0.16
Nodes (20): Focused recurrence at 13:47:30 UTC, Timeline, adapter_for(), _capture_cycle_phase(), test_annotated_comment_reopens_editably(), test_annotation_rejects_overlapping_ownership(), test_annotation_releases_navigation(), test_capture_camera_matches_view_after_markup_activation() (+12 more)

### Community 22 - "pathlib"
Cohesion: 0.21
Nodes (9): asyncio, importlib_util, io, Editable evidence through NVIDIA's supported Markup Core API., math, pathlib, Offline ownership regression; framework events stand in for native render…, Evidence keeps render/Markup content and restores controls on every exit. (+1 more)

### Community 23 - "session_api"
Cohesion: 0.10
Nodes (6): AccBcfTests, AccPersistenceTests, persistence_sdk(), session_api(), EditSessionTests, Draft changes preserve saved records and evidence until details Save.

### Community 26 - "Pin creation and Markup verification"
Cohesion: 0.50
Nodes (3): Limits, Pin creation and Markup verification, Results

### Community 27 - "ViewportAdapter"
Cohesion: 0.11
Nodes (3): ViewportAdapter, collect(), test_imported_metadata_does_not_invalidate_coordinate_frame()

### Community 29 - "._operation"
Cohesion: 0.11
Nodes (6): add(), add(), annotate(), focus(), open_view(), reattach()

### Community 30 - "test_acc_ui.py"
Cohesion: 0.08
Nodes (17): Combo, FillPolicy, ImageWithProvider, IwpFillPolicy, panel_types(), Enum, str, Native UI boundary doubles exercise real panel code without a Kit process. (+9 more)

### Community 31 - "service_for_new_scene"
Cohesion: 0.27
Nodes (8): service_for_new_scene(), test_failed_issue_transaction_has_no_partial_records(), test_issue_comment_status_survive_reopen(), test_issue_undo_preserves_unrelated_scene_edits(), test_listeners_observe_complete_records(), test_root_layer_ownership_and_read_only(), test_unsaved_state_and_next_reviewer(), test_viewpoint_lookup_does_not_walk_building_geometry()

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
Cohesion: 0.13
Nodes (26): dataclasses, importlib, os, pil, subprocess, sys, tempfile, Progress replacement survives transient locks without hiding persistent… (+18 more)

### Community 37 - "test_issue_editor.py"
Cohesion: 0.24
Nodes (5): ast, editor_type(), IssueEditorTests, Offline native-editor behavior checks without importing or replacing Kit…, StringModel

### Community 39 - "Recovered ACC issue creation and editing requirements"
Cohesion: 0.20
Nodes (10): Acceptance workflow, Confirmed intent, Creation and editing, Integration policy for completing the recovered work, Issue list, Recovered ACC issue creation and editing requirements, Recovery status and evidence, Requirements inferred from the unfinished implementation (+2 more)

### Community 40 - "ACC workflow verification, 2026-10-01"
Cohesion: 0.22
Nodes (7): ACC workflow execution decisions, 2026-10-01, Decision record, ACC workflow verification, 2026-10-01, Actual results, Artifacts and inspection, Authored coverage, Lead-run commands

### Community 42 - "verification_dependencies.py"
Cohesion: 0.19
Nodes (12): argparse, contextlib, json, shutil, stat, Report source BCF cameras and optional default USD mapping without saving…, main(), prepare_snapshot() (+4 more)

### Community 43 - "Ownership and shared interfaces"
Cohesion: 0.31
Nodes (4): Ownership and shared interfaces, Task 1: Recover staged records, USD migration, and BCF fields, Task 3: Wire creation, editing, and evidence ownership, Task 4: Independent review and complete Composer verification

### Community 45 - "CameraOptionsTests"
Cohesion: 0.21
Nodes (4): CameraOptionsTests, CopyEvidenceTests, capture(), discard()

### Community 46 - "elements.py"
Cohesion: 0.23
Nodes (16): hashlib, attachment_state(), geometry_digest(), Match source identities within a reference instance, never by proximity., Resolution, resolve_element(), world_anchor(), Separate dockable issue list and staged details panels. (+8 more)

### Community 47 - "BCF camera alignment"
Cohesion: 0.33
Nodes (5): Acceptance limits, BCF camera alignment, Global constraints, Intent, Required behavior

### Community 48 - "That Open BCF camera research"
Cohesion: 0.33
Nodes (5): Implications for issues.tag and ACC, Local sample evidence, That Open BCF camera research, Verified BCF version difference, Verified That Open behavior

### Community 49 - "frames"
Cohesion: 0.26
Nodes (16): make_anchor(), preview_issue_pins(), preview_native_gesture_placement(), Visible acceptance: a native mouse event must complete surface placement., require_viewport(), test_completed_pick_cannot_cross_scene_close(), test_overlay_tracks_scene_and_stage_scope(), test_pin_cache_tracks_camera_parent_geometry() (+8 more)

### Community 50 - "ImportWindow"
Cohesion: 0.09
Nodes (12): copy, ViewpointImportOptions, camera_diagnostics(), Read-only camera evidence for BCF import review and offline reports., Pair retained source evidence with converted cameras by viewpoint UUID., ImportWindow, Review imported BCF field conflicts before applying the import plan., Resolve staged changes before closing details or switching issues. (+4 more)

### Community 51 - "Crash investigation, 2026-09-30"
Cohesion: 0.18
Nodes (11): Cleanup-wave comparison checkpoint, Crash investigation, 2026-09-30, Delivered-frame gate verification, Isolated follow-up verification, Live viewport remains impaired, Preserved work and evidence, Private rendered run at 13:34:10 UTC, Recurrence after delivered-frame gate at 14:40 UTC (+3 more)

### Community 52 - "viewport.py"
Cohesion: 0.13
Nodes (9): matrix(), pin_is_visible(), _PinManipulator, on_build(), _PlacementClick, on_ended(), Review camera state and surface anchors for one native viewport., Build a native scene gesture without requiring a global input hook. (+1 more)

### Community 53 - "enable_extension"
Cohesion: 0.19
Nodes (14): get_runtime_service(), test_destroy_during_creation_callback_releases_capture(), cancel_and_destroy(), test_extension_activation_and_shutdown(), test_markup_compatibility(), test_native_pin_registry_cleanup_across_reload_and_reopen(), Rendered check of the Issues entry on Kit's main toolbar., test_toolbar_click_opens_and_reuses_issues_panel() (+6 more)

### Community 54 - "service.py"
Cohesion: 0.20
Nodes (9): carb_settings, datetime, copy_issues(), Undo only issue records, preserving unrelated root-layer opinions., restore_issues(), UpdateIssuesCommand, Scene-scoped issue actions and notifications., omni_kit_commands (+1 more)

### Community 55 - "extension.py"
Cohesion: 0.13
Nodes (8): ReferenceSelectionRequired, IssuesExtension, Lifecycle and the Issues menu entry., Manager-owned registration; pending work belongs to the detached controller., ReferenceSelectionWindow, omni_ext, omni_kit_menu_utils, ValueError

### Community 59 - "replace_progress"
Cohesion: 0.33
Nodes (5): patch, ProgressReportTests, time, Bounded Windows sharing-lock recovery for durable verification progress., replace_progress()

### Community 60 - "reference_for_prim"
Cohesion: 0.31
Nodes (10): reference_for_prim(), exercise_mouse_navigation(), navigate(), exercise_saved_view(), preview_native_saved_view_allows_mouse_navigation(), Native saved Markup camera recall without rendering a thumbnail., saved_scene_content(), test_saved_native_issue_view_recalls_camera_without_annotation() (+2 more)

### Community 61 - "pxr"
Cohesion: 0.24
Nodes (7): flatten(), omni_kit_viewport_utility, pxr, _close_values(), test_inactive_viewport_does_not_capture_active_section_box(), test_section_box_controls_and_planes_restore_with_issue(), test_unsectioned_issue_disables_later_section_controller()

### Community 62 - "ACC issue workflow recovery implementation plan"
Cohesion: 0.29
Nodes (5): ACC issue workflow recovery implementation plan, Global constraints, Recovery record, Review focus, Self-review and handoff

### Community 64 - "Markup ownership and USD edit targets"
Cohesion: 0.40
Nodes (5): Markup ownership and USD edit targets, Runtime coverage, Selecting saved evidence without entering annotation, Why the root target remains selected during drawing, thumbnail()

## Knowledge Gaps
- **92 isolated node(s):** `Decision record`, `Authored coverage`, `Lead-run commands`, `Artifacts and inspection`, `Actual results` (+87 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 415 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Omniverse issue management implementation plan` connect `Omniverse issue management implementation plan` to `bcf.py`, `Omniverse issue management specification`, `Issues for Omniverse`, `elements.py`, `frames`, `ImportWindow`, `test_markup.py`, `viewport.py`, `enable_extension`, `service.py`, `extension.py`, `pathlib`, `service_for_new_scene`?**
  _High betweenness centrality (0.142) - this node is a cross-community bridge._
- **Why does `IssuesController` connect `IssuesController` to `bcf.py`, `CameraDiagnosticsTests`, `MarkupAdapter`, `IssueService`, `Settings`, `Ownership and shared interfaces`, `IssuesWindow`, `IssuesToolbarButton`, `ImportWindow`, `extension.py`, `._dispatch`, `DirtyDetailsDialog`, `ViewportAdapter`, `._operation`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `ViewportAdapter` connect `ViewportAdapter` to `bcf.py`, `MarkupAdapter`, `IssuesController`, `IssuesToolbarButton`, `frames`, `Crash investigation, 2026-09-30`, `viewport.py`, `test_markup.py`, `pathlib`, `extension.py`, `pxr`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `IssuesController` (e.g. with `ReferenceSelectionRequired` and `IssueEditSession`) actually correct?**
  _`IssuesController` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `ViewportAdapter` (e.g. with `Reopened scene with stale cyan pins` and `IssuesController`) actually correct?**
  _`ViewportAdapter` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `controller_sdk()` (e.g. with `begin()` and `capture()`) actually correct?**
  _`controller_sdk()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Decision record`, `Authored coverage`, `Lead-run commands` to the rest of the system?**
  _92 weakly-connected nodes found - possible documentation gaps or missing edges._