# Graph Report - issues.tag  (2026-10-01)

## Corpus Check
- 73 files · ~61,993 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .xsd 6, (none) 1, .toml 1)

## Summary
- 1157 nodes · 2576 edges · 44 communities (34 shown, 10 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 180 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cdaef6da`
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
- ImportWindow
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
- test_acc_ui.py
- controller_sdk
- ACCUITests
- Stability and saved view recall
- pathlib
- test_acc_controller.py
- test_issue_editor.py
- Widget
- Recovered ACC issue creation and editing requirements
- ACC workflow verification, 2026-10-01
- Details
- ACC issue workflow recovery implementation plan
- ReviewCameraTests

## God Nodes (most connected - your core abstractions)
1. `frames()` - 60 edges
2. `IssuesController` - 53 edges
3. `ViewportAdapter` - 50 edges
4. `ACCUITests` - 47 edges
5. `controller_sdk()` - 41 edges
6. `Omniverse issue management implementation plan` - 39 edges
7. `IssueService` - 38 edges
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
- `Task 2: Recover separate issue list and details panels` --references--> `IssuesWindow`  [INFERRED]
  docs/superpowers/plans/2026-10-01-acc-issue-workflow-recovery.md → issues_tag/window.py

## Import Cycles
- None detected.

## Communities (44 total, 10 thin omitted)

### Community 0 - "test_lifecycle.py"
Cohesion: 0.12
Nodes (16): gc, _failure(), lifecycle_sdk(), destroy(), __init__(), ManagerShutdownTests, Run real lifecycle code with narrow SDK boundaries and injected failures. The…, Resource (+8 more)

### Community 1 - "bcf.py"
Cohesion: 0.07
Nodes (72): base64, copy, BcfDocument, _component(), Conflict, export_view(), import_view(), Map standard BCF world coordinates through a composed USD reference. (+64 more)

### Community 2 - "Omniverse issue management specification"
Cohesion: 0.11
Nodes (18): Acceptance criteria, BCF file exchange, Core workflow, Delivery and review, Omniverse issue management specification, Further Notes, Implementation Decisions, Issue interactions and lifecycle (+10 more)

### Community 3 - "frames"
Cohesion: 0.08
Nodes (57): apply_import(), ImportSummary, _action(), _arrow(), _button(), _close(), _comment_evidence_trace(), _create() (+49 more)

### Community 4 - "enable_extension"
Cohesion: 0.05
Nodes (62): get_runtime_service(), flatten(), omni_kit_viewport_utility, omni_usd, patch, ProgressReportTests, _cancel_native_capture(), caller() (+54 more)

### Community 5 - "MarkupAdapter"
Cohesion: 0.11
Nodes (11): clean_evidence_ui(), overlapping_windows(), Temporarily suppress viewport overlays without changing the application's UI., MarkupAdapter, _native_camera_matches(), Recall an existing native camera without entering Markup review or editing., Evaluate the vendor's attribute-copy result without changing the live scene., Delete this adapter's unsaved native draft in its originating scene. (+3 more)

### Community 6 - "IssueService"
Cohesion: 0.08
Nodes (8): IssueService, operation(), operation(), migrated_operation(), setter, setter, record(), Service

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
Cohesion: 0.11
Nodes (4): _dock_when_ready(), IssueDetailsWindow, IssuesWindow, test_panel_reports_unsupported_scene_schema()

### Community 14 - "Issue viewport design"
Cohesion: 0.25
Nodes (8): Issue viewport design, Pin eligibility, Scoped source identity, Session-layer restoration, Stage-safe picking, Unresolved component retention, Independent pin anchors, Saved review context

### Community 15 - "ImportWindow"
Cohesion: 0.08
Nodes (9): ImportWindow, Review imported BCF field conflicts before applying the import plan., DirtyDetailsDialog, Resolve staged changes before closing details or switching issues., Native issue-panel palette and widget states., IssuesToolbarButton, Issues entry beside Section Box on Kit's main toolbar., omni_kit_widget_toolbar (+1 more)

### Community 16 - "Implementation verification record"
Cohesion: 0.29
Nodes (7): Crash investigation, Decisions and costs, Follow-up development and review, Implementation verification record, Independent review, Open acceptance gates, Runtime evidence

### Community 17 - "Issues panel design"
Cohesion: 0.14
Nodes (14): BCF XML 3.0, Bounded ZIP parsing, Supported BCF file profile, Native viewpoint metadata, Three-way import baseline, Behavior and accessibility, Issues panel design, Explicit import preview (+6 more)

### Community 19 - "test_markup.py"
Cohesion: 0.09
Nodes (31): Cleanup-wave comparison checkpoint, Crash investigation, 2026-09-30, Delivered-frame gate verification, Focused recurrence at 13:47:30 UTC, Isolated follow-up verification, Live viewport remains impaired, Preserved work and evidence, Private rendered run at 13:34:10 UTC (+23 more)

### Community 21 - "verification_dependencies.py"
Cohesion: 0.31
Nodes (9): argparse, shutil, stat, main(), prepare_snapshot(), qualify_extension_paths(), Prepare ordinary dependency copies for verification, without starting Kit., _reject_link() (+1 more)

### Community 22 - "IssueStore"
Cohesion: 0.12
Nodes (11): carb_settings, datetime, copy_issues(), Undo only issue records, preserving unrelated root-layer opinions., restore_issues(), UpdateIssuesCommand, Scene-scoped issue actions and notifications., encode() (+3 more)

### Community 23 - "session_api"
Cohesion: 0.09
Nodes (8): AccBcfTests, AccPersistenceTests, persistence_sdk(), session_api(), CopyEvidenceTests, capture(), discard(), EditSessionTests

### Community 26 - "Pin creation and Markup verification"
Cohesion: 0.50
Nodes (3): Limits, Pin creation and Markup verification, Results

### Community 27 - "ViewportAdapter"
Cohesion: 0.05
Nodes (45): hashlib, attachment_state(), geometry_digest(), make_anchor(), Match source identities within a reference instance, never by proximity., reference_for_prim(), Resolution, resolve_element() (+37 more)

### Community 29 - "IssuesController"
Cohesion: 0.06
Nodes (18): Ownership and shared interfaces, Task 1: Recover staged records, USD migration, and BCF fields, Task 2: Recover separate issue list and details panels, Task 3: Wire creation, editing, and evidence ownership, Task 4: Independent review and complete Composer verification, IssuesController, add(), add() (+10 more)

### Community 30 - "Widget"
Cohesion: 0.07
Nodes (5): ComboModel, ImageWithProvider, Session, ValueModel, Widget

### Community 31 - "test_acc_ui.py"
Cohesion: 0.23
Nodes (10): io, Editable evidence through NVIDIA's supported Markup Core API., Combo, FillPolicy, IwpFillPolicy, Enum, str, Native UI boundary doubles exercise real panel code without a Kit process. (+2 more)

### Community 32 - "controller_sdk"
Cohesion: 0.05
Nodes (11): controller_sdk(), capture(), finish(), ControllerTests, place(), fail(), NativeCallbackDispatchTests, start() (+3 more)

### Community 33 - "ACCUITests"
Cohesion: 0.06
Nodes (8): Markup ownership and USD edit targets, Runtime coverage, Selecting saved evidence without entering annotation, Why the root target remains selected during drawing, ACCUITests, find(), dispatch(), thumbnail()

### Community 34 - "Stability and saved view recall"
Cohesion: 0.40
Nodes (4): Progress, Sequence and evidence, Shared interfaces and ownership, Stability and saved view recall

### Community 35 - "pathlib"
Cohesion: 0.20
Nodes (12): asyncio, importlib_util, os, pathlib, sys, Progress replacement survives transient locks without hiding persistent…, Offline ownership regression; framework events stand in for native render…, Offline draft-deletion ownership checks against public SDK doubles. (+4 more)

### Community 36 - "test_acc_controller.py"
Cohesion: 0.18
Nodes (16): contextlib, dataclasses, importlib, pil, tempfile, Title/type exchange and repeat imports through real project records., Controller transitions with real USD transactions and controlled native…, Offline staged Save and migration checks using real USD and issue commands. (+8 more)

### Community 37 - "test_issue_editor.py"
Cohesion: 0.24
Nodes (5): ast, editor_type(), IssueEditorTests, Offline native-editor behavior checks without importing or replacing Kit…, StringModel

### Community 39 - "Recovered ACC issue creation and editing requirements"
Cohesion: 0.20
Nodes (10): Acceptance workflow, Confirmed intent, Creation and editing, Integration policy for completing the recovered work, Issue list, Recovered ACC issue creation and editing requirements, Recovery status and evidence, Requirements inferred from the unfinished implementation (+2 more)

### Community 40 - "ACC workflow verification, 2026-10-01"
Cohesion: 0.22
Nodes (7): ACC workflow execution decisions, 2026-10-01, Decision record, ACC workflow verification, 2026-10-01, Actual results, Artifacts and inspection, Authored coverage, Lead-run commands

### Community 42 - "ACC issue workflow recovery implementation plan"
Cohesion: 0.29
Nodes (5): ACC issue workflow recovery implementation plan, Global constraints, Recovery record, Review focus, Self-review and handoff

## Knowledge Gaps
- **79 isolated node(s):** `Decision record`, `Authored coverage`, `Lead-run commands`, `Artifacts and inspection`, `Actual results` (+74 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 366 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Omniverse issue management implementation plan` connect `Omniverse issue management implementation plan` to `bcf.py`, `Omniverse issue management specification`, `frames`, `enable_extension`, `Issues for Omniverse`, `ImportWindow`, `test_markup.py`, `IssueStore`, `ViewportAdapter`, `test_acc_ui.py`?**
  _High betweenness centrality (0.161) - this node is a cross-community bridge._
- **Why does `ACCUITests` connect `ACCUITests` to `controller_sdk`, `test_acc_ui.py`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Why does `IssuesController` connect `IssuesController` to `bcf.py`, `frames`, `MarkupAdapter`, `IssueService`, `Settings`, `IssuesWindow`, `ImportWindow`, `ViewportAdapter`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `IssuesController` (e.g. with `IssueEditSession` and `ImportWindow`) actually correct?**
  _`IssuesController` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `ViewportAdapter` (e.g. with `Reopened scene with stale cyan pins` and `IssuesController`) actually correct?**
  _`ViewportAdapter` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `controller_sdk()` (e.g. with `begin()` and `capture()`) actually correct?**
  _`controller_sdk()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Decision record`, `Authored coverage`, `Lead-run commands` to the rest of the system?**
  _79 weakly-connected nodes found - possible documentation gaps or missing edges._