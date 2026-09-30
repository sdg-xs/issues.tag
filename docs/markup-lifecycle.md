# Markup ownership and USD edit targets

NVIDIA's installed Markup Tool draws in its primary `Viewport` window. The Issues adapter validates that window before mutation and binds camera capture, saved-view restoration, and PNG capture to the same viewport. Secondary-viewport evidence requests fail with a readable instruction to select the primary viewport.

Camera capture happens after Markup activation completes. Creation waits for the public creation callback; PNG capture waits for a delivered viewport frame. The adapter keeps the created Markup identity before awaiting thumbnail completion so cancellation can end its edit and release navigation. Capture keeps a local reference to the vendor core and originating USD context for cleanup even when the Issues extension is disabled.

An editing session owns its Markup identity, stage generation, viewport window, and record identity. The adapter rejects overlapping local operations. Before producing evidence, it checks that NVIDIA's selected Markup still matches the owned identity. If the user replaces it, the operation rejects its result and preserves the replacement review. An abandoned owned edit is ended separately from clearing the selected review. Cleanup never cancels a replacement scene's annotation.

## Why the root target remains selected during drawing

The installed core's `edit_context` uses `Usd.EditTarget(None)` when no sidecar is configured. Native tool gestures call its mutation methods directly, so they author through the stage's current edit target. Two workers compared alternatives against the installed SDK:

- Restoring the previous target immediately after Begin would send subsequent native drawing into that layer. The public gesture commands expose no per-operation layer argument. This option would require replacing vendor gesture routing or patching its singleton.
- A shared root-target lease retains the original target while supported native drawing runs, then restores it after the final owned session ends. This keeps annotations in the parent USD without vendor patches.

The implementation uses the lease. Its private registry belongs to the scene's IssueService and coordinates its adapters. Each token releases once. State records the originating context, stage generation, original target, imposed root target, and active count. An old scene cannot restore into a replacement scene or delete its new lease. A user-selected target change remains the restoration destination.

Losing Markup ownership still releases the target lease. If a direct NVIDIA edit remains active, the final lease retains its restoration obligation and watches application updates until that edit ends. It then restores the original target only if the stage still has the imposed target. It leaves an explicit later target choice intact. Deferred restoration changes the target without clearing the external review.

## Runtime coverage

The lead-controlled Markup case verifies initial-view editing, overlapping operations, Apply navigation cleanup, failure during Begin, stage replacement, editable Save/reopen with a rendered arrow and note, replacement vendor owners, activation-time camera movement, cancellation from the real creation callback, external native edits, selection-only recall, actual Issues extension disable during capture, and explicit target changes. These tests use the installed public APIs and real Kit rendering.
