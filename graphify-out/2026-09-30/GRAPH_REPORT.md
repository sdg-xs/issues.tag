# Graph Report - issues.tag  (2026-09-30)

## Corpus Check
- 37 files · ~28,850 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .xsd 6, (none) 1, .toml 1)

## Summary
- 476 nodes · 1112 edges · 21 communities (18 shown, 3 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 59 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cdaef6da`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- extension.py
- bcf.py
- Omniverse issue management specification
- IssuesWindow
- ViewportAdapter
- ImportWindow
- IssueService
- IssueStore
- commands.py
- MarkupAdapter
- Issues for Omniverse
- graphify
- Omniverse issue management implementation plan
- Issues panel design
- Issue viewport design
- make_anchor
- Implementation verification record
- Supported BCF file profile
- markup.py
- test_markup.py
- bcf-21-compatibility.md

## God Nodes (most connected - your core abstractions)
1. `IssuesWindow` - 55 edges
2. `ViewportAdapter` - 49 edges
3. `Omniverse issue management implementation plan` - 39 edges
4. `IssueService` - 34 edges
5. `Status` - 32 edges
6. `frames()` - 30 edges
7. `read_bcf()` - 26 edges
8. `make_anchor()` - 24 edges
9. `Omniverse issue management specification` - 24 edges
10. `MarkupAdapter` - 22 edges

## Surprising Connections (you probably didn't know these)
- `test_issue_comment_status_survive_reopen()` --uses--> `Status`  [INFERRED]
  tests/test_persistence.py → issues_tag/model.py
- `preview_panel()` --uses--> `Status`  [INFERRED]
  tests/test_ui.py → issues_tag/model.py
- `test_panel_record_actions()` --uses--> `Status`  [INFERRED]
  tests/test_ui.py → issues_tag/model.py
- `test_panel_requires_selection_before_editing()` --uses--> `Status`  [INFERRED]
  tests/test_ui.py → issues_tag/model.py
- `preview_issue_pins()` --uses--> `Status`  [INFERRED]
  tests/test_viewpoints.py → issues_tag/model.py

## Import Cycles
- None detected.

## Communities (21 total, 3 thin omitted)

### Community 0 - "extension.py"
Cohesion: 0.10
Nodes (24): carb_settings, importlib, importlib_util, get_runtime_service(), Lifecycle and the Issues menu entry., json, omni_ext, omni_kit_app (+16 more)

### Community 1 - "bcf.py"
Cohesion: 0.08
Nodes (66): base64, dataclasses, datetime, Enum, apply_import(), BcfDocument, _component(), Conflict (+58 more)

### Community 2 - "Omniverse issue management specification"
Cohesion: 0.11
Nodes (18): Acceptance criteria, BCF file exchange, Core workflow, Delivery and review, Omniverse issue management specification, Further Notes, Implementation Decisions, Issue interactions and lifecycle (+10 more)

### Community 3 - "IssuesWindow"
Cohesion: 0.07
Nodes (17): IssuesWindow, finished(), preview_panel(), preview_placement_prompt(), Issue panel behavior tests against the active service and its real USD stage., Visible-only native UI evidence, dispatched separately from headless tests., Capture the real armed placement guidance and native Cancel action., require_panel() (+9 more)

### Community 4 - "ViewportAdapter"
Cohesion: 0.09
Nodes (24): flatten(), ViewportAdapter, omni_kit_viewport_utility, _close_values(), Acceptance coverage for the installed Section Box public integration., test_inactive_viewport_does_not_capture_active_section_box(), test_section_box_controls_and_planes_restore_with_issue(), test_unsectioned_issue_disables_later_section_controller() (+16 more)

### Community 5 - "ImportWindow"
Cohesion: 0.19
Nodes (4): ImportWindow, Review imported BCF field conflicts before applying the import plan., Native issue-panel palette and widget states., omni_ui

### Community 6 - "IssueService"
Cohesion: 0.12
Nodes (3): IssueService, operation(), setter

### Community 8 - "commands.py"
Cohesion: 0.31
Nodes (5): copy_issues(), Undo only issue records, preserving unrelated root-layer opinions., restore_issues(), UpdateIssuesCommand, omni_kit_commands

### Community 9 - "MarkupAdapter"
Cohesion: 0.11
Nodes (4): IssuesExtension, MarkupAdapter, _RootTargetLease, _RootTargetState

### Community 10 - "Issues for Omniverse"
Cohesion: 0.14
Nodes (11): Markup ownership and USD edit targets, Runtime coverage, Why the root target remains selected during drawing, Section Box acceptance verification, BCF exchange, Current boundaries, Issues for Omniverse, Install and use (+3 more)

### Community 12 - "Omniverse issue management implementation plan"
Cohesion: 0.13
Nodes (15): Omniverse issue management implementation plan, File structure, Global Constraints, Local evidence and prerequisites, Plan review and execution handoff, Review Focus, Shared interfaces, Task 1: Isolated runtime and extension activation (+7 more)

### Community 13 - "Issues panel design"
Cohesion: 0.22
Nodes (9): Three-way import baseline, Behavior and accessibility, Issues panel design, Explicit import preview, Layout, Protected review drafts, Tokens, Verification (+1 more)

### Community 14 - "Issue viewport design"
Cohesion: 0.25
Nodes (8): Issue viewport design, Pin eligibility, Scoped source identity, Session-layer restoration, Stage-safe picking, Unresolved component retention, Independent pin anchors, Saved review context

### Community 15 - "make_anchor"
Cohesion: 0.10
Nodes (29): asyncio, hashlib, inspect, attachment_state(), geometry_digest(), make_anchor(), Match source identities within a reference instance, never by proximity., reference_for_prim() (+21 more)

### Community 16 - "Implementation verification record"
Cohesion: 0.29
Nodes (7): Crash investigation, Decisions and costs, Follow-up development and review, Implementation verification record, Independent review, Open acceptance gates, Runtime evidence

### Community 17 - "Supported BCF file profile"
Cohesion: 0.40
Nodes (5): BCF XML 3.0, Bounded ZIP parsing, Supported BCF file profile, Native viewpoint metadata, Editable Markup evidence

### Community 18 - "markup.py"
Cohesion: 0.10
Nodes (13): io, Editable evidence through NVIDIA's supported Markup Core API., os, pil, sys, tempfile, BcfCompatibilityTests, Offline BCF compatibility checks; no Kit app or user scene is opened. (+5 more)

### Community 19 - "test_markup.py"
Cohesion: 0.17
Nodes (17): adapter_for(), test_annotated_comment_reopens_editably(), test_annotation_rejects_overlapping_ownership(), test_annotation_releases_navigation(), test_capture_camera_matches_view_after_markup_activation(), test_capture_preserves_replacement_vendor_owner(), test_capture_stage_change_discards_result(), test_creation_callback_cancellation_releases_markup_and_edit_target() (+9 more)

## Knowledge Gaps
- **49 isolated node(s):** `Initial BCF import sample`, `Why the root target remains selected during drawing`, `Runtime coverage`, `Section Box acceptance verification`, `Runtime evidence` (+44 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 138 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Omniverse issue management implementation plan` connect `Omniverse issue management implementation plan` to `extension.py`, `bcf.py`, `Omniverse issue management specification`, `ViewportAdapter`, `ImportWindow`, `commands.py`, `Issues for Omniverse`, `make_anchor`, `markup.py`, `test_markup.py`?**
  _High betweenness centrality (0.328) - this node is a cross-community bridge._
- **Why does `IssuesWindow` connect `IssuesWindow` to `extension.py`, `MarkupAdapter`, `bcf.py`, `make_anchor`?**
  _High betweenness centrality (0.172) - this node is a cross-community bridge._
- **Why does `Omniverse issue management specification` connect `Omniverse issue management specification` to `Issues for Omniverse`, `Omniverse issue management implementation plan`, `Issues panel design`, `Issue viewport design`, `Supported BCF file profile`?**
  _High betweenness centrality (0.133) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `IssuesWindow` (e.g. with `IssuesExtension` and `Status`) actually correct?**
  _`IssuesWindow` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `ViewportAdapter` (e.g. with `IssuesExtension` and `MarkupAdapter`) actually correct?**
  _`ViewportAdapter` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `IssueService` (e.g. with `IssuesExtension` and `CommentRecord`) actually correct?**
  _`IssueService` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Status` (e.g. with `apply_import()` and `plan_import()`) actually correct?**
  _`Status` has 14 INFERRED edges - model-reasoned connections that need verification._