# Recovered ACC issue creation and editing requirements

## Recovery status and evidence

This document reconstructs the direction of the closed `/btw` discussion. It is not the original transcript or an exact copy of its plan. The user confirmed the intent in the main conversation: copy the ACC workflow, adjust the UI, and separate issue creation from the issue list.

An unfinished implementation was found at `C:/Users/StevenGomba/.codex/tmp/acc-workflow-20261001/issues.tag`. Its newer source files were modified around 13:48–13:50 on October 1. A verified archive of all 70 non-cache files is preserved at `verification/recovery/acc-workflow-20261001.zip`, with SHA-256 hashes in the adjacent manifest. The archive is local and ignored by Git. The source checkout was left unchanged.

The older [SPEC.md](../../../SPEC.md) remains the baseline for USD ownership, BCF exchange, saved views, and deferred permissions. This supplement records the recovered UI direction. It does not claim exact parity with every ACC feature.

## Confirmed intent

- Follow the ACC issue creation and editing workflow in USD Composer.
- Separate creating or editing an issue from browsing the issue list.
- Preserve the earlier requested pin, Markup, saved-view, and screenshot capabilities.
- Continue embedding issue data in the parent USD that references the building models, with BCF file integration.

## Requirements inferred from the unfinished implementation

These are concrete choices in the recovered code, not verified quotations from the missing discussion.

### Issue list

- A dockable `Issues` panel contains the list, a `Create issue` action, search, status/type filters, and BCF import/export.
- Search matches issue number, title, or description, without case sensitivity.
- Rows show issue number, title, status, and type. Selecting one opens a separate details panel.
- The recovered layout docks the list to the left of the primary viewport, with a default width of 330 pixels.
- Its filter refresh assigns the visible issue IDs to the viewport adapter. Pin filtering is an intended integration dependency, not a completed feature.

### Creation and editing

- A separate `Issue details` panel contains title, status, type, description, screenshot preview, annotation/replacement actions, attribution, attached element, and comments.
- The recovered layout docks details to the right, with a default width of 370 pixels.
- A new record is an in-memory `IssueEditSession`, separate from saved USD records.
- Existing records use the same staged editing model. Typing and changing controls do not immediately persist changes.
- Save validates a trimmed title of 1–255 characters and a recognized project issue type, then commits the record, changed viewpoint, and pending comment in one issue transaction.
- Cancel discards the staged changes. Saved evidence must survive cancellation of annotation or screenshot replacement.
- New issues receive a stable UUID and a positive project display number when committed. Issue types are stored at project level, with `Default` as the initial type.
- Scene generation and the original saved record are checked before committing. A stale edit must not overwrite a replacement scene or another edit.

### Screenshot, annotation, and BCF

- The details panel displays the saved PNG and offers `Annotate screenshot` and `Replace screenshot`.
- `MarkupAdapter.copy_for_edit(record)` creates owned draft evidence rather than editing saved annotation prims directly. This recovered method still requires integration and behavior verification.
- Save associates accepted evidence with the issue. Cancel deletes only owned unsaved evidence after safe native capture settling.
- BCF mapping was extended for title and issue type, and conflict planning includes those fields alongside description and status.
- The recovered store accepts schema versions 1 and 2, and writes version 2. Existing records require compatible defaults and stable numbering migration.

## Integration policy for completing the recovered work

The following resolves gaps in the partial code using existing project requirements. These are proposed completion decisions, not recovered interview answers.

- Keep `Create issue` in the list as the entry point. Arm placement in the primary viewport, capture its initial evidence, and open the separate details editor. Retain automatic native Markup activation from the previously requested creation flow unless the user changes that requirement.
- Creation remains an unsaved draft until the details Save action. Saving an issue changes the parent stage; normal scene Save writes the file to disk.
- Closing dirty details or switching to another issue offers Save, Discard, or Stay. Failed validation or screenshot capture keeps the draft and error visible.
- A saved issue opens its existing review view through the established native/portable recall routing. Editing metadata must not alter its view accidentally.
- Filters may hide saved pins, but must not block placing a new pin. A newly saved issue is selected and made discoverable even when its fields do not match the current filters.
- New drafts are separate from the existing saved record and its native annotations. Replacing a screenshot or cancelling must preserve saved evidence.
- Permissions, assignment, simultaneous editors, and ACC synchronization remain outside this recovery scope.

## What is incomplete

The recovered `window.py` requires callbacks such as `on_select` and `on_create`, while its `extension.py` still constructs the old window with `on_place_pin` and other old callbacks. Creation and editor lifecycle orchestration therefore remain unwired. No new recovery-specific acceptance tests or rendered verification report were found.

The live extension still has the earlier combined list/details UI and description-only creation editor. The recovered implementation has not been deployed. Its model/store/service/Markup/BCF changes are partial evidence, not proof of a completed workflow.

## Acceptance workflow

1. Open a writable parent scene with referenced building USDs and open Issues from its toolbar button.
2. Browse and filter the saved issue list independently of the details panel.
3. Choose Create issue, place a pin, annotate the view, enter a title/type/description, and Save.
4. Confirm one saved issue, its number and anchor, and a clean annotated screenshot. Save and reopen the parent USD and confirm the same data.
5. Open that issue and stage changes to title, description, status, and a comment. Discard once and confirm unchanged saved data; repeat and Save, then confirm persistence.
6. Replace or annotate its screenshot. Discard once and verify the original PNG and native annotations survive; repeat and Save, then verify accepted evidence.
7. Export/read BCF and verify title, type, status, description, comments, and supported viewpoint evidence. Reimport unchanged data without duplicates.
8. Verify dirty close/switch handling, read-only scenes, stale drafts, cancel during capture, extension disable, saved-view mouse navigation, and filter interactions.

The earlier intermittent GPU fault remains unresolved. Passing these narrow workflows must not be described as a broad crash fix.
