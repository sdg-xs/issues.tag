# Implementation verification record

Date: 2026-09-30. Branch: `feature/issues`. Approved baseline: `ace2f88`. Runtime setup: `2fba6d4`.

The implementation covers the native issue panel, root-layer USD persistence, undoable record changes, scoped model attachments, viewport pins, saved review context, editable Markup evidence, and BCF 3.0 file import/export with conflict previews. The lead integrated the workers' changes and controlled all Kit runs. UI, persistence/BCF, and viewport workers had separate file ownership and shared immutable record/service interfaces.

## Runtime evidence

Verification command: `./run-verify-kit.ps1 -Case all -Visible`.

The initial checkpoint `51da352` reported 43 passes and zero failures. The follow-up development run reported 57 passes and zero failures with process exit zero, including 16 Markup cases and three live Section Box cases. Anchor checks include translation, rotation, and scale.

The tested runtime is Kit 110.2.0, Python 3.12.13, and OpenUSD 0.25.11. Installed Markup Core 1.3.1 and Tool 1.2.82 target Kit 107.3 in their manifests; their activation and evidence workflow run in the installed 110.2 runtime. Vendor manifests and implementation were not changed. Official BCF 3.0 schemas validate the generated XML through the test-only lxml dependency.

The suite includes rendered surface picking, hidden/clipped pin eligibility, independent viewport cameras, Save/reopen, attributed reviewer handoff, geometry-change detection and explicit repair, editable annotations, imported evidence, repeated import, conflict choices, stale previews, malformed archives, and atomic persistence. Preview cases also produce screenshots; they count toward the 57 registered outcomes. The complete suite expects installed `section.box` 1.1.0 in the shared extension folder.

Local evidence, excluded from Git because it is generated:

- `verification/results.json` names every outcome.
- `verification/stdout.log` and `verification/kit.log` retain runtime output.
- `verification/issues-panel.png` shows the native panel beside rendered geometry.
- `verification/issues-pins.png` shows pins, including an attachment behind covering geometry.
- `verification/markup-after.png` shows the rendered red arrow and note.

## Independent review

A separate reviewer inspected the combined source against the approved specification. The review found four Important defects and no Critical or Minor findings. Each accepted finding received a failing behavior test before its fix and subsequent passing verification:

1. Imported BCF metadata incorrectly invalidated the native coordinate frame. Restore now compares the frame's units and up axis, while retaining exchange metadata.
2. An initial issue viewpoint had no editable Markup association. Annotation now creates the association while retaining the original viewpoint identity and camera.
3. Overlapping annotation sessions could replace the owning evidence record. Capture and editing now reserve an owner and reject overlapping operations.
4. Malformed native Section Box state could reach partial viewport restoration. Import now checks enabled state, finite invertible matrix, positive dimensions, and supported face names before mutation.

Reviewer questions about actual annotation pixels and navigation were resolved by rendered arrow/note evidence and an Apply cleanup test. Source review and internal round trips do not replace production-model or external-partner acceptance. Those gates remain open below.

## Follow-up development and review

The user requested continued development after the initial checkpoint. A worker prepared real Section Box tests in separate owned files while the lead implemented adapters and controlled all Kit runs. An independent reviewer examined viewport ownership and cleanup, then verified the accepted fixes in source. The final review found no remaining Critical or Important defect introduced by this pass.

The live Section Box cases first failed when restored controls could not turn clipping off, when an unsectioned saved issue left a newer controller active, and when an inactive viewport captured the active viewport's box. The adapter now lets the native controller own restored box planes, releases it before restoring an unsectioned review, and checks the viewport during capture and restore. All three cases pass without changes to the neighboring extension.

Markup regressions reproduced mismatched viewport evidence, a vendor edit left active after failed Begin, a stale scene blocking later captures, replacement owners being overwritten, a camera captured before activation-time navigation, cancellation leaving a created Markup active, overlapping sessions losing the original edit target, and extension shutdown abandoning callbacks. Additional checks cover externally controlled edits, selection-only recall, and a newer explicit edit-target choice.

The adapter binds evidence to the primary viewport, tracks created identity before thumbnail completion, checks vendor ownership before capturing evidence, and retains the originating core/context for cleanup. A shared root-target lease preserves the original target across overlapping adapters. If an external native edit continues, restoration waits for that edit to end without clearing its review. Each reproduced defect received failing runtime evidence before its fix. The final 57-outcome suite verifies the combined behavior. See [Markup lifecycle](markup-lifecycle.md) and [Section Box verification](section-box-verification.md) for the contracts and runtime cases.

## Crash investigation

An isolated verifier run encountered an NVIDIA GPU page fault during Markup testing. The crash logs and GPU dump are retained locally under `verification/markup-gpu-crash.*`. The installed Markup `wait()` only waits eight application updates; it does not establish thumbnail-capture completion.

The adapter now awaits the public Markup creation callback and a delivered viewport frame before snapshot capture. It also clears the active Markup after Apply so navigation is released. The five Markup checks and the complete 43-outcome suite subsequently passed. These results support the lifecycle corrections but do not establish the GPU driver's crash root cause or guarantee the crash cannot recur.

## Decisions and costs

- Keep the installed extension in place on a new feature branch. There was no preexisting implementation branch to isolate. If that assumption changes, register an isolated checkout and confirm which extension copy loads.
- Coordinate parallel implementation through separate file ownership. Integration remains the lead's responsibility; incorrect interface assumptions require integration rework.
- Separate runtime activation from rendered Markup acceptance. Rendered evidence now supplies the latter. Another installed Markup version may require adapter and fixture changes.
- Use BCF 3.0 as the initial concrete file profile. A selected partner requiring another version will need a separate profile adapter.
- Use the installed Markup API's integer color and text dimensions in verification. Another API version may require different test inputs.
- Consolidate Tasks 2 through 7 into an integrated implementation checkpoint after the user authorized parallel development. One complete runtime run verifies the combined changes; separate commits cannot represent overlapping implementation chronology without rewriting it.
- Retain the feature branch locally. There is no configured integration destination or external publication request.
- Require the visible primary viewport for Markup evidence. The installed tool captures there, so secondary requests fail before mutation. Supporting annotation in secondary windows will require a supported vendor binding or a different integration.
- Keep a shared root-target lease during interactive native drawing. Restoring the target immediately after Begin would send vendor gestures into the previous layer. The lease preserves parent-layer ownership and restores the original target after the last edit. A future vendor API with per-operation layer targets could simplify this integration.

## Open acceptance gates

Live pin acceptance on 2026-09-30: the lead used the user's open SOL11-23 scene and created one `New issue` on the rooftop chiller through Place pin and a native surface click. The viewport displayed a turquoise pin and the panel showed one open record. The issue survived extension reload; the scene was left unsaved. This exposed an internal USD reference with an empty asset path. Reference identity now skips that internal arc when finding the enclosing external building reference. Five isolated anchor tests passed, including the new regression. A separate visible native mouse test also passed, proving gesture-to-surface-anchor completion without directly invoking the pick handler. Independent review found no Critical or Important defect in this focused change.

Composer temporarily stopped responding for roughly 70 seconds during this live attempt, then recovered without a restart. A read-only native stack sample is retained locally at `verification/live-pin-hang-stack.txt`. The cause of that pause is not established, and this acceptance does not claim large-model responsiveness.

- Select a BCF partner and perform an actual exchange. Schema validation and internal round trips do not establish external interoperability.
- Validate identifiers and geometry revisions on a representative building. Synthetic repeated references do not establish production metadata correctness or all native USD instance-proxy cases.
- Inspect clipping visually on a representative building. The live Section Box control and RTX-plane synchronization gate is now verified.
- Secondary-window Markup annotation remains unsupported. Requests are explicitly rejected; saved review cameras still support separate viewports.
- Measure large-model responsiveness before setting a performance guarantee.

The requested graph refresh could not run because the installed `graphify` wrapper points to a missing `C:/Users/StevenGomba/.local/bin/graphify` file. Its wrapper returned exit zero despite the Python error. Existing graph and local agent configuration files were preserved; the graph is not claimed current.

Assignment, permissions, authentication, concurrent editors, ACC synchronization, and BCF server exchange remain outside this approved milestone.
