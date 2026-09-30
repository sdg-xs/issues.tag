# Issues panel design

The Issues panel is a native Omniverse dock. It uses the Kit system font and a compact industrial layout so reviewers can keep the model viewport visible. The visual signature is a teal selection rule on the active issue row. Neutral surfaces and text carry the remaining hierarchy.

## Layout

The panel defaults to 420 pixels wide and 720 pixels tall. It remains useful at 380 pixels wide. All controls follow a single vertical reading order. The upper toolbar provides Place pin, Import BCF, and Export BCF. A second row shows the editable author name. An unsaved-state label explains that scene Save persists changes.

The issue list shows status text and a one-line description excerpt. Status remains readable without its color. Selecting an issue displays its full description, status control, author, and timestamps. Open review view and Focus related elements are separate actions. Related elements have their own section and do not replace the pin anchor.

The comments section preserves author names and timestamps. Each comment can expose its saved viewpoint. A labeled multiline comment field is followed by Add comment, Capture viewpoint, and Annotate controls. Comments with no viewpoint remain valid. Assignment and permission controls do not appear.

BCF import opens a separate preview before any issue data is changed. The preview shows imported issue count, exchange warnings, and every conflicting description or status with local and imported values. Each conflict defaults to Keep local. The reviewer can choose Use imported per field, then Apply import or Cancel. A failed or stale import leaves the preview open and displays its error. The preview does not silently choose incoming edits.

The empty state explains surface placement and permits creation of a non-spatial record for imported or unresolved issues. With no stage open, issue mutation controls are disabled and the panel asks the reviewer to open the parent USD scene.

## Tokens

| Token | Value | Use |
| --- | --- | --- |
| Background | `#141a1e` | Window background |
| Surface | `#20292e` | Inputs and issue rows |
| Raised surface | `#2b373e` | Hover and focus |
| Text | `#edf3f5` | Main text |
| Muted text | `#acbcc4` | Attribution and supporting labels |
| Accent | `#2de1c2` | Active row, primary action, focus |
| Border | `#455861` | Section boundaries |
| Error text | `#ffd4cb` | Recoverable failure messages |
| Spacing | 4, 8, 12, 16 px | Consistent alignment |
| Radius | 2 px | Native CAD controls |

Use native typography without downloaded fonts. Body text is 14 px, supporting text 12 px, and section labels 13 px. The teal primary action uses dark text. No decorative animation is required for a persistent review dock.

## Behavior and accessibility

Every input has a visible label. Buttons use explicit action text and tooltips. Native Kit focus and keyboard navigation remain available. Status controls present the exact four status strings. Failure messages stay in the panel rather than silently dismissing edits. Blank descriptions and comments are rejected before modifying records. Text edits use explicit Apply and Add comment actions.

Selecting a list entry opens its saved review view. Refresh retains an existing selection and clears it when that record no longer belongs to the current stage. Refresh must not overwrite in-progress input while typing. Pending comment viewpoints belong to the selected issue and are cleared on selection or stage change.

## Verification

Behavior tests call the same panel actions used by buttons against the real service and USD store. They verify values and attribution after creation, editing, commenting, reopening, and status changes. They also check rejected blank input and selection cleanup after a stage change. Native application review checks readable 380-pixel layout, enabled-state behavior, focus order, and no-stage guidance. Screenshots and a live Kit review are required before describing the visual result as verified.

The visible-only `preview_panel` helper builds a small USD wall, door, and duct fixture, opens a real rendered viewport, places the Issues panel beside it, and captures the application swapchain into `verification/issues-panel.png`. It uses NVIDIA's [renderer capture interface](https://docs.omniverse.nvidia.com/kit/docs/omni.kit.renderer.capture/1.0.2/omni.kit.renderer.capture/omni.kit.renderer.capture.IRendererCapture.html). The runner dispatches this helper only for visible verification; headless behavior tests do not claim visual acceptance. The panel can be docked by the reviewer using Kit's normal window controls.
