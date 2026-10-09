# D12 — I4 Closure Decision Record

**Gate:** I4 closure — M2 execution + R6 replay / E2E determinism qualification.
**Recorded:** 2026-10-09.
**Decision authority:** Ramki (explicit D12 directive, 2026-10-09: "D12 — I4 CLOSURE / DURABILITY PUBLICATION").
**Parent records:** D08 (MD-11 / MD-13 / MD-15 patterns), D11 (replay-qualification corrections K1/K2/K3 + G6; R0–R7; E1–E10), I4 Replay/E2E determinism investigation (pre-correction findings), D11 remote reconciliation (2026-10-09, read-only: **ACCEPT**).
**Style precedent:** D08 §14/§15/§19.

---

## 1. Decision

> **DECISION.** Upon successful completion of the remote verification in §9, ratify:
>
> ### **I4 = CLOSED / DURABLE / REMOTELY VERIFIED**
>
> I4 closure is **not** claimed before remote verification succeeds. If verification fails, I4
> remains **NOT CLOSED**, and the failure is recorded rather than worked around (D08 §15 pattern).

## 2. Authority and basis

1. The decision authority issued the explicit D12 directive to "proceed with the I4 closure work
   identified by the completed D11 remote reconciliation", identifying this execution as
   "the publication step identified by the completed D11 reconciliation".
2. The D11 remote reconciliation (read-only, 2026-10-09) returned **ACCEPT**: publication verified
   (commit, directory, package SHA256, blob identity), E1–E10 reconciled, R6 verdict independently
   re-proven (three-source digest cross-checks + physical free-disk corroboration), findings C.1–C.7
   recorded, determination: "The Windows R6 PASS is sufficiently evidenced and durably published for
   Arena to accept the I4 replay/E2E determinism qualification."
3. This record cites **only** evidence actually established by D11 and the M2 execution record.
   It introduces no new measurements, no new corpus access, no Windows execution, no replay re-run,
   and no engine/runner implementation change.

## 3. What I4 was, and what was done

* **I4** (D08 §13, MD-13): "the **non-production** 10-year historical corpus replay / full historical
  run under the approved I3 contract", with the content-level traceability boundary (D08 §4.3) and
  the MD-11 retained-output requirements.
* **Executed** on Windows as run `i4-20261008-M2` (M2): 2,462 members; 5,689,949 rows; 12 partitions;
  0 quarantined; **0 gating divergences** (39,402 reconciliation records); `verify --package` PASS
  (verify-01…verify-07); package = **4,948 files, 21,119,807,344 bytes**; `PACKAGE_MANIFEST.sha256`
  digest `e7c7e4c8271f3a1c8ef42d76b926fe048a8997a342c92d89819eecd79e73b9dc`; engine fingerprint
  `d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9` (17 declared modules); runner
  fingerprint `f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a` (6 declared
  modules); corpus archive-set digest `54d8150706ccf5d813a6f0af668e8230e147a7e370db20ea15dda1b72bf8b100`;
  composite run identity `9609c7fccef1d2438810a564ef70aa8232d8ad1c69fded8702e488c13657802d`;
  peak RSS 318.1 MB ≤ 6,144 MB declared limit and ≤ the unchanged 2.5 GB M1 criterion.

## 4. R6 replay qualification (D11 gate) — established facts

* A = completed M2 package (root `i4-20261008-M2`); B = **fresh** replay (root
  `i4-20261008-M2-REPLAY`, **same run id** `i4-20261008-M2` per RD-10), produced under the memory
  monitor with the pinned thresholds.
* Two distinct fresh executions (K3): monitor traces with distinct PIDs and windows — A: pid 18664,
  2026-10-08 16:43:52 → 17:29:10 IST, 537 samples, peak 318.1 MB, exit code `null` (documented
  anomaly); B: pid 8904, 2026-10-09 01:33:41 → 02:21:47 IST, 564 samples, peak 318.8 MB, exit code
  `0`. Each execution wrote the full 21,119,807,344-byte package, independently corroborated by
  free-disk physics in the unedited traces (78.84 GB → 57.70 GB; B starting at 57.70 GB — A's
  package preserved on disk — then 57.70 GB → 36.56 GB).
* **R6 verdict** (`D11_R6_REPLAY_QUALIFICATION_VERDICT.json`, sha256
  `d8e33f13cef1d023ed09f3bd47abdd36adcfe3b0be78284f1b9224ac71ab8027`): `result: "pass"`,
  `failures: []`, `comparison_permitted: true`; **RQ-01…RQ-13 all pass**; the byte comparison was
  executed **only after** all gating preconditions held (K1); total byte-exact comparison
  4,948 == 4,948 files, `first_difference: null`, no exclusion list, no normalisation.
* **K1 — addressed:** both packages pass `verify_package`; both completion markers bound to their
  manifest (`e7c7e4c8…`) and run id (RQ-01/02/08); the comparison is never reached without them
  (RQ-13 gating).
* **K2 — addressed:** one declared revision / run id / corpus identity enforced from the **executed
  bytes** (RQ-03/04/05/06/07); the verdict's `revision` block carries the full K2 record
  (repository, ref `arena/9021d1a1-nse-historical-data-engine`, commit `8ade8372…`, tree
  `8e1557de…`, both fingerprints, run id, corpus digest).
* **K3 — addressed:** per-run package-bound evidence bundles (Phase-I facts + monitor summary +
  monitor trace + package listing), cross-consistent and digest-bound (RQ-09/10/11); a byte copy of
  A cannot satisfy the bundle; distinctness proven (pid / window / peak / sample count / exit code).
* **G6 — addressed:** the verdict document is path-free, clock-free and host-free.
* **R0–R7 — all evidenced:** R0 gate transfer (verdict schema `i4-replay-qualification/1.0`);
  R1 executed bytes = pinned fingerprints; R2 A verify pass + manifest pin; R3 B under the pinned-
  threshold monitor; R4 B verify pass; R5 Phase-I evidence for both runs; R6 gate exit-0 PASS;
  R7 transfer manifest (E9: 12/12 listed file hashes re-verified) + durable publication at
  `1507b740…`.

## 5. Durable evidence (on `origin/main` since commit `1507b740…`)

| Item | Value |
|---|---|
| Publication commit | `1507b74004c84d716b9f2752a13aa232dd7bf99d` ("docs: publish D11 replay qualification evidence", 2026-10-09T07:42:08Z; parent `6a60583f…`; exactly +2 files) |
| Evidence directory | `evidence/D11_REPLAY_QUALIFICATION_20261009/` |
| Package | `D11_E1_E10_TRANSFER_20261009.tar.gz` — sha256 `8e78fcc8b39b9ed7344f3bb6348ef2036e2f50b325141b7108f01967687e8f6f` (recomputed from the downloaded bytes; git blob `428a9767…`) |
| Publication note | `D11_EVIDENCE_PUBLICATION.md` — sha256 `539d2fffd8f6a4211f00fc865165c1fd26f1ccd03fe5d8c42aa13912cf4810f0` |
| E1–E10 | All satisfied per the reconciliation (E2 embedded in RQ-01/02; E7/E8 single-copy per §6.2; E10 not applicable — no failed precondition) |

## 6. Findings carried forward **without suppression** (D11 reconciliation C.7)

1. **Recorded `repo_head` differs from the declared executed revision.** The Phase-I facts record
   `repo_head 6a60583f…` / `repo_tree ad882bec…` (the Windows worktree's git HEAD was `main`, with
   the M2 payload applied over worktree files; `repo_status_entries: 65`), while the declared
   executed revision is `8ade8372…` / `8e1557de…`. The verdict records this transparently
   (RQ-12, `recorded_head_must_equal_revision: false`; A == B held). Revision identity is enforced
   from the **executed bytes** (RQ-04/05 = the pinned fingerprints; the 29-file M2 payload was
   established in D11 to be byte-identical to `8ade8372…`'s blobs). Not suppressed; not a finding
   against the execution, and not reinterpreted.
2. **E7/E8 are single-copy** because A/B **whole-tree byte identity is proven** (RQ-13,
   `first_difference: null`, 4,948 == 4,948): one `PACKAGE_MANIFEST.sha256` / `RUN_COMPLETE.json` /
   `RUN_RECORD.json` represents both packages, and both per-run facts bind to the identical digests
   (marker `cfca01f2…`, run record `ad457d41…`, manifest `e7c7e4c8…`).
3. **The publication note's "Replay run: `i4-20261008-M2-REPLAY`" is B's output-root label, not the
   run id** — the run id is `i4-20261008-M2` in both packages (RQ-03).
4. **A's Phase-I facts were re-captured during R5** (2026-10-09, 10:10 IST) against the intact A
   root (Phase-I is re-runnable by design); A's monitor transcript is from the original 2026-10-08
   execution, as it must be.
5. **A's runner exit-code `null` anomaly is preserved verbatim**, never reinterpreted (B: `0`).
6. **Residual operator-attestation boundary:** a fabricated evidence bundle cannot be
   cryptographically excluded by this gate; the attestation layer is the operator attestation plus
   the unedited, hash-verified, now-durable monitor transcripts. Carried forward, unchanged.

## 7. MD-11 satisfaction (D08 §12 — the 11 retained-evidence items)

| # | MD-11 item | Satisfied by |
|---|---|---|
| 1 | input identity | `RUN_RECORD.json` (E8: authority/boundary/composite identity) + `GOVERNED_INPUTS.json` (covered by the 4,948-row listing + manifest digests) |
| 2 | input hashes | `INPUT_MANIFEST.jsonl` + `GOVERNED_INPUTS.json` digests in the listing/manifest; corpus archive-set digest `54d81507…` and inventory-LF pin `336b9531…` in both facts |
| 3 | output identity | package structure + `RUN_RECORD.json` counts/verification block |
| 4 | output hashes | `PACKAGE_MANIFEST.sha256` (`e7c7e4c8…`) + full 4,948-row `PACKAGE_FILES.tsv` listing (per-file sha256) |
| 5 | tool identity / version / hash | engine `d3269b73…` (17 modules, modules digest `3a3bfebb…`) / runner `f3ebf624…` recorded inside the packages; verdict `revision` block |
| 6 | run identity | run id `i4-20261008-M2` + composite identity `9609c7fc…` |
| 7 | **deterministic replay evidence** | **R6 verdict (byte-exact, 4,948 == 4,948, `first_difference: null`) + per-run execution bundles (E3/E4/E5)** — the item that kept I4 open |
| 8 | validation / reconciliation results | RQ-01/02 (`verify_package` pass both packages) + `RUN_COMPLETE.json` reconciliation (0 gating divergences, 39,402 records) |
| 9 | unresolved-state evidence | `w2/unresolved.jsonl` + reconciliation `by_result`/`by_tier` census (carried, never resolved) |
| 10 | manifest information | `PACKAGE_MANIFEST.sha256` + 12 partition manifests (hashes in both facts) with declared hash bases |
| 11 | approved content-level traceability boundary | `RUN_RECORD.json` authority block + D08 §4.3 (on `origin/main`) |

## 8. Publication scope (this commit)

This publication is **one commit** (a merge, parents `edbda829d43ce0b31133ad59b81ae6f65d7b16f8`
(session-branch tip) and `1507b74004c84d716b9f2752a13aa232dd7bf99d` (`origin/main` tip)), carrying
exactly:

1. **This record:** `docs/investigations/D12_I4_CLOSURE_DECISION.md`.
2. **README status-block update:** I4 M2 execution complete; R6 replay qualification PASS;
   I4 CLOSED (conditional on §9 verification); plus the D12 record bullet.
3. **D11/I4 qualification artifacts made durable** (from the current working tree; previously on no
   ref): `docs/investigations/D11_REPLAY_QUALIFICATION_CORRECTION.md`;
   `docs/investigations/I4_REPLAY_E2E_DETERMINISM_INVESTIGATION.md`;
   `tools/i4_m2/i4_replay_qualification.py` (the D11 gate, stdlib only);
   `tests/test_i4_replay_qualification.py` (45 tests); **G6-corrected** `tests/test_i4_runner.py`
   (whole-file Windows-path detection + `PathDetectionRegressionTests`).
4. **Session-branch content carried by the merge** (already durable on
   `arena/9021d1a1-nse-historical-data-engine` at `edbda829…`; absent from `main`):
   `docs/investigations/D09_BOUNDED_MEMORY_ENGINE_STATE.md`;
   `docs/investigations/D10_M2_SELFTEST_JSON_CAPTURE_CORRECTION.md`;
   `src/nse_engine/compact.py`; `src/nse_engine/w2_stream.py`;
   `tests/test_compact_containers.py`; `tests/test_i4_m2_monitor_launch.py`;
   `tests/test_i4_m2_selftest_json_capture.py`; `tests/test_w2_stream_equivalence.py`;
   `tests/test_w2_stream_memory.py`; `tools/i4_m2/I4_M2_MEMORY_MONITOR.ps1` (blob `e6272c3a…`);
   `tools/i4_m2/I4_M2_TEST_LAUNCH_QUOTING.ps1` (blob `01f9d13f…`);
   `tools/i4_m2/README_I4_M2_MONITOR_FIX.md`.
5. **Engine/runner alignment — not an implementation change.** `main`'s engine predated the
   executed M2 revision: it lacked `compact.py` / `w2_stream.py` (15 of 17 declared modules) and
   carried 5 engine modules + 2 runner files differing from the executed bytes. This publication
   carries the **executed-revision bytes**: all 7 files byte-identical to the published
   session-branch blobs (`edbda829…`), and recomputed from the final tree they reproduce exactly
   the pins recorded in the M2/R6 evidence — engine `d3269b73…` (17 modules), runner
   `f3ebf624…` (6 modules). `tools/i4_runner/i4_output.py` is **unchanged** (blob `0a8b60f7…`); no
   engine or runner implementation was modified by this publication.
6. **Carried from `main` unchanged:** everything else, including the cited D11 evidence
   (`evidence/D11_REPLAY_QUALIFICATION_20261009/`, 2 files) and the D02–D08 records.

**Explicitly excluded:** `_transfer_delivery/` (working transfer staging — never committed); no
I5 artifact (I5 has no definition in the repository — §10); no unrelated path.

**Publication path:** the commit is published on `refs/heads/arena/9021d1a1-nse-historical-data-engine`
(session constraint of this execution environment: commits/pushes are bound to the session branch),
then advanced onto `origin/main` by the decision authority's fast-forward push — the established
publication pattern of this repository (`4e044acc`, `6a60583f`, `1507b740` are authority-pushed
`main` commits). The §9 verification is bound to the **commit object** (tree hash), not to the ref:
the `main` fast-forward carries the identical tree.

## 9. Remote verification protocol (read-only; D08 §14 pattern)

All checks are read-only GitHub/API inspections of the published commit:

1. the commit exists on the publication ref (session branch at publication; `origin/main` after the
   authority's fast-forward);
2. the closure record exists at `docs/investigations/D12_I4_CLOSURE_DECISION.md` with the ratification
   line (§1) and the §5 citations (commit `1507b740…`, package sha256 `8e78fcc8…`, R6 verdict sha256
   `d8e33f13…`) and the §6 findings;
3. the README status block carries the I4 entry (execution complete / R6 PASS / CLOSED) and the D12
   record bullet;
4. the cited D11 evidence remains present: both files of `evidence/D11_REPLAY_QUALIFICATION_20261009/`
   with blob shas `428a9767…` / `03d5cbed…`, and the package sha256 `8e78fcc8…`;
5. all intended Task-22 artifacts are present (D11 record, I4 replay/E2E record, gate + 45-test
   module, G6-corrected runner tests) with the expected blob shas;
6. engine/runner integrity: `tools/i4_runner/i4_output.py` blob `0a8b60f7…` unchanged; the declared
   engine (17) and runner (6) module blobs reproduce `d3269b73…` / `f3ebf624…`;
7. no unrelated paths entered the publication commit: the tree delta vs `1507b740…` is exactly the
   26 paths documented in §8 (5 new closure files + 12 session-branch files + 7 aligned
   engine/runner files + G6 test + README).

**Failure semantics:** if any check fails, I4 remains **NOT CLOSED**; the failure is recorded, not
worked around; no corpus or replay re-run is implied by a failure.

## 10. Carried forward (unchanged by this record)

* **I5 has no authoritative definition, runbook, or gate in the repository** (prior discovery,
  unchanged). This record **creates no I5 definition and infers none**; it does not reference I5 as
  a stage. The only documented forward pointer remains D08 §16's "future M/N gate" (serving /
  consumer-result contracts, deferred by sequencing).
* `STORAGE TECHNOLOGY = UNDECIDED` (MD-12 withheld); MD-08/MD-09 deferred by sequencing; MD-16
  (DEC-1) deferred unchanged; MD-17 out of scope.
* D07 §9's nine unresolved canonical semantics remain OPEN; W1-DIV-1 preserved; the three
  unexplained calendar dates remain `null` / `unexplained-by-obtained-circulars`.
* The documented, non-gating monitor `null` exit-code anomaly is carried unchanged (§6.5).
* The failed run `i4-20261007` and the M2/replay roots on Windows remain untouched evidence.

## 11. Final disposition

**D12 = RECORDED.** Upon successful §9 remote verification:

> ### **I4 = CLOSED / DURABLE / REMOTELY VERIFIED**

I4 closure (this ratification) is claimed **only after** that verification passes; the verifying
commit SHA and tree hash are reported in the publication report for this gate (D08 §14 pattern).
I5 is not started, defined, or inferred by this record.
