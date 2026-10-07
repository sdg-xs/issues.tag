# Graph Report - issues.tag  (2026-10-06)

## Corpus Check
- 74 files · ~64,549 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .xsd 6, (none) 1, .toml 1)

## Summary
- 1211 nodes · 2706 edges · 56 communities (43 shown, 13 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 188 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `539ead2c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_lifecycle.py
- bcf.py
- Omniverse issue management specification
- test_acc_workflow.py
- test_ui.py
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
- IssueStore
- session_api
- ._exercise_native_delivery
- RecallTests
- Pin creation and Markup verification
- ViewportAdapter
- DependencySnapshotTests
- IssuesController
- test_acc_ui.py
- frames
- controller_sdk
- ACCUITests
- Stability and saved view recall
- test_capture_probe.py
- test_acc_controller.py
- test_issue_editor.py
- Widget
- Recovered ACC issue creation and editing requirements
- ACC workflow verification, 2026-10-01
- Details
- verification_dependencies.py
- IssueEditSession
- ._finish_annotation
- pathlib
- test_creation.py
- test_import_reference.py
- Crash investigation, 2026-09-30
- service_for_new_scene
- replace_progress
- test_native_recall.py
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
- `Focused recurrence at 13:47:30 UTC` --references--> `test_creation_cancellation_then_scene_replacement_repeated()`  [INFERRED]
  docs/crash-investigation-2026-09-30.md → tests/test_markup.py
- `Ownership and shared interfaces` --references--> `IssuesExtension`  [INFERRED]
  docs/superpowers/plans/2026-10-01-acc-issue-workflow-recovery.md → issues_tag/extension.py
- `Private rendered run at 13:34:10 UTC` --references--> `test_external_vendor_edit_defers_original_target_restoration()`  [INFERRED]
  docs/crash-investigation-2026-09-30.md → tests/test_markup.py

## Import Cycles
- None detected.

## Communities (56 total, 13 thin omitted)

### Community 0 - "test_lifecycle.py"
Cohesion: 0.10
Nodes (17): gc, _failure(), lifecycle_sdk(), destroy(), __init__(), ManagerShutdownTests, Run real lifecycle code with narrow SDK boundaries and injected failures. The…, Resource (+9 more)

### Community 1 - "bcf.py"
Cohesion: 0.07
Nodes (73): base64, copy, apply_import(), BcfDocument, _component(), Conflict, export_view(), import_view() (+65 more)

### Community 2 - "Omniverse issue management specification"
Cohesion: 0.11
Nodes (18): Acceptance criteria, BCF file exchange, Core workflow, Delivery and review, Omniverse issue management specification, Further Notes, Implementation Decisions, Issue interactions and lifecycle (+10 more)

### Community 3 - "test_acc_workflow.py"
Cohesion: 0.19
Nodes (28): _action(), _arrow(), _button(), _close(), _comment_evidence_trace(), _create(), _discard(), _dock_primary_viewport() (+20 more)

### Community 4 - "test_ui.py"
Cohesion: 0.14
Nodes (17): ImportWindow, close_controller(), controller_for(), preview_panel(), preview_placement_prompt(), Separate issue panels, staged edits, and import preview on a real Kit stage., Visible-only native UI evidence, dispatched separately from headless tests., Capture the real armed placement guidance and native Cancel action. (+9 more)

### Community 5 - "MarkupAdapter"
Cohesion: 0.11
Nodes (13): clean_evidence_ui(), overlapping_windows(), MarkupAdapter, _native_camera_matches(), Editable evidence through NVIDIA's supported Markup Core API., Recall an existing native camera without entering Markup review or editing., Evaluate the vendor's attribute-copy result without changing the live scene., Delete this adapter's unsaved native draft in its originating scene. (+5 more)

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
Cohesion: 0.25
Nodes (7): BCF exchange, Current boundaries, Issues for Omniverse, Install and use, Normal scene Save, Verification, Parent USD ownership

### Community 13 - "IssuesWindow"
Cohesion: 0.07
Nodes (11): Task 2: Recover separate issue list and details panels, Review imported BCF field conflicts before applying the import plan., Native issue-panel palette and widget states., _dock_when_ready(), IssueDetailsWindow, IssuesWindow, IssueTypesWindow, Separate dockable issue list and staged details panels. (+3 more)

### Community 14 - "Issue viewport design"
Cohesion: 0.25
Nodes (8): Issue viewport design, Pin eligibility, Scoped source identity, Session-layer restoration, Stage-safe picking, Unresolved component retention, Independent pin anchors, Saved review context

### Community 15 - "IssuesToolbarButton"
Cohesion: 0.15
Nodes (4): drain(), IssuesToolbarButton, Issues entry beside Section Box on Kit's main toolbar., omni_kit_widget_toolbar

### Community 16 - "Implementation verification record"
Cohesion: 0.17
Nodes (8): Section Box acceptance verification, Crash investigation, Decisions and costs, Follow-up development and review, Implementation verification record, Independent review, Open acceptance gates, Runtime evidence

### Community 17 - "Issues panel design"
Cohesion: 0.14
Nodes (14): BCF XML 3.0, Bounded ZIP parsing, Supported BCF file profile, Native viewpoint metadata, Three-way import baseline, Behavior and accessibility, Issues panel design, Explicit import preview (+6 more)

### Community 19 - "test_markup.py"
Cohesion: 0.15
Nodes (21): Timeline, adapter_for(), _capture_cycle_phase(), test_annotated_comment_reopens_editably(), test_annotation_rejects_overlapping_ownership(), test_annotation_releases_navigation(), test_capture_camera_matches_view_after_markup_activation(), test_capture_preserves_replacement_vendor_owner() (+13 more)

### Community 22 - "IssueStore"
Cohesion: 0.25
Nodes (3): encode(), IssueStore, Materialize derived legacy fields once, inside the caller's undo command.

### Community 23 - "session_api"
Cohesion: 0.08
Nodes (8): AccBcfTests, AccPersistenceTests, persistence_sdk(), session_api(), CopyEvidenceTests, capture(), discard(), EditSessionTests

### Community 26 - "Pin creation and Markup verification"
Cohesion: 0.50
Nodes (3): Limits, Pin creation and Markup verification, Results

### Community 27 - "ViewportAdapter"
Cohesion: 0.06
Nodes (43): hashlib, attachment_state(), geometry_digest(), make_anchor(), Match source identities within a reference instance, never by proximity., reference_for_prim(), Resolution, resolve_element() (+35 more)

### Community 29 - "IssuesController"
Cohesion: 0.19
Nodes (3): IssuesController, add(), add()

### Community 30 - "test_acc_ui.py"
Cohesion: 0.11
Nodes (10): Combo, FillPolicy, ImageWithProvider, IwpFillPolicy, Enum, str, Native UI boundary doubles exercise real panel code without a Kit process., Session (+2 more)

### Community 31 - "frames"
Cohesion: 0.16
Nodes (21): get_runtime_service(), omni_kit_app, _disable_runtime(), test_extension_activation_and_shutdown(), test_markup_compatibility(), test_native_pin_registry_cleanup_across_reload_and_reopen(), _close_values(), test_inactive_viewport_does_not_capture_active_section_box() (+13 more)

### Community 32 - "controller_sdk"
Cohesion: 0.06
Nodes (9): controller_sdk(), capture(), finish(), ControllerTests, place(), fail(), NativeCallbackDispatchTests, start() (+1 more)

### Community 33 - "ACCUITests"
Cohesion: 0.06
Nodes (8): Markup ownership and USD edit targets, Runtime coverage, Selecting saved evidence without entering annotation, Why the root target remains selected during drawing, ACCUITests, find(), dispatch(), thumbnail()

### Community 34 - "Stability and saved view recall"
Cohesion: 0.40
Nodes (4): Progress, Sequence and evidence, Shared interfaces and ownership, Stability and saved view recall

### Community 35 - "test_capture_probe.py"
Cohesion: 0.10
Nodes (28): carb_settings, datetime, copy_issues(), Undo only issue records, preserving unrelated root-layer opinions., restore_issues(), UpdateIssuesCommand, Scene-scoped issue actions and notifications., omni_kit_commands (+20 more)

### Community 36 - "test_acc_controller.py"
Cohesion: 0.18
Nodes (16): dataclasses, importlib, io, pil, tempfile, Title/type exchange and repeat imports through real project records., Controller transitions with real USD transactions and controlled native…, Offline staged Save and migration checks using real USD and issue commands. (+8 more)

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
Cohesion: 0.23
Nodes (11): argparse, json, os, shutil, stat, main(), prepare_snapshot(), qualify_extension_paths() (+3 more)

### Community 43 - "IssueEditSession"
Cohesion: 0.16
Nodes (10): ACC issue workflow recovery implementation plan, Global constraints, Ownership and shared interfaces, Recovery record, Review focus, Self-review and handoff, Task 1: Recover staged records, USD migration, and BCF fields, Task 3: Wire creation, editing, and evidence ownership (+2 more)

### Community 44 - "._finish_annotation"
Cohesion: 0.21
Nodes (5): annotate(), capture(), focus(), open_view(), reattach()

### Community 45 - "pathlib"
Cohesion: 0.21
Nodes (11): asyncio, importlib_util, pathlib, sys, Progress replacement survives transient locks without hiding persistent…, Offline ownership regression; framework events stand in for native render…, Offline draft-deletion ownership checks against public SDK doubles., Evidence keeps render/Markup content and restores controls on every exit. (+3 more)

### Community 46 - "test_creation.py"
Cohesion: 0.21
Nodes (9): contextlib, Temporarily suppress viewport overlays without changing the application's UI., test_acc_create_cancel_removes_native_draft(), test_acc_create_save_clean_native_evidence(), exercise_creation(), edit_draft(), Lead-controlled rendered pin, native Markup, save and cancel workflow., test_cancel_pin_markup_draft_leaves_no_issue() (+1 more)

### Community 47 - "test_import_reference.py"
Cohesion: 0.28
Nodes (4): panel_types(), UpdateStream, Reference selection uses real dialog callbacks with native UI boundary doubles., reference_window_type()

### Community 48 - "Crash investigation, 2026-09-30"
Cohesion: 0.17
Nodes (12): Cleanup-wave comparison checkpoint, Crash investigation, 2026-09-30, Delivered-frame gate verification, Focused recurrence at 13:47:30 UTC, Isolated follow-up verification, Live viewport remains impaired, Preserved work and evidence, Private rendered run at 13:34:10 UTC (+4 more)

### Community 50 - "service_for_new_scene"
Cohesion: 0.27
Nodes (8): service_for_new_scene(), test_failed_issue_transaction_has_no_partial_records(), test_issue_comment_status_survive_reopen(), test_issue_undo_preserves_unrelated_scene_edits(), test_listeners_observe_complete_records(), test_root_layer_ownership_and_read_only(), test_unsaved_state_and_next_reviewer(), test_viewpoint_lookup_does_not_walk_building_geometry()

### Community 51 - "replace_progress"
Cohesion: 0.33
Nodes (5): patch, ProgressReportTests, time, Bounded Windows sharing-lock recovery for durable verification progress., replace_progress()

### Community 52 - "test_native_recall.py"
Cohesion: 0.33
Nodes (9): exercise_mouse_navigation(), navigate(), exercise_saved_view(), preview_native_saved_view_allows_mouse_navigation(), Native saved Markup camera recall without rendering a thumbnail., saved_scene_content(), test_saved_native_issue_view_recalls_camera_without_annotation(), test_saved_native_parent_camera_uses_portable_world_pose() (+1 more)

### Community 60 - "extension.py"
Cohesion: 0.17
Nodes (6): IssuesExtension, Lifecycle and the Issues menu entry., Manager-owned registration; pending work belongs to the detached controller., ReferenceSelectionWindow, omni_ext, omni_kit_menu_utils

## Knowledge Gaps
- **79 isolated node(s):** `Decision record`, `Authored coverage`, `Lead-run commands`, `Artifacts and inspection`, `Actual results` (+74 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 380 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Omniverse issue management implementation plan` connect `Omniverse issue management implementation plan` to `bcf.py`, `Omniverse issue management specification`, `test_capture_probe.py`, `MarkupAdapter`, `Issues for Omniverse`, `IssuesWindow`, `Implementation verification record`, `service_for_new_scene`, `test_markup.py`, `ViewportAdapter`, `extension.py`, `frames`?**
  _High betweenness centrality (0.181) - this node is a cross-community bridge._
- **Why does `IssuesController` connect `IssuesController` to `bcf.py`, `test_ui.py`, `MarkupAdapter`, `IssueService`, `Settings`, `IssueEditSession`, `._finish_annotation`, `IssuesWindow`, `IssuesToolbarButton`, `._open_details`, `._dispatch`, `DirtyDetailsDialog`, `ViewportAdapter`, `extension.py`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Why does `controller_sdk()` connect `controller_sdk` to `BcfCompatibilityTests`, `test_acc_controller.py`, `test_import_reference.py`, `session_api`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `IssuesController` (e.g. with `ReferenceSelectionRequired` and `IssueEditSession`) actually correct?**
  _`IssuesController` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `ViewportAdapter` (e.g. with `Reopened scene with stale cyan pins` and `IssuesController`) actually correct?**
  _`ViewportAdapter` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `controller_sdk()` (e.g. with `begin()` and `capture()`) actually correct?**
  _`controller_sdk()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Decision record`, `Authored coverage`, `Lead-run commands` to the rest of the system?**
  _79 weakly-connected nodes found - possible documentation gaps or missing edges._