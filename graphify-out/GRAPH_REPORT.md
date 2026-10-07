# Graph Report - issues.tag  (2026-10-07)

## Corpus Check
- 80 files · ~68,658 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: .xsd 6, (none) 2, .toml 1)

## Summary
- 1252 nodes · 2774 edges · 57 communities (42 shown, 15 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 192 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9fa6c84e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_lifecycle.py
- bcf.py
- Omniverse issue management specification
- test_acc_workflow.py
- ImportWindow
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
- make_anchor
- session_api
- ._exercise_native_delivery
- RecallTests
- Pin creation and Markup verification
- frames
- DependencySnapshotTests
- IssuesController
- test_acc_ui.py
- enable_extension
- controller_sdk
- ACCUITests
- Stability and saved view recall
- test_capture_probe.py
- pathlib
- markup.py
- Widget
- Recovered ACC issue creation and editing requirements
- ACC workflow verification, 2026-10-01
- Details
- verification_dependencies.py
- IssueEditSession
- ._finish_annotation
- viewport.py
- _PlacementClick
- BCF camera alignment
- That Open BCF camera research
- copy
- Markup ownership and USD edit targets
- test_native_recall.py
- collect
- ._dispatch
- DirtyDetailsDialog
- extension.py

## God Nodes (most connected - your core abstractions)
1. `frames()` - 61 edges
2. `IssuesController` - 55 edges
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
- `Ownership and shared interfaces` --references--> `IssuesExtension`  [INFERRED]
  docs/superpowers/plans/2026-10-01-acc-issue-workflow-recovery.md → issues_tag/extension.py
- `Task 3: Import-review controls and temporary camera preview` --references--> `ImportWindow`  [INFERRED]
  docs/superpowers/plans/2026-10-07-bcf-camera-alignment.md → issues_tag/import_window.py
- `Task 2: Recover separate issue list and details panels` --references--> `IssuesWindow`  [INFERRED]
  docs/superpowers/plans/2026-10-01-acc-issue-workflow-recovery.md → issues_tag/window.py

## Import Cycles
- None detected.

## Communities (57 total, 15 thin omitted)

### Community 0 - "test_lifecycle.py"
Cohesion: 0.10
Nodes (18): gc, _failure(), lifecycle_sdk(), destroy(), __init__(), ManagerShutdownTests, Run real lifecycle code with narrow SDK boundaries and injected failures. The…, Resource (+10 more)

### Community 1 - "bcf.py"
Cohesion: 0.06
Nodes (87): base64, apply_import(), BcfDocument, _component(), Conflict, export_view(), import_view(), Map standard BCF world coordinates through a composed USD reference. (+79 more)

### Community 2 - "Omniverse issue management specification"
Cohesion: 0.11
Nodes (18): Acceptance criteria, BCF file exchange, Core workflow, Delivery and review, Omniverse issue management specification, Further Notes, Implementation Decisions, Issue interactions and lifecycle (+10 more)

### Community 3 - "test_acc_workflow.py"
Cohesion: 0.08
Nodes (39): encode(), IssueStore, Materialize derived legacy fields once, inside the caller's undo command., _action(), _arrow(), _button(), _close(), _comment_evidence_trace() (+31 more)

### Community 4 - "ImportWindow"
Cohesion: 0.08
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
Cohesion: 0.06
Nodes (12): Review imported BCF field conflicts before applying the import plan., Native issue-panel palette and widget states., Issues entry beside Section Box on Kit's main toolbar., _dock_when_ready(), IssueDetailsWindow, IssuesWindow, IssueTypesWindow, Separate dockable issue list and staged details panels. (+4 more)

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
Cohesion: 0.07
Nodes (38): Cleanup-wave comparison checkpoint, Crash investigation, 2026-09-30, Delivered-frame gate verification, Focused recurrence at 13:47:30 UTC, Isolated follow-up verification, Live viewport remains impaired, Preserved work and evidence, Private rendered run at 13:34:10 UTC (+30 more)

### Community 22 - "make_anchor"
Cohesion: 0.25
Nodes (18): hashlib, attachment_state(), geometry_digest(), make_anchor(), Match source identities within a reference instance, never by proximity., reference_for_prim(), Resolution, resolve_element() (+10 more)

### Community 23 - "session_api"
Cohesion: 0.08
Nodes (8): AccBcfTests, AccPersistenceTests, persistence_sdk(), session_api(), CopyEvidenceTests, capture(), discard(), EditSessionTests

### Community 26 - "Pin creation and Markup verification"
Cohesion: 0.50
Nodes (3): Limits, Pin creation and Markup verification, Results

### Community 27 - "frames"
Cohesion: 0.10
Nodes (17): ViewportAdapter, preview_issue_pins(), preview_native_gesture_placement(), Visible acceptance: a native mouse event must complete surface placement., require_viewport(), test_completed_pick_cannot_cross_scene_close(), test_imported_metadata_does_not_invalidate_coordinate_frame(), test_overlay_tracks_scene_and_stage_scope() (+9 more)

### Community 29 - "IssuesController"
Cohesion: 0.19
Nodes (3): IssuesController, add(), add()

### Community 30 - "test_acc_ui.py"
Cohesion: 0.08
Nodes (15): ast, Combo, FillPolicy, ImageWithProvider, IwpFillPolicy, panel_types(), Enum, str (+7 more)

### Community 31 - "enable_extension"
Cohesion: 0.13
Nodes (20): get_runtime_service(), service_for_new_scene(), test_failed_issue_transaction_has_no_partial_records(), test_issue_comment_status_survive_reopen(), test_issue_undo_preserves_unrelated_scene_edits(), test_listeners_observe_complete_records(), test_root_layer_ownership_and_read_only(), test_unsaved_state_and_next_reviewer() (+12 more)

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
Cohesion: 0.10
Nodes (28): carb_settings, datetime, copy_issues(), Undo only issue records, preserving unrelated root-layer opinions., restore_issues(), UpdateIssuesCommand, Scene-scoped issue actions and notifications., omni_kit_commands (+20 more)

### Community 36 - "pathlib"
Cohesion: 0.11
Nodes (31): argparse, contextlib, dataclasses, importlib, importlib_util, json, os, pathlib (+23 more)

### Community 37 - "markup.py"
Cohesion: 0.16
Nodes (8): asyncio, io, Editable evidence through NVIDIA's supported Markup Core API., editor_type(), IssueEditorTests, Offline native-editor behavior checks without importing or replacing Kit…, StringModel, weakref

### Community 39 - "Recovered ACC issue creation and editing requirements"
Cohesion: 0.20
Nodes (10): Acceptance workflow, Confirmed intent, Creation and editing, Integration policy for completing the recovered work, Issue list, Recovered ACC issue creation and editing requirements, Recovery status and evidence, Requirements inferred from the unfinished implementation (+2 more)

### Community 40 - "ACC workflow verification, 2026-10-01"
Cohesion: 0.22
Nodes (7): ACC workflow execution decisions, 2026-10-01, Decision record, ACC workflow verification, 2026-10-01, Actual results, Artifacts and inspection, Authored coverage, Lead-run commands

### Community 42 - "verification_dependencies.py"
Cohesion: 0.36
Nodes (8): shutil, stat, main(), prepare_snapshot(), qualify_extension_paths(), Prepare ordinary dependency copies for verification, without starting Kit., _reject_link(), validate_snapshot()

### Community 43 - "IssueEditSession"
Cohesion: 0.15
Nodes (11): ACC issue workflow recovery implementation plan, Global constraints, Ownership and shared interfaces, Recovery record, Review focus, Self-review and handoff, Task 1: Recover staged records, USD migration, and BCF fields, Task 2: Recover separate issue list and details panels (+3 more)

### Community 44 - "._finish_annotation"
Cohesion: 0.21
Nodes (5): annotate(), capture(), focus(), open_view(), reattach()

### Community 45 - "viewport.py"
Cohesion: 0.14
Nodes (10): flatten(), matrix(), Review camera state and surface anchors for one native viewport., _ViewportItem, omni_kit_app, omni_kit_viewport_utility, _close_values(), test_inactive_viewport_does_not_capture_active_section_box() (+2 more)

### Community 46 - "_PlacementClick"
Cohesion: 0.25
Nodes (5): _PinManipulator, on_build(), _PlacementClick, on_ended(), Build a native scene gesture without requiring a global input hook.

### Community 47 - "BCF camera alignment"
Cohesion: 0.33
Nodes (5): Acceptance limits, BCF camera alignment, Global constraints, Intent, Required behavior

### Community 48 - "That Open BCF camera research"
Cohesion: 0.33
Nodes (5): Implications for issues.tag and ACC, Local sample evidence, That Open BCF camera research, Verified BCF version difference, Verified That Open behavior

### Community 50 - "copy"
Cohesion: 0.40
Nodes (4): copy, camera_diagnostics(), Read-only camera evidence for BCF import review and offline reports., Pair retained source evidence with converted cameras by viewpoint UUID.

### Community 51 - "Markup ownership and USD edit targets"
Cohesion: 0.40
Nodes (5): Markup ownership and USD edit targets, Runtime coverage, Selecting saved evidence without entering annotation, Why the root target remains selected during drawing, thumbnail()

### Community 52 - "test_native_recall.py"
Cohesion: 0.33
Nodes (9): exercise_mouse_navigation(), navigate(), exercise_saved_view(), preview_native_saved_view_allows_mouse_navigation(), Native saved Markup camera recall without rendering a thumbnail., saved_scene_content(), test_saved_native_issue_view_recalls_camera_without_annotation(), test_saved_native_parent_camera_uses_portable_world_pose() (+1 more)

### Community 60 - "extension.py"
Cohesion: 0.18
Nodes (7): ReferenceSelectionRequired, IssuesExtension, Lifecycle and the Issues menu entry., Manager-owned registration; pending work belongs to the detached controller., omni_ext, omni_kit_menu_utils, ValueError

## Knowledge Gaps
- **92 isolated node(s):** `Decision record`, `Authored coverage`, `Lead-run commands`, `Artifacts and inspection`, `Actual results` (+87 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 402 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Omniverse issue management implementation plan` connect `Omniverse issue management implementation plan` to `bcf.py`, `Omniverse issue management specification`, `test_capture_probe.py`, `markup.py`, `Issues for Omniverse`, `IssuesWindow`, `viewport.py`, `test_markup.py`, `make_anchor`, `frames`, `extension.py`, `enable_extension`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Why does `Omniverse issue management specification` connect `Omniverse issue management specification` to `Stability and saved view recall`, `Omniverse issue management implementation plan`, `ACC workflow verification, 2026-10-01`, `Issues for Omniverse`, `Issue viewport design`, `Issues panel design`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Why does `ACCUITests` connect `ACCUITests` to `test_acc_ui.py`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `IssuesController` (e.g. with `ReferenceSelectionRequired` and `IssueEditSession`) actually correct?**
  _`IssuesController` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `ViewportAdapter` (e.g. with `Reopened scene with stale cyan pins` and `IssuesController`) actually correct?**
  _`ViewportAdapter` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `controller_sdk()` (e.g. with `begin()` and `capture()`) actually correct?**
  _`controller_sdk()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Decision record`, `Authored coverage`, `Lead-run commands` to the rest of the system?**
  _92 weakly-connected nodes found - possible documentation gaps or missing edges._