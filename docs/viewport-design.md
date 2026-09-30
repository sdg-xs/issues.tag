# Issue viewport design

The adapter resolves the active viewport when a user begins an action. An explicitly supplied viewport is retained for verification or a pinned review surface. A render query retains its originating viewport and scene generation through the asynchronous callback; a stage replacement discards its result.

Issue placement uses the installed viewport raycast API. The returned element and world-space surface hit become an element-local anchor. IFC GlobalId and Revit UniqueId are recognized within a reference-instance scope. The referenced asset identity must also match. HOOPS AssetIDGUID remains an unverified candidate, because its presence does not prove element uniqueness. Path-only anchors support the current scene without promising reliable revision matching.

A native viewport scene registration creates one issue manipulator for every viewport. Pins use a world-space position with a camera-facing screen-space transform. They draw in the viewport UI scene, above the rendered model. Eligibility is computed separately from drawing: hidden attachments, clipped anchor locations, missing/ambiguous identities, and changed geometry remove the pin but retain the issue record. Update subscriptions keep pin positions and visibility current after model transforms and scene changes.

Placement arms a native screen click gesture only on the originating viewport. A click asks that viewport for its rendered surface hit. Clicking empty space leaves placement armed. A new placement request replaces the pending request; shutdown or a stage change cancels it. Clicking an issue pin invokes the panel callback or opens the issue directly.

Review viewpoints contain a camera pose/projection, clipping coefficients, component visibility, selected element references, stage units/up axis, and optional Section Box state. Restore authors a dedicated camera and temporary visibility/clipping in the session layer. The building source layers remain unchanged. It switches only the current viewport camera. Focus related elements is a separate navigation action and does not mutate the stored review record. A different coordinate frame requires explicit model mapping before restore.

The Section Box integration uses its public runtime state and only restores controls when that state belongs to the same stage. Imported viewpoints can restore clipping planes directly without claiming an editable Section Box configuration.

Verification uses the real Kit viewport: rendered center hit, transform-following scoped anchors, revision changes, missing/ambiguous matches, hidden/clipped pin filtering, overlay stage cleanup, pending placement cancellation, camera/visibility/selection restoration, and second-viewport camera isolation. The lead owns every Kit launch to avoid competing test processes.
