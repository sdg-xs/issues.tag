# Orbit after BCF issue focus

Kit110.2 disables tumble/look for orthographic cameras unless omni:kit:orthoRotate is true. Unlocking omni:kit:cameraLock alone does not enable rotation. Standard BCF orthographic viewpoints take the portable ViewportAdapter.restore path, which previously left orthoRotate absent or inherited as false.

The recall path now enables this attribute on the active review camera inside its existing session-layer edit context. Projection, imported camera data, snapshots and model layers are retained. A camera shared by another viewport still receives the existing dedicated review-camera fallback.

Two new offline regressions failed before the fix (false/missing rotation flag). After the one-line fix, all6 review-camera tests pass. They cover session-only overrides and shared-viewport isolation. Existing recall tests10 pass using the installed USD libraries.

Native acceptance: verification/bcf-orbit/run-05,1PASS0FAIL, natural runner exit0, zero Error lines in full kit.log. The fixture reads/imports a synthetic orthographic BCF2.1 archive and opens the stored issue. The real SDK controller first disables tumble with the flag false, then enables it after recall and applies a real camera rotation. Emulated Alt-left-drag rotates a perspective baseline and the imported orthographic camera; projection and stored viewpoint remain unchanged.

Command: run-verify-kit.ps1 -Case bcf_orbit -DependencyRoot C:/Users/StevenGomba/.codex/worktrees/issues-tag-improvements/verification-dependencies -Visible

Only the owned verification instance received simulated input; the user's running Composer application was neither operated nor closed. Source files stayed frozen during each native run. Runtime: Kit110.2.0, Python3.12.13, USD0.25.11.

Earlier artifacts are retained: run01 UI extension imported before activation; run02 synthetic archive lacked required creation metadata; run03 modifier emulation omitted the SDK's delay and did not rotate; run04 native controller and baseline-input diagnostics passed; run05 asserts actual imported-camera Alt-drag rotation. No earlier run is presented as final acceptance.

This fixes the reproduced orthographic orbit gate. The reported live issue's projection and pan/zoom behavior have not yet been supplied, so another failure mode is not ruled out. The live checkout remains unchanged; use the updated development branch to load this fix.

Focused independent review: no Critical, Important or Minor findings. The reviewer confirmed the exact SDK gate, session-layer scope, primary/shared-camera regressions and run05 completedPASS evidence. Limits: the live issue's projection is unknown; other SDK versions and independent test reruns were not verified.
