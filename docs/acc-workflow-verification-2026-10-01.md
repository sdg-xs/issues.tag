# ACC workflow verification, 2026-10-01

The recovered workflow is specified in [the supplement](superpowers/specs/2026-10-01-acc-issue-workflow-recovered.md) and [SPEC.md](../SPEC.md). The rendered acceptance fixture is [test_acc_workflow.py](../tests/test_acc_workflow.py). It uses native USD, viewport mouse input, native Markup and real separate panels. It does not substitute a capture or Markup double.

## Authored coverage

These are runnable checks, not runtime results. Each function is independently selectable with `-TestName`.

| Function after `test_acc_` | User behavior and evidence |
| --- | --- |
| `spec_snapshot_preserves_nested_subtree` | Cheap real USD helper check: nested evidence and annotation values copy exactly, snapshotting leaves the source unchanged, and changed annotation content changes the snapshot. |
| `create_save_clean_native_evidence` | Composes the frozen `test_creation.exercise_creation(save=True)`. Real mouse pin placement, automatic native Markup, separate details title/description Save, red-arrow PNG, floating-window and pin suppression, parent reopen and BCF snapshot read. |
| `create_cancel_removes_native_draft` | Composes the same frozen creation helper with Cancel. No saved record or remaining owned native draft. |
| `dirty_native_close_and_switch_save_discard_stay` | Actual list selection and real mouse clicks on the dirty dialog. Native details close and issue switching each exercise Save, Discard and Stay. Each Stay retains the exact staged record, pending comment, title/description/comment UI models and status/type selections. Accepted edits save, discarded edits leave the original record intact. |
| `native_annotation_and_replacement_save_cancel` | Actual list Create button and viewport click build native initial evidence. Initial annotation Save produces red-arrow PNG. Annotate and Replace each discard an owned draft while preserving the original record, PNG and root-layer Markup spec. Repeating each action with Save accepts the exact replacement ID and PNG. Native image-widget queries reject failed preview rebuilds. |
| `filtered_parent_related_comment_and_bcf_journey` | An empty combined search/status/type filter hides pins but permits a real new placement. Save reveals and selects the new issue. Native pin item state tracks list search. Actual details callbacks stage Add/Remove related against the original tuple, including the automatically attached anchor, while preserving saved data and anchor position. Focus related changes the viewport camera world pose. With staged metadata still open, a native Open review view click restores camera, selection, visibility, clipping and section context while retaining the exact draft and saved evidence. They capture/annotate/Add comment, exercise existing comment annotation Discard and Save, and use real mouse reattachment. Accepted initial evidence remains unchanged. Exporting the parent and reopening through the USD context preserves records, numbers and PNGs; the referenced source building file and layer remain unchanged. BCF export/read retains supported fields and accepted PNGs. Reimporting the same document twice keeps identities, display numbers, comments and viewpoints without duplicates. |
| `runtime_disable_drains_native_draft_before_reenable` | The real extension manager disables/re-enables the extension. Native creation Save supplies a saved issue, followed by copied annotation and a pending actual Save. A lifecycle observer retains `_shutdown_task` before Kit clears the IExt dictionary and waits for its completion. Full serialized saved records, including every viewpoint field and PNG byte, and the native subtree survive across module reload; owned draft disappears; re-enable opens a clean saved issue. No stage replacement occurs before the previous shutdown drains. |

The existing `workflow` case remains complementary coverage for reviewer authorship, statuses and handoff. The existing `native_recall` case checks portable and native recall, primary-camera reuse and shared-camera preservation. Its visible preview adds real mouse-wheel navigation before and after native annotation. These fixtures have their own limits; their presence does not establish that they passed.

The parent journey sets the author through the Issues author field and an actual Apply click, then verifies issue and comment attribution. It selects In progress and Quality through the native details combo models and verifies both persisted values after Save.

## Lead-run commands

Close the user's Composer before launching the isolated verification process. Use the validated ordinary-copy dependency snapshot outside the extension root. Do not change the shared NVIDIA SDK.

```powershell
$deps = 'C:/Users/StevenGomba/.codex/worktrees/issues-tag-improvements/verification-dependencies'
./run-verify-kit.ps1 -Case acc_workflow -TestName test_acc_dirty_native_close_and_switch_save_discard_stay -DependencyRoot $deps -Visible
./run-verify-kit.ps1 -Case acc_workflow -TestName test_acc_native_annotation_and_replacement_save_cancel -DependencyRoot $deps -Visible
./run-verify-kit.ps1 -Case acc_workflow -TestName test_acc_filtered_parent_related_comment_and_bcf_journey -DependencyRoot $deps -Visible
./run-verify-kit.ps1 -Case acc_workflow -TestName test_acc_runtime_disable_drains_native_draft_before_reenable -DependencyRoot $deps -Visible
./run-verify-kit.ps1 -Case native_recall -DependencyRoot $deps -Visible
```

`verify_kit.py` already selects `test_acc_workflow.py` by its existing case glob. Running the four new narrow functions, the existing `creation` Save/Cancel pair and the native recall checks provides the composed rendered coverage in the matrix. The complete case, including the cheap USD helper check, is also runnable by omitting `-TestName`; a redundant full rerun is unnecessary after the same selected functions pass unless later changes justify it. No launcher changes are needed. Do not use `-Case all` for this acceptance work.

The mouse helpers wait for frame settling, delivery of a native viewport frame, and at least 0.6 seconds between gestures. Button clicks call public WidgetRef.focus, re-find the button, and send emulate_mouse_move_and_click at its fresh center. They assert that visible Issues/details panels remain docked, including when a floating dirty dialog is clicked. WidgetRef.click is unsuitable here because the installed SDK deliberately undocks the owning window before focusing it. Dispatched actions are awaited. Before any context stage replacement, controller work closes and drains. Runtime shutdown is separately awaited before re-enable or creating another stage.

The verification app depends on `omni.kit.mainwindow`, matching the installed SDK's Viewport layout tests. That extension creates and owns MainWindow during app startup and docks Viewport into DockSpace. The fixture observes the settled framework layout before showing Issues, without constructing a second MainWindow or issuing competing dock requests. It requires visible docked Issues/details panels and a surface point outside their rectangles. Markup Tool activates through the real capture adapter after placement; the fixture does not eagerly create its input-owning canvas or hide panels to pass a click.

The previous late-created MainWindow attempts failed. An ordinary control docked, but Viewport remained floating while that control was alive, after its removal, and before focus. Those results rule out global docking failure, an emptied root and immediate focus as explanations. SDK Viewport startup installs its own deferred docking request; the app had omitted the early MainWindow owner used by SDK layout tests. The fixture now records `native_mainwindow_startup_layout`, including registered ownership and Workspace/Viewport identity. Subsequent lead runs established Viewport and panel docking and native annotation/replacement acceptance. The corrected parent and manager-disable journeys below still need final runs.

## Artifacts and inspection

Each run overwrites `verification/results.json`, `progress.json`, `kit.log`, `stdout.log` and `loaded-extensions.json`. Preserve them with the run's name before starting another check. The last progress phase and current test distinguish a fixture failure, a dependency failure, an action error and a process exit without a final report. A reported PASS must also be checked against native UI build exceptions in the Kit log.

Purposeful artifacts include `acc-initial-annotated.png`, `acc-edited-annotation.png`, `acc-replaced-screenshot.png`, `acc-comment-annotated.png`, `acc-comment-edited.png`, `acc-parent-saved.usda`, `acc-source-building.usda` and `acc-parent-exchange.bcf`. Composed creation uses the existing `clean-evidence.png`, `pin-markup-parent.usda` and `pin-markup.bcf` names.

Inspect the PNGs for visible model geometry and annotation, readable framing, and absence of issue details, pins and floating tool overlays. Pixel assertions prove PNG decoding, image size, rendered variation and red-arrow presence; they do not replace visual inspection. The composed creation case additionally checks a conspicuous overlapping UI probe is absent from the captured image.

## Actual results

Local evidence and the deployment helper are kept in the isolated execution checkout at `C:/Users/StevenGomba/.codex/worktrees/acc-issue-workflow/issues.tag/verification/`. They are not installed as live extension files.

Lead-owned acceptance completed on October 1, 2026. Final product code is commit `1f0456e`; subsequent `b15acb3` and `d3e2e40` changes correct the native fixtures. All accepted runs exited normally and their Kit logs contain no UI build errors or GPU faults.

| Check | Revision and result | Local evidence under verification/ |
| --- | --- | --- |
| Full parent, comments, repair and BCF journey | b15acb3, 1 PASS | acc-parent-pass-20261001-1420 |
| Actual extension-manager disable/re-enable | d3e2e40, 1 PASS | acc-manager-pass-20261001-1424 |
| Dirty native close/switch Save, Discard and Stay | d3e2e40, 1 PASS | acc-dirty-final-pass-20261001-1426 |
| Annotate/replace screenshot Save and Discard | d3e2e40, 1 PASS | acc-annotation-final-pass-20261001-1427 |
| Native/portable recall, shared camera and real mouse navigation | a51748c product, 4 PASS | acc-native-recall-pass-20261001-1358 |
| Initial creation Save/Cancel with clean native evidence | 5e0b767, 2 PASS | creation-preview-fixed-20261001-1249 |

The full parent journey exercises actual author Apply and status/type controls, filtered list/pins, staged related changes, review recall retaining dirty metadata, native draft guidance, comment annotation Save/Discard, reattachment, parent reopening and repeated BCF imports. The referenced building file and layer remain unchanged. Saved records, stable numbers, accepted PNGs and native evidence survive reopening. BCF preserves the supported fields and PNGs; importing twice creates no duplicates.

The manager run verifies a pending native Save drains during real disable, saved full serialized records/viewpoints and PNGs remain identical, original native evidence is intact, the owned draft disappears, and a new controller opens a clean issue after re-enable. The final assertion checks the existing native Core through its public singleton, without initializing a new editor.

Fresh lead-run offline verification on d3e2e40 passed 158 checks: 90 ACC/session/persistence/BCF checks, 60 evidence/BCF compatibility/recall/lifecycle/editor checks, and eight standalone lifecycle checks. The runner uses installed Kit Python, tests/ on sys.path, and verification/python for isolated Pillow/lxml dependencies. Compilation and whitespace checks also pass. New regressions cover same-issue recall, capture failure before navigation, draft and owned-evidence retention, live unsaved guidance without rebuilding fields per keystroke, model-listener release, valid native annotation coordinates and preservation of failed PNG artifacts.

Independent whole-branch review found the missing recall route, incorrect related-element baseline, SDK click helper undocking and missing draft guidance. One coordinated fix wave addressed all four. The scoped re-review approved spec compliance and code quality with no new findings or parked issues. Coordinator decisions are preserved in [the decision record](acc-workflow-decisions-2026-10-01.md).

Inspected initial/edited annotated images contain model geometry and red annotations without issue panels, pins or floating tool overlays. The synthetic arrows include lines reaching the image edge; these fixtures establish rendering and UI suppression, not representative building framing or all drawing styles. These tests use small scenes. They do not establish production-scale model behavior or external partner BCF interoperability.

Earlier failed runs are retained locally for diagnosis. Their causes were the native image enum binding, startup layout, first-update docking, missing USD destination ancestors, dependency import ordering, SDK test clicks that explicitly undock windows, invalid out-of-range percent coordinates, Python class identity after module reload and a lazy adapter cache assertion. Complete serialization comparisons detect changes to title, PNG or evidence path and do not discard the independent native-spec/drain assertions. No shared NVIDIA SDK was modified.

Deployment uses verification/deploy_acc.py to check all 71 original live-file hashes before copying the reviewed Git delta. It preserves live Git metadata, unrelated files and the original baseline backup, backs up overwritten delta files, and checks normalized hashes after copying. Its deployment-audit.json records the actual result and tested commit. Composer must remain closed during this copy.

The lifecycle fixture deliberately checks a runtime boundary absent from standalone doubles. This SDK's `ExtensionModules.shutdown` clears an IExt instance dictionary immediately after `on_shutdown` returns. The integrated extension therefore uses a thin IExt wrapper and a plain controller that owns deferred work. The fixture retains the real controller and its shutdown task before manager teardown, then awaits native drain. A pending-disable failure should be handed to the controller owner with its logs rather than worked around in the fixture.

The historical GPU/scene-replacement fault remains unresolved. If a GPU fault or abnormal exit occurs, preserve that run's artifacts and stop broad reruns. Reduce to the selected function and capture its last phase. Passing these checks would verify their specific workflows, not a general renderer safety guarantee, GPU fence, representative-model placement performance, or external partner BCF interoperability.
