# Graph Report - issues.tag  (2026-10-05)

## Corpus Check
- 73 files · ~63,126 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .xsd 6, (none) 1, .toml 1)

## Summary
- 1180 nodes · 2627 edges · 62 communities (45 shown, 17 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 181 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `77b79d47`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_lifecycle.py
- bcf.py
- Omniverse issue management specification
- frames
- enable_extension
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
- verification_dependencies.py
- IssueStore
- session_api
- ._exercise_native_delivery
- RecallTests
- Pin creation and Markup verification
- ViewportAdapter
- DependencySnapshotTests
- IssuesController
- Widget
- markup.py
- controller_sdk
- ACCUITests
- Stability and saved view recall
- test_capture_probe.py
- test_acc_controller.py
- asyncio
- Widget
- Recovered ACC issue creation and editing requirements
- ACC workflow verification, 2026-10-01
- Details
- ACC issue workflow recovery implementation plan
- Ownership and shared interfaces
- ._finish_annotation
- pathlib
- Service
- ComboModel
- service_for_new_scene
- Crash investigation, 2026-09-30
- verify_kit.py
- commands.py
- replace_progress
- AccBcfTests
- test_acc_ui.py
- Markup ownership and USD edit targets
- ._dispatch
- DirtyDetailsDialog
- Combo
- panel_types
- IssuesExtension

## God Nodes (most connected - your core abstractions)
1. `frames()` - 61 edges
2. `IssuesController` - 53 edges
3. `ACCUITests` - 51 edges
4. `ViewportAdapter` - 50 edges
5. `controller_sdk()` - 41 edges
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

## Communities (62 total, 17 thin omitted)

### Community 0 - "test_lifecycle.py"
Cohesion: 0.10
Nodes (17): gc, _failure(), lifecycle_sdk(), destroy(), __init__(), ManagerShutdownTests, Run real lifecycle code with narrow SDK boundaries and injected failures. The…, Resource (+9 more)

### Community 1 - "bcf.py"
Cohesion: 0.06
Nodes (77): base64, copy, apply_import(), BcfDocument, _component(), Conflict, export_view(), import_view() (+69 more)

### Community 2 - "Omniverse issue management specification"
Cohesion: 0.11
Nodes (18): Acceptance criteria, BCF file exchange, Core workflow, Delivery and review, Omniverse issue management specification, Further Notes, Implementation Decisions, Issue interactions and lifecycle (+10 more)

### Community 3 - "frames"
Cohesion: 0.09
Nodes (53): _action(), _arrow(), _button(), _close(), _comment_evidence_trace(), _create(), _disable_runtime(), _discard() (+45 more)

### Community 4 - "enable_extension"
Cohesion: 0.16
Nodes (16): get_runtime_service(), flatten(), omni_kit_viewport_utility, omni_usd, test_destroy_during_creation_callback_releases_capture(), cancel_and_destroy(), test_extension_activation_and_shutdown(), test_markup_compatibility() (+8 more)

### Community 5 - "MarkupAdapter"
Cohesion: 0.09
Nodes (17): MarkupAdapter, _native_camera_matches(), Recall an existing native camera without entering Markup review or editing., Evaluate the vendor's attribute-copy result without changing the live scene., Delete this adapter's unsaved native draft in its originating scene., Copy saved annotations into owned evidence; never edit the saved prim., _RootTargetLease, _RootTargetState (+9 more)

### Community 6 - "IssueService"
Cohesion: 0.08
Nodes (8): IssueService, operation(), migrated_operation(), setter, caller(), CopyEvidenceTests, capture(), discard()

### Community 7 - "Omniverse issue management implementation plan"
Cohesion: 0.13
Nodes (15): Omniverse issue management implementation plan, File structure, Global Constraints, Local evidence and prerequisites, Plan review and execution handoff, Review Focus, Shared interfaces, Task 1: Isolated runtime and extension activation (+7 more)

### Community 8 - "test_window_cleanup.py"
Cohesion: 0.17
Nodes (9): ast, inspect, leaf_errors(), make_window(), Standalone destructor checks using SDK boundary stubs, without Kit imports., Resource, Service, window_type() (+1 more)

### Community 9 - "Settings"
Cohesion: 0.17
Nodes (4): finish(), EvidenceCaptureTests, window(), Settings

### Community 10 - "Issues for Omniverse"
Cohesion: 0.17
Nodes (8): Section Box acceptance verification, BCF exchange, Current boundaries, Issues for Omniverse, Install and use, Normal scene Save, Verification, Parent USD ownership

### Community 13 - "IssuesWindow"
Cohesion: 0.06
Nodes (12): Review imported BCF field conflicts before applying the import plan., Resolve staged changes before closing details or switching issues., Native issue-panel palette and widget states., _dock_when_ready(), IssueDetailsWindow, IssuesWindow, IssueTypesWindow, Separate dockable issue list and staged details panels. (+4 more)

### Community 14 - "Issue viewport design"
Cohesion: 0.25
Nodes (8): Issue viewport design, Pin eligibility, Scoped source identity, Session-layer restoration, Stage-safe picking, Unresolved component retention, Independent pin anchors, Saved review context

### Community 15 - "IssuesToolbarButton"
Cohesion: 0.15
Nodes (4): drain(), IssuesToolbarButton, Issues entry beside Section Box on Kit's main toolbar., omni_kit_widget_toolbar

### Community 16 - "Implementation verification record"
Cohesion: 0.29
Nodes (7): Crash investigation, Decisions and costs, Follow-up development and review, Implementation verification record, Independent review, Open acceptance gates, Runtime evidence

### Community 17 - "Issues panel design"
Cohesion: 0.14
Nodes (14): BCF XML 3.0, Bounded ZIP parsing, Supported BCF file profile, Native viewpoint metadata, Three-way import baseline, Behavior and accessibility, Issues panel design, Explicit import preview (+6 more)

### Community 19 - "test_markup.py"
Cohesion: 0.16
Nodes (20): Focused recurrence at 13:47:30 UTC, Timeline, adapter_for(), _capture_cycle_phase(), test_annotated_comment_reopens_editably(), test_annotation_rejects_overlapping_ownership(), test_annotation_releases_navigation(), test_capture_camera_matches_view_after_markup_activation() (+12 more)

### Community 21 - "verification_dependencies.py"
Cohesion: 0.29
Nodes (9): argparse, json, shutil, stat, main(), prepare_snapshot(), Prepare ordinary dependency copies for verification, without starting Kit., _reject_link() (+1 more)

### Community 22 - "IssueStore"
Cohesion: 0.29
Nodes (3): encode(), IssueStore, Materialize derived legacy fields once, inside the caller's undo command.

### Community 23 - "session_api"
Cohesion: 0.15
Nodes (4): AccPersistenceTests, persistence_sdk(), session_api(), EditSessionTests

### Community 26 - "Pin creation and Markup verification"
Cohesion: 0.50
Nodes (3): Limits, Pin creation and Markup verification, Results

### Community 27 - "ViewportAdapter"
Cohesion: 0.06
Nodes (43): hashlib, attachment_state(), geometry_digest(), make_anchor(), Match source identities within a reference instance, never by proximity., reference_for_prim(), Resolution, resolve_element() (+35 more)

### Community 29 - "IssuesController"
Cohesion: 0.18
Nodes (4): IssuesController, add(), add(), focus()

### Community 31 - "markup.py"
Cohesion: 0.17
Nodes (11): contextlib, io, clean_evidence_ui(), overlapping_windows(), Temporarily suppress viewport overlays without changing the application's UI., Editable evidence through NVIDIA's supported Markup Core API., os, pil (+3 more)

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
Cohesion: 0.21
Nodes (18): _cancel_native_capture(), _markup_prelude_then_native_cancel(), _milestone(), _native_capture(), _native_probe(), _new_scene(), _prepare_camera(), Explicit capture diagnostics: select Case capture_probe, never part of Case all. (+10 more)

### Community 36 - "test_acc_controller.py"
Cohesion: 0.25
Nodes (11): dataclasses, importlib, Title/type exchange and repeat imports through real project records., Controller transitions with real USD transactions and controlled native…, Offline staged Save and migration checks using real USD and issue commands., Copy annotation specs into draft evidence without changing saved native prims., Draft changes preserve saved records and evidence until details Save., Creation retries keep the same draft and accept only a complete Save. (+3 more)

### Community 37 - "asyncio"
Cohesion: 0.24
Nodes (5): asyncio, editor_type(), IssueEditorTests, Offline native-editor behavior checks without importing or replacing Kit…, StringModel

### Community 39 - "Recovered ACC issue creation and editing requirements"
Cohesion: 0.20
Nodes (10): Acceptance workflow, Confirmed intent, Creation and editing, Integration policy for completing the recovered work, Issue list, Recovered ACC issue creation and editing requirements, Recovery status and evidence, Requirements inferred from the unfinished implementation (+2 more)

### Community 40 - "ACC workflow verification, 2026-10-01"
Cohesion: 0.22
Nodes (7): ACC workflow execution decisions, 2026-10-01, Decision record, ACC workflow verification, 2026-10-01, Actual results, Artifacts and inspection, Authored coverage, Lead-run commands

### Community 42 - "ACC issue workflow recovery implementation plan"
Cohesion: 0.29
Nodes (5): ACC issue workflow recovery implementation plan, Global constraints, Recovery record, Review focus, Self-review and handoff

### Community 43 - "Ownership and shared interfaces"
Cohesion: 0.27
Nodes (5): Ownership and shared interfaces, Task 1: Recover staged records, USD migration, and BCF fields, Task 2: Recover separate issue list and details panels, Task 3: Wire creation, editing, and evidence ownership, Task 4: Independent review and complete Composer verification

### Community 44 - "._finish_annotation"
Cohesion: 0.23
Nodes (4): annotate(), capture(), open_view(), reattach()

### Community 45 - "pathlib"
Cohesion: 0.22
Nodes (10): importlib_util, pathlib, sys, Progress replacement survives transient locks without hiding persistent…, Offline ownership regression; framework events stand in for native render…, Offline draft-deletion ownership checks against public SDK doubles., Evidence keeps render/Markup content and restores controls on every exit., Portable recall reuses the primary perspective camera without changing saved… (+2 more)

### Community 46 - "Service"
Cohesion: 0.15
Nodes (5): operation(), operation(), setter, record(), Service

### Community 48 - "service_for_new_scene"
Cohesion: 0.27
Nodes (8): service_for_new_scene(), test_failed_issue_transaction_has_no_partial_records(), test_issue_comment_status_survive_reopen(), test_issue_undo_preserves_unrelated_scene_edits(), test_listeners_observe_complete_records(), test_root_layer_ownership_and_read_only(), test_unsaved_state_and_next_reviewer(), test_viewpoint_lookup_does_not_walk_building_geometry()

### Community 49 - "Crash investigation, 2026-09-30"
Cohesion: 0.18
Nodes (11): Cleanup-wave comparison checkpoint, Crash investigation, 2026-09-30, Delivered-frame gate verification, Isolated follow-up verification, Live viewport remains impaired, Preserved work and evidence, Private rendered run at 13:34:10 UTC, Recurrence after delivered-frame gate at 14:40 UTC (+3 more)

### Community 50 - "verify_kit.py"
Cohesion: 0.28
Nodes (8): carb_settings, datetime, qualify_runtime(), Run behavior checks in a separate Kit process, never the user's scene., run(), write_progress(), qualify_extension_paths(), traceback

### Community 51 - "commands.py"
Cohesion: 0.31
Nodes (5): copy_issues(), Undo only issue records, preserving unrelated root-layer opinions., restore_issues(), UpdateIssuesCommand, omni_kit_commands

### Community 52 - "replace_progress"
Cohesion: 0.33
Nodes (5): patch, ProgressReportTests, time, Bounded Windows sharing-lock recovery for durable verification progress., replace_progress()

### Community 54 - "test_acc_ui.py"
Cohesion: 0.36
Nodes (7): FillPolicy, IwpFillPolicy, Enum, str, Native UI boundary doubles exercise real panel code without a Kit process., Status, weakref

### Community 55 - "Markup ownership and USD edit targets"
Cohesion: 0.40
Nodes (5): Markup ownership and USD edit targets, Runtime coverage, Selecting saved evidence without entering annotation, Why the root target remains selected during drawing, thumbnail()

### Community 58 - "Combo"
Cohesion: 0.29
Nodes (3): Combo, ImageWithProvider, Session

## Knowledge Gaps
- **79 isolated node(s):** `Decision record`, `Authored coverage`, `Lead-run commands`, `Artifacts and inspection`, `Actual results` (+74 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 369 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Omniverse issue management implementation plan` connect `Omniverse issue management implementation plan` to `bcf.py`, `Omniverse issue management specification`, `enable_extension`, `Issues for Omniverse`, `IssuesWindow`, `service_for_new_scene`, `verify_kit.py`, `commands.py`, `test_markup.py`, `ViewportAdapter`, `IssuesExtension`, `markup.py`?**
  _High betweenness centrality (0.153) - this node is a cross-community bridge._
- **Why does `ACCUITests` connect `ACCUITests` to `panel_types`, `test_acc_ui.py`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Why does `Omniverse issue management specification` connect `Omniverse issue management specification` to `Stability and saved view recall`, `Omniverse issue management implementation plan`, `ACC workflow verification, 2026-10-01`, `Issues for Omniverse`, `ACC issue workflow recovery implementation plan`, `Issue viewport design`, `Issues panel design`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `IssuesController` (e.g. with `IssueEditSession` and `ImportWindow`) actually correct?**
  _`IssuesController` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `ViewportAdapter` (e.g. with `Reopened scene with stale cyan pins` and `IssuesController`) actually correct?**
  _`ViewportAdapter` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `controller_sdk()` (e.g. with `begin()` and `capture()`) actually correct?**
  _`controller_sdk()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Decision record`, `Authored coverage`, `Lead-run commands` to the rest of the system?**
  _79 weakly-connected nodes found - possible documentation gaps or missing edges._