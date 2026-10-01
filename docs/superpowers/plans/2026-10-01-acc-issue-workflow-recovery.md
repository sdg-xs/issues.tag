# ACC issue workflow recovery implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Complete the recovered ACC-style workflow with separate issue browsing and staged creation/editing in USD Composer.

**Architecture:** Preserve the recovered `IssueEditSession` as the boundary between UI drafts and persistent USD records. The list and details panels call a lead-owned controller that coordinates placement, native Markup, draft cleanup, and atomic Save. Reuse existing saved-view recall and BCF integration.

**Tech stack:** Python, native `omni.ui`, OpenUSD, installed NVIDIA Markup Core/Tool, and BCF XML file exchange.

**Spec:** [Recovered requirements](../specs/2026-10-01-acc-issue-workflow-recovered.md) and [baseline SPEC.md](../../../SPEC.md).

## Recovery record

This plan is reconstructed from user clarification and unfinished source, not fetched verbatim from the closed `/btw` conversation. Source: `C:/Users/StevenGomba/.codex/tmp/acc-workflow-20261001/issues.tag`. Verified local snapshot: `verification/recovery/acc-workflow-20261001.zip` and its adjacent hash manifest. Preserve that snapshot before moving or editing the partial checkout.

No task below is marked complete merely because a partial implementation exists. The old extension controller and new window interface are incompatible. No recovery-specific runtime results were found. Do not copy the unfinished checkout directly into Composer.

## Global constraints

- The parent USD owns project-wide records and accepted evidence; referenced building layers remain unchanged.
- One person edits at a time. Assignment and permission settings are deferred.
- Statuses are Open, In progress, Resolved, and Closed.
- Creation and editing use separate details UI from the issue list.
- Saved native evidence uses public Markup recall; primary portable views reuse the existing perspective camera where safe.
- New or edited records persist only on details Save. Scene Save remains the disk persistence action.
- Only the lead launches Kit. Close user Composer before rendered verification or deployment; never modify shared NVIDIA SDK files.
- Use global Graphify before code exploration and after source edits. Preserve live uncommitted work and audit differences before copying files.

## Review focus

1. Dirty close or issue switching must not lose edits or silently save them. Owned by Task 3.
2. Cancelling annotation/replacement must preserve previously saved evidence. Owned by Task 3.
3. A scene replacement, stale saved record, or read-only scene must reject Save without partial persistent changes. Owned by Task 1 and Task 3.
4. Filters must not obstruct new placement or make the newly saved issue appear lost. Owned by Task 2 and Task 3.
5. Legacy issue data and repeated BCF imports must retain identities, comments, evidence, and stable display numbers. Owned by Task 1.

## Ownership and shared interfaces

Agree these contracts before workers start. Never let workers edit the same file concurrently.

| Owner | Exclusive files | Responsibility |
| --- | --- | --- |
| Persistence/BCF worker | `issues_tag/model.py`, `store.py`, `service.py`, `edit_session.py`, `bcf.py`; `tests/test_edit_session.py`, `tests/test_acc_persistence.py`, `tests/test_acc_bcf.py` | Draft records, legacy migration, atomic Save, project types and BCF fields |
| UI worker using frontend-design | `issues_tag/window.py`, `styles.py`; `tests/test_acc_ui.py` | Separate list/details UI and callback contracts |
| Lead | `issues_tag/extension.py`, `markup.py`, `viewport.py`, `issue_editor.py`; `tests/test_acc_controller.py`, `tests/test_acc_workflow.py`; integration documents | Creation/edit controller, owned draft evidence, filtered pins, old caller migration and runtime checks |
| Independent reviewer | Read-only combined changes | Requirements, lifecycle, backwards compatibility and user workflow |

Retain unrelated toolbar and clean screenshot changes already present in the live checkout.

Recovered shared contracts:

- `IssueRecord.title: str`, `issue_type: str`, `number: int`, with backwards-compatible defaults.
- `IssueEditSession.create(service, anchor, issue_type, viewpoint) -> IssueEditSession`.
- `IssueEditSession.edit(service, issue_id) -> IssueEditSession`.
- `IssueEditSession.update(**fields) -> None`, `require_current(service) -> None`, and `is_new`/`dirty` properties.
- `IssueService.list_types() -> tuple[str, ...]`, `create_type(name: str) -> str`, `commit_session(session: IssueEditSession) -> str`.
- `IssuesWindow(service, *, on_select, on_create, on_import, on_export, on_error)`, plus `show()`, `refresh()`, and `destroy()`.
- `IssueDetailsWindow(session, types, *, on_save, on_cancel, on_annotate, on_replace, on_comment_view)`, plus `sync()`, `set_error(message)`, `set_busy(busy)`, `refresh()`, and `destroy()`.
- `MarkupAdapter.copy_for_edit(record: ViewpointRecord) -> ViewpointRecord` is asynchronous. The returned native evidence belongs to the draft; saved evidence is unchanged.
- `ViewportAdapter.filtered_issue_ids: frozenset[str] | None`. `None` means no list filter. Placement gestures ignore this filter.

The new controller methods below are completion proposals, not already recovered implementations: `begin_creation()`, `select_issue(issue_id)`, `save_details()`, and `cancel_details()`. They belong to `IssuesExtension`, keeping persistent mutation in `commit_session` and UI state in one owned session.

### Task 1: Recover staged records, USD migration, and BCF fields

**Files:** Persistence/BCF worker's exclusive files above.

**Consumes:** Existing issue mutation/undo transaction and parent-layer ownership rules.

**Produces:** The recovered model, session and service contracts, legacy migration, and BCF title/type support.

- [ ] Write `tests/test_edit_session.py` to assert that creating/updating a session does not mutate the store, and that editing preserves the original record/viewpoint until commit.
- [ ] Write `tests/test_acc_persistence.py` for legacy schema 1 reads, version 2 Save/reopen, stable positive numbers, title validation at 0/1/255/256 trimmed characters, unknown types, stale original records, read-only scenes, and transaction rollback on viewpoint failure.
- [ ] Run the new offline tests against the existing implementation and record meaningful failures before recovering the partial model/store/service/session files.
- [ ] Recover those files into an isolated execution checkout. Fix validation, defaults and migration based on tests; do not persist migration during read-only list access. Allocate display numbers only on successful new-record commit and preserve them across later edits.
- [ ] Write `tests/test_acc_bcf.py` for title/type/status/description round-trip, legacy title fallback, title/type conflict choices, and unchanged repeat import without duplicated records or display numbers.
- [ ] Recover BCF changes and verify them alongside existing compatibility tests. Preserve supported BCF 2.1/3.0 import and 3.0 export.
- [ ] Run `python -m unittest discover -s tests -p 'test_edit_session.py'`, then the corresponding `test_acc_persistence.py` and `test_acc_bcf.py` modules in the project's established offline SDK environment. Expected: all new behavior checks pass, with existing BCF compatibility checks still passing.
- [ ] Commit this verifiable unit after reviewing the scoped diff.

### Task 2: Recover separate issue list and details panels

**Files:** UI worker's exclusive files above.

**Consumes:** Frozen Task 1 record/session/service interfaces. Work can proceed in parallel using agreed interface doubles.

**Produces:** The recovered `IssuesWindow` and `IssueDetailsWindow` contracts without direct persistence calls.

- [ ] Write `tests/test_acc_ui.py` for case-insensitive number/title/description search, status/type filters, deterministic list order, Create and Select callbacks, details synchronization, busy/error controls, and teardown listener removal.
- [ ] Run the test module to establish failures against the combined UI.
- [ ] Recover the partial list/details code. Keep the list left and details right with the viewport usable; use native project styles. Show title, type, status, description, screenshot, comment history and pending comment.
- [ ] Add explicit Save and Cancel actions. Closing details delegates to the controller rather than destroying the draft. When displayed types change, keep the type selection and label consistent.
- [ ] Verify filter updates publish saved visible IDs without mutating USD. Test that a hidden panel's refresh and a destroyed panel's callback cannot operate on released UI.
- [ ] Run `python -m unittest discover -s tests -p 'test_acc_ui.py'` using native UI doubles. Expected: all callbacks and draft-only behavior pass. Lead verifies actual docking/rendering later.
- [ ] Commit this UI unit after scoped review.

### Task 3: Wire creation, editing, and evidence ownership

**Files:** Lead's controller/Markup/viewport files and `tests/test_acc_controller.py`.

**Dependencies:** Tasks 1 and 2 contracts must be implemented and checked before integration. This task is sequential.

**Produces:** A complete controller using the separate UI and staged Save contract.

- [ ] Write controller regressions for Create → pick → details/Markup → Save, Cancel before/after capture, missing/invalid title, stale scene, failed commit, dirty close/switch, and extension shutdown.
- [ ] Write evidence regressions for editing saved annotations through an owned copy, replacement failure, repeated replacement, Cancel preserving saved bytes/native prims, and Save associating only accepted evidence.
- [ ] Run new tests to expose the old callback incompatibility and saved-evidence mutation risks.
- [ ] Implement `begin_creation()` and `select_issue(issue_id)` using one owned `IssueEditSession` and one details window. Preserve saved-view recall; keep placement/capture tasks owned through shutdown.
- [ ] Implement `save_details()` to synchronize inputs, finish accepted annotation, hide overlapping UI for capture, validate/commit the session, and select the saved issue. Failure keeps the draft and error visible. Scene Save is separate.
- [ ] Implement `cancel_details()` and the dirty Save/Discard/Stay decision. Save must succeed before an issue switch proceeds. Discard deletes only the draft's unsaved evidence and leaves saved records unchanged.
- [ ] Recover and verify `MarkupAdapter.copy_for_edit` without weakening native settling, scene checks, root-target leases, or external-owner protection. Timeout before safe settling remains a documented limitation.
- [ ] Implement `filtered_issue_ids` for saved pin visibility. Creation gestures remain active outside list filters; saving a new issue reveals/selects it predictably.
- [ ] Migrate all old window/editor callers and tests. Delete the obsolete description-only creation editor only after its callers have moved. Preserve unrelated toolbar and evidence UI suppression behavior.
- [ ] Run `python -m unittest discover -s tests -p 'test_acc_controller.py'` and existing draft/capture/recall regressions. Expected: no partial Save, saved-evidence loss, orphan owned settled draft, or stale-scene write.
- [ ] Commit the integrated controller unit after review.

### Task 4: Independent review and complete Composer verification

**Files:** `tests/test_acc_workflow.py`, requirements/verification documents; fixes go to their original owners.

**Consumes:** The integrated implementation from Tasks 1–3.

- [ ] Request an independent combined review against this recovered spec and baseline. Fix accepted findings and rerun their targeted regressions.
- [ ] Add lead-owned rendered tests for both new creation and existing-issue editing. Use real viewport input, native Markup, and separate list/details UI.
- [ ] With user Composer closed and private dependencies validated, run `./run-verify-kit.ps1 -Case acc_workflow -Visible`. Expected: Create/Save/Cancel; edit Save/Discard; screenshot annotate/replace; list filters; dirty close/switch; USD Save/reopen; BCF export/read/reimport all pass.
- [ ] Run the narrow native recall/navigation case. Confirm the primary viewport remains navigable and another viewport's shared camera is preserved.
- [ ] Inspect screenshot artifacts for visible model/annotations and absence of details/tool overlays. Verify source building layers remain unchanged.
- [ ] Record actual results and limits. If a GPU fault occurs, preserve evidence and reduce it rather than repeatedly running the broad suite.
- [ ] Audit the current live checkout against the execution checkout, back up differing originals, and deploy only compatible integrated files with Composer closed. Verify copied content and refresh global Graphify.
- [ ] Update the concise resume record with the new workflow and verification paths. Commit the final reviewed unit when requested/authorized by the execution workflow.

## Self-review and handoff

Confirmed scope is covered by separate list/details UI in Task 2 and creation/edit orchestration in Task 3. Inferred metadata, migration and BCF support belong to Task 1. Every review focus has a named owner and test requirement. Tasks 1 and 2 can run independently after agreeing contracts; Task 3 depends on both; review and rendered verification follow integration.

Open distinction: the missing conversation's exact decisions are unavailable. Automatic Markup activation and dirty-close behavior above preserve or complete existing requirements and are explicitly identified as completion policies in the recovered spec. Implementation must not label them recovered quotations.

The user's earlier execution preference was coordinated workers with frontend-design for UI and a separate persistence/BCF worker, followed by independent review and lead-controlled Kit testing. Preserve that approach when execution is requested. This recovery delivers the snapshot, requirements and plan; it does not deploy the unfinished code or claim its tests passed.
