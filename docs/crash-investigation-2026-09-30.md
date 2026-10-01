# Crash investigation, 2026-09-30

The user reported another crash during the pin improvement pass. Further Kit test launches stopped. The existing Composer process was not terminated, restarted, or saved.

## Timeline

- 13:34:28 Budapest time / 11:34:28 UTC: Composer logged a filesystem reload event on NVIDIA's installed `omni.kit.viewport.window/.../window.py`. Kit then shut down Composer's viewport dependencies.
- 13:34:44: vendor shutdown reported a missing `ManipulatorFactory`.
- 13:34:48: the separate visible verification app started, after the live reload had already begun.
- 13:35:27: the verification app reported a GPU device crash during `test_replacement_edit_preserves_newer_explicit_target`.
- 13:35:51: that test process terminated with access violation `0xC0000005`. The native stack includes `gpu.foundation.plugin.dll` and `omni.kit.renderer.plugin.dll`.
- 13:36:17 onward: Composer attempted to restart dependencies; environment and manipulator imports failed during the reload.
- Subsequent inspection: original Composer PID 30340 remained alive and rendering; later inspection confirmed impaired viewport control. Its window still displayed unsaved SOL11-23 and the user's issue pins.

The installed viewport `window.py` has SHA-256 `CA8B008D92EC7524080A38E3DBB40B5DB837D7BEABCE2AAA667F0129B4A7D5B4`, matching the SDK extension copy. Its timestamps remain July 29. The filesystem event does not establish a content edit or identify its originating process. The verification runner and changes inspected here contain no writes to NVIDIA's viewport source.

The earlier isolated GPU crash also occurred during Markup testing, in `test_annotated_comment_reopens_editably`. These native renderer failures and Composer's extension reload are separate observations. Their causal relationship and the exact initiating GPU operation remain unknown.

## Preserved work and evidence

The last committed checkpoint is `cdaef6d`, the successful live pin/reference fix. Improvements remain uncommitted and are copied to branch `feature/pin-improvements` in a worktree outside Composer's extension search folder. The original checkout and unsaved USD scene are retained. Further edits belong in the isolated worktree.

Local evidence in the original checkout's ignored `verification/` directory:

- `improvement-renderer-crash.log` preserves the failed GPU test process output.
- `pre-crash-improvements.patch` preserves the source changes before isolation.
- `live-pin-hang-stack.txt` records the earlier temporary placement pause; it is a different incident.
- GPU dump and native diagnostic files retain the vendor crash output.

The live log is `C:/Users/StevenGomba/.nvidia-omniverse/logs/Kit/My USD Composer/0.1/kit_20260930_124545.log`; the filesystem trigger is at line 50185.

## Verification state

### Reopened scene with stale cyan pins

After reopening SOL11-23 inside the same Composer process, the issue panel showed zero records while three cyan squares remained on rooftop equipment. Read-only offline Sdf inspection found no `/Issues` container in the saved root file. Live diagnostics also found no `/Issues` container and zero records in the current runtime service. Two older `ViewportAdapter` objects still had registered scene factories and native manipulators, but `_update_sub` was `None`; the current runtime adapter remained subscribed. A bounded cleanup unregistered only those two older adapters. Its assertions verified unchanged root-layer text and zero issue records; the cyan pins disappeared. The cleanup log is at 12:01:52 UTC. No issue data was deleted or saved. This confirms orphaned viewport registration as the cause of this mismatch, without establishing the originating reload trigger or resolving the broader manipulator failure. Extension lifecycle cleanup needs a regression before it can be considered fixed in source.

### Live viewport remains impaired

The user subsequently reported loss of viewport control. Composer PID 30340 was responsive and rendering, but an injected scroll over the viewport produced no visible camera movement. Read-only Script Editor diagnostics found the active camera `/OmniverseKit_Persp` with no lock-named attributes. The live log documents `ValueError: prim:1space already exist!` during `omni.kit.manipulator.prim.core` startup at 11:36:27 UTC and later `PrimTransformManipulator` missing `_enabled` during selection. Rendering recovery is therefore not full application recovery. These facts establish broken transform initialization, but do not yet identify the precise camera-input failure. No live USD content was saved, overwritten or closed during diagnosis; no broad extension restart was attempted. Recommend preserving a recovery copy before restarting Composer.

The user confirmed that no other coding agent or extension update was running around 13:34. Inspection found that the installed viewport package shares backing files with the global extension cache. Windows reports system-managed last-access updates enabled. A read or cache metadata event is therefore a possibility, but the watcher filter and originating process have not been established. Matching file contents cannot resolve that question.

SDK configuration uses both an app registry cache and a global registry cache; package installation can create links to the global cache. Separate app data, config and rendering-cache paths alone did not isolate dependencies. The isolated worktree's verification launcher now requires dependency snapshot directories, replaces default extension search paths, supplies private registry caches and disables registry links and registry access. After the user confirmed Composer was closed, ordinary private dependency copies were prepared and validated without hard links. The activation check passed with actual loaded extension paths qualified. The runner now also qualifies paths immediately after test-driven activation and before and after feature cases. This verifies isolation for those launches; the original crash cause remains unknown.

An earlier combined visible run passed 63 checks. A later run passed 66 checks and failed the native placement check. The next combined run crashed before producing a report. The queued-click token check and its gesture rebuild fix are not yet runtime verified. Do not describe this improvement pass as complete or claim a clean final suite.

Before further rendered testing, identify the viewport file-event source where possible and isolate the test app's extension cache from the live Composer process. Use the smallest reproduction for Markup and pin retries. A full suite is not the next diagnostic step. Do not restore, close, or overwrite the unsaved user scene as part of reproduction.

## Isolated follow-up verification

The first private snapshot was nested beneath the Issues extension root. A disable/re-enable regression revealed that Kit removed copied SDK Python modules while surviving viewport objects retained their old registry. Kernel importer source confirms path-based module removal during extension shutdown. Moving the snapshot to the sibling verification-dependencies directory kept the registry class stable, preserved native factories, restored exactly one Issues overlay, and removed all pins on empty-scene reopen. That regression passed. Prelaunch checks now reject overlapping dependency and extension roots in either direction. This controlled result explains the test-only reload failure, not the original live vendor file event or GPU crash.

Native saved-evidence recall and the transformed-parent/shared-camera fallback checks passed without thumbnail capture. The combined visible workflow remains pending.

## Private rendered run at 13:34:10 UTC

The subsequent private combined run failed with a GPU page fault at 36.480 seconds of application uptime. Its stdout, Kit log, loaded extension paths, GPU dump, shader debug data, and crash archive are preserved in `verification/crash-20260930-133410/`. No final test report was produced. A printed test start does not prove that the preceding test passed.

The last test start was `test_external_vendor_edit_defers_original_target_restoration`. Its fixture replaces the scene before running the body. The renderer destroyed the previous stage cache at 33.612 seconds, shortly after the real creation-callback cancellation test. This locates the observed boundary; it does not identify the exact GPU operation responsible.

Read-only SDK inspection found that initial Markup creation schedules a thumbnail capture task. Its creation callback runs inside buffer delivery and does not expose the task's completion. `Capture.wait_for_result` waits two completion frames, but its future may resolve when readback is scheduled, before buffer delivery. This establishes a missing completion contract and possible overlap, not the ordering of every GPU operation. The Issues adapter awaited the creation notification and could release ownership immediately on cancellation. The public `ViewportMarkup.wait()` waits eight application updates, following the vendor's settling convention; it is not a GPU fence. The proposed correction retains the capture task during caller cancellation and waits through that public method before releasing resources. Targeted cancellation followed by immediate scene replacement must verify the correction before another combined run.

Independent review also found a test that replaced the shared viewport adapter without restoring it. That cleanup leak is being corrected separately. It has not been established as the GPU crash cause.

Actual mouse navigation passed with Markup Core alone and after a genuine capture, arrow annotation, Apply, and issue recall with Markup Tool enabled. The earlier baseline failure came from enabling the Tool's drawing canvas before any active-Markup setting transition. These targeted passes do not establish full workflow stability.

## Focused recurrence at 13:47:30 UTC

Four offline capture-ownership regressions failed before the shielded task and public settling changes, then passed after implementation. The lead ran only `test_creation_cancellation_then_scene_replacement_repeated` in visible private Kit. It GPU-crashed again at 20.526 seconds of application uptime. Durable progress records locate it in the test body, with zero completed test outcomes. Native logs show stage-cache destruction before the fault. Evidence is preserved in `verification/crash-20260930-134730/`.

This disproves the claim that the ownership change and public settling method alone resolve the rendered failure. No combined suite or deployment followed. The next diagnostic comparison removes Issues entirely and exercises supported native Markup creation and scene replacement. Per-cycle milestones will distinguish capture delivery, adapter cleanup, and scene replacement. The independent reviewer also identified a missing pending-capture guard on annotation Begin; it is a separate Python overlap defect.

## Sequence-dependent recurrence at 13:57 UTC

The five-scene cancellation test passed when rerun with per-cycle milestones. A subsequent Markup-only run durably recorded twelve passing checks, then stalled inside its first repeated scene replacement after cancellation. `capture-cycle.json` records cycle 0, `before_stage`, at 27.349 seconds. The old scene cache was destroyed at 27.412 seconds. Initial GPU fault detection was at 31.761 seconds; device-loss handling later reported another failure at 60.162 seconds. The originating capture cancellation had already returned. Evidence is preserved in `verification/crash-20260930-135737/`, including the crash archive. There is no final report for that run.

The following five-cycle diagnostic comparisons each completed with one passing test and no failure: native capture with Issues disabled in empty scenes; Issues cancellation in an unchanged simple scene; native capture with Issues enabled in empty scenes; the same native path with Session-to-Root-to-Session edit-target restoration; and native callback cancellation with that edit-target restoration. Their results and stdout are retained separately under `verification/`. These passes weaken simple single-operation explanations. They do not rule out sequence, timing, or GPU-load effects.

The next narrow change distinguishes application updates from delivered viewport frames. Capture must retain ownership while waiting for actual frame delivery after the native thumbnail callback. The public API still provides no general GPU fence. Rendered recurrence after the same preceding Markup sequence remains the acceptance gate.

## Delivered-frame gate verification

Capture now retains the original USD context and viewport while waiting for two delivered frames after native settling, within the existing deadline. Service teardown can detach its context before settling completes, so the gate checks the retained context rather than the detached service. Six offline capture regressions pass, including service teardown during settling. Independent review found no remaining concrete source defect in this correction.

The same Markup sequence completed with 17 passing checks and no crash. The following combined visible run completed with 81 passing checks and one failing mouse-navigation check, also without a crash. Save/reopen, comments, status, annotated evidence, BCF exchange, and gesture pin placement passed. Reports and logs are retained under `verification/markup-frame-gate-*` and `verification/combined-frame-gate-*`. These results support the correction for the reproduced sequence; they do not establish that every GPU fault is resolved.

The remaining native recall check moved the baseline camera but did not move the returned issue camera. Recomputing the viewport center per gesture still produced 3 passes and 1 failure in the native recall module. Those results are preserved under `verification/native-recall-geometry-*`. SDK source shows scroll events within 0.4 seconds at the same cursor position can merge without rebinding the camera target. The next diagnostic separates independent gestures by 0.6 seconds and records the previous camera transform. This is a test change; no product or vendor camera code has been changed for this hypothesis.

Composer reopened at 14:29:18 UTC, PID 48432. Further rendered tests are paused while it is running. The current improvement changes remain isolated and have not been deployed to the original watched extension.

## Recurrence after delivered-frame gate at 14:40 UTC

After the user closed Composer, the separated-gesture native recall module passed all four checks. Both saved native recall and real annotation Apply allowed mouse navigation; the old baseline camera remained unchanged. The previous failure was removed by separating gestures outside the SDK scroll-merge interval. Rapid scrolling across a camera switch remains a distinct, unverified native SDK interaction.

The next combined run completed without a crash, with 80 passes and two failures before test execution. Both failures were Windows access-denied errors atomically replacing `progress.json`. The progress writer now retries only Windows sharing/access errors for at most nine 10 ms waits, then propagates failure. Three offline checks and independent review passed. Newer BCF work in the original checkout was preserved in the isolated checkout; its 12 offline compatibility checks passed without skips. Forty-two additional offline dependency, recall, lifecycle, cleanup, capture, and progress checks also passed.

The following combined run crashed again. Durable progress records 34 passes and no failures, not a completed suite. The creation-callback cancellation check had passed. The next repeated-cancellation test was still in its fixture/dependency boundary, before its body and cycle markers. Initial renderer frame-command failure and GPU crash detection occurred at 33.478 seconds; page-fault reporting followed at 33.516 seconds. Evidence, GPU dump, shader debug data, and crash archive are preserved in `verification/crash-20260930-144050/`. The test app and crash reporter exited; no user Composer process was running.

This disproves the delivered-frame gate as a complete fix. Broad rendered testing and deployment stop here. The next source investigation checks whether annotation cleanup or review removal starts further asynchronous rendering after the capture gate. The frame gate proves delivery before cleanup, not completion of all subsequent renderer work. No further wait or vendor patch has been added for this recurrence.

## Cleanup-wave comparison checkpoint

Private SDK inspection confirms `end_edit_markup(..., update_thumbnail=False)` does not schedule another thumbnail. Clearing active/editing settings does hide the Tool canvas, clear renderer UI, and schedule toolbar clearing. These actions occur after the existing capture gate. They establish another asynchronous boundary, not the cause of the GPU fault.

Two explicit diagnostic arms in `tests/test_capture_probe.py` reuse the actual first eleven Markup tests, then perform five native callback cancellations and scene replacements. Issues and Core remain enabled in both arms; only Tool activation after the prelude differs. The enabled arm must reproduce before disabled-arm success can support a conclusion. Atomic milestones record cleanup phases and viewport camera/resolution. These diagnostics are excluded from the combined acceptance suite.

The Tool-enabled arm completed with one passing diagnostic and no crash. Evidence is retained under `verification/prelude-native-tool-on-*`. Its eleven-test prelude and five cancellation cycles completed, but it did not reproduce the fault. The disabled arm was therefore not run. The Tool-cleanup explanation remains unconfirmed. This comparison also differs from the failing acceptance path: its final captures use native Core directly rather than the Issues adapter and its test cleanup. The next reduction should distinguish those remaining differences while retaining the preceding sequence. No production change was made for the cleanup hypothesis.
