# That Open BCF camera research

Reviewed 2026-10-07 against official documentation and `ThatOpen/engine_components` main commit `8479a7c5c6a3c0cf8c7ceab1d1fb329a3f7d1922`. This is source inspection, not an ACC interoperability test.

## Verified That Open behavior

`BCFTopics.load()` reads the ZIP, creates viewpoints before topics, and links them by GUID. Its camera parser maps both position and direction from BCF `(X, Y, Z)` to Three.js `(X, Z, -Y)`. It copies `FieldOfView` or `ViewToWorldScale`, uses `AspectRatio` when present and otherwise 1, but discards the original `CameraUpVector` and stores a zero vector. There is no version-dependent horizontal/vertical FOV conversion in this parser. [BCFTopics source, lines 485–716](https://github.com/ThatOpen/engine_components/blob/8479a7c5c6a3c0cf8c7ceab1d1fb329a3f7d1922/packages/core/src/openbim/BCFTopics/index.ts#L485).

The fragments manager obtains `baseCoordinationMatrix` from the first loaded model. `applyBaseCoordinateSystem()` combines the inverse original coordinate system with that matrix. This is a model-coordinate transform in addition to the camera axis conversion. [FragmentsManager source, lines 100–113 and 345–369](https://github.com/ThatOpen/engine_components/blob/8479a7c5c6a3c0cf8c7ceab1d1fb329a3f7d1922/packages/core/src/fragments/FragmentsManager/index.ts#L100).

`Viewpoint.position` applies the base matrix. `updateCamera()` applies its inverse to the saved position. Direction is read without that transformation. `go()` changes projection and calls `setLookAt(position, position + 80 * direction)`. It does **not** restore imported FOV, aspect ratio, orthographic scale, or camera roll/up vector. Export remaps Three.js vectors to BCF `(x, -z, y)`, copies the FOV scalar, and synthesizes the up vector from direction. Consequently, the implementation demonstrates useful coordinate separation but is not a complete camera-restoration reference. [Viewpoint source, lines 128–165, 353–479 and 765–817](https://github.com/ThatOpen/engine_components/blob/8479a7c5c6a3c0cf8c7ceab1d1fb329a3f7d1922/packages/core/src/core/Viewpoints/src/viewpoint.ts#L128).

## Verified BCF version difference

BCF 2.1 documentation explicitly identifies `FieldOfView` as **horizontal**, specifies lengths in meters and angles in degrees, and has no camera `AspectRatio` field. [BCF 2.1 specification](https://github.com/buildingSMART/BCF-XML/blob/release_2_1/Documentation/README.md#perspectivecamera-optional).

BCF 3.0 explicitly defines FOV and orthographic scale as **vertical** and requires aspect ratio. Its implementation notes acknowledge inconsistent earlier implementations, recommend aspect 1 when converting legacy files lacking it, and require nonzero, nonparallel direction/up vectors. When the destination aspect is narrower, it advises increasing vertical coverage to retain original content. [BCF 3.0 camera specification](https://github.com/buildingSMART/BCF-XML/blob/release_3_0/Documentation/README.md#camera).

For a known horizontal FOV `h` and source aspect `a`, the corresponding vertical angle is `v = 2 * atan(tan(h / 2) / a)`. Use consistent radians internally. The equation follows perspective projection geometry; source aspect inferred from a screenshot is an interoperability heuristic, not a mandatory BCF 2.1 field.

## Implications for issues.tag and ACC

The parent investigation reports that our parser currently treats every FOV as vertical and infers missing aspect from the snapshot. This differs from documented 2.1 semantics when the exporter supplies horizontal FOV. It can explain framing or zoom differences, but cannot move the camera eye. The horizontal/vertical conversion makes no difference for aspect 1 and does not apply to orthographic cameras. Whether ACC follows horizontal 2.1 semantics requires checking a non-square perspective viewpoint against its matching snapshot.

That Open's axis remapping belongs to its Three.js Y-up scene; copying it directly into a Z-up USD stage would introduce a second axis conversion. Preserve the distinction between BCF axes/units and the reference model's original-to-stage transform. Apply translation to the position; apply rotation to direction and up, then normalize and orthogonalize.

For the reported location problem, compare one failing ACC viewpoint's raw position/direction/up with the model's original placement, composed USD transform, stage units, and imported camera pose. Compare the resulting render against the embedded snapshot. Keep origin/placement failures separate from FOV/aspect failures. No ACC-specific offset, coordinate-unit exception, or origin convention was established by the sources above.

An open issue in the specification repository asks which IFC origin a camera references when a topic names several files. It records an unresolved implementer question, not a normative answer. [buildingSMART issue 398](https://github.com/buildingSMART/BCF-XML/issues/398).

## Local sample evidence

Read-only inspection of `~/Downloads/2026-09-30 11_36 106 Issues.bcf` found 108 cameras: 21 perspective and 87 orthographic. Of these, 98 have survey-sized positions near X=579,000 and Y=6,633,000; 10 have both horizontal coordinates below 10,000 in magnitude. Those ranges are observations, not proof that the topics belong to the same model or use different origins. Local-position topics have indices 1, 3, 4, 5, 6, 9, 10, 20 and 21; topic 3 has two camera viewpoints.

`issues_tag/bcf.py:plan_import` computes one reference mapping for the document and applies it to each standard camera. `issues_tag/bcf_coordinates.py:stage_mapping` compares the original source placement with composed placement. It does not choose between model-local and survey coordinates for individual viewpoints. The saved SOL scene regression verifies that this mapping leaves every source camera pose unchanged. Therefore it verifies the existing mapping assumption, not rendered agreement with ACC snapshots. A near-origin viewpoint belonging to the georeferenced SOL building would need its origin convention established separately.

Four perspective snapshots are not square, on topic indices 1, 3, 5 and 612. Horizontal versus vertical FOV interpretation can affect these; it cannot explain a displaced eye. Topic 612 has a 1502 by 891 snapshot. The reader's universal vertical interpretation can be compared with the documented 2.1 horizontal interpretation without changing the scene. This does not establish which interpretation ACC actually used.

Verification command: `& 'C:/kit-app-template/_build/windows-x86_64/release/kit/python/python.exe' tests/test_bcf_compat.py -v`. All 18 checks passed on 2026-10-07, including the local sample import/save/reopen/repeat and saved SOL frame check. No rendered test was run, no user scene was saved, and no product code was changed. The reported wrong camera location has not yet been reproduced against an identified affected topic and matching model.
