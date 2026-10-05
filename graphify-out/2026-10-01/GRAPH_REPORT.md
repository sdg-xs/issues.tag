# Graph Report - issues.tag  (2026-10-01)

## Corpus Check
- 61 files · ~45,039 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .xsd 6, (none) 1, .toml 1)

## Summary
- 807 nodes · 1771 edges · 40 communities (26 shown, 14 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 104 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cdaef6da`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- lifecycle_sdk
- bcf.py
- Omniverse issue management specification
- IssuesWindow
- ViewportAdapter
- MarkupAdapter
- IssueService
- Omniverse issue management implementation plan
- test_window_cleanup.py
- Settings
- Issues for Omniverse
- graphify
- DraftMarkupTests
- Issues panel design
- Issue viewport design
- ImportWindow
- Implementation verification record
- Supported BCF file profile
- BcfCompatibilityTests
- test_markup.py
- bcf-21-compatibility.md
- verification_dependencies.py
- IssueStore
- test_capture_probe.py
- ._exercise_native_delivery
- RecallTests
- Pin creation and Markup verification
- viewport.py
- DependencySnapshotTests
- IssuesExtension
- replace_progress
- markup.py
- .exercise
- verification-report.md
- Stability and saved view recall
- commands.py
- test_creation.py
- IssueEditor
- Widget
- .restore_viewpoint

## God Nodes (most connected - your core abstractions)
1. `IssuesWindow` - 57 edges
2. `ViewportAdapter` - 50 edges
3. `frames()` - 43 edges
4. `Omniverse issue management implementation plan` - 39 edges
5. `IssueService` - 35 edges
6. `Status` - 32 edges
7. `MarkupAdapter` - 29 edges
8. `enable_extension()` - 29 edges
9. `read_bcf()` - 28 edges
10. `make_anchor()` - 26 edges

## Surprising Connections (you probably didn't know these)
- `Reopened scene with stale cyan pins` --references--> `ViewportAdapter`  [INFERRED]
  docs/crash-investigation-2026-09-30.md → issues_tag/viewport.py
- `Focused recurrence at 13:47:30 UTC` --references--> `test_creation_cancellation_then_scene_replacement_repeated()`  [INFERRED]
  docs/crash-investigation-2026-09-30.md → tests/test_markup.py
- `Timeline` --references--> `test_annotated_comment_reopens_editably()`  [INFERRED]
  docs/crash-investigation-2026-09-30.md → tests/test_markup.py
- `Private rendered run at 13:34:10 UTC` --references--> `test_external_vendor_edit_defers_original_target_restoration()`  [INFERRED]
  docs/crash-investigation-2026-09-30.md → tests/test_markup.py
- `Timeline` --references--> `test_replacement_edit_preserves_newer_explicit_target()`  [INFERRED]
  docs/crash-investigation-2026-09-30.md → tests/test_markup.py

## Import Cycles
- None detected.

## Communities (40 total, 14 thin omitted)

### Community 0 - "lifecycle_sdk"
Cohesion: 0.06
Nodes (37): asyncio, importlib_util, os, pathlib, pil, sys, tempfile, Progress replacement survives transient locks without hiding persistent… (+29 more)

### Community 1 - "bcf.py"
Cohesion: 0.07
Nodes (78): base64, carb_settings, dataclasses, datetime, Enum, apply_import(), BcfDocument, _component() (+70 more)

### Community 2 - "Omniverse issue management specification"
Cohesion: 0.11
Nodes (18): Acceptance criteria, BCF file exchange, Core workflow, Delivery and review, Omniverse issue management specification, Further Notes, Implementation Decisions, Issue interactions and lifecycle (+10 more)

### Community 3 - "IssuesWindow"
Cohesion: 0.07
Nodes (17): IssuesWindow, finished(), preview_panel(), preview_placement_prompt(), Issue panel behavior tests against the active service and its real USD stage., Visible-only native UI evidence, dispatched separately from headless tests., Capture the real armed placement guidance and native Cancel action., require_panel() (+9 more)

### Community 4 - "ViewportAdapter"
Cohesion: 0.05
Nodes (57): importlib, make_anchor(), reference_for_prim(), get_runtime_service(), flatten(), ViewportAdapter, collect(), test_destroy_during_creation_callback_releases_capture() (+49 more)

### Community 6 - "IssueService"
Cohesion: 0.13
Nodes (3): IssueService, operation(), setter

### Community 7 - "Omniverse issue management implementation plan"
Cohesion: 0.13
Nodes (15): Omniverse issue management implementation plan, File structure, Global Constraints, Local evidence and prerequisites, Plan review and execution handoff, Review Focus, Shared interfaces, Task 1: Isolated runtime and extension activation (+7 more)

### Community 8 - "test_window_cleanup.py"
Cohesion: 0.18
Nodes (8): ast, leaf_errors(), make_window(), Standalone destructor checks using SDK boundary stubs, without Kit imports., Resource, Service, window_type(), WindowCleanupTests

### Community 10 - "Issues for Omniverse"
Cohesion: 0.25
Nodes (7): BCF exchange, Current boundaries, Issues for Omniverse, Install and use, Normal scene Save, Verification, Parent USD ownership

### Community 13 - "Issues panel design"
Cohesion: 0.33
Nodes (6): Behavior and accessibility, Issues panel design, Layout, Protected review drafts, Tokens, Verification

### Community 14 - "Issue viewport design"
Cohesion: 0.25
Nodes (8): Issue viewport design, Pin eligibility, Scoped source identity, Session-layer restoration, Stage-safe picking, Unresolved component retention, Independent pin anchors, Saved review context

### Community 15 - "ImportWindow"
Cohesion: 0.13
Nodes (7): ImportWindow, Review imported BCF field conflicts before applying the import plan., Native description entry while the owning workflow manages Markup and…, Native issue-panel palette and widget states., Issues entry beside Section Box on Kit's main toolbar., omni_kit_widget_toolbar, omni_ui

### Community 16 - "Implementation verification record"
Cohesion: 0.29
Nodes (7): Crash investigation, Decisions and costs, Follow-up development and review, Implementation verification record, Independent review, Open acceptance gates, Runtime evidence

### Community 17 - "Supported BCF file profile"
Cohesion: 0.25
Nodes (8): BCF XML 3.0, Bounded ZIP parsing, Supported BCF file profile, Native viewpoint metadata, Three-way import baseline, Explicit import preview, Conflict-aware BCF exchange, Editable Markup evidence

### Community 19 - "test_markup.py"
Cohesion: 0.09
Nodes (31): Cleanup-wave comparison checkpoint, Crash investigation, 2026-09-30, Delivered-frame gate verification, Focused recurrence at 13:47:30 UTC, Isolated follow-up verification, Live viewport remains impaired, Preserved work and evidence, Private rendered run at 13:34:10 UTC (+23 more)

### Community 21 - "verification_dependencies.py"
Cohesion: 0.27
Nodes (10): argparse, json, shutil, stat, main(), prepare_snapshot(), qualify_extension_paths(), Prepare ordinary dependency copies for verification, without starting Kit. (+2 more)

### Community 23 - "test_capture_probe.py"
Cohesion: 0.19
Nodes (19): _cancel_native_capture(), caller(), _markup_prelude_then_native_cancel(), _milestone(), _native_capture(), _native_probe(), _new_scene(), _prepare_camera() (+11 more)

### Community 26 - "Pin creation and Markup verification"
Cohesion: 0.50
Nodes (3): Limits, Pin creation and Markup verification, Results

### Community 27 - "viewport.py"
Cohesion: 0.09
Nodes (27): hashlib, inspect, attachment_state(), geometry_digest(), Match source identities within a reference instance, never by proximity., Resolution, resolve_element(), world_anchor() (+19 more)

### Community 30 - "replace_progress"
Cohesion: 0.33
Nodes (5): patch, ProgressReportTests, time, Bounded Windows sharing-lock recovery for durable verification progress., replace_progress()

### Community 31 - "markup.py"
Cohesion: 0.14
Nodes (10): io, clean_evidence_ui(), overlapping_windows(), Temporarily suppress viewport overlays without changing the application's UI., Editable evidence through NVIDIA's supported Markup Core API., _RootTargetLease, _RootTargetState, omni_kit_app (+2 more)

### Community 33 - "verification-report.md"
Cohesion: 0.22
Nodes (5): Markup ownership and USD edit targets, Runtime coverage, Selecting saved evidence without entering annotation, Why the root target remains selected during drawing, Section Box acceptance verification

### Community 34 - "Stability and saved view recall"
Cohesion: 0.40
Nodes (4): Progress, Sequence and evidence, Shared interfaces and ownership, Stability and saved view recall

### Community 35 - "commands.py"
Cohesion: 0.31
Nodes (5): copy_issues(), Undo only issue records, preserving unrelated root-layer opinions., restore_issues(), UpdateIssuesCommand, omni_kit_commands

### Community 36 - "test_creation.py"
Cohesion: 0.32
Nodes (6): contextlib, exercise_creation(), wait(), Lead-controlled rendered pin, native Markup, save and cancel workflow., test_cancel_pin_markup_draft_leaves_no_issue(), test_pin_opens_markup_and_saves_annotated_initial_view()

### Community 39 - ".restore_viewpoint"
Cohesion: 0.50
Nodes (3): _native_camera_matches(), Recall an existing native camera without entering Markup review or editing., Evaluate the vendor's attribute-copy result without changing the live scene.

## Knowledge Gaps
- **62 isolated node(s):** `Initial BCF import sample`, `Preserved work and evidence`, `Live viewport remains impaired`, `Isolated follow-up verification`, `Sequence-dependent recurrence at 13:57 UTC` (+57 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 272 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Omniverse issue management implementation plan` connect `Omniverse issue management implementation plan` to `verification-report.md`, `bcf.py`, `commands.py`, `Omniverse issue management specification`, `ViewportAdapter`, `Issues for Omniverse`, `ImportWindow`, `test_markup.py`, `viewport.py`, `IssuesExtension`, `markup.py`?**
  _High betweenness centrality (0.206) - this node is a cross-community bridge._
- **Why does `IssuesWindow` connect `IssuesWindow` to `bcf.py`, `viewport.py`, `test_creation.py`, `IssuesExtension`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Why does `Omniverse issue management specification` connect `Omniverse issue management specification` to `Stability and saved view recall`, `Omniverse issue management implementation plan`, `Issues for Omniverse`, `Issue viewport design`, `Supported BCF file profile`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `IssuesWindow` (e.g. with `IssuesExtension` and `Status`) actually correct?**
  _`IssuesWindow` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `ViewportAdapter` (e.g. with `Reopened scene with stale cyan pins` and `IssuesExtension`) actually correct?**
  _`ViewportAdapter` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `IssueService` (e.g. with `IssuesExtension` and `CommentRecord`) actually correct?**
  _`IssueService` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Initial BCF import sample`, `Preserved work and evidence`, `Live viewport remains impaired` to the rest of the system?**
  _62 weakly-connected nodes found - possible documentation gaps or missing edges._