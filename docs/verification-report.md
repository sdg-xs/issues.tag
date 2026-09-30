# Implementation verification record

Date: 2026-09-30. Branch: `feature/issues`. Approved baseline: `ace2f88`. Runtime setup: `2fba6d4`.

The implementation covers the native issue panel, root-layer USD persistence, undoable record changes, scoped model attachments, viewport pins, saved review context, editable Markup evidence, and BCF 3.0 file import/export with conflict previews. The lead integrated the workers' changes and controlled all Kit runs. UI, persistence/BCF, and viewport workers had separate file ownership and shared immutable record/service interfaces.

## Runtime evidence

Verification command: `./run-verify-kit.ps1 -Case all -Visible`.

The final run reported 43 passes and zero failures with process exit zero. It also checks rotation of an anchored model instance in addition to translation and scale.

The tested runtime is Kit 110.2.0, Python 3.12.13, and OpenUSD 0.25.11. Installed Markup Core 1.3.1 and Tool 1.2.82 target Kit 107.3 in their manifests; their activation and evidence workflow run in the installed 110.2 runtime. Vendor manifests and implementation were not changed. Official BCF 3.0 schemas validate the generated XML through the test-only lxml dependency.

The suite includes rendered surface picking, hidden/clipped pin eligibility, independent viewport cameras, Save/reopen, attributed reviewer handoff, geometry-change detection and explicit repair, editable annotations, imported evidence, repeated import, conflict choices, stale previews, malformed archives, and atomic persistence. Preview cases also produce screenshots; they count toward the 43 registered outcomes.

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

## Open acceptance gates

- Select a BCF partner and perform an actual exchange. Schema validation and internal round trips do not establish external interoperability.
- Validate identifiers and geometry revisions on a representative building. Synthetic repeated references do not establish production metadata correctness or all native USD instance-proxy cases.
- Exercise live Section Box controls with the neighboring extension enabled. Current runtime tests verify clipping-plane restoration and viewport isolation; source validation covers native Section Box state.
- Validate Markup ownership in additional viewport layouts. NVIDIA's installed tool uses the primary `Viewport` window for annotation capture.
- Measure large-model responsiveness before setting a performance guarantee.

The requested graph refresh could not run because the installed `graphify` wrapper points to a missing `C:/Users/StevenGomba/.local/bin/graphify` file. Its wrapper returned exit zero despite the Python error. Existing graph and local agent configuration files were preserved; the graph is not claimed current.

Assignment, permissions, authentication, concurrent editors, ACC synchronization, and BCF server exchange remain outside this approved milestone.
