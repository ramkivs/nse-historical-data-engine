# D11 — I4 replay qualification corrections (K1/K2/K3 + G6)

**Gate:** `I4 → replay / E2E determinism qualification → I5`
**Scope:** Arena/Linux correction. **No Windows execution, no PowerShell execution, no access to
`G:\` or `C:\IIPS_Data`, and the 2,462-member corpus was not executed.** Every test runs on
synthetic fixtures in a temporary directory.
**Supersedes the open items of:** `docs/investigations/I4_REPLAY_E2E_DETERMINISM_INVESTIGATION.md`
(that record remains the investigation of the replay mechanism and its Class 1/2/3 boundary; the
qualification-contract corrections it demanded are applied here).

---

## 1. Inputs (determination carried into this correction)

| Item | Determination |
| --- | --- |
| Replay **mechanism** (`i4_output.replay_compare`) | **Sound and unchanged.** Total file-by-file comparison, no exclusion list, no normalisation, distinct directories required, verdict outside both packages, decision independent of the truncated forensic lists. |
| Replay **qualification contract** | **Insufficient** before this record: K1 (no completeness precondition), K2 (no revision pin), K3 (execution evidence not required) |
| Test defect | G6: the retained-package path scan missed a Windows absolute path anywhere except the start of the file |
| M2 baseline (operator facts) | run id `i4-20261008-M2`; 2,462 members; 5,689,949 rows; 0 quarantined; 12 partitions; 39,402 reconciliation records; 0 gating divergences; verify PASS; evidence PASS; peak RSS 318.1 MB; engine `d3269b73…`; runner `f3ebf624…`; package manifest `e7c7e4c8…` |
| Second full replay for closure | **still required** (D08 MD-11 #7). Nothing in this record reduces that requirement; it makes the replay qualifiable. |

### 1.1 Exact repository revision of the M2 run (K2, determined from the repository itself)

The M2 run executed the payload of the M2 transfer package. Verified in Arena:

| Check | Result |
| --- | --- |
| `I4_M2_WINDOWS_MANIFEST.tsv` payload files whose bytes equal the blob at `8ade8372…` | **29 / 29** |
| Engine fingerprint recomputed from `8ade8372…`'s module blobs | `d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9` = **M2 evidence** |
| Runner fingerprint recomputed from `8ade8372…`'s module blobs | `f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a` = **M2 evidence** |
| Same recomputation at the delivery branch tip `edbda829…` | identical engine and runner fingerprints (the module bytes are unchanged) |
| `origin/main` `6a60583f…` | **not** the run revision: 15 engine modules (no `compact.py`, no `w2_stream.py`), fingerprints `7bee8490…` / `618bfd4c…` |

**Authoritative revision for the M2 replay:**

| Field | Value |
| --- | --- |
| repository | `ramkivs/nse-historical-data-engine` |
| ref | `refs/heads/arena/9021d1a1-nse-historical-data-engine` (remote `origin`; published) |
| revision / commit | `8ade8372e150e541a52206baa377a02249a308f4` |
| tree | `8e1557de766d4c952be7261c4f72aa743f81de0b` |
| delivery branch tip (superset, same module bytes) | `edbda829d43ce0b31133ad59b81ae6f65d7b16f8`, tree `c1c549301a304208ea4361ff3c6f3fb3c22989c9` |
| engine fingerprint | `d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9` |
| runner fingerprint | `f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a` |
| excluded revision | `origin/main` `6a60583f62905c1fbda9cc7529019e2a9ed0b097` (tree `ad882becd89992e3c62a2bdff00a78bc6d80dbc0`) — pre-bounded-memory, cannot reproduce the M2 package |

Lineage of the delivery branch (each commit reachable from the tip):
`c280c0d7…` → `8ade8372e150e541a52206baa377a02249a308f4` → `818c128c82f102324f28d5abbe3c058f7ef88f9e`
→ `43f233bc6b0eaf42c98294325b84b2f6eee323cc` → `edbda829d43ce0b31133ad59b81ae6f65d7b16f8`.

---

## 2. K1 — completeness precondition

**Finding.** `replay_compare` has no completeness precondition: two identical directories that
contain nothing but `notes.txt` return `pass`, and two identical **incomplete** packages (marker
removed on both sides) also return `pass` while `verify` returns `fail` (`verify-04`). A replay
PASS was therefore reachable without either side being a complete, verified package.

**Correction (qualification layer; no mechanism change).** `tools/i4_m2/i4_replay_qualification.py`
refuses to invoke the comparison unless both packages pass the existing package verification and
both markers are bound to their own manifest and run id:

* `RQ-01` / `RQ-02` — `i4_output.verify_package(A)` and `(B)` must return `pass` (all of
  `verify-01`…`verify-07`); a verifier exception is caught and fails closed.
* `RQ-08` — `RUN_COMPLETE.json` present in both, `package_manifest_sha256` equal to the manifest's
  own digest on disk, and the marker's `run_id` equal to the package's run id.
* `RQ-13` — the byte comparison runs **only** when every gating precondition holds. Otherwise the
  report records `"comparison": null`, `comparison_permitted: false` and `RQ-13: not-run`, so a
  contract failure can never be mistaken for a byte result.

`i4_output.py` is untouched: the comparison keeps its total, exclusion-free semantics, and the
existing `verify`/`replay` commands behave exactly as before.

## 3. K2 — exact revision pin

**Finding.** The delivered runbook's replay phase was optional and named no revision. `main`
(`6a60583f…`, engine `7bee8490…`, runner `618bfd4c…`) is a *different* revision from the one that
produced the M2 package (`8ade8372…`, engine `d3269b73…`, runner `f3ebf624…`), so a replay started
from the current default branch could not reproduce the baseline and would fail — or, worse, would
be pointed at a stale pin.

**Correction.** The qualification record captures, and the gate enforces from the **bytes that
actually ran** (recorded inside each package), one shared identity for both executions:

* `RQ-03` — one declared run id: A == B == `--expect-run-id` (the single declared run-metadata field).
* `RQ-04` / `RQ-05` — one engine revision and one runner revision: A == B == expectation, read from
  `engine_identity.tool_sha256` / `runner_identity.runner_sha256` recorded in each package's
  `RUN_RECORD.json` (plus `verify-07` inside `RQ-01`/`RQ-02`, which recomputes them from the host's
  modules). The pre-M1 `main` fingerprints fail closed here.
* `RQ-06` — one corpus identity: `corpus.archive_set_digest`, A == B == expectation.
* `RQ-07` — one composite run identity (engine + runner + governed inputs + corpus + run id).
* `RQ-12` — the recorded host checkout (`repo_head`/`repo_tree` from the evidence facts) must be
  present and identical for A and B; with `--strict-recorded-head` it must equal
  `--expect-commit`/`--expect-tree`. Non-strict is the default because the Windows run applied the
  payload onto a checkout that may legitimately sit on a different base commit — the executed bytes,
  and therefore the revision, are pinned by `RQ-04`/`RQ-05`, not by the checkout metadata. That
  deviation is *recorded*, never silently accepted.
* The report additionally records `repository`, `authoritative_ref`, `revision_commit`,
  `revision_tree`, run id, corpus digest, the observed fingerprints, the engine module count and a
  digest of the recorded engine-module fact list — the qualification record required by K2.

## 4. K3 — genuine independent replay

**Finding.** Byte identity is not proof of execution: a byte copy of package A passes the
comparison, and nothing in the contract required evidence that package B came from a second run.

**Correction.** Each package must be accompanied by its **own execution-evidence bundle**, and the
gate refuses to compare without it. The bundle is exactly what the delivered tooling already
produces (Phase-I evidence script and the memory monitor), so no new Windows tooling is implied:

| Document | Producer | Enforced bindings |
| --- | --- | --- |
| `<run-id>.EVIDENCE_FACTS.json` | `I4_M2_EVIDENCE_WINDOWS.ps1` (Phase I) | `result == "PASS"`, `problems == []`, run id, `out_root` basename == package directory, `repo_head`/`repo_tree` present, engine+runner fingerprints, completion-marker digest, run-record digest, package-manifest digest, reconciliation digest, member/row/observation/quarantine counts, composite identity, archive-set digest, `package_file_count`, `package_total_bytes`, monitor summary path recorded |
| `<prefix>.summary.json` | `I4_M2_MEMORY_MONITOR.ps1` (Phase E) | run id, `out_root` basename, `completion_marker_present == true`, `breach == false`, `runner_exit_code ∈ {0, null}` (see below), peak RSS equal to the facts' peak and to the trace's peak, declared limit equal to the facts' limit |
| `<prefix>.jsonl` (monitor trace) | `I4_M2_MEMORY_MONITOR.ps1` (Phase E) | ≥ 2 samples, `sample` numbering 1..N, **line count == summary `samples`**, peak `rss_mb` == summary `peak_rss_mb`, **no sample above the declared limit**, min `available_mb` == summary `min_available_mb` |
| `<run-id>.PACKAGE_FILES.tsv` | `I4_M2_EVIDENCE_WINDOWS.ps1` (Phase I) | the listing **equals the package's total inventory** (every path, size and digest), and its row count equals the facts' `package_file_count` |

Additional cross-bundle rule (`RQ-11`): the two transcripts must be distinct documents. Facts,
summary and trace each carry a root, a timestamp or a process id, so two genuine runs can never
produce identical bytes; the package **listing** is a deterministic function of the package bytes
and is therefore *expected* to be identical for a byte-identical replay.

**Carried anomaly (unchanged, not reinterpreted).** The M2 monitor recorded `runner_exit_code: null`
— the documented, non-gating anomaly. The gate accepts `0` **and** `null`, records which value was
observed, and carries the note verbatim; it never silently rewrites the anomaly into a `0`.

**Residual limit (stated, not hidden).** The gate proves that a complete, internally consistent,
package-bound execution-evidence bundle exists for B — including a monitor trace whose samples,
count, peak and ordering agree with the summary. It cannot cryptographically prove that a human did
not fabricate that bundle while copying A's package. Remote attestation is out of scope for this
gate; the operator's execution statement plus the unedited monitor trace remain the attestation
layer, and both must be transferred for review.

## 5. G6 — Windows path detection test correction

**Finding.** `tests/test_i4_runner.py::DeterminismTests.test_retained_package_is_clock_free_and_path_free`
compiled the Windows branch as `(^[A-Za-z]:\\\\|/(home|tmp|Users|mnt|var)/)` — anchored to the
start of the file (and requiring the JSON-escaped double backslash). A Windows absolute path
embedded mid-document inside a JSON value — the realistic leak, and the leak that matters because
the replay runs on Windows — was **not detected** (demonstrated: repo pattern `no match`,
unanchored pattern `match`).

**Correction.** The detection is factored into module-level `CLOCK_LIKE_RE` / `ABSOLUTE_PATH_RE`
with helpers `clock_like_hits()` / `absolute_path_hits()`; the Windows branch is now
`[A-Za-z]:\\` (a drive-letter path in raw or JSON-escaped form) searched **anywhere** in the body.
The POSIX branch is unchanged (the declared root list; broadening it is out of scope). The retained
package test now scans the whole file through the helpers, and `PathDetectionRegressionTests` pins
detection at the beginning, in the middle and at the end, in both forms, plus path-free bodies that
must not be flagged. No normalisation was introduced anywhere: a detected path fails the test.

**False-positive sweep.** The corrected detector was run over 26 real artifact bodies (a produced
runner package and the W1/W2 determinism-harness artifacts from the published fixtures): **no
absolute-path hit, no clock-like hit.** The corrected branch is strictly more general than the
previous one, and the artifact set contains no drive-letter text.

---

## 6. Files changed

| File | Change | In the delivery revision? |
| --- | --- | --- |
| `tools/i4_m2/i4_replay_qualification.py` | **new** — the qualification gate (K1/K2/K3), library + CLI, stdlib only | new file |
| `tests/test_i4_replay_qualification.py` | **new** — 45 tests (K1/K2/K3 + gate CLI + script mode) | new file |
| `tests/test_i4_runner.py` | G6 correction: module-level detection patterns/helpers, whole-file scan, `PathDetectionRegressionTests` (4 tests) | modified (tests only) |
| `docs/investigations/D11_REPLAY_QUALIFICATION_CORRECTION.md` | this record | new file |

**Not changed:** `src/nse_engine/**` (engine), `tools/i4_runner/**` (runner, including
`i4_output.py`), `tools/i4_m2/I4_M2_MEMORY_MONITOR.ps1`,
`tools/i4_m2/I4_M2_TEST_LAUNCH_QUOTING.ps1`, the governed corpus, inventory, labels and D01
evidence. Nothing was merged into `main`.

## 7. Tests added / changed

New — `tests/test_i4_replay_qualification.py` (45 tests):

| Class | Coverage |
| --- | --- |
| `CompletenessPreconditionTests` (K1) | two complete packages → comparison permitted and passing; incomplete A → FAIL with `comparison = null`; incomplete B → FAIL; missing completion marker → FAIL and named; marker not bound to the manifest → FAIL; corrupted package (either side) → FAIL; internally consistent tamper (manifests rebuilt, verification passes) → comparison still FAILS naming the artifact; **all 22 artifacts mutated one at a time → every one is caught** (content artifacts by the comparison, manifest/marker artifacts by K1 verification); unlisted extra file → FAIL; hidden dotfile → FAIL; removed artifact → FAIL; run-id difference → FAIL |
| `RevisionPinTests` (K2) | matching revision/fingerprints → pass; engine fingerprint mismatch → FAIL; runner fingerprint mismatch → FAIL; **pre-M1 `main` fingerprints → FAIL**; run-id mismatch → FAIL; corpus identity mismatch → FAIL; recorded host revision mismatch → FAIL; `--strict-recorded-head` → FAIL when the recorded head differs from the declared revision; the revision record is captured in the report |
| `ExecutionEvidenceTests` (K3) | copy without an evidence bundle → FAIL; copy with A's evidence reused → FAIL; transcript reuse detected per document (facts / summary / trace); copy with its own execution evidence → procedural preconditions satisfied; monitor breach → FAIL; non-zero exit code → FAIL; **null exit code accepted and recorded**; trace count ≠ summary `samples` → FAIL; trace peak ≠ summary peak → FAIL; trace sample above the declared limit → FAIL; trace sample numbering broken → FAIL; listing not covering the package → FAIL; stale listing digest → FAIL; evidence `result = FAIL` → FAIL; evidence bound to another run id → FAIL; recorded package digests must bind → FAIL |
| `QualificationCliTests` | same directory refused; **symlink to the same package refused** (`realpath`, closing the vacuous-PASS vector the earlier investigation demonstrated); incomplete expectation refused; verdict inside package A refused; **verdict inside package B refused** (closing gap G5); end-to-end CLI PASS with a canonical, path-free, clock-free, host-free verdict document outside both packages; end-to-end FAIL exit code; **script-mode invocation** (the Windows operator path) returns PASS |

Changed — `tests/test_i4_runner.py` (G6): the path-free test now scans the whole body via the
helpers, and `PathDetectionRegressionTests` adds 4 tests (detection at beginning/middle/end in raw
and escaped form; POSIX branch unchanged; valid path-free bodies not flagged; clock branch
unchanged). The pre-existing tests are otherwise untouched.

Preserved and re-run unchanged (the replay comparison contract): identical packages → PASS; changed
row artifact → FAIL; changed evidence artifact → FAIL; changed manifest → FAIL; changed partition
manifest → FAIL; changed completion marker → FAIL; added artifact → FAIL; hidden artifact → FAIL;
removed artifact → FAIL; run-id difference → FAIL; verdict placement rules; verify-vs-replay
distinction; determinism/hash-seed independence.

## 8. Test results

| Run | Result |
| --- | --- |
| `python3 -m unittest discover -s tests -t .` (full suite, repo root) | **481 tests OK** (73.9 s) — 432 pre-existing (the path-free test was *modified in place*, so the pre-existing count is unchanged) + 45 new qualification + 4 new path-detection |
| `tests.test_i4_replay_qualification` (focused) | 45 OK |
| `tests.test_i4_replay_qualification` + `tests.test_i4_runner.PathDetectionRegressionTests` | 49 OK |
| `tests.test_i4_replay_qualification.QualificationCliTests` (focused, includes script mode) | 7 OK |
| `tests.test_i4_runner.PathDetectionRegressionTests` + `DeterminismTests` | 11 OK |
| `python3 -m compileall -q tests tools/i4_m2 tools/i4_runner src` | clean |
| Corrected-detector sweep over 26 real artifact bodies | 0 hits (no false positives) |

## 9. Fingerprints

| Identity | Before | After |
| --- | --- | --- |
| engine (`tool_fingerprint`) | `d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9` | `d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9` (unchanged) |
| runner (`runner_fingerprint`) | `f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a` | `f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a` (unchanged) |
| `tools/i4_runner/i4_output.py` | blob `0a8b60f7d1bb27e96afb7dcce0ebce9658ce417c` | **unchanged** — `i4_output.py` did not change |
| `tools/i4_runner/i4_runner.py` | blob `8481f76e0e2f2f79580a66dbb5c3ff9b145f8bd9` | unchanged |
| M2 monitor (`I4_M2_MEMORY_MONITOR.ps1`) | sha256 `7ef9db125c3e25135ab51c251b7cc46b38da33a329949ac2fbcd1a171dc78f00` | unchanged |
| M2 self-test (`I4_M2_TEST_LAUNCH_QUOTING.ps1`) | sha256 `4986b1fbe5cb054062cadb8eee1c75b4bc46f13f7634033f6fd04601a3ae74e4` | unchanged |

No mechanism-level change was required: procedure- and test-level enforcement satisfies K1/K2/K3,
and G6 is a test defect. **The pre-existing M2 package and its recorded fingerprints remain valid**
— no requalification of the M2 run is implied by this record.

---

## 10. Exact Windows replay preconditions

Apply after transferring the replay tooling (this module plus the corrected test file) to the
Windows host. Every step is fail-closed; stop at the first failure and report the exact output.

```
R0  Revision: materialise the Windows worktree so the executed module bytes are
      engine d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9
      runner f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a
    (revision 8ade8372e150e541a52206baa377a02249a308f4, tree
     8e1557de766d4c952be7261c4f72aa743f81de0b; a CRLF checkout fails PF-01/PF-02)
R1  Self-test first: powershell -ExecutionPolicy Bypass -File .\scripts\I4_M2_TEST_LAUNCH_QUOTING.ps1
      -> must print the PASS line (script sha256 4986b1fbe5cb054062cadb8eee1c75b4bc46f13f7634033f6fd04601a3ae74e4)
R2  Baseline A: verify --package "<A>" -> result "pass" with every check;
      SHA-256(<A>\PACKAGE_MANIFEST.sha256) == e7c7e4c8271f3a1c8ef42d76b926fe048a8997a342c92d89819eecd79e73b9dc
R3  Run B: memory monitor (sha256 7ef9db125c3e25135ab51c251b7cc46b38da33a329949ac2fbcd1a171dc78f00)
      -RepoRoot <Repo> -OutRoot "<fresh root B, outside repo and both corpus roots>"
      -RunId "i4-20261008-M2"                    (the M2 run id, unchanged)
      -RssLimitMB/-AvailableFloorMB              (as recorded for the M2 run)
      -EvidencePrefix "<new prefix, outside the run root>"
    The monitor itself pins the corpus roots, the inventory/labels/D01 inputs, --expect-records 2462,
      --expect-tool-fingerprint d3269b73…, --expect-runner-fingerprint f3ebf624…,
      --expect-inventory-lf-sha256 336b9531cd34f48e9a2e7e7593cc4e9c2736b3864d8213bc65d6ab8b488729d2
      and --min-free-bytes 15000000000; do not change any threshold after starting.
R4  Verify B: verify --package "<B>" -> result "pass" with every check.
R5  Evidence for both runs (Phase I): the facts file and the package listing for A and for B.
R6  Qualification gate (this correction; refuses to compare unless everything above holds):
      python -B "tools\i4_m2\i4_replay_qualification.py" ^
        --a "<A>" --b "<B>" ^
        --facts-a "<A>.EVIDENCE_FACTS.json"     --facts-b "<B>.EVIDENCE_FACTS.json" ^
        --summary-a "<A>.summary.json"          --summary-b "<B>.summary.json" ^
        --trace-a "<A>.jsonl"                   --trace-b "<B>.jsonl" ^
        --listing-a "<A>.PACKAGE_FILES.tsv"     --listing-b "<B>.PACKAGE_FILES.tsv" ^
        --expect-repository "ramkivs/nse-historical-data-engine" ^
        --expect-ref "arena/9021d1a1-nse-historical-data-engine" ^
        --expect-commit "8ade8372e150e541a52206baa377a02249a308f4" ^
        --expect-tree "8e1557de766d4c952be7261c4f72aa743f81de0b" ^
        --expect-engine-fingerprint "d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9" ^
        --expect-runner-fingerprint "f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a" ^
        --expect-run-id "i4-20261008-M2" ^
        --expect-corpus-archive-set-digest "<read from <A>\RUN_RECORD.json -> corpus.archive_set_digest>" ^
        --verdict "<path outside both packages>"
      -> exit 0 and "I4 REPLAY QUALIFICATION = PASS" (exit 2 is a FINDING, exit 1 is a usage error)
R7  Capture and transfer the evidence set (§11); stop and report on any failure.
```

## 11. Exact Windows evidence requirements (transfer before Arena accepts the replay)

| # | Item | Purpose |
| --- | --- | --- |
| E1 | Qualification verdict document (`--verdict`, canonical JSON, path-free) | the qualifiable result |
| E2 | `verify --package` output for A and for B | proves both packages complete and self-consistent |
| E3 | `<run-id>.EVIDENCE_FACTS.json` for A and B | the package-bound facts (identities, digests, counts, listing size) |
| E4 | `<prefix>.summary.json` for A and B | the monitored execution record (peak RSS, thresholds, breach, marker, exit code) |
| E5 | `<prefix>.jsonl` (monitor trace) for A and B | the sampled execution trace (count/peak/limit/ordering cross-checks) |
| E6 | `<run-id>.PACKAGE_FILES.tsv` for A and B | the total package inventory |
| E7 | `PACKAGE_MANIFEST.sha256` and `RUN_COMPLETE.json` for A and B | baseline pin `e7c7e4c8…` and both completion markers |
| E8 | `RUN_RECORD.json` for A and B (or at least the `engine_identity`/`runner_identity`/`corpus` blocks) | the recorded revision and corpus identity |
| E9 | Transfer manifest (path + SHA-256 of every transferred file) | lets Arena verify the bytes it reviews |
| E10 | If a precondition fails: the exact failing step, its stdout/stderr, and the qualification report | forensics — never a repair task |

The multi-GB packages themselves are **not** required: every check above is hash- or small-document
based. Arena requests specific artifacts only if the verdict reports a mismatch — and a mismatch is
a finding, never something to normalise.

---

## 12. Determination

> ### `REPLAY QUALIFICATION CORRECTIONS COMPLETE — WINDOWS REPLAY AUTHORIZABLE`

* **K1 — addressed** (gate refuses the comparison unless both packages verify and both markers are
  bound; a comparison is never executed while a gating precondition fails).
* **K2 — addressed** (single declared revision / run id / corpus identity enforced from the executed
  bytes; the exact M2 revision determined from repository history; `main` fails closed).
* **K3 — addressed** (a package-bound execution-evidence bundle is required for both runs, with
  monitor-trace cross-consistency; a copy cannot satisfy it without its own bundle).
* **G6 — addressed** (whole-file Windows-path detection, regression cases at beginning/middle/end in
  both forms, valid path-free bodies preserved, real-artifact sweep clean).
* **Mechanism unchanged** (`i4_output.py` untouched, both fingerprints unchanged) and **no engine,
  runner, threshold, corpus or output-contract change**.
* **Residual, recorded limits:** (a) the gate cannot cryptographically disprove a fabricated
  evidence bundle — the operator attestation plus the unedited monitor trace are the attestation
  layer and must be transferred; (b) the POSIX branch of the path scan keeps the declared root list;
  (c) the second full replay is still required for I4 closure (D08 MD-11 #7) — this record makes it
  qualifiable, it does not perform it.
* **No Windows execution occurred.** No PowerShell was invoked, `G:\` and `C:\IIPS_Data` were never
  accessed, the 2,462-member corpus was not executed, and no Windows evidence was fabricated.
