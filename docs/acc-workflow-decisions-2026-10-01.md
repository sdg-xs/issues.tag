# ACC workflow execution decisions, 2026-10-01

These are coordinator decisions made while implementing the recovered workflow. The recovered plan is a reconstruction, not the original closed /btw transcript. The private SDK was read-only; lead-owned rendered results are recorded in acc-workflow-verification-2026-10-01.md.

The late MainWindow experiment was superseded by the canonical startup dependency. The historical GPU crash remains outside the verified scope.

## Decision record

- Ruling: Parallelize Tasks 1 and 2 with disjoint file ownership — user explicitly requested parallel independent workers and plan permits these tasks in parallel — coordination cost if contracts need revision.
- Ruling: Lead serializes scoped commits for both workers — a shared worktree Git index must have one writer — slight delay before review packages, no lost index edits.
- Ruling: Workers recover from the verified archive, not the mutable original scratch directory — preserve exact recovered state — newer scratch work would need a separate audit.
- Ruling: Invoke existing isolated SDK/Python dependencies explicitly — no new GPU tests or vendor edits by workers — tests might need portable fixture path repair by lead.
- Ruling: Retain recovered IssueEditSession.record/viewpoint/comment_text names — avoid conflicting aliases between parallel workers — low cost if additional UI helpers later needed.
- Ruling: Add IssuesWindow.clear_filters() and visible_issue_ids — controller can reveal a newly saved record excluded by filters — resets filters only after explicit new-record Save.
- Ruling: on_error retains dispatcher contract on_error(callback,*args) — controller must own asynchronous UI callback tasks — no separate exception-only alias.
- Ruling: Task3 owns migration of older combined-window callers/tests — new split cannot retain old UI-only submit methods solely for tests — broader test migration required, runtime stays lead-owned.
- Ruling: Busy capture keeps Cancel/native-close available — user must be able to leave pending capture — controller drains owned native task before deleting evidence.
- Ruling: Add list.set_placement_state(active,on_cancel) without changing constructor — split UI must retain baseline cancel before details opens — one extra view-state helper.
- Ruling: Fix accepted migration performance issue before integration — avoid repeated full-project rewrites in normal schema2 editing — requires once-only migration/unchanged-record regression, not a cache layer.
- Ruling: Extend Task3 exclusive ownership to window/session/service plus their relevant tests while prior workers remain frozen — restore baseline user workflows with atomic staged Save rather than directservice test bypass — larger integration fix requires scoped review.
- Ruling: Extend frozen text-only pendingcomment contract to staged comment evidence and saved comment edits — baseline SPEC retained annotated comment workflow — cross-task session/UI changes are necessary and must preserve original evidence on Discard.
- Ruling: Separate thin manager-owned IssuesExtension from plain IssuesController runtime ownership — actualKit clears IExt__dict__ onshutdownbefore asyncdrainfinishes — smallcaller migration and independent lifecycle review required; persistent state cannot live in wrapper.
- Ruling: Use exactSDK ui.MainWindow/DockSpace fixture to establishreal native docklayout and deferMarkupactivation toadapter — minimaltestappfloatingViewport +eagertoolcanvas occludedactualsurfaceclick — fixtureownsMainWindowlifetime; actualdocking/inputstillmustpassruntime.
- Ruling: Freshruntimefixtureowner alsoowns exclusivewindow.py/test_acc_ui.py for nativefirst-updatepaneldocking — actualcanonicalViewportdocksbutnewpanelimmediateconstructorrequestignored, strictUIDoublemustmodelboundary — minimalsharedsubscriptionsmustpreservecapturetemporaryhide and destroycleanup; nativebothpanelsstillrequireacceptance.
- Ruling: Restore user author configuration before acceptance — prior supported UI and baseline SPEC require attribution setup — one retained list control plus focused tests, no permission/assignment expansion.
- Ruling: Run independent whole-branch source review against frozen820fb8e while lead completes remaining native acceptance — user requested parallel independent work, all implementation/taskreviews clean, reviewer never drivesGPU — acceptance/deployment remain gated on both, any later sourcefix requires scoped review.
- Ruling: Accept reviewer declined-scope items as explicit recovery boundaries — creation remains pin-first, preview replaces separate snapshot popout, externalBCF/scale/GPUqualification and deferredpermissions/sync stay unclaimed — omittedlegacyextraactions may need later UX work; no impact on required savedviewrecall or author/comment preservation.
- Ruling: Compare complete serialized values across actual extension reload — model class identity changes on SDK teardown/reimport even when all persisted bytes are equal — test must retain all fields/PNG/native-subtree, pendingdrain, ownedcleanup checks; reduced structural comparison would miss real data loss.
- Ruling: Replace the earlier late MainWindow fixture with the installed SDK canonical omni.kit.mainwindow startup dependency — ordinary control docked while Viewport startup delegation defeated late manual ownership — no shared SDK or production settings changes; wrong test setup would require renewed native layout qualification.
- Ruling: Bound fixture Arrow coordinates to native drag domain 0..100 percent before another parent run — installed renderer uses ui.Percent and native handlers clamp coordinates, priorend_x110/130 inflatedtoolwidth836/1793 whileviewport613 — corrected run retains diagnostics/pixel/spec checks; if inflation has another cause boundedrun will still expose it, no production fix assumed.
