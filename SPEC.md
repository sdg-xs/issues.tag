# Omniverse issue management specification

This specification is the single product and implementation reference for native Omniverse issue management. The first milestone uses ACC model-viewer issues as the interaction reference and includes persistent surface pins, comments, saved review viewpoints, Markup annotations, and BCF file exchange. Product scope is confirmed. The testing approach below is proposed for review, and the technical validation items remain open.

## Problem Statement

Reviewers need to identify problems in a building model, record their context, and return to those problems after saving or updating the scene. A description alone does not identify the affected geometry or reproduce the camera, section cuts, and visibility used during review.

The project scene is a parent USD file that references building USD files. Reviewers need one project-wide issue list in that parent scene and a way to exchange issues through BIM Collaboration Format, or BCF. Different people can take turns editing. Simultaneous editing is outside the first milestone.

## Solution

Add an Issues panel and interactive viewport pins. A reviewer clicks a model surface to create an issue, writes a description, and manages its related elements. The extension captures the initial review viewpoint and restores it when the issue opens.

Reviewers add comments, optional comment viewpoints, and annotations through supported Omniverse Markup functionality. Issue records persist in the parent USD scene and use its normal Save workflow. BCF files carry supported issue data and viewpoints between tools. Missing model references remain visible and recoverable rather than causing an issue to disappear.

The primary user is a model reviewer. A subsequent reviewer can open the saved parent scene, investigate an issue, add evidence, and update its status. Reviewers initially have equal access to supported issue actions, with assignment and detailed permissions deferred.

### Product goals

- Create issues on model surfaces and identify additional related elements.
- Preserve descriptions, comments, statuses, viewpoints, and annotations through scene Save and reopen.
- Restore the review context when an issue opens.
- Retain reliable attachments across model transforms and revisions, with explicit recovery for unresolved references.
- Exchange supported issue content through BCF files without duplicates or silent overwrite of conflicting local edits.
- Reuse supported Omniverse Markup functionality for annotations and viewpoint evidence.

### Core workflow

1. Open the parent USD scene and its referenced building models.
2. Click a surface to place a pin and automatically attach the hit element.
3. Write the description and adjust the related-element list.
4. Capture the initial viewpoint, including camera, section cuts, visibility, and selection.
5. Add annotations through supported Markup functionality.
6. Save the parent scene.
7. Open an issue from the list or its pin to restore the review context.
8. Add comments and optional annotated comment viewpoints.
9. Update the status and save the scene.
10. Import or export BCF files to exchange supported issue content.

## User Stories

1. As a reviewer, I want one issue list for the parent scene, so that I can review problems across its referenced building models.
2. As a reviewer, I want to click a model surface to create an issue pin, so that I can identify the problem's location.
3. As a reviewer, I want the clicked element attached automatically, so that I do not need to select it again.
4. As a reviewer, I want to write and edit an issue description, so that I can explain the problem.
5. As a reviewer, I want a stable issue identifier, so that saving, reopening, and exchanging the issue preserve its identity.
6. As a reviewer, I want to add related elements, so that an issue can describe a problem involving several components.
7. As a reviewer, I want to remove related elements without losing the pin anchor, so that I can correct the issue's scope.
8. As a reviewer, I want to distinguish the pin's attached element from the related-element list, so that changing the list does not unintentionally move the pin.
9. As a reviewer, I want pins to remain readable as I navigate, so that I can find issues at different zoom levels.
10. As a reviewer, I want pins visible through geometry, so that intervening surfaces do not conceal eligible issues.
11. As a reviewer, I want pins hidden when their attached elements are hidden or excluded by section cuts, so that the viewport reflects my review context.
12. As a reviewer, I want hidden-pin issues to remain in the issue list, so that viewport visibility does not remove access to them.
13. As a reviewer, I want to open an issue from its pin or list entry, so that both navigation paths reach the same record.
14. As a reviewer, I want the initial camera saved with the issue, so that I can return to the original angle.
15. As a reviewer, I want section cuts, visibility, and selection saved with the viewpoint, so that reopening reproduces the review context.
16. As a reviewer, I want opening an issue to restore its saved viewpoint, so that I can understand the original observation.
17. As a reviewer, I want a separate Focus related elements action, so that I can inspect the affected geometry without replacing the saved viewpoint.
18. As a reviewer, I want to add comments, so that I can record investigation and resolution evidence.
19. As a reviewer, I want to add a viewpoint to a comment, so that I can show evidence from another angle.
20. As a reviewer, I want the initial viewpoint preserved when new comment viewpoints are added, so that the original evidence remains available.
21. As a reviewer, I want to configure my author name, so that new comments identify their author.
22. As a reviewer, I want author names and timestamps retained on comments, so that I can understand their sequence and provenance.
23. As a reviewer, I want imported comments to retain their original authors, so that file exchange does not rewrite their attribution.
24. As a reviewer, I want to draw arrows, shapes, strokes, and notes on viewpoints, so that I can explain the issue visually.
25. As a reviewer, I want annotations editable after reopening the scene, so that I can refine the evidence.
26. As a reviewer, I want annotated snapshots included in BCF exports, so that another tool can display visual evidence.
27. As a reviewer, I want Open, In progress, Resolved, and Closed statuses, so that I can distinguish investigation, reported fixes, and verified fixes.
28. As a reviewer, I want to reopen an issue, so that I can report a recurring or incomplete fix.
29. As a reviewer, I want to edit issues without assignment or role restrictions in this milestone, so that deferred permissions do not obstruct review.
30. As a reviewer, I want issue changes included in the scene's Save workflow, so that I control when persistent changes are written.
31. As a reviewer, I want an unsaved-change indication, so that I know when issue edits have not been persisted.
32. As a reviewer, I want saved issues, comments, viewpoints, and annotations restored after reopening, so that work survives an application restart.
33. As a subsequent reviewer, I want to open the same saved parent scene and continue editing, so that people can take turns reviewing.
34. As a reviewer, I want the pin to follow its attached element's transform, so that moving a building or element does not leave the pin behind.
35. As a reviewer, I want surviving stable element IDs matched after model replacement, so that issues retain their attachments where a reliable match exists.
36. As a reviewer, I want missing or uncertain attachments identified explicitly, so that the extension does not silently attach an issue to the wrong element.
37. As a reviewer, I want to reattach unresolved references manually, so that I can recover issues after model changes.
38. As a reviewer, I want to import BCF files, so that I can review issues created elsewhere.
39. As a reviewer, I want to export BCF files, so that I can return supported issue data and evidence to other tools.
40. As a reviewer, I want matching BCF topic IDs to update existing issues, so that exchange does not create duplicate topics.
41. As a reviewer, I want repeated imports to add comments and viewpoints only once, so that importing the same file twice is harmless.
42. As a reviewer, I want conflicts shown before imported descriptions or statuses replace local changes, so that I can choose which value to keep.
43. As a reviewer, I want issues imported even when their elements cannot be found, so that useful descriptions and evidence remain available.
44. As a reviewer, I want unresolved BCF references available for manual mapping, so that I can connect imported issues to the loaded model.
45. As a reviewer, I want a spatial pin shown only when its scene location can be established, so that an unresolved import does not display a misleading location.
46. As a reviewer, I want supported issue data preserved through a BCF round trip, so that exchange does not lose the agreed review content.

## Implementation Decisions

### Project ownership and persistence

- The parent USD scene owns the project-wide issue records. Referenced building models provide geometry and source identity.
- Issue records, comments, viewpoints, and editable annotations persist as USD data in the parent scene. The exact schema and representation of embedded snapshots remain technical design work.
- Each issue has a stable identity. Imported BCF topic identities remain available for later matching and export.
- Issue changes use the existing scene Save workflow and show an unsaved state. An issue edit does not trigger an automatic save of unrelated scene changes.
- One person edits at a time. This is a workflow limit, not a commitment to implement locking, user authentication, or concurrent merge behavior.

### Issue interactions and lifecycle

- The extension provides an issue list, issue details, comment history, viewport pin interactions, BCF exchange, and model-reference resolution.
- Surface placement attaches the hit element automatically. The pin anchor and the editable related-element list are separate concepts.
- Issue fields include description, status, stable identity, and creation and modification attribution. Comments include author names and timestamps.
- Author names are configurable for this milestone. Imported authors remain unchanged. These names are attribution, not authenticated identity.
- Statuses are Open, In progress, Resolved, and Closed. Resolved indicates a reported fix. Closed indicates verification. Reopening is supported, with no role-based transition restrictions in this milestone.
- Assignment and permission settings are deferred. The exact policy for any additional status transitions remains an implementation detail to document.

### Pin attachment and visibility

- Pins have a readable screen size and draw through intervening geometry.
- Pins hide when the attached element is hidden or excluded by section cuts. Their issues remain accessible in the issue list.
- Anchors follow element transforms. The original review viewpoint remains evidence and is not silently rewritten when geometry moves.
- Model references must distinguish the source model and its instance in the parent scene. A prim path alone does not establish stable identity across reimports.
- After model replacement, reliable stable source-element IDs restore references. Missing or ambiguous matches remain unresolved.
- Changes to an element's shape can invalidate the saved surface location even when its identity survives. Uncertain attachments require review or manual reattachment.
- The extension must not use proximity or a similar name to silently bind an issue to another element.

### Viewpoints and Markup reuse

- Each issue has an initial viewpoint. Comments can optionally add viewpoints without replacing the original.
- A viewpoint records the camera, section cuts, visibility, and selected elements needed to restore the review context.
- Opening an issue restores its saved review view. Focus related elements is a separate action and does not overwrite that saved view.
- Supported Omniverse Markup APIs are reuse candidates for camera capture and recall, annotations, and snapshots. Surface-attached pins and the issue lifecycle require their own behavior.
- Markup annotations remain editable in USD. BCF exports include annotated snapshots. Exchange of editable annotation primitives depends on the eventual BCF compatibility target.
- Rendering and viewpoint conversion must account for stage units, axes, model placement, and the coordinate frame used by BCF.

### BCF file exchange

- The milestone supports file import and export. It does not connect to a BCF server or Autodesk issue service.
- Import matches existing issues by BCF topic identity. New comments and viewpoints are added once, with their exchange identities preserved.
- Reimporting the same unchanged file must not duplicate issues, comments, or viewpoints.
- Conflicting descriptions and statuses are presented before replacing locally changed values. The comparison baseline and conflict UI still need technical design.
- Missing elements do not prevent import of descriptions, statuses, comments, viewpoints, or available snapshots.
- Unresolved element references remain available for manual mapping. A pin appears only when its scene position can be established reliably.
- Round-trip preservation covers the supported content defined here. Unsupported data handling must be documented rather than silently presented as full BCF fidelity.
- The BCF version, external partner application, component identity mapping, status mapping, and required BCF metadata mapping are deferred compatibility decisions.

## Testing Decisions

The proposed primary test boundary is the extension as experienced inside the target Kit application. Tests drive the issue panel, viewport, Save workflow, and BCF file actions. Saved USD and exported BCF are observable outputs. This boundary is proposed for user confirmation, not yet confirmed.

Tests must assert user-visible behavior and persistent results. Tests must not depend on internal class structure, callback counts, or the exact USD attribute layout. Small focused tests are appropriate for coordinate conversion, identity matching, and import comparison when they detect defects that are hard to diagnose through the application workflow.

The surfaces under test are issue management, viewport anchors, viewpoint restoration, Markup integration, USD persistence, and BCF exchange. The extension workspace is empty, so it has no existing tests, glossary, or ADRs to reuse. Neighboring extensions and installed Markup provide implementation references, but reusable test infrastructure has not been established.

### Acceptance criteria

The milestone must demonstrate these outcomes in the target Kit application:

| Scenario | Required result |
| --- | --- |
| Create an issue | The pin appears on the clicked surface and the hit element is attached. |
| Change related elements | Adding or removing elements does not unintentionally move the pin anchor. |
| Save and reopen | Stable identity, description, status, attribution, comments, viewpoints, and editable annotations remain available. |
| Open an issue | Camera, section cuts, visibility, and selection are restored. |
| Focus related elements | Geometry is framed without overwriting the stored viewpoint. |
| Add annotated comment evidence | Both initial and comment viewpoints survive Save and reopen, with editable annotations. |
| Move attached geometry | The pin follows its transform and the original stored viewpoint remains unchanged. |
| Hide or section out an attachment | The pin hides while its issue remains in the list. |
| Replace a model | Reliable stable-ID matches survive. Missing or ambiguous references become unresolved. |
| Repair a reference | Manual reattachment survives Save and reopen. |
| Repeat a BCF import | Topic, comment, and viewpoint counts do not grow on the second import of the same file. |
| Import conflicting changes | Conflicts appear before local descriptions or statuses are replaced. |
| Import missing elements | Available issue content and snapshots are retained. Unresolved references are shown without creating a misleading pin. |
| Complete a BCF round trip | Supported topic identities, descriptions, statuses, authors, timestamps, comments, viewpoints, component references, and annotated snapshots survive. |
| Continue as another reviewer | Saved issues can be read, commented on, and updated by the next editor without assignment or role restrictions. |
| Edit without saving | Unsaved state is visible and the scene is not automatically saved. |

Integration tests use a numeric tolerance of 1e-6 for native camera and clipping comparisons and generated repeated-reference model fixtures. The implemented file profile is BCF XML 3.0. External compatibility testing remains pending until a partner application is chosen; representative production models and revisions still need validation.

No performance limits or model-size targets have been agreed. Technical planning must establish them before treating them as measured capabilities.

## Out of Scope

- Issue assignment, assignee controls, and assignment notifications.
- Detailed permissions, role settings, and authenticated identity management.
- Simultaneous issue editing, conflict resolution between live editors, and real-time collaboration guarantees.
- Direct synchronization with Autodesk issues or a BCF server.
- Automatic clash detection, deadlines, reporting dashboards, and a full clone of every ACC feature.
- Guaranteed recovery when source-element identity is absent, ambiguous, or changed.
- Automatic relocation onto changed surface geometry without review.
- Universal BCF version support or compatibility claims for unnamed external applications.
- Full exchange of editable annotation primitives before partner capabilities are validated.

## Further Notes

The product scope above comes from the confirmed design interview. The first milestone is complete when the acceptance workflows pass in the target application and the agreed BCF exchange subset is validated. Choosing the external BCF partner later must not be mistaken for completed interoperability validation.

The implementation has been exercised in the installed Kit 110.2.0 runtime with Python 3.12.13 and OpenUSD 0.25.11. Markup Core 1.3.1 and Markup Tool 1.2.82 target Kit 107.3 in their manifests; activation and editable evidence persistence have passed local Kit 110.2 integration tests. Compatibility with other applications or SDK versions is not established.

A neighboring model browser exposes an Asset ID GUID field, but its uniqueness and stability at the element level are unverified. A representative parent scene and model revision must establish the usable source identity and coordinate mapping before attachment behavior is claimed complete.

Technical validation must establish the target Kit version, Markup public API compatibility, USD schema and embedded snapshot representation, element identity, repeated-reference handling, section-cut behavior, BCF metadata mapping, import comparison baseline, and viewpoint conversion tolerances. These checks do not reopen the confirmed product scope.

### Delivery and review

The approved Superpowers implementation plan follows persistent issue records, surface pins and model references, viewpoint restoration and Markup evidence, then BCF exchange and the complete acceptance workflow. UI, persistence/BCF, and viewport workers own separate files; the lead owns integration and all Kit verification runs.

The specification and implementation plan were accepted before development. Runtime evidence, internal BCF/schema validation, and independent review are recorded with the implementation. External BCF exchange, production source identity, and performance acceptance remain separate open validation items.

### Reuse constraints and references

NVIDIA source packages contain proprietary notices. Reuse should use supported extension dependencies and public APIs. Copying or redistributing source requires checking the applicable terms.

Reference material:

- [Omniverse Markup documentation](https://docs.omniverse.nvidia.com/extensions/latest/ext_markup.html) describes the annotation workflow and shared-session editing limits.
- [Markup Core API documentation](https://docs.omniverse.nvidia.com/kit/docs/omni.kit.markup.core/latest/omni.kit.markup.core.html) identifies the public API reuse candidate. Documentation for the installed version must be checked during implementation.
- [buildingSMART BCF XML specification](https://github.com/buildingSMART/BCF-XML) is the reference for file exchange.
- [buildingSMART BCF API specification](https://github.com/buildingSMART/BCF-API) describes the separate server interface, which is outside this milestone.
- [Autodesk viewer state](https://aps.autodesk.com/blog/customize-viewer-state-using-filter-object-part-1) provides background for the ACC-style review context.
- [Autodesk model alignment](https://aps.autodesk.com/blog/managing-multi-model-alignment-aps-viewer) provides background for model units, transforms, and offsets.

This specification has not been published to an issue tracker. Tracker destination and triage configuration are unavailable. After configuration, publication should apply the `ready-for-agent` label required by the to-spec workflow.
