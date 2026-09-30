# Omniverse issue management implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking. Execution method remains for the user to select.

**Goal:** Build the approved native issue workflow in Omniverse, with USD persistence, model anchors, review viewpoints, Markup evidence, and BCF file exchange.

**Architecture:** The parent USD scene owns all issue records. An issue service coordinates a USD store, element resolver, viewport adapter, and Markup adapter, while the panel invokes that service. BCF parsing and merge planning remain separate from mutation so imported conflicts can be reviewed before application.

**Tech Stack:** Python 3.12, OpenUSD, Omniverse Kit 110.2, omni.ui, viewport APIs, supported Markup APIs, the local Section Box extension, and Python standard-library ZIP and XML handling. No database or external service is required.

**Spec:** [Omniverse issue management specification](../../../SPEC.md)

**Execution checkpoint, 2026-09-30:** The user approved development and parallel workers. Tasks 1–6 are implemented; Task 7's internal workflow and delivery checks pass. The follow-up visible Kit run reports 57 passing outcomes with process exit zero. Live Section Box controls and Markup lifecycle cleanup now have runtime coverage. External BCF interoperability and representative production identity remain open acceptance gates. Markup annotation requires the primary viewport. See [the verification record](../../verification-report.md) for evidence, review fixes, decisions, and limits. The original task checklist below is retained as the approved plan rather than treated as proof that every acceptance gate has closed.

## Global Constraints

- The parent USD scene owns the project-wide issue records.
- Issue records, comments, viewpoints, and editable annotations persist as USD data in the parent scene.
- One person edits at a time.
- Author names are configurable for this milestone. Imported authors remain unchanged.
- Statuses are Open, In progress, Resolved, and Closed.
- Assignment and permission settings are deferred.
- The pin anchor and the editable related-element list are separate concepts.
- Opening an issue restores its saved review view. Focus related elements is a separate action and does not overwrite that saved view.
- Reimporting the same unchanged file must not duplicate issues, comments, or viewpoints.
- Product implementation starts only after this plan is reviewed and an execution method selected.

## Local evidence and prerequisites

The installed SDK configuration reports Kit 110.2.0 and its Python reports 3.12.13. Its executable is `C:/kit-app-template/_build/windows-x86_64/release/kit/kit.exe`. Standalone `kit/python.bat` does not add USD to the Python import path. Prefer the isolated Kit runner for integration checks.

Markup Core 1.3.1 and Markup Tool 1.2.82 are installed, with manifest targets of Kit 107.3. Compatibility is unverified. Task 1 must check their activation before dependent work. Do not change vendor manifests to force compatibility.

The neighboring Section Box extension supplies `section_box.get_runtime_state()`, render-product clipping, and separate Kit verification runners. Its use of `omni.kit.test.AsyncTestCase` and temporary test scenes provides prior art. Reference these interfaces without modifying the neighboring extension unless a specific integration gap is demonstrated.

This extension folder is not a Git repository and contains only the approved specification. At execution setup, initialize version control here and commit the approved documents as a baseline. Keep the separate Kit SDK checkout unchanged. Do not move the installed extension out of the shared extension directory solely to create a worktree. If Git isolation is required, use a checkout registered as a separate extension search path and verify which copy loads.

Three prerequisites can constrain later stages without blocking earlier deliverables:

1. Markup must load and persist evidence in the parent root layer. If its supported APIs cannot do that, report the compatibility finding and propose the smallest alternative before implementing annotations.
2. Revision-safe matching requires a representative model and trustworthy source IDs. Synthetic fixtures prove the matching algorithm; they cannot establish the metadata contract of the real building.
3. The BCF version and partner application remain deferred by the user. Choose the concrete file profile before Task 6 writes version-specific XML, and choose the partner before claiming external interoperability. Do not assume all BCF versions or editable annotation formats are supported.

## File structure

Create these files within the extension root. This is a proposed structure, not existing implementation.

| File | Responsibility |
| --- | --- |
| `config/extension.toml` | Extension dependencies, settings, and test registration. |
| `issues_tag/__init__.py` | Public extension and runtime service exports. |
| `issues_tag/extension.py` | Lifecycle, menu entry, stage subscriptions, and cleanup. |
| `issues_tag/model.py` | Immutable records and the supported status enum. |
| `issues_tag/store.py` | Root-layer serialization and validation. |
| `issues_tag/service.py` | Issue actions, attribution, and stage-scoped state. |
| `issues_tag/commands.py` | Undoable root-layer mutations. |
| `issues_tag/window.py` | Issue list, details, comments, status, and unsaved state. |
| `issues_tag/elements.py` | Scoped source identity, matching, and anchor transforms. |
| `issues_tag/viewport.py` | Surface picking, pin overlays, focus, and viewpoint restoration. |
| `issues_tag/markup.py` | Supported Markup integration and screenshot conversion. |
| `issues_tag/bcf.py` | File parsing, export, comparison baseline, and merge plan. |
| `issues_tag/import_window.py` | Import summary and per-field conflict choices. |
| `tests/issues_test.kit` | Separate verification app with isolated settings. |
| `tests/fixtures.py` | Small generated parent scenes and referenced model revisions. |
| `tests/verify_kit.py` | Async test dispatch and machine-readable results. |
| `tests/test_*.py` | Behavior tests grouped by the tasks below. |
| `run-verify-kit.ps1` | Launch the isolated app, select a case, and propagate failures. |
| `README.md` | Installation, Save behavior, workflow, and supported BCF profile. |
| `verification/` | Generated logs, temporary USD, BCF, and evidence. Exclude from Git. |

## Shared interfaces

These contracts are planning decisions. Keep imports that require Kit in the runtime adapters.

- `Status`: string enum with exactly `Open`, `In progress`, `Resolved`, and `Closed`.
- `ElementRef`: source model identity, reference-instance scope, source ID kind/value, and last resolved prim path. Resolution result is `resolved`, `missing`, or `ambiguous`.
- `Anchor`: an `ElementRef`, an element-local position, and attachment confidence. Never substitute the related-element list for the anchor.
- Anchor confidence is `verified` or `needs_review`. Store a digest of the attached mesh's local points and topology at placement. A changed digest flags a surviving identity for review; transforms alone do not change this digest. Reattachment captures a new digest. Non-mesh attachments require a corresponding geometry signature or remain explicitly uncertain after replacement.
- `ViewpointRecord`: stable ID, camera projection and pose, clipping planes, component visibility, selection, optional Markup prim relationship, and snapshot bytes.
- `CommentRecord`: stable ID, text, author, UTC timestamp, and optional viewpoint ID.
- `IssueRecord`: stable ID, optional BCF topic ID, description, `Status`, author/timestamps, optional anchor, related elements, initial viewpoint ID, and comments.
- `IssueStore(stage: Usd.Stage)`: `list_issues() -> tuple[IssueRecord, ...]`, `get_issue(issue_id: str) -> IssueRecord`, `put_issue(issue: IssueRecord) -> None`, `put_viewpoint(viewpoint: ViewpointRecord) -> None`, `get_viewpoint(viewpoint_id: str) -> ViewpointRecord`.
- `IssueService`: `create_issue(description: str, anchor: Anchor | None, viewpoint: ViewpointRecord | None) -> str`, `set_description(issue_id: str, text: str) -> None`, `set_status(issue_id: str, status: Status) -> None`, `add_comment(issue_id: str, text: str, viewpoint: ViewpointRecord | None = None) -> str`, `set_related_elements(issue_id: str, refs: tuple[ElementRef, ...]) -> None`, `reattach(issue_id: str, anchor: Anchor) -> None`, `open_issue(issue_id: str) -> None`, `focus_related(issue_id: str) -> None`.
- `get_runtime_service() -> IssueService | None` exposes the active extension service for integration tests and supported callers.
- Store issues under `/Issues`, viewpoints under their owning issue's children, and author custom attributes in the `issues:` namespace. Use UUID-derived valid prim names. Record `issues:schemaVersion = 1` on the container. Relationships connect records to their owned viewpoints and Markup evidence.
- Runtime restoration writes transient visibility, camera, and clipping opinions in the session layer where possible. Issue mutations explicitly target the root layer. Never inherit a user's selected edit target for issue persistence.

Use typed USD attributes for scalar fields and a versioned UTF-8 payload for composite references and viewpoint state. Embed PNG snapshot bytes as base64 strings in USD attributes. The payload schema is validated on load; it is not an external JSON store. Return understandable errors for unknown schema versions and malformed records.

## Review Focus

These conditions receive explicit tests in their owning tasks:

1. Closing a stage during an asynchronous capture must discard the old result rather than write evidence into a newly opened scene. Task 5.
2. Two instances of the same referenced model must resolve independently. A shared source ID is insufficient without instance scope. Task 3.
3. A read-only parent or a non-root edit target must not cause issue data to be authored in building sources. Task 2.
4. A malformed or unsafe BCF archive must fail before partial import and must not write files outside verification or export locations. Task 6.
5. Restoring an issue and then navigating must not leave a hidden camera lock or steal another viewport's state. Task 4 and Task 5.

## Verification contract

The planned command is `./run-verify-kit.ps1 -Case <case>` with cases `runtime`, `persistence`, `anchors`, `viewpoints`, `markup`, `bcf`, and `workflow`. Omit `-Case` to run the whole suite. Add `-Visible` only when real window or swapchain capture is needed. These commands become available in Task 1; they do not exist yet.

The runner launches a separate Kit process and temporary scenes. It writes `verification/results.json`, test names, failures, and screenshots. Success requires process exit zero and every selected test passing. Failure returns a nonzero exit code and identifies the failed assertion. A rendered or UI test cannot be replaced by a mocked adapter and still count as application acceptance.

Each task follows RED, GREEN, then refactor. Add a failing test, run it, and check that the failure names the missing behavior. Implement only that behavior, run the case, then run all implemented cases. Commit the task once those pass. Import errors or an unavailable test runner are setup failures to fix, not the expected RED evidence.

### Task 1: Isolated runtime and extension activation

**Files:** Create the manifest, package entry point, extension lifecycle, verification runner, test app, test dispatcher, `tests/test_runtime.py`, and `.gitignore`.

**Interfaces:** Produces the verification contract and `get_runtime_service()`. The service may initially expose no issue actions. It must be stage-scoped and cleaned up on extension shutdown.

- [ ] Add `test_extension_activation_and_shutdown`: assert the extension loads, exports a runtime service, and releases it on disable. Add `test_markup_compatibility`: enable both Markup extensions, create and recall one markup in an isolated scene, and assert no extension activation failure.
- [ ] Run `./run-verify-kit.ps1 -Case runtime`. First prove the runner works independently, then observe the extension behavior fail before implementation. A Markup activation failure is a compatibility finding, not an issue-implementation defect.
- [ ] Implement the lifecycle and manifest using the installed `omni.ui`, `omni.usd`, viewport, and Markup dependencies. Register and remove the Issues menu action exactly once.
- [ ] Run the runtime case twice with fresh app processes. Expected: all lifecycle assertions pass, with no stale subscriptions or activation failures.
- [ ] Commit as `feat: add isolated issues extension runtime`. Record exact loaded dependency versions and the compatibility result in the verification report.

### Task 2: Persistent records and usable issue panel

**Files:** Create `model.py`, `store.py`, `commands.py`, `service.py`, `window.py`, `tests/fixtures.py`, and `tests/test_persistence.py`. Modify extension wiring.

**Interfaces:** Produces the record types, store methods, and create/edit/comment/status/related-elements service actions defined above. Opening the panel initially supports records without a spatial anchor.

- [ ] Add `test_issue_comment_status_survive_reopen`: create a record through panel actions, edit its description, add an attributed comment, set Resolved then Closed then Open, save, and reopen. Assert stable IDs, field values, author, and UTC timestamp preservation.
- [ ] Add `test_root_layer_ownership_and_read_only`: set the user's edit target to a referenced layer, create an issue, and assert `/Issues` is authored only in the parent root. Make the parent read-only and assert the action reports failure with no source-layer changes.
- [ ] Add `test_unsaved_state_and_next_reviewer`: assert an edit dirties the root without saving its backing file, then save/reopen under a second configured author. Assert the second author can comment and existing attribution is unchanged.
- [ ] Run the persistence case and observe failed field or persistence assertions. Implement validated records, undoable root edits, list/detail/comment controls, exact statuses, and unsaved state.
- [ ] Run persistence and runtime cases, then the whole implemented suite. Expected: all pass, including Save/reopen from disk. Commit as `feat: persist project issues and review comments in USD`.

### Task 3: Surface pins and reliable element attachment

**Files:** Create `elements.py`, `viewport.py`, and `tests/test_anchors.py`. Extend the panel and service for placement and manual reattachment.

**Interfaces:** Produces `resolve_element(stage: Usd.Stage, ref: ElementRef) -> Resolution`, `world_anchor(stage: Usd.Stage, anchor: Anchor) -> tuple[float, float, float] | None`, and `ViewportAdapter.pick(screen_x: float, screen_y: float) -> Anchor | None`. `Resolution` contains a state and resolved prim path only for a unique match.

- [ ] Add `test_surface_pick_and_related_list_independence`: pick the center of a rendered cube, assert the pin belongs to that surface, add another related element, and remove it. Assert the anchor remains unchanged.
- [ ] Add `test_pin_follows_transform_and_instance_scope`: reference one model twice, attach to each instance, move only one instance, and assert only that pin moves. Test translation, rotation, and scale.
- [ ] Add `test_revision_matching_and_manual_repair`: rename a prim while keeping its synthetic source ID, then remove or duplicate the ID. Assert unique matching succeeds, other cases become unresolved, and explicit reattachment survives reopen. Change local mesh points while retaining the ID and assert the attachment becomes `needs_review`; manual reattachment resets that confidence without replacing the saved original viewpoint.
- [ ] Run anchors and observe the missing behaviors. Implement the viewport's supported hit-query path, element-local positions, instance-scoped IDs, and screen-space pin overlays. Render overlays without depth occlusion while keeping eligibility separate from rendering.
- [ ] Use synthetic IFC/source IDs in fixtures. Treat the nearby Asset ID GUID as a candidate only. Inspect a real model before configuring its production identity mapping. Missing IDs permit same-scene path attachment but must not imply revision-safe identity.
- [ ] Run anchors plus the implemented suite. Expected: all pass, with pin evidence images and no proximity-based reassignment. Commit as `feat: anchor issue pins to scoped model elements`.

### Task 4: Saved review context and pin filtering

**Files:** Extend `viewport.py`, `service.py`, and `window.py`. Create `tests/test_viewpoints.py`.

**Interfaces:** Produces `ViewportAdapter.capture() -> ViewpointRecord`, `restore(viewpoint: ViewpointRecord) -> None`, `focus(refs: tuple[ElementRef, ...]) -> None`, and service `open_issue` and `focus_related`.

- [ ] Add `test_viewpoint_restore_and_focus_independence`: save a camera, component visibility, selection, and active Section Box planes. Change all of them, open the issue, and assert restoration. Focus related elements and assert the stored viewpoint is byte-for-byte unchanged.
- [ ] Add `test_pin_filtering_and_issue_access`: hide the attachment and section out its bounds. Assert its pin hides and the panel retains the issue. Include a partially clipped element with its anchor outside the retained volume; hide that pin rather than presenting a clipped-away location.
- [ ] Add `test_viewport_and_stage_isolation`: open the issue in one viewport, navigate away, and assert another viewport retains its camera. Close/open the stage and assert old issue selection and overlays are cleared.
- [ ] Run viewpoints and observe failed restoration and visibility assertions. Capture camera projection and pose, component state, and clip coefficients. Integrate supported Section Box state so its controls agree with the restored planes. Apply temporary review state without modifying building source layers.
- [ ] Use fixture tolerances of `1e-6` scene units for numeric state comparisons. Rendered evidence verifies framing and clipping separately; numeric tolerance alone does not prove visual correctness.
- [ ] Run viewpoints, anchors, and the whole implemented suite. Commit as `feat: restore issue review context and filter viewport pins`.

### Task 5: Markup evidence and annotated comment viewpoints

**Files:** Create `markup.py` and `tests/test_markup.py`. Extend service and panel evidence actions.

**Interfaces:** Produces `MarkupAdapter.capture_viewpoint() -> Awaitable[ViewpointRecord]`, `edit(viewpoint_id: str) -> None`, and `snapshot_png(viewpoint_id: str) -> bytes`. Service comments consume the captured record without replacing the initial viewpoint.

- [ ] Add `test_annotated_comment_reopens_editably`: use supported Markup APIs to create an arrow and note, add the evidence as a comment viewpoint, save/reopen, and assert annotation editability, distinct viewpoint IDs, and a decodable annotated PNG.
- [ ] Add `test_capture_stage_change_discards_result`: start capture, switch the stage before completion, and assert no evidence appears in the new scene. Add `test_markup_unlocks_after_edit` to verify navigation works after Apply or Cancel.
- [ ] Run markup with `-Visible` if the installed API requires a swapchain. Observe the evidence or cleanup assertion fail before implementing the adapter.
- [ ] Use `omni.kit.markup.core.get_instance()`, documented creation/recall/edit callbacks, and owned prim relationships. Confirm every stored Markup prim and embedded snapshot is persistent in the parent scene. Do not patch NVIDIA internals or silently fall back to temporary sidecar storage.
- [ ] Run markup plus the whole implemented suite. Compare an annotated capture against an unannotated capture and confirm the arrow/note is visible. Commit as `feat: attach editable Markup evidence to issue comments`.

### Task 6: BCF parsing, export, and safe import merging

**Files:** Create `bcf.py`, `import_window.py`, and `tests/test_bcf.py`. Add import/export actions to the panel.

**Interfaces:** Produces `read_bcf(path: Path) -> BcfDocument`, `write_bcf(document: BcfDocument, path: Path) -> None`, `plan_import(document: BcfDocument, store: IssueStore) -> ImportPlan`, and `apply_import(plan: ImportPlan, choices: dict[str, str], service: IssueService) -> ImportSummary`. Decisions are `keep_local` or `use_imported` per conflict. The file-profile gate defines the version-specific XML mapping without changing these interfaces.

- [ ] Before version-specific implementation, select and record a supported BCF file profile. Map required title and project metadata, statuses, component IDs, and viewpoints explicitly. Do not introduce a new mandatory issue-title UI field without reconciling it with the approved description-first workflow.
- [ ] Add `test_bcf_round_trip_supported_fields`: export two issues with initial/comment viewpoints and annotated snapshots, then import into an empty parent scene. Assert preservation of supported identities, values, attribution, timestamps, component references, and image bytes.
- [ ] Add `test_repeat_import_and_conflict_choices`: import twice and assert unchanged counts. Edit a local description/status, change the incoming values, and assert preview conflicts without store mutation. Apply keep-local and use-imported choices in separate fixtures.
- [ ] Add `test_missing_components_preserve_evidence`: import unknown component IDs, retain evidence and unresolved references, and show no pin until reliable mapping exists.
- [ ] Add `test_invalid_archive_has_no_partial_import`: reject malformed XML, unsupported profile versions, duplicate ZIP member names, paths that escape the archive namespace, and XML external-entity declarations. Limit total uncompressed content to 100 MiB and 10,000 ZIP members as provisional internal safeguards, with clear errors. Do not extract members to disk.
- [ ] Run BCF and observe missing conversion, merge, or rejection behaviors. Implement parsing before mutation, atomic issue-command application, and stable imported IDs. Store the last accepted import baseline in parent USD so later comparison survives Save/reopen.
- [ ] Write exports to a temporary sibling file and replace the destination only after successful completion. Preserve available unresolved component IDs for export. Document unsupported fields and any exchange loss explicitly.
- [ ] Run BCF plus the whole suite. Validate against the chosen profile's official schemas and inspect exported ZIP content. Commit as `feat: exchange BCF files with conflict-aware issue merging`.

### Task 7: Complete user workflow and delivery documentation

**Files:** Create `tests/test_workflow.py` and `README.md`. Update manifest documentation metadata and the verification runner's complete-suite registration.

**Interfaces:** Consumes all preceding interfaces. Produces installation instructions, compatibility evidence, and a full acceptance report.

- [ ] Add `test_full_review_workflow`: place an issue, edit related elements, add annotated evidence, save/reopen, restore context, change status, move and revise the model, repair a reference, and complete BCF export/import. Assert user-visible outcomes rather than service callback counts.
- [ ] Add `test_reviewer_handoff`: save under one author, reopen under another, comment and change status, then verify both authors and persistent evidence.
- [ ] Run the complete suite and observe any cross-feature failure. Fix each defect through its own failing behavior test rather than broad refactoring.
- [ ] Document the exact tested Kit and Markup versions, supported BCF profile, source identity mapping, Save behavior, single-editor limitation, and installation search path. Include how to run the full verification suite.
- [ ] Once the partner application is selected, perform the actual external BCF round trip. Until then, report internal/schema validation separately and keep external compatibility acceptance open.
- [ ] Run `./run-verify-kit.ps1`, using `-Visible` for capture-dependent tests. Expected: all registered cases pass and `verification/results.json` names every acceptance outcome. Perform one live issue-panel/viewport review on a temporary scene.
- [ ] Commit as `test: verify the complete Omniverse issue review workflow`. Complete the Superpowers verification and independent review steps required by the selected execution method. Do not claim the full milestone complete while a required compatibility gate remains open.

## Plan review and execution handoff

The plan covers all 46 user stories and all 16 acceptance scenarios. It preserves deferred assignment, permission rules, concurrent editing, server exchange, and universal BCF compatibility. It proposes record representation and provisional test tolerances without presenting them as measured product guarantees.

The extension is one connected subsystem, so a single staged plan keeps its contracts together. Native execution is recommended: one implementer can maintain the closely coupled stage, anchor, viewpoint, and import contracts, followed by an independent whole-change review. Subagent-driven execution is also available if the user prefers a fresh implementer and reviewer for each task.

Review this plan and select Native or Subagent-driven execution before product code is written. After approval, execution begins with the baseline and Task 1 compatibility checks. Reconcile failed prerequisites with the spec before dependent tasks proceed.
