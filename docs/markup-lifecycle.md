# Markup ownership and USD edit targets

New pins open native Markup and a description editor. Save & close hides the editor before capturing the annotated PNG and creates the issue with that initial evidence. Cancel removes the adapter's unsaved native record. Capture failure, cancellation before the editor opens, and extension shutdown use the same ownership checks. Pending captures retain originating cleanup handles through shutdown and delete only after native settling and viewport delivery. A timeout before that gate preserves the in-flight native record because the installed SDK exposes no safe cancellation fence.

NVIDIA's installed Markup Tool draws in its primary `Viewport` window. The Issues adapter validates that window before mutation and binds camera capture, saved-view restoration, and PNG capture to the same viewport. Secondary-viewport evidence requests fail with a readable instruction to select the primary viewport.

Camera capture happens after Markup activation completes. Creation waits for the public creation callback, the native Markup's public settling method, and two frames delivered to the originating viewport before releasing ownership. These waits share the creation deadline. PNG capture separately waits for a delivered viewport frame. Caller cancellation retains the owned capture task until cleanup completes, then propagates cancellation. Repeated cancellation cannot release the root-target lease early or allow another local capture or annotation to overlap. Capture keeps local references to the vendor core, viewport window, and originating USD context for cleanup even when the Issues extension is disabled.

The installed `ViewportMarkup.wait()` waits eight application updates. This is a vendor settling convention, not a GPU fence or a guarantee for arbitrary external scene disposal. The SDK does not expose a creation option to skip or cancel its initial thumbnail. Creation retains its existing 30-second deadline. A timed-out capture or a scene replaced externally still needs careful runtime diagnosis; no vendor task or renderer implementation is patched here.

An editing session owns its Markup identity, stage generation, viewport window, and record identity. The adapter rejects overlapping local operations. Before producing evidence, it checks that NVIDIA's selected Markup still matches the owned identity. If the user replaces it, the operation rejects its result and preserves the replacement review. An abandoned owned edit is ended separately from clearing the selected review. Cleanup never cancels a replacement scene's annotation.

## Why the root target remains selected during drawing

The installed core's `edit_context` uses `Usd.EditTarget(None)` when no sidecar is configured. Native tool gestures call its mutation methods directly, so they author through the stage's current edit target. Two workers compared alternatives against the installed SDK:

- Restoring the previous target immediately after Begin would send subsequent native drawing into that layer. The public gesture commands expose no per-operation layer argument. This option would require replacing vendor gesture routing or patching its singleton.
- A shared root-target lease retains the original target while supported native drawing runs, then restores it after the final owned session ends. This keeps annotations in the parent USD without vendor patches.

The implementation uses the lease. Its private registry belongs to the scene's IssueService and coordinates its adapters. Each token releases once. State records the originating context, stage generation, original target, imposed root target, and active count. An old scene cannot restore into a replacement scene or delete its new lease. A user-selected target change remains the restoration destination.

Losing Markup ownership still releases the target lease. If a direct NVIDIA edit remains active, the final lease retains its restoration obligation and watches application updates until that edit ends. It then restores the original target only if the stage still has the imposed target. It leaves an explicit later target choice intact. Deferred restoration changes the target without clearing the external review.

## Runtime coverage

The lead-controlled Markup case verifies initial-view editing, overlapping operations, Apply navigation cleanup, failure during Begin, stage replacement, editable Save/reopen with a rendered arrow and note, replacement vendor owners, activation-time camera movement, cancellation from the real creation callback, external native edits, selection-only recall, actual Issues extension disable during capture, and explicit target changes. These tests use the installed public APIs and real Kit rendering.

## Selecting saved evidence without entering annotation

`IssueService.restore_viewpoint(record)` offers an optional synchronous native recaller and retains the portable viewport restoration fallback. Ordinary pins and imported BCF viewpoints keep their stored camera data and use that fallback. They do not create Markup records, request thumbnails, or activate Markup merely because an issue is selected.

For existing native evidence, the adapter uses the documented `ViewportMarkup.recall` method directly. It first checks that the exact saved Markup path and camera belong to the current scene, that the visible primary viewport is eligible, and that no local capture or native review/edit is active. The Issues record restores its own coordinate frame, visibility, selection, and section state before camera recall; invalid frames fail before the native camera changes. The context-only viewport restoration avoids creating an additional Issues review camera.

This call excludes `info`, `Approve`, and `thumbnail`, leaving the installed Markup Core 1.3.1 camera setting. The native camera setting copies its saved camera into the session layer's `/OmniverseKit_Persp` and selects it in the active viewport. Calling the Markup instance directly avoids `core.recall_markup`, whose selection setter disables navigation and clears selection. The adapter does not enter annotation, select a native review, acquire a root-target lease, or rewrite evidence.

This integration follows the installed 1.3.1 setting names. A future core version with additional settings needs a fresh review of its public recall behavior before native compatibility is claimed. No private `CameraSetting` member is used. Ordinary issues and imported BCF views reuse the existing `/OmniverseKit_Persp` camera in the primary viewport, matching Markup's camera destination and session-layer edits. They do not create a new review camera for each issue. Portable data supplies the world-space pose and lens without creating a synthetic Markup record or thumbnail. Missing, animated, shared, or secondary-viewport perspective cameras retain the isolated per-viewport fallback.

Native recall declines if another viewport in the same scene consumes `/OmniverseKit_Persp`; the portable per-viewport camera preserves that other view. It also checks the vendor's saved local attributes against the portable world-space camera. An anonymous USD camera evaluates the attribute-copy result without live scene edits or rendering. Transformed-parent cameras and incompatible projection or lens data use the portable fallback instead of showing the wrong review pose.

Native recall also declines an animated destination camera. The vendor writes default attribute values without clearing existing time samples, so a sampled pose or lens could override the saved view despite matching defaults. The portable camera avoids changing those samples.

October 1 camera update: four standalone checks cover primary-camera reuse, saved root-layer preservation, shared-viewport isolation, animated-camera preservation, and clearing an earlier lens shift for centered portable views. The extra-camera regression failed before implementation. Existing capture and cleanup work remains unchanged. Rendered acceptance is pending; this camera change does not resolve or conceal the recurring GPU crash.

Ten offline tests exercise the real service and adapter routing with framework doubles and real USD camera attributes: native evidence, ordinary/BCF fallback, foreign scene metadata, coordinate rejection, preservation of an external edit, an unavailable native core, shared perspective cameras, local/world or projection mismatches, animated destination cameras, and service cleanup after a notice failure. The camera fixture matches the portable pose and uses a generic saved prim as the vendor does. These prove routing and ownership decisions. They do not prove native rendering or free camera navigation; those remain a lead-controlled Kit verification requirement for this isolated change. Standalone USD imports use the private verification dependency snapshot.

Lead-controlled Kit checks passed for native evidence recall, transformed-parent fallback, and shared-camera fallback. They verify pose/lens, selection/visibility, native ownership, subsequent camera movement, and unchanged root-layer issue, evidence, model, and source-camera specs.

The separated-gesture native recall module also passed all four checks, including real mouse navigation after saved-view recall and annotation Apply. Tests separate independent scroll gestures by 0.6 seconds because the installed SDK merges same-position scrolls within 0.4 seconds and may retain the earlier camera target. Rapid scrolling across a camera switch remains unverified.

Current stability acceptance remains open. A Markup sequence passed 17/0 and combined runs completed without crashes, but a subsequent combined run GPU-crashed after cancellation at the next scene replacement. The delivered-frame gate precedes native review cleanup; it does not establish completion of UI teardown or all GPU work. Evidence and subsequent hypotheses are recorded in [crash investigation](crash-investigation-2026-09-30.md). These changes remain isolated pending a reliable fix.

Kit 110.2 can update the render-product camera relationship and author exposure metadata on a runtime review camera when switching views. Those renderer writes can dirty the parent layer even with a session edit context. Saved issues and Markup evidence remain unchanged. This integration does not roll back renderer writes or patch vendor code.
