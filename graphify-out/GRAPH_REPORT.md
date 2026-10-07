# Graph Report - issues.tag  (2026-10-07)

## Corpus Check
- 88 files · ~78,503 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .xsd 6, (none) 1, .toml 1)

## Summary
- 1391 nodes · 3171 edges · 68 communities (44 shown, 24 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 213 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- lifecycle_sdk
- Omniverse issue management specification
- frames
- test_bcf_camera_workflow.py
- MarkupAdapter
- IssueService
- Omniverse issue management implementation plan
- test_window_cleanup.py
- Settings
- test_acc_controller.py
- graphify
- DraftMarkupTests
- IssuesWindow
- Issue viewport design
- IssuesToolbarButton
- IssueStore
- Supported BCF file profile
- BcfCompatibilityTests
- test_markup.py
- ComboModel
- ValueModel
- commands.py
- AccPersistenceTests
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
- pathlib
- test_issue_editor.py
- Widget
- Recovered ACC issue creation and editing requirements
- ACC workflow verification, 2026-10-01
- Details
- verify_kit.py
- Ownership and shared interfaces
- IssuesController
- CameraOptionsTests
- pxr
- BCF camera alignment
- AccBcfTests
- viewport.py
- ImportWindow
- logging
- SDD ledger — plan: docs/superpowers/plans/2026-10-07-bcf-camera-alignment.md
- enable_extension
- Implementation verification record
- bcf.py
- ._dispatch
- DirtyDetailsDialog
- ImportCameraReviewTests
- ACC issue workflow recovery implementation plan
- Issues panel design
- .test_acceptance_click_preserves_panels_and_refinds_after_public_focus
- .test_author_setting_uses_owner_dispatcher_without_rewriting_saved_attribution
- ImportCameraPreviewTests
- IssuesExtension
- editor_type
- .test_screenshot_provider_reuses_decoded_evidence_and_releases_on_clear
- collect

## God Nodes (most connected - your core abstractions)
1. `frames()` - 71 edges
2. `IssuesController` - 57 edges
3. `ACCUITests` - 51 edges
4. `ViewportAdapter` - 50 edges
5. `controller_sdk()` - 43 edges
6. `IssueService` - 39 edges
7. `Omniverse issue management implementation plan` - 39 edges
8. `Status` - 36 edges
9. `enable_extension()` - 35 edges
10. `read_bcf()` - 34 edges

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

## Communities (68 total, 24 thin omitted)

### Community 0 - "lifecycle_sdk"
Cohesion: 0.09
Nodes (20): gc, importlib_util, Evidence keeps render/Markup content and restores controls on every exit., _failure(), lifecycle_sdk(), destroy(), __init__(), ManagerShutdownTests (+12 more)

### Community 2 - "Omniverse issue management specification"
Cohesion: 0.10
Nodes (20): Normal scene Save, Acceptance criteria, BCF file exchange, Core workflow, Delivery and review, Omniverse issue management specification, Further Notes, Implementation Decisions (+12 more)

### Community 3 - "frames"
Cohesion: 0.09
Nodes (53): _action(), _arrow(), _button(), _close(), _comment_evidence_trace(), _create(), _disable_runtime(), _discard() (+45 more)

### Community 4 - "test_bcf_camera_workflow.py"
Cohesion: 0.05
Nodes (41): difflib, Camera review and corrections, Initial BCF import sample, ACC limits, BCF camera verification, 2026-10-07, Evidence and commands, Preview ownership found by native testing, Runtime and fixture (+33 more)

### Community 5 - "MarkupAdapter"
Cohesion: 0.08
Nodes (20): clean_evidence_ui(), overlapping_windows(), Temporarily suppress viewport overlays without changing the application's UI., MarkupAdapter, _native_camera_matches(), Recall an existing native camera without entering Markup review or editing., Evaluate the vendor's attribute-copy result without changing the live scene., Delete this adapter's unsaved native draft in its originating scene. (+12 more)

### Community 6 - "IssueService"
Cohesion: 0.07
Nodes (9): IssueService, operation(), operation(), operation(), migrated_operation(), setter, setter, record() (+1 more)

### Community 7 - "Omniverse issue management implementation plan"
Cohesion: 0.09
Nodes (21): Section Box acceptance verification, Omniverse issue management implementation plan, File structure, Global Constraints, Local evidence and prerequisites, Plan review and execution handoff, Review Focus, Shared interfaces (+13 more)

### Community 8 - "test_window_cleanup.py"
Cohesion: 0.21
Nodes (7): leaf_errors(), make_window(), Standalone destructor checks using SDK boundary stubs, without Kit imports., Resource, Service, window_type(), WindowCleanupTests

### Community 9 - "Settings"
Cohesion: 0.17
Nodes (4): finish(), EvidenceCaptureTests, window(), Settings

### Community 10 - "test_acc_controller.py"
Cohesion: 0.27
Nodes (5): Controller transitions with real USD transactions and controlled native…, persistence_sdk(), session_api(), EditSessionTests, Creation retries keep the same draft and accept only a complete Save.

### Community 13 - "IssuesWindow"
Cohesion: 0.08
Nodes (6): _dock_when_ready(), IssueDetailsWindow, IssuesWindow, IssueTypesWindow, test_panel_manage_types_create_delete_and_undo(), test_panel_reports_unsupported_scene_schema()

### Community 14 - "Issue viewport design"
Cohesion: 0.25
Nodes (8): Issue viewport design, Pin eligibility, Scoped source identity, Session-layer restoration, Stage-safe picking, Unresolved component retention, Independent pin anchors, Saved review context

### Community 16 - "IssueStore"
Cohesion: 0.26
Nodes (3): encode(), IssueStore, Materialize derived legacy fields once, inside the caller's undo command.

### Community 17 - "Supported BCF file profile"
Cohesion: 0.25
Nodes (8): BCF XML 3.0, Bounded ZIP parsing, Supported BCF file profile, Native viewpoint metadata, Three-way import baseline, Explicit import preview, Conflict-aware BCF exchange, Editable Markup evidence

### Community 18 - "BcfCompatibilityTests"
Cohesion: 0.09
Nodes (3): BcfCompatibilityTests, ImportReferenceTests, reference_window_type()

### Community 19 - "test_markup.py"
Cohesion: 0.09
Nodes (33): Cleanup-wave comparison checkpoint, Crash investigation, 2026-09-30, Delivered-frame gate verification, Focused recurrence at 13:47:30 UTC, Isolated follow-up verification, Live viewport remains impaired, Preserved work and evidence, Private rendered run at 13:34:10 UTC (+25 more)

### Community 20 - "ComboModel"
Cohesion: 0.17
Nodes (3): ComboModel, ImageWithProvider, Session

### Community 22 - "commands.py"
Cohesion: 0.31
Nodes (5): copy_issues(), Undo only issue records, preserving unrelated root-layer opinions., restore_issues(), UpdateIssuesCommand, omni_kit_commands

### Community 26 - "Pin creation and Markup verification"
Cohesion: 0.50
Nodes (3): Limits, Pin creation and Markup verification, Results

### Community 27 - "ViewportAdapter"
Cohesion: 0.10
Nodes (15): make_anchor(), ViewportAdapter, preview_issue_pins(), require_viewport(), test_completed_pick_cannot_cross_scene_close(), test_imported_metadata_does_not_invalidate_coordinate_frame(), test_overlay_tracks_scene_and_stage_scope(), test_pin_cache_tracks_camera_parent_geometry() (+7 more)

### Community 29 - "._operation"
Cohesion: 0.11
Nodes (6): add(), add(), annotate(), focus(), open_view(), reattach()

### Community 30 - "test_acc_ui.py"
Cohesion: 0.09
Nodes (13): Combo, FillPolicy, IwpFillPolicy, panel_types(), Enum, str, Native UI boundary doubles exercise real panel code without a Kit process., Status (+5 more)

### Community 31 - "service_for_new_scene"
Cohesion: 0.27
Nodes (8): service_for_new_scene(), test_failed_issue_transaction_has_no_partial_records(), test_issue_comment_status_survive_reopen(), test_issue_undo_preserves_unrelated_scene_edits(), test_listeners_observe_complete_records(), test_root_layer_ownership_and_read_only(), test_unsaved_state_and_next_reviewer(), test_viewpoint_lookup_does_not_walk_building_geometry()

### Community 32 - "controller_sdk"
Cohesion: 0.06
Nodes (10): controller_sdk(), capture(), finish(), ControllerTests, place(), fail(), NativeCallbackDispatchTests, start() (+2 more)

### Community 34 - "Stability and saved view recall"
Cohesion: 0.40
Nodes (4): Progress, Sequence and evidence, Shared interfaces and ownership, Stability and saved view recall

### Community 35 - "test_capture_probe.py"
Cohesion: 0.09
Nodes (34): argparse, patch, shutil, stat, ProgressReportTests, _cancel_native_capture(), caller(), _markup_prelude_then_native_cancel() (+26 more)

### Community 36 - "pathlib"
Cohesion: 0.12
Nodes (28): contextlib, dataclasses, importlib, io, Editable evidence through NVIDIA's supported Markup Core API., json, math, pathlib (+20 more)

### Community 37 - "test_issue_editor.py"
Cohesion: 0.33
Nodes (3): ast, Offline native-editor behavior checks without importing or replacing Kit…, StringModel

### Community 39 - "Recovered ACC issue creation and editing requirements"
Cohesion: 0.20
Nodes (10): Acceptance workflow, Confirmed intent, Creation and editing, Integration policy for completing the recovered work, Issue list, Recovered ACC issue creation and editing requirements, Recovery status and evidence, Requirements inferred from the unfinished implementation (+2 more)

### Community 40 - "ACC workflow verification, 2026-10-01"
Cohesion: 0.22
Nodes (7): ACC workflow execution decisions, 2026-10-01, Decision record, ACC workflow verification, 2026-10-01, Actual results, Artifacts and inspection, Authored coverage, Lead-run commands

### Community 42 - "verify_kit.py"
Cohesion: 0.14
Nodes (13): asyncio, inspect, os, sys, Progress replacement survives transient locks without hiding persistent…, Offline ownership regression; framework events stand in for native render…, Rendered check of the Issues entry on Kit's main toolbar., Offline routing tests; native camera/render behavior still needs Kit… (+5 more)

### Community 43 - "Ownership and shared interfaces"
Cohesion: 0.27
Nodes (5): Ownership and shared interfaces, Task 1: Recover staged records, USD migration, and BCF fields, Task 2: Recover separate issue list and details panels, Task 3: Wire creation, editing, and evidence ownership, Task 4: Independent review and complete Composer verification

### Community 45 - "CameraOptionsTests"
Cohesion: 0.21
Nodes (4): CameraOptionsTests, CopyEvidenceTests, capture(), discard()

### Community 46 - "pxr"
Cohesion: 0.20
Nodes (18): hashlib, attachment_state(), geometry_digest(), Match source identities within a reference instance, never by proximity., Resolution, resolve_element(), world_anchor(), pin_is_visible() (+10 more)

### Community 47 - "BCF camera alignment"
Cohesion: 0.33
Nodes (5): Acceptance limits, BCF camera alignment, Global constraints, Intent, Required behavior

### Community 49 - "viewport.py"
Cohesion: 0.12
Nodes (9): matrix(), _PinManipulator, on_build(), _PlacementClick, on_ended(), Review camera state and surface anchors for one native viewport., Build a native scene gesture without requiring a global input hook., _ViewportItem (+1 more)

### Community 50 - "ImportWindow"
Cohesion: 0.08
Nodes (13): copy, ViewpointImportOptions, camera_diagnostics(), Read-only camera evidence for BCF import review and offline reports., Pair retained source evidence with converted cameras by viewpoint UUID., ImportWindow, Review imported BCF field conflicts before applying the import plan., ReferenceSelectionWindow (+5 more)

### Community 52 - "SDD ledger — plan: docs/superpowers/plans/2026-10-07-bcf-camera-alignment.md"
Cohesion: 0.29
Nodes (6): BCF camera development record, Final review — BCF camera alignment, Final reviewer declined-to-judge adjudication, Preflight, SDD ledger — plan: docs/superpowers/plans/2026-10-07-bcf-camera-alignment.md, Tasks

### Community 53 - "enable_extension"
Cohesion: 0.18
Nodes (14): get_runtime_service(), flatten(), omni_usd, test_extension_activation_and_shutdown(), test_markup_compatibility(), test_native_pin_registry_cleanup_across_reload_and_reopen(), _close_values(), test_inactive_viewport_does_not_capture_active_section_box() (+6 more)

### Community 54 - "Implementation verification record"
Cohesion: 0.29
Nodes (7): Crash investigation, Decisions and costs, Follow-up development and review, Implementation verification record, Independent review, Open acceptance gates, Runtime evidence

### Community 55 - "bcf.py"
Cohesion: 0.05
Nodes (89): base64, carb_settings, datetime, apply_import(), BcfDocument, _component(), Conflict, export_view() (+81 more)

### Community 59 - "ACC issue workflow recovery implementation plan"
Cohesion: 0.29
Nodes (5): ACC issue workflow recovery implementation plan, Global constraints, Recovery record, Review focus, Self-review and handoff

### Community 60 - "Issues panel design"
Cohesion: 0.33
Nodes (6): Behavior and accessibility, Issues panel design, Layout, Protected review drafts, Tokens, Verification

### Community 68 - ".test_screenshot_provider_reuses_decoded_evidence_and_releases_on_clear"
Cohesion: 0.17
Nodes (5): Markup ownership and USD edit targets, Runtime coverage, Selecting saved evidence without entering annotation, Why the root target remains selected during drawing, thumbnail()

## Knowledge Gaps
- **99 isolated node(s):** `Decision record`, `Authored coverage`, `Lead-run commands`, `Artifacts and inspection`, `Actual results` (+94 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 427 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Omniverse issue management implementation plan` connect `Omniverse issue management implementation plan` to `IssuesExtension`, `Omniverse issue management specification`, `pathlib`, `verify_kit.py`, `pxr`, `viewport.py`, `ImportWindow`, `test_markup.py`, `enable_extension`, `commands.py`, `bcf.py`, `ViewportAdapter`, `service_for_new_scene`?**
  _High betweenness centrality (0.160) - this node is a cross-community bridge._
- **Why does `Omniverse issue management specification` connect `Omniverse issue management specification` to `Stability and saved view recall`, `Omniverse issue management implementation plan`, `ACC workflow verification, 2026-10-01`, `Issue viewport design`, `Supported BCF file profile`, `ACC issue workflow recovery implementation plan`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `IssuesController` connect `IssuesController` to `IssuesExtension`, `frames`, `test_bcf_camera_workflow.py`, `MarkupAdapter`, `IssueService`, `Settings`, `Ownership and shared interfaces`, `IssuesWindow`, `IssuesToolbarButton`, `ImportWindow`, `bcf.py`, `._dispatch`, `DirtyDetailsDialog`, `ViewportAdapter`, `._operation`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `IssuesController` (e.g. with `ReferenceSelectionRequired` and `IssueEditSession`) actually correct?**
  _`IssuesController` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `ViewportAdapter` (e.g. with `Reopened scene with stale cyan pins` and `IssuesController`) actually correct?**
  _`ViewportAdapter` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `controller_sdk()` (e.g. with `begin()` and `capture()`) actually correct?**
  _`controller_sdk()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Decision record`, `Authored coverage`, `Lead-run commands` to the rest of the system?**
  _99 weakly-connected nodes found - possible documentation gaps or missing edges._