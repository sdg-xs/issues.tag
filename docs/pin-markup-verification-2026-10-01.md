# Pin creation and Markup verification

The lead tested the isolated extension with private SDK copies after the user closed Composer. The combined changes received an independent review. Two draft cleanup findings were fixed and the reviewer cleared both corrections.

The new workflow places a surface pin, opens native Markup and the description editor, then saves the issue and annotated screenshot with Save & close. Saved native views use Markup's recall API. Ordinary primary-view issues and BCF views reuse the existing perspective camera in the session layer.

## Results

- 52 focused offline checks passed across issue creation, editor controls, camera reuse, recall routing, lifecycle teardown, draft ownership, and capture cancellation.
- The rendered creation case passed both Save and Cancel workflows. It used a real native mouse click on a rendered cube. Save preserved the description and PNG through parent USD export/reopen and BCF file export/read. Cancel left neither an issue nor a native draft.
- All four rendered native recall checks passed, including subsequent real mouse navigation and shared-camera isolation.
- A final creation run with an illuminated model passed. The lead inspected the exported BCF screenshot: it contains the model and red annotation, without the description editor.
- Python compilation and diff whitespace checks passed.

The first creation run timed out because the floating Issues panel covered the simulated surface click. The test now hides that panel during placement, refocuses the viewport, waits for a delivered frame, and verifies the center surface raycast before issuing native input.

## Limits

These narrow runs completed without a GPU crash. They do not establish a fix for the earlier intermittent GPU crash after scene replacement. No broad crash reproduction was run.

Capture cleanup waits for native settling and viewport delivery. A timeout before that gate preserves in-flight native evidence because the SDK exposes no safe cancellation fence. Saved evidence and externally selected Markup remain protected from draft deletion.
