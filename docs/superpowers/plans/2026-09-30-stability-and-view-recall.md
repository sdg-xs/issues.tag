# Stability and saved view recall

> Execute with Superpowers test-first development and parallel workers. The lead owns integration and every Kit runtime launch.

Goal: prevent ghost pins after reload, isolate verification from Composer, and reuse native Markup camera recall while retaining BCF viewpoints.

Spec: [SPEC.md](../../../SPEC.md). User approved the ordered work and saved-view behavior in chat.

## Shared interfaces and ownership

- Lifecycle worker owns `issues_tag/viewport.py`, `issues_tag/extension.py`, and `tests/test_lifecycle.py`. Preserve synchronous `viewport.restore(record)` and make startup rollback and teardown idempotent. Attempt all cleanup before reporting errors.
- View recall worker owns `issues_tag/markup.py`, `issues_tag/service.py`, `tests/test_view_recall.py`, and `docs/markup-lifecycle.md`. Agree the recall interface before implementation. Existing native evidence may use native recall; BCF data remains authoritative and available as fallback. Ordinary recall must not enter annotation or leave navigation locked.
- Lead owns dependency preparation, launcher guards, runtime qualification, SPEC updates, integration wiring after workers finish, and verification records. No source changes in the original watched checkout during this pass.

## Sequence and evidence

1. Add regressions for partial startup and cleanup failures; observe failures, implement cleanup, then verify locally.
2. Add standalone checks rejecting shared/link dependency directories; prepare ordinary private copies and qualify actual loaded extension paths before any feature test.
3. Implement and test agreed native recall routing without rendering new thumbnails for ordinary selection. Preserve section state, visibility and selection.
4. Integrate workers. Lead runs narrow Kit lifecycle and saved-view cases, followed by placement retry, scene switching, save/reopen, BCF and Markup checks. A renderer fault stops broader rendered testing and is recorded.
5. Independent reviewer inspects the combined changes. Fix accepted findings and verify the complete workflow before claiming completion.

## Progress

- Composer exited before dependency preparation; no Kit process remained on inspection.
- Lifecycle API agreed: signatures unchanged, all resources attempted during teardown, errors reported after cleanup.
- Native recall implemented with portable fallbacks for incompatible or shared cameras. Private dependency guards implemented and checked.
- Prior rendered tests are not evidence that this follow-up passes. Runtime acceptance remains pending.

Checkpoint: native lifecycle reload/empty reopen passed; three SDK native recall cases passed. Offline dependency guards 11, view recall 10, lifecycle 8, and window cleanup 4 passed. First combined visible run completed with 78 passing and 3 failing cases. Installed the missing private XML validator and fixed a test that retained a destroyed service adapter. Actual mouse navigation subsequently passed with Core alone and after a genuine annotation lifecycle with Tool enabled. The baseline input failure was the Tool's initial canvas activation in the test fixture.

The next combined run GPU-crashed at 13:34:10 UTC during scene replacement after creation-callback cancellation. Evidence is preserved; no final report exists. A capture lifecycle worker owns `issues_tag/markup.py` and `tests/test_capture_lifecycle.py`. A harness worker owns `tests/test_markup.py`, `tests/test_native_recall.py`, and `tests/verify_kit.py`. The agreed interface retains capture ownership through cancellation and waits through the public native settling method. The lead owns rendered cancellation/scene-replacement verification and integration; a separate reviewer inspects combined changes. Test cleanup and durable progress records are implemented. Full runtime acceptance remains pending. No changes were deployed to the original watched checkout.

Follow-up: five-cycle native comparisons passed with Issues disabled, with Issues enabled, with session edit-target restoration, and with native caller cancellation. The Markup-only sequence still crashed after twelve passing checks, during the next scene replacement after a completed cancellation. Evidence and cycle milestones distinguish this from an individual test failure. Capture now waits for two delivered viewport frames after native settling, within the existing deadline. Independent review identified a service-detachment edge in that gate; its retained-context fix and regression are the next integration checkpoint.

Graphify updates use the global launcher with `PYTHONHASHSEED=0` to avoid its Windows re-exec path bug. Original legacy document IDs were preserved from a hash-verified backup; original graph has 456 nodes. The isolated graph is refreshed separately and excludes verification artifacts and SDK copies. Composer was reopened by the user at 14:10:09 UTC. Further rendered tests are paused pending saved scene changes and Composer closure; offline work continues in the isolated checkout.

Latest checkpoint: retained-context frame-gate fix reviewed; six offline capture regressions pass. Markup sequence completed 17/0 without a crash. Combined visible run completed 81/1 without a crash; save/reopen and BCF workflow passed. The remaining native mouse-navigation check also fails in isolation after recomputing input geometry. Next verify independent scroll gestures outside the SDK's 0.4-second merge window and inspect the old camera for stale-target writes. Composer reopened at 14:29:18 UTC, so rendered verification is paused pending closure. Current changes remain undeployed. Runtime acceptance is still pending.

Current checkpoint: Composer closed; separated-gesture native recall passed 4/0. A combined run completed 80/2 without a crash, with both failures caused by progress-file replacement before test execution. Bounded sharing-lock retries passed three checks and review. Original newer BCF 2.1/coordinate changes were preserved and their 12 offline checks passed; 42 stability/harness offline checks passed. The next combined run GPU-crashed after 34 durable passes, during the fixture following creation-callback cancellation. Evidence is in `verification/crash-20260930-144050/`. The delivered-frame gate is not a complete crash fix. No deployment or further broad rendered run; inspect cleanup-triggered asynchronous rendering before choosing the next narrow experiment. Independent source review found no concrete integration defect but cannot establish GPU completion.

Cleanup comparison prepared in the explicit capture probe module. Matched eleven-test prelude followed by five native cancellations with Tool enabled passed. It did not reproduce the acceptance fault, so the disabled arm was not run and no Tool-root-cause claim is justified. Evidence is preserved. Next distinguish native final capture from Issues adapter/test cleanup with the same preceding sequence. Original watched extension remains unchanged by this stability pass; its separate newer BCF work is preserved.
