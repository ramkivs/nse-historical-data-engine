# I4 Replay / E2E Integration & Determinism Qualification — Arena investigation

**Gate:** `I4 → Replay / E2E integration/determinism qualification → I5`
**Scope:** Arena/Linux investigation only. No Windows or PowerShell was invoked, `G:\` and `C:\IIPS_Data`
were never accessed, and the 2,462-member corpus was **not executed**. Every experiment ran on
synthetic fixtures written to a temporary directory.
**Date:** 2026-10-08 (Arena)

> **Status update (2026-10-08, correction applied).** The three contract deficiencies this record
> identified (K1 completeness precondition, K2 revision pin, K3 independent execution evidence) and
> the G6 path-detection test defect have been corrected at the **qualification/procedure and test
> layer** — no engine, runner or `i4_output.py` change, both fingerprints unchanged. See
> `docs/investigations/D11_REPLAY_QUALIFICATION_CORRECTION.md`, which also fixes the exact M2
> revision (`8ade8372e150e541a52206baa377a02249a308f4`, tree `8e1557de…`), the exact Windows replay
> preconditions and the exact evidence set to transfer. The findings below stand as the record of
> the pre-correction state of the contract; where they state that a correction is required, D11 is
> the correction.

---

## 1. Authoritative repository state (established from the repository, not assumed)

| Item | Value |
| --- | --- |
| Repository | `ramkivs/nse-historical-data-engine` (public) |
| Authoritative ref | `origin/main` |
| `origin/main` commit | `6a60583f62905c1fbda9cc7529019e2a9ed0b097` |
| `origin/main` tree | `ad882becd89992e3c62a2bdff00a78bc6d80dbc0` |
| `origin/main` shape | **root commit** — `git log -1 --format=%P` is empty, `git rev-list --count origin/main` = 1 |
| `origin/main` message / author / date | `Apply I4 Windows runner` · Ramaki `<sairam260573@gmail.com>` · Wed Oct 7 18:09:55 2026 +0530 |
| `origin/main` paths | 121 |
| Other refs | `refs/heads/arena/9021d1a1-nse-historical-data-engine` = `edbda829d43ce0b31133ad59b81ae6f65d7b16f8`; `refs/heads/arena/01a10c83-nse-historical-data-engine` = `db604063b305f9a96d2ac038ed001ff7344c17c8`; `refs/tags/d08-transfer-2026-10-06` = `a1f0b585f9650da262b15eea4f8a00b86fd4a32b` |
| Local checkout | branch `arena/9021d1a1-…`, HEAD `89ce965c7961088950faf08b83a31f961e6fc214` (stale), worktree holds the M2 delivery as untracked paths (`src/`, `tests/`, `tools/i4_runner/`, `tools/i4_m2/`, `_transfer_delivery/`) |
| Working-tree status | 2 modified tracked files (`README.md`, `docs/specs/D05_CANONICAL_MODEL_SPEC.md`) — pre-existing, not touched by this investigation |

### 1.1 `main` is **not** the revision that produced the Windows M2 run (material finding)

The milestone context states the completed M2 run recorded engine fingerprint
`d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9` and runner fingerprint
`f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a`. Computed **from `main`'s own
bytes** in a fresh clone:

| Fingerprint | `origin/main` (`6a60583f`) | M2 delivery revision (workspace / `edbda829`) | M2 run evidence |
| --- | --- | --- | --- |
| engine | `7bee84902f8cb0e5c60703acbe1b17d6e85a9b9762289bab1741d9f003df5a52` | `d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9` | `d3269b73…` |
| runner | `618bfd4c4919f3224a3e0f64682c21617c356580ebccd807f8abce528302c904` | `f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a` | `f3ebf624…` |

`main` also **lacks** the bounded-memory engine modules (`src/nse_engine/compact.py`,
`src/nse_engine/w2_stream.py` — 15 engine modules instead of 17), the compact/stream tests, the
`tools/i4_m2/` monitor and self-test, and `docs/investigations/D09`/`D10`. Its `tests/test_i4_runner.py`
still declares `GOVERNED_TOOL_FINGERPRINT = 7bee8490…` (pre-M1) and has no runner-fingerprint pin.

`main`'s runner uses the retained-build W2 path (`from nse_engine.pipeline import build_w2`), while the
M2 revision feeds a bounded-memory accumulator (`nse_engine.w2_stream.W2Accumulator`) and releases each
member. **The two revisions therefore cannot produce the same package bytes and cannot be mixed across a
replay.** The replay of the M2 run must be performed with the M2 revision
(`tools/i4_runner/i4_runner.py` blob `8481f76e0e2f2f79580a66dbb5c3ff9b145f8bd9`,
`src/nse_engine/*` = the 17-module set), not with `main`.

What *is* identical between the two revisions is the replay implementation itself: `tools/i4_runner/i4_output.py`
is blob `0a8b60f7d1bb27e96afb7dcce0ebce9658ce417c` in both `main` and the workspace.

### 1.2 Windows output package is not present in Arena

`grep` for the recorded package manifest `e7c7e4c8271f3a1c8ef42d76b926fe048a8997a342c92d89819eecd79e73b9dc`
across the workspace returns nothing; no `RUN_COMPLETE.json` or `PACKAGE_MANIFEST.sha256` exists anywhere
in it. Arena holds only the **transfer** material (`_transfer_delivery/`), whose 29-file M2 payload is
byte-identical (29/29 git blob ids) to the current worktree.

---

## 2. Replay implementation (from source, not documentation)

### 2.1 Entry points

| Layer | Location | Behaviour |
| --- | --- | --- |
| CLI | `tools/i4_runner/i4_runner.py` `build_parser()` → `replay` subparser (`--a`, `--b`, `--verdict` optional) | `replay_command` (`:723`) |
| Command | `replay_command(args)` | calls `output.replay_compare(abspath(a), abspath(b))`; writes the verdict if `--verdict` was given; prints the canonical JSON; exit `0` pass / `2` fail / `1` usage |
| Comparison | `tools/i4_runner/i4_output.py` `replay_compare(dir_a, dir_b)` (`:352`) | total byte comparison |

### 2.2 Exact comparison rules (`replay_compare`, verbatim behaviour)

1. `os.path.abspath(dir_a) == os.path.abspath(dir_b)` → `OutputError("replay requires two distinct
   package directories")` → CLI exit `1`. The guard is **lexical** (`abspath`, not `realpath`/inode).
2. `listing(root)`: `os.walk` the whole tree, `dirnames.sort()`, `filenames` sorted; every **file**
   becomes a key = relative POSIX path, value = SHA-256 of its bytes (1 MiB streaming).
3. `only_a = set(files_a) − set(files_b)`, `only_b = set(files_b) − set(files_a)`,
   `differing = {paths in both with different digests}`, each sorted.
4. `result = "fail" if (only_a or only_b or differing) else "pass"` — **the decision is computed from
   the full sets**, never from the truncated lists.
5. `first_difference` = `{only_in_a[:20], only_in_b[:20], differing[:20], differing_count}` (the lists
   cap at 20; the count is exact).
6. The document also reports `run_metadata_declared = ["provenance.run_id"]`, `files_a`, `files_b`,
   `manifest_sha256_a/b` (SHA-256 of each side's `PACKAGE_MANIFEST.sha256`), and the note
   *"total comparison: no exclusion list is consulted. A mismatch is REPLAY-FAILED and must not be
   normalised away (RD-9 case 6)."*
7. Verdict placement guard (`replay_command`): if `--verdict` is inside either package
   (`== package` or `startswith(package + os.sep)`) → stderr
   `replay error: verdict must be written outside both packages`, exit `1`, nothing written. The guard
   is separator-aware, so a sibling path that merely *prefixes* a package name is accepted.
8. The verdict file receives exactly the same canonical JSON as stdout plus a final newline; it is
   written **before** the exit code is derived, so a failing comparison still produces a durable
   `"result":"fail"` verdict.

**There is no exclusion list, no normalization, no tolerance and no run-metadata special case anywhere
in the comparison path** — verified by reading the whole function and by the exhaustive mutation
experiment (§4.E).

### 2.3 The determinism contract the comparison is applied to

* `contract.RUN_METADATA_FIELDS = ("provenance.run_id",)` — the single declared run-metadata field
  (`src/nse_engine/contract.py:433`; placeholder at `:434`), with `RUN_METADATA_PLACEHOLDER = "<run-metadata:excluded>"`.
* The placeholder is used **only** when a caller asks for the run-metadata-excluded view
  (`serialize.canonical_row_dict(..., include_run_metadata=False)`; used by `build_evidence`,
  `tests/determinism_check.py` and the W1/W2 determinism tests).
* The runner writes canonical rows **with** the real run id:
  `writer.write_text(rows_path, rows_jsonl(build.rows))` (`i4_runner.py:202`, default
  `include_run_metadata=True`). Consequently `provenance.run_id` is present in every row artifact and
  the **same declared run id is required for byte-identity**.
* Retained artifacts are LF-canonical (`newline=""`), clock-free, path-free and host-free by
  construction; numerics are emitted as published text (no float formatting); JSON is canonical
  (sorted keys, compact separators, `ensure_ascii=False`, `allow_nan=False`).
* Preflight `PF-03` **gates** the run on a source scan of the six declared `RUNNER_MODULES` for clock,
  randomness and environment tokens plus forbidden network imports. The 15/17 engine modules are not
  part of that scan; their freedom from clock/host values is established by the engine's own
  determinism tests and by the retained-package scan (§3, Class 1 note).

---

## 3. Determinism matrix

Counts for the real package are **derived** from the layout and the recorded member count (2,462); they
are marked *(derived)* where Arena cannot observe them directly.

| Artifact / class | Compared? | Byte-exact? | Allowed difference? | Evidence |
| --- | --- | --- | --- | --- |
| `partitions/<family>/<year>/rows/<stem>.rows.jsonl` (2,462 files *(derived)*) | yes | yes | none — carries `provenance.run_id`, so the **same run id** is required | `i4_runner.py:202`; E2 (mutate → fail); E7 (run id → 9 files carry it) |
| `partitions/<family>/<year>/evidence/<stem>.evidence.json` (2,462 *(derived)*) | yes | yes | none — evidence uses the run-metadata-excluded view, so it is byte-identical **even across different run ids** | `serialize.build_evidence`; E3 (mutate → fail); E7 (not in the differing set) |
| `w2/calendar.jsonl`, `w2/metrics.json`, `w2/identity_summary.json`, `w2/unresolved.jsonl` | yes | yes | none | E10/E11 coverage; E7 (identical across run ids) |
| `w2/associations.jsonl` | yes | yes | none — carries the run id via identity records | E7 (in the differing set) |
| `PREFLIGHT.jsonl`, `INPUT_MANIFEST.jsonl`, `RECONCILIATION.jsonl` | yes | yes | none | E10/E11; E7 (`PREFLIGHT.jsonl` carries the run id) |
| `GOVERNED_INPUTS.json`, `RUN_RECORD.json` | yes | yes | none — both carry `run_id` | E7 (both in the differing set) |
| `manifests/<family>_<year>.sha256` (12 *(derived)*) | yes | yes | none; content is derived from the artifacts it lists | E4b (mutate → fail); E7 (differ when their targets differ) |
| `PACKAGE_MANIFEST.sha256` | yes (not covered by any manifest) | yes | none | E4 (mutate → fail); `UNMANIFESTED` |
| `RUN_COMPLETE.json` | yes (not covered by any manifest) | yes | none | E4c (mutate → fail) |
| Any unlisted extra file (incl. dotfiles) | yes | — | none — `only_in_*` forces FAIL | E5, E5b (add → fail) |
| A removed artifact (any) | yes | — | none — `only_in_*` forces FAIL | E6, E11 (remove each of 22 → fail) |
| `RUN_FAILED.json` (failed run) | yes | yes | n/a — a failed root is not a package and is never replayed (no completion marker) | `i4_output.write_failure`, RD-9 |
| Transient artifacts `*.tmp`, `*.log`, `*.part`, `scratch/*` (MD-05 class 4) | would be compared | — | n/a — must never be retained; `self_check` fails the run if any unlisted file appears | `TRANSIENT_PATTERNS`; `self_check` |
| Monitor evidence `<prefix>.baseline.json`, `.summary.json`, `.jsonl`, `.runner.stdout.txt`, `.runner.stderr.txt` | **no** — structurally outside the package | no | **yes** — host/process/RSS/timing data | the monitor fails closed unless `-EvidencePrefix` is outside `-OutRoot`, `-OutRoot` is outside the repo and both corpus roots (`I4_M2_MEMORY_MONITOR.ps1:120-124`) |
| Replay verdict JSON | **no** — outside both roots by rule | no | yes (it is the comparison's own output) | `replay_command` guard; E8 |
| File modes / ownership / directory mtimes | no | — | yes — the contract is content-level (`listing()` hashes file bytes only) | `replay_compare` source |
| Empty directories | no | — | yes — files-only walk cannot see a directory-only difference | `listing()` source (theoretical: the runner creates no empty directory) |

**Class 1 (MUST be byte-identical):** every retained file under the run root — *(derived)* 2,462 rows +
2,462 evidence + 12 partition manifests + 5 `w2` artifacts + `PREFLIGHT.jsonl` + `INPUT_MANIFEST.jsonl` +
`RECONCILIATION.jsonl` + `GOVERNED_INPUTS.json` + `RUN_RECORD.json` + `PACKAGE_MANIFEST.sha256` +
`RUN_COMPLETE.json` = **4,948 files**, pending confirmation against the Windows package's own
`<run-id>.PACKAGE_FILES.tsv`.

**Class 2 (MAY legitimately differ):** only artifacts **outside** the package boundary — the monitor's
five evidence files and the replay verdict. Nothing inside a complete package may differ.

**Class 3 (must not be silently ignored) — the implementation normalizes nothing, but four boundary
properties must be handled by the qualification procedure:**

1. **A PASS does not certify that either side is a package.** `replay_compare` has no completeness
   precondition (§4.P1/P2).
2. **Distinctness is lexical.** `--a` and `--b` may be two paths to the same directory (symlink or
   junction) and yield a vacuous PASS (§4.V1).
3. **A byte copy of A passes as "B".** Nothing in the mechanism proves that B came from a second
   execution; that proof must come from B's own run evidence (§5.W6).
4. **The verdict truncates its forensic lists at 20 entries** while reporting the exact
   `differing_count`; the PASS/FAIL decision is unaffected (§4.V3).

---

## 4. Arena experiments (synthetic fixtures; 25 replay cases + 6 boundary probes, 0 unexpected)

Command (repo root, read-only w.r.t. the repository; all output under a temp directory):

```
PYTHONPATH=src:. python3 /tmp/replay_e2e/run_experiments.py /home/user/nse-historical-data-engine
```

Setup: the repository's own synthetic member builders (`tests/test_i4_runner.py::Corpus`, 4 members:
2 LEGACY + 2 UDIFF, 8 rows) produced two packages with the same declared run id `i4-probe-2026`
(22 files each, 139,863 bytes), a third with a different run id, and every package **self-verifies
`pass`**. All 15 durability-class rules are exercised by this 22-file package (checked by
`fnmatch` against `ARTIFACT_CLASS_RULES`; no file matches zero or two rules).

| # | Case | Observed |
| --- | --- | --- |
| E1 | identical packages | `pass`, 22/22 files, both manifest digests equal, CLI exit `0` |
| E2 | one canonical-rows byte appended | `fail`, `differing=["partitions/legacy13/2024/rows/cm01JUL2024bhav.csv.rows.jsonl"]` |
| E3 | one evidence artifact byte appended | `fail`, `differing=["…/evidence/cm01JUL2024bhav.csv.evidence.json"]` |
| E4 | `PACKAGE_MANIFEST.sha256` byte appended | `fail`, `differing=["PACKAGE_MANIFEST.sha256"]` |
| E4b | partition manifest byte appended | `fail`, `differing=["manifests/legacy13_2024.sha256"]` |
| E4c | `RUN_COMPLETE.json` byte appended | `fail`, `differing=["RUN_COMPLETE.json"]` |
| E5 | unlisted artifact added | `fail`, `only_in_b=["extra_artifact.json"]` |
| E5b | hidden dotfile added | `fail`, `only_in_b=[".hidden"]` |
| E6 | `w2/metrics.json` removed | `fail`, `only_in_a=["w2/metrics.json"]` |
| E7 | different run id (`…-OTHER`) | `fail`, 12 differing files: **9 carry the run id** (`GOVERNED_INPUTS.json`, `PREFLIGHT.jsonl`, `RUN_COMPLETE.json`, `RUN_RECORD.json`, the 4 row artifacts, `w2/associations.jsonl`) and **3 are derived** (`PACKAGE_MANIFEST.sha256` + the 2 partition manifests). `w2/calendar.jsonl`, `w2/metrics.json`, `w2/identity_summary.json`, `w2/unresolved.jsonl` and every evidence artifact are byte-identical |
| E9 | verdict written outside both roots | written, `result=pass`, exit `0` |
| E8 | verdict inside A / inside B / nested inside A | exit `1`, stderr `verdict must be written outside both packages`, nothing written |
| E8b | verdict at a sibling path that merely *prefixes* A's name | accepted (exit `0`) — the guard is separator-aware by design |
| E10 | **append one byte to every one of the 22 artifacts, one at a time** | `fail` 22/22 — no artifact is excluded from the comparison |
| E11 | **remove each of the 22 artifacts, one at a time** | `fail` 22/22 |
| F1 | tamper a row, then rebuild every partition manifest + package manifest + marker (so the package is internally consistent again) | `verify` = **pass**, `replay` = **fail** — replay is strictly stronger than self-verification and is the only gate that can catch a re-manifested package |

Boundary probes (separate run):

| # | Probe | Observed |
| --- | --- | --- |
| P1 | two identical directories containing only `notes.txt` | `replay` = **`pass`**, CLI exit `0` — **a PASS does not require packages** |
| P2 | two identical **incomplete** packages (marker removed on both sides) | `replay` = **`pass`**, exit `0`, while `verify` = `fail` (`verify-04`) |
| P3 | replay with a real difference | exit `2`, `"result":"fail"` |
| P4 | package versus a byte copy at another path | `pass` (correct, but see Class 3.3: a copy is indistinguishable from a second run) |
| P5 | verdict inside a package | exit `1`, nothing written |
| V1 | package versus a **symlink** to that same package | `pass`, exit `0` — the distinctness guard is lexical |
| V2 | failing replay with `--verdict` | exit `2`, verdict written with `"result":"fail"` |
| V3 | 21 artifacts tampered | `differing_count=21`, but only 20 paths are listed — re-derive the full list for forensics |

Determinism-hazard checks:

* `DeterminismTests` pass under `PYTHONHASHSEED` 0, 1 and 7919 (hash-seed independent).
* No clock, randomness, environment or network use reaches the artifact paths: the engine contains no
  `.now()`/`.time()`/`random`/`uuid` call; `datetime` is imported in `calendar.py`/`parsing.py` only for
  date parsing; `PF-03` gates the six runner modules at preflight.
* Set/dict iterations that could reach artifacts are either wrapped in `sorted()` (`replay_compare`
  itself) or order-independent accumulations (census counters serialized through canonical JSON).
* **The fingerprints are CRLF-sensitive** (raw module bytes): engine LF `d3269b73…` vs CRLF
  `c1b6e53dc1e6ac4d304e77a2d7365dbf3e9e5ea2db6b90943f39f19897d31e62`; runner LF `f3ebf624…` vs CRLF
  `c838a138321c3b6f8d532122900b3936ac9fa5a6f94c3854db6527d9d87f27ec`. The `lf_sha256` per module is
  invariant (verified). A replay host whose worktree has CRLF module bytes fails closed at PF-01/PF-02
  and can never start the run — so the replay revision must be materialised with its committed line
  endings (the transfer tarball preserves them).
* Path-free scan of a produced package (all 22 files): no clock-like string, no absolute path, no
  declaration path, no `/tmp/` or drive-letter leak.

---

## 5. Existing test coverage and gaps

Covered today (`tests/test_i4_runner.py`): same-run-id byte-identity (`DeterminismTests`), first-difference
reporting, replay CLI exit codes, verdict-inside-package rejection, two-distinct-directories requirement,
different-run-id failure plus a normalisation check proving only the declared field differs, clock-free/
path-free package, LF/final-newline artifacts, and `VerifyTests` (manifest, tampering, unlisted artifact,
missing marker, partition-manifest inconsistency, identity drift).

Gaps identified (each verified above):

| Gap | What is missing | Why it matters |
| --- | --- | --- |
| G1 | No test that **every** retained/emitted artifact class, mutated one at a time, forces a replay FAIL | The "no hidden exclusion" property is asserted in prose (`note`) but not proven per artifact — E10/E11 prove it ad hoc, not in the suite |
| G2 | No test that a replay **PASS requires a complete package** (no test at P1/P2) | A vacuous PASS is currently reachable by both the function and the CLI |
| G3 | No test that `--a`/`--b` are genuinely distinct (symlink/junction to one directory) | Vacuous PASS vector V1 |
| G4 | No test asserting `RUN_COMPLETE.json`/`PACKAGE_MANIFEST.sha256` (the two `UNMANIFESTED` files) are inside the comparison | They are compared (E4/E4c) but nothing pins it |
| G5 | Verdict-inside-package is tested only for package **A** | The loop covers both; the test does not |
| G6 | The path-free test's drive-letter branch is anchored to the start of the file (`^[A-Za-z]:\\\\`, no `MULTILINE`), so a Windows absolute path embedded mid-file (e.g. inside a JSON value) is **not detected** — demonstrated: repo regex `False`, unanchored `[A-Za-z]:\\` `True` | The replay will run on **Windows**; this is exactly the leak the test is meant to catch |
| G7 | `PF-03` (clock/random/environment scan) covers the 6 runner modules only | Engine-side clock/host leakage would not be caught at preflight (currently clean by inspection + engine tests) |
| G8 | The verdict's 20-entry cap is undocumented in tests | Forensic readers must re-derive the full list |

---

## 6. Cross-check against the completed Windows M2 evidence

Facts Arena can establish: the transfer payload (29 files) is byte-identical to the worktree; the
required fingerprints match the worktree and **not** `main`; the package layout, artifact classes and
comparison semantics are as above. Facts Arena **cannot** establish (no Windows access, no output
package in Arena): the packages themselves, their manifest hash `e7c7e4c8…`, the completion marker's
counts, the monitor's `null` exit-code classification anomaly (documented, non-gating — not
reinterpreted here), and any replay verdict (the M2 runbook's Phase H marks replay **optional**, and no
replay verdict is reported in the milestone context).

### 6.1 Is a second full 2,462-member Windows replay required for I4 closure?

**Yes — on the evidence available it is the only outstanding qualification, and no substitute exists.**
D08 MD-11 item 7 requires *deterministic replay evidence* among the retained I4 evidence, and the
runner README documents the replay as the determinism gate (MD-03 #11 / MD-11 #7). The repository's
determinism harness (`tests/determinism_check.py`) and the frozen determinism manifest `5589ee2c…`
cover **eight published row-sample fixtures** — they are not corpus-scale evidence. Row counts,
member counts and reconciliation counts matching is explicitly *not* sufficient. Therefore exactly one
second full run, from the same corpus with the same run id, compared byte-for-byte against the
completed package, is required; nothing in this investigation reduces that requirement.

Conditions under which the completed M2 package may serve as the baseline (package A):

1. it still exists at its recorded root and is **read-only** for the duration of the replay;
2. `verify --package <A>` returns `pass` with every check listed (`verify-01…verify-07`);
3. `SHA-256(PACKAGE_MANIFEST.sha256)` equals the frozen `e7c7e4c8…`;
4. the replay run declares the **identical run id** (`i4-20261008-M2`, per the milestone context) — a
   different run id must fail by design (E7);
5. the replay host's engine/runner module bytes reproduce `d3269b73…` / `f3ebf624…` (LF checkout);
6. the second package is produced into a **fresh, non-existent** root and is itself verified `pass`;
7. the verdict is written **outside both roots**.

### 6.2 Windows evidence that must be transferred before Arena can review the replay

| # | Item | Why |
| --- | --- | --- |
| W1 | Replay verdict JSON (canonical, as written by `replay`) | the qualification's primary result |
| W2 | Baseline `PACKAGE_MANIFEST.sha256` **and** `RUN_COMPLETE.json` **and** the `verify --package` output (all checks, `run_id`) | proves A is a complete, self-consistent package and pins the baseline manifest hash to `e7c7e4c8…` |
| W3 | Second package's `PACKAGE_MANIFEST.sha256`, `RUN_COMPLETE.json`, and its `verify --package` output | proves B is complete and self-consistent |
| W4 | `RUN_RECORD.json` (or its identity block) for both packages | binds the comparison to the recorded engine/runner fingerprints, module facts, counts, partitions and corpus digest |
| W5 | Second package's `PREFLIGHT.jsonl` (PF-01/PF-02/PF-03 records and declarations) and `GOVERNED_INPUTS.json` | proves the same revision, the same governed inputs and the declared expectations |
| W6 | Second run's monitor evidence: `<prefix>.baseline.json`, `<prefix>.summary.json`, `<prefix>.jsonl`, `.runner.stdout.txt`, `.runner.stderr.txt` (new prefix) | proves a **fresh execution actually happened** (E/P4: a byte copy would replay clean) and records peak RSS/thresholds/exit classification |
| W7 | The second package's `<run-id>.PACKAGE_FILES.tsv` (file list) and `<run-id>.EVIDENCE_FACTS.json` | confirms the 4,948-file *(derived)* boundary and the artifact-class census |
| W8 | Transfer manifest (path + SHA-256 for every transferred file) | lets Arena verify the bytes it reviews |
| W9 | If the verdict is `fail`: the operator-re-derived full differing list (the verdict caps at 20) plus the named artifacts | forensics, not normalization |

Not required: the multi-GB packages themselves. The comparison is hash-based; Arena can qualify the
result from W1–W8, requesting specific artifacts only if a mismatch is reported.

---

## 7. Replay contract determination

> ### `REPLAY CONTRACT INSUFFICIENT — CORRECTION REQUIRED`

The **comparison mechanism** is sufficient and needs no semantic change: it is total over files, has no
exclusion list, normalizes nothing, refuses a same-path comparison, refuses a verdict inside either
package, and its FAIL/PASS decision is independent of the truncated forensic lists (E1–E11, F1). Call
the mechanism *sound*.

The **qualification contract** is insufficient as it stands, because three properties required for a
meaningful verdict are not guaranteed by it:

| # | Deficiency | Required correction (narrow, fail-closed) |
| --- | --- | --- |
| K1 | A replay PASS is reachable for inputs that are not complete packages and were never verified (P1, P2) | Make the procedure mandatory and ordered: `verify --package A` → pass, `verify --package B` → pass, **then** `replay`; record both verify outputs and both manifest hashes in the evidence set. Optionally harden `replay_command` to refuse a comparison unless both roots carry a completion marker whose `package_manifest_sha256` matches the manifest on disk (requires explicit authorization: it is a behaviour change, not a comparison change) |
| K2 | The replay is not pinned to the revision that produced the run; `main` (7bee8490…/618bfd4c…) cannot reproduce the M2 package | The authorization must name the run revision (engine `d3269b73…`, runner `f3ebf624…`) and require the operator to prove the module facts on the replay host before running. Partial mitigation already in the delivered tooling: the memory monitor **hard-wires** `--expect-records 2462`, `--expect-tool-fingerprint d3269b73…`, `--expect-runner-fingerprint f3ebf624…` and `--expect-inventory-lf-sha256 336b9531…`, so a monitored replay run fails closed at PF-01/PF-02 before writing anything if the host revision or corpus inventory differs (`I4_M2_MEMORY_MONITOR.ps1:140-195`) |
| K3 | A pass is not distinguishably the product of a second execution (a byte copy passes) | Require the second run's own execution evidence (W6) and a fresh root; the manifest equality then has to be reproduced by a real run |

One test defect and one test gap should be corrected at the same time (they are cheap and touch no
engine/runner logic): G6 (the Windows-path branch of the path-free test) and G1/G2/G4 (per-artifact
mutation coverage, completeness precondition, `UNMANIFESTED` coverage).

---

## 8. Gate recommendation

> ### `CORRECTION REQUIRED BEFORE WINDOWS REPLAY`

Rationale: the replay mechanism is sound, but authorizing a Windows replay today would let an operator
follow the delivered runbook (whose Phase H is optional and does not chain verification) and produce a
PASS that the contract cannot defend — exactly the failure mode the I4 gate's critical constraint
forbids. The corrections are procedure/evidence-level plus one narrow test repair; **none of them
changes engine semantics, runner run semantics, thresholds, the corpus contract or the output contract.**

**No implementation mutation is required to make the comparison correct.** If the operator prefers
mechanism-level enforcement of K1 (a completeness precondition inside `replay_command`), that is a
separate, explicitly authorized change (it alters CLI behaviour and therefore needs its own corrective
revision + tests + fingerprints unchanged, since `i4_output.py` would be edited: the runner fingerprint
`f3ebf624…` **would change** if `i4_output.py` changed — an important consequence to weigh before
authorizing it, because the fingerprint is part of the evidence chain).

---

## 9. Exact Windows replay authorization specification (for a later phase — do not execute now)

**Preconditions (all fail-closed, verified in order):**

```
S0  Revision match: engine fingerprint = d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9
                   runner fingerprint = f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a
    (module bytes must equal the transferred LF bytes; a CRLF worktree fails PF-01/PF-02)
    Monitor:    tools\i4_m2\I4_M2_MEMORY_MONITOR.ps1     sha256 7ef9db125c3e25135ab51c251b7cc46b38da33a329949ac2fbcd1a171dc78f00
    Self-test:  scripts\I4_M2_TEST_LAUNCH_QUOTING.ps1    sha256 4986b1fbe5cb054062cadb8eee1c75b4bc46f13f7634033f6fd04601a3ae74e4
S1  Self-test first:  powershell -ExecutionPolicy Bypass -File .\scripts\I4_M2_TEST_LAUNCH_QUOTING.ps1
                      must print the PASS line before any governed work
S2  Baseline A = <the M2 package root exactly as recorded in the M2 evidence — NOT a path this
                  investigation may assume; the M2 record's own prohibition protects the sibling
                  legacy root G:\My Engines\I4_RUNS\i4-20261008>, treated read-only:
      python -B tools\i4_runner\i4_runner.py verify --package "<A>"   -> result "pass", all checks
      SHA-256(<A>\PACKAGE_MANIFEST.sha256) == e7c7e4c8271f3a1c8ef42d76b926fe048a8997a342c92d89819eecd79e73b9dc
S3  Run B — the monitor declares every expectation itself, so the operator supplies only the roots,
    the run id and the thresholds; the declared run id must be the M2 record's run id
    (i4-20261008-M2 per the M2 facts), and the second root must be fresh and must not exist:
      & "<Pkg>\scripts\I4_M2_MEMORY_MONITOR.ps1" -RepoRoot "<Repo>" `
          -OutRoot "<fresh second root, outside repo and both corpus roots>" `
          -RunId "<the M2 run id exactly as recorded>" `
          -RssLimitMB <as recorded for the M2 run> -AvailableFloorMB <as recorded> `
          -EvidencePrefix "<new prefix, outside the run root>"
    Written into the plan by this package (not operator choices): corpus roots
    C:\IIPS_Data\NSE_Legacy_Acquisition\archives and C:\IIPS_Data\NSE_CM_UDiFF_10Y\archives,
    inventory/labels/D01 inputs under <Repo>\evidence\..., --expect-records 2462,
    --expect-tool-fingerprint d3269b73…, --expect-runner-fingerprint f3ebf624…,
    --expect-inventory-lf-sha256 336b9531cd34f48e9a2e7e7593cc4e9c2736b3864d8213bc65d6ab8b488729d2,
    --min-free-bytes 15000000000.
S4  Verify B:  python -B tools\i4_runner\i4_runner.py verify --package "<B>"  -> result "pass", all checks
S5  Replay:    python -B tools\i4_runner\i4_runner.py replay `
                 --a "<A>" --b "<B>" --verdict "<a path outside both A and B>"
               expect exit 0 and "result":"pass"; exit 2 with any difference is a FINDING (not a task)
S6  Capture W1–W8 and transfer; stop at the first failed step and report the exact output
```

**Prohibitions for that phase:** no modification of package A; no reuse of any existing output root; no
run-id change; no normalization or hand-repair of a difference; no `main` merge; no production; the
failed root `i4-20261007` and the M2 root remain untouched evidence.

---

## 10. Statements

* `I4 REPLAY/E2E = SETTLED BY INVESTIGATION` … **No.** This investigation does **not** close I4: the
  corpus-scale replay has not been performed, and the contract corrections in §7 must be applied first.
* No Windows execution, no PowerShell invocation, no `G:\`/`C:\IIPS_Data` access, no corpus execution,
  no production work occurred in Arena during this investigation.
* The documented, non-gating monitor `null` exit-code anomaly is carried unchanged and is not
  reinterpreted.
* `main` (`6a60583f…`) was not modified, and no revision is merged into it.
