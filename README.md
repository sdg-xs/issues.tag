# Issues for Omniverse

Native scene review built from [SPEC.md](SPEC.md): descriptions, four statuses, attributed comments, surface pins, saved views, editable Markup evidence, and BCF 3.0 file exchange.

## Install and use

Add the parent `shared/exts` directory to the Kit extension search paths, enable `issues.tag`, then open **Window → Issues**. This build targets the locally installed Kit 110.2.0, Python 3.12.13, and OpenUSD 0.25.11. Markup Core 1.3.1 and Markup Tool 1.2.82 are enabled when evidence is captured. Their installed manifests target 107.3; integration is checked in the local 110.2 runtime.

Open your parent USD scene containing referenced building models. Set your author name. Enter a description and choose **Place pin**, then click a visible model surface. You can also create a record without a pin. Select an issue to restore its original review view; **Focus related** frames its related elements separately. Add selected geometry to the related list without moving the pin. Reattach explicitly when geometry changes or an identity no longer resolves.

Use **Capture comment view**, then **Annotate** to draw with NVIDIA's Markup tools. Apply or cancel the annotation before adding the comment. The original issue view remains separate. Imported snapshots can be retained without editable Markup geometry.

Use ordinary **scene Save** to persist changes. Issue records and embedded PNGs live in the parent root layer under `/Issues`; editable evidence lives under `/Viewport_Markups`. Review camera and visibility opinions use the session layer. Building reference layers remain untouched by issue mutations. Save a writable copy if the parent is read-only. Undo affects issue records without undoing unrelated model edits.

## BCF exchange

**Import BCF** previews changes before applying them. Choose Keep local or Use imported for conflicting descriptions and statuses. Reimporting unchanged topics, comments, and views preserves their identities. **Export BCF** writes the supported BCF 3.0 subset and annotated snapshots. See [the file profile](docs/bcf-profile.md) for mappings and limits.

BCF imports retain unresolved component references and evidence; they do not invent surface pins. External partner interoperability is still pending selection and an actual exchange test. Internal round trips and official XML schema validation are separate verification outcomes.

## Verification

The runner launches a separate Kit process with temporary scenes. It does not operate on your open project. Install the schema-validation dependency into the ignored verification directory once:

```powershell
& C:/kit-app-template/_build/windows-x86_64/release/kit/python/python.exe -m pip install --target verification/python lxml==6.1.3
./run-verify-kit.ps1 -Case all -Visible
```

Use `-KitRoot` for another SDK location. Individual cases are `runtime`, `persistence`, `ui`, `anchors`, `viewpoints`, `markup`, `section_box`, `bcf`, and `workflow`. The complete integration suite expects the installed `section.box` 1.1.0 extension in the shared parent folder. Markup and screenshot verification require a visible window. The runner returns nonzero on failure and writes `verification/results.json`, logs, generated USD/BCF files, and PNG evidence. Run only one verification process at a time.

## Current boundaries

One editor at a time; configurable author names are attribution, not authentication. Assignment, permission policies, concurrent editing, ACC synchronization, and BCF server exchange remain deferred.

Synthetic fixtures verify IFC GlobalId and Revit UniqueId matching within each referenced model instance. Production metadata still needs a representative building and revision. Path-only attachments provide same-scene identity; unverified HOOPS asset GUIDs are not treated as unique element IDs. Changed local geometry, missing IDs, and ambiguous matches require review or reattachment. No model-size or performance guarantee has been measured.

Markup capture and annotation require the visible primary `Viewport` window. The adapter rejects secondary viewport requests before creating evidence. Ordinary saved review cameras remain scoped to their viewport. Live Section Box tests verify restored controls, clipping toggles, and active viewport ownership. See [the verification record](docs/verification-report.md) for complete test results and open gates, and [Markup lifecycle](docs/markup-lifecycle.md) for cancellation and edit-target behavior.
