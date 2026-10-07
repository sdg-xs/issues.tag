# BCF camera development record

Product commit: ca795fbe3c6c6504052a601bd3db834f2567c54d. Independent clone preserved; no merge, push or deployment. Native evidence: verification/bcf-camera/run-23 and run-24. Offline reports/logs retained in verification/bcf-camera/offline-evidence.

# SDD ledger — plan: docs/superpowers/plans/2026-10-07-bcf-camera-alignment.md

Worktree: C:/Users/StevenGomba/.codex/worktrees/issues-bcf-camera/issues.tag
Branch: feature/bcf-camera-alignment
Baseline: bef1889, existing uncommitted source/tests/graph copied and committed only in this isolated branch. Plan: 9fa6c84.
Baseline checks: 18 compatibility + 4 import reference, all passing.

Ruling: Execute after writing the plan without an additional approval checkpoint — the user explicitly requested planning then execution — if the scope differs from their intent, these isolated commits need revision.
Ruling: Keep current legacy camera interpretation as the default and make horizontal FOV/reference-local placement explicit choices — ACC's actual failing convention is not established — if the exporter convention is later confirmed, defaults may need a follow-up change.

## Preflight

| Tasks | Producer / consumer or self-consistency | Finding |
|---|---|---|
| 1 | Provenance, report, CLI tests match their files and exact output keys | Consistent |
| 2 | Options/mapping/reimport signatures match tests and old callers | Consistent |
| 3 | Camera-only preview matches no-selection/no-clipping side effects | Consistent |
| 4 | Selected Kit case consumes existing verifier, not a new runner | Consistent |
| 1 / 2 | bcf_source_camera metadata consumed by options; both touch bcf.py | Sequential ownership; original metadata preserved |
| 1 / 3 | Diagnostics source/converted document API consumed by import UI | Matching names and row keys |
| 1 / 4 | Diagnostic CLI referenced by verification docs | Matching archive/scene/reference args |
| 2 / 3 | ViewpointImportOptions and source_document consumed by replanning UI | Matching defaults/signatures; kwargs keep old callers valid |
| 2 / 4 | Corrected plan consumed by runtime import/reimport | Test runtime product interfaces, no duplicated mapper |
| 3 / 4 | UI + temporary camera consumed by runtime fixture | Camera-only preview explicit; full BCF clipping acceptance out of scope |

## Tasks

- [x] Task 1: provenance and diagnostics
- [x] Task 2: per-viewpoint correction
- [x] Task 3: import UI and preview
- [x] Task 4: runtime acceptance and documentation

Task 1: dispatched, BASE 9fa6c84.

Task 1: Ruling: Add optional BcfDocument.viewpoint_topics ownership tuples — archive viewpoints need topic labels even when not linked to initial/comment evidence — consumers must preserve this extra document metadata or diagnostic ownership becomes incomplete.

Task 1: implemented 5655ab3; diagnostics4 + compatibility18 + reference4 pass; review pending. Baseline window cleanup reproduces both errors. Isolated recall tests pass10 on baseline and current, same injected USD environment; broader discovery comparison pending. Private Kit dependency snapshot validated; Pillow/lxml copied into ignored verification/python.

Baseline comparison: full standalone discovery on bef1889 reproduces exactly the same 2 failures and 14 errors (182 tests versus Task1's 186). Log baseline-broad.log. Both isolated recall runs pass10. These are established baseline/harness failures, not new Task1 regressions; keep outside this camera scope.

Task 1: minor (deferred): bcf.py ownership tuples lack validation; dangling view raises KeyError, unknown topic silently drops ownership. Final review must triage. Task1 report warning/broad failure concern resolved by baseline comparison; Pillow warning preexisting. Cannot-verify items resolved by local manifest/runtime guidance, captured sample commands and unchanged original checkout status.
Task 1: complete (commits 9fa6c84..5655ab3, review clean of Critical/Important; one deferred minor).
Task 2: dispatched, BASE 5655ab3.

Sample observation: inspected topic indices1,3,5,20,21,612 have no Header/File entries. Archive metadata does not establish which model/origin those cameras belong to; continue explicit choices, no automatic magnitude-based remapping.

Original checkout verification: initial and current binary git diffs have identical SHA256 84091FE67A7C60F259A994C913142544EBB89D8C2687D5A3965371A9D97FD237; original HEAD remains539ead2.

Task 2: Ruling: Add IssueStore.list_viewpoints(issue_id) and export all owned persisted views — otherwise newly preserved archive viewpoints disappear on scene export — this adds a small store API to maintain; if ownership assumptions are wrong its traversal needs revision.

Task 2: implemented f021050, options13 + compatibility18 + diagnostics4 + reference4 passing; task review pending. Interfaces: source_document; viewpoint_frame_signatures pairs(viewid,mapping); viewpoint_options_signatures pairs(viewid,effective frozen options). Added bcf_source_clipping_planes original equations. Task1 ownership validation minor addressed in shared validator; review2 must verify.

Task1 ownership-reference minor resolved and verified by Task2 review. Task2 minor (deferred): bcf.py:448 unhashable ownership ID values raise TypeError instead of ValueError; final review must triage.
Task 2: complete (commits 5655ab3..f021050, review clean of Critical/Important; one deferred minor).
Runtime read-only verification: Kit Python3.12.13, installed OpenUSD(0,25,11). Kit app version will be verified in actual runtime logs.
Task 3: dispatched, BASE f021050.

Task 3: complete (commits f021050..310457b, review clean). Focused checks62 pass. Prior cleanup fixture issue is established baseline and outside scope. Rendered acceptance unresolved until Task4.
Task 4: dispatched, BASE 310457b. Parent will not run Kit while this worker owns verification.
Task 4: Ruling: Give camera preview its own temporary session-layer render product, copying current authored render settings through public viewport APIs — native deferred Hydra camera/exposure updates otherwise author the root layer, while the named SDK probe preserved it — this adds render-product ownership/cleanup logic that may need adjustment for future viewport SDK behavior.
Task 4: Ruling: Remove SDK-created opinions for collision-checked, preview-owned UUID camera/render-product paths from session and parent root during cleanup — native independent navigation leaves a root over after the session definition is removed — this extends cleanup to the parent root; if ownership assumptions fail an edit to that temporary path could be lost, so all unrelated paths and model layers must remain untouched.
Task 4: Ruling: Clean the owned temporary render-product target from SDK-authored render-settings relationships in session and parent root — otherwise deleting the product leaves a dangling target and Hydra errors — selective list-op cleanup must preserve all unrelated targets and authored semantics, or another render product could be affected.
Ruling: Continue in an independent clone inside the newly writable workspace after the permission change — the earlier isolated worktree and shared Git metadata became read-only — this preserves the live source but leaves a separate repository whose completed commits need deliberate integration later.
Task 4: Ruling: Restore the viewport synchronously but defer owned preview-resource deletion until two rendered frames, with a bounded wait and controller shutdown drain — native main acceptance still reports Hydra use-after-delete even after dangling-target cleanup — this adds asynchronous cleanup whose timeout/cancellation behavior must remain tested; an incorrect wait may leave resources briefly or trigger renderer warnings.
Post-migration original checkout check: binary tracked diff still matches initial SHA256 84091fe67a7c60f259a994c913142544ebb89d8c2687d5a3965371a9d97fd237 exactly. Process-only Git safe.directory used for read access; no global configuration change.
Task 4: Ruling: Replace the temporary render-product/deferred-cleanup approach with a preauthored session camera relationship, audited source exposure schemas/values and scoped camera setter, restoring only the owned relationship opinion — SDK run22 proves root preservation, exact session list-op restore, rendered framing, distinct independent navigation and zero error lines — future SDK authoring behavior or ownership assumptions could require adjustment; prior render-product/target/deferred-cleanup rulings are superseded and their machinery is removed.
Parent verification: independently read run23 progress (3 PASS / 0 FAIL) and full log (zero Error lines; existing hardware/SDK warnings retained). Inspected expected and corrected centimetres/Y-up PNGs: landmarks align, with intentional preview selection outline. Navigation after-close PNG visibly shifts all landmarks, confirming independent camera choice is rendered rather than only cached.
Parent final integration checks on4159ea7: unittest discovery test_acc_bcf4 and test_acc_persistence12, direct test_acc_ui45 all PASS, exit0. Logs final-acc-bcf.log/final-acc-persistence.log/final-acc-ui.log. Direct first loads of BCF/persistence modules executed no tests and were corrected to discovery; only actual discovery results count. Adds61 passing existing behavior checks without broad harness rerun.
Task4 review4159ea7: two Important cleanup ownership defects (new direct relationship targets overwritten via stale viewport cache; independent relationship metadata lost by whole-property restore/delete). Fix round1/5 dispatched to original implementer. Deferred Minor: runtime log gate misses renderer errors lacking preview-path/omni.ui strings; existing environment warnings recorded. Cannot-verify isolation/exclusive execution/no deployment resolved by coordinator evidence; actual ACC is an explicit acceptance limit.

Task 4: Ruling: Resume repository bookkeeping after our verification process exited despite a later external Kit process — the source-freeze rule protects our owned verification, and no evidence ties the later process to this isolated clone; its command-line read was access-denied and no bypass or app operation was attempted — if the external process loads this clone, graph/document changes could prompt its extension reload.

Task 4: fix round1/5 (2 addressed,0 open; commits4159ea7..ca795fb), fresh scoped reviewer approved; native run24 independently read1PASS0FAIL, full log zero Error lines. Task4 report commands/output inspected.
Task 4: complete (commits310457b..ca795fb, review clean of Critical/Important; log-filter minor deferred to final review).
Final review: 539ead2..ca795fb, strongest available reviewer, no Critical/Important findings; technical approval. Two Minor follow-ups: malformed programmatic ownership-ID TypeError and narrow automated renderer log filter.
Ruling: Defer the two nonblocking final-review minors — parsed archive IDs are strings, malformed inputs still stop before mutation, and accepted native logs were independently scanned with zero errors — malformed API inputs retain inconsistent exception types and future automation could miss renderer errors until the gate is broadened.

## Final reviewer declined-to-judge adjudication

| Item | Coordinator resolution |
|---|---|
| Actual ACC topic/model camera alignment | Remains an explicit unverified acceptance limit; no actual ACC fix claim. |
| Full BCF visibility/selection/clipping/Markup preview | Camera-only scope is intentional; persisted import still maps clipping. |
| Automatic origin/FOV/orthographic guesses | Explicit choices and preserved defaults satisfy the binding spec. |
| Physical input/dialog layout | Native controls/callbacks verified; physical interaction and layout not claimed. |
| Standalone discovery repairs | Same 2 failures/14 errors on baseline and current; outside camera scope. |
| Other Kit versions/interoperability | Supported evidence limited to specified Kit/Python/USD and existing tests. |
| Research links/generated graph | Earlier official-source research saved; graph AST update completed, not manually audited. |
| Isolation/deployment history | Original tracked diff SHA verified unchanged; independent clone preserved, no merge/push/deployment. |

Ruling: Accept the eight disclosed review limits with the resolutions above — evidence supports this camera correction workflow, not actual ACC alignment, full preview state, physical UI layout, other runtimes or a manually audited graph — a broader requirement would need additional affected-model, interaction, interoperability or environment verification.
Ruling: Preserve the independent development branch without integration and finish using focused checks — the spec prohibits merge/push/deploy and the full standalone harness is already proven non-green on the baseline — the user must integrate deliberately later, and unrelated harness failures remain unresolved.
Parent closing checks: native run24 four source hashes still match; original live binary tracked diff SHA256 remains84091fe67a7c60f259a994c913142544ebb89d8c2687d5a3965371a9d97fd237; git diff --check clean; product HEADca795fb. No further Kit run warranted.


# Final review — BCF camera alignment

Reviewed539ead2..ca795fbe3c6c6504052a601bd3db834f2567c54d against the spec/plan/ledger, distinguishing preexistingbef1889 snapshot from new development.

Technical assessment: ready, no Critical or Important defects found. No integration or deployment authorized.

Strengths: original camera/clipping provenance; explicit coordinate/FOV choices and compatibility defaults; pose/scale/clipping conversion; atomic stage/issue/reference checks; idempotent correction preserving snapshots/identities and rejecting editable Markup changes; source-based replanning with dirty controls blocking apply; dialog ownership; camera/product/relationship ownership checks and metadata/list-op preservation; numerical/native evidence distinguished from unresolved ACC alignment. Reviewer independently read run23 (3PASS0FAIL) and run24 (1PASS0FAIL), without tests/Kit reruns or checkout mutation.

Minor1 — issues_tag/bcf.py:448: unhashable programmatic viewpoint_topics IDs raise TypeError rather than ValueError. Parsed archives provide strings and rejection occurs before mutation. Follow up with identifier-type validation and a malformed-input regression.
Minor2 — tests/test_bcf_camera_workflow.py:29: automated error filter only matches IssuesImportPreview_ or omni.ui; future renderer errors without these strings could pass. Broaden unexpected-error detection with narrow documented exceptions. Full accepted logs were independently scanned and contained zero errors.
Recorded hardware/SDK warnings do not establish a product defect. Both minors are nonblocking follow-ups; no additional broad suite or Kit run justified.

Declined to judge:
- Actual ACC snapshot alignment/location failure: affected topic and matching model unidentified.
- Full BCF visibility/selection/clipping/Markup reproduction in preview: camera-only scope.
- Automatic origin inference/universal horizontal FOV/guessed orthographic scale: explicit choices and compatibility defaults required.
- Physical mouse/keyboard input/dialog layout: native controls/callbacks exercised, not physical input/layout.
- Standalone discovery repairs: identical baseline/current failures outside camera paths.
- Other Kit versions/external interoperability: specified runtime acceptance only.
- Independent research-link/generated-graph audit: implementation/evidence review; generated graph diff excluded.
- Independent reconstruction of isolation/deployment history: coordinator ledger relied upon; review itself read-only.

Coordinator resolutions for every declined item are recorded in the accompanying ledger. Actual ACC visual correctness remains unverified.

