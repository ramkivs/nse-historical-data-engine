# I4 Runner — operator runbook

**Status: non-production.** The runner orchestrates the unmodified engine over the governed
historical corpus. It selects **no** storage technology (MD-12 remains `UNDECIDED`), exposes no
API/UI, performs **no** network access, and never writes to the corpus.

Authorized scope: I4 runner implementation (RD-1…RD-10). Execution of the corpus is a separate
authorization (D08 §13 / MD-13) and is **not** granted by this tool's existence.

---

## 1. What the runner does

| Responsibility | Where |
|---|---|
| R1 verify the corpus archive set against the governed D01 inventory | `i4_preflight.py` (PF-10, PF-11, PF-12) |
| R2 read each archive's single CSV member verbatim | `i4_inputs.py` (`csv_member_names`, `read_member_bytes`) |
| R3 construct `SourceDescriptor` from governed facts (`archive_sha256_basis="D01-inventory"`) | `i4_inputs.build_source` |
| R4 invoke the existing `build_canonical` and reconcile per member | `i4_runner._member_records`, `i4_reconcile.py` |
| R5 compose the existing `build_w2` | `i4_runner` (single `build_w2` call, explicit `member_facts`) |
| R6 deterministic LF output, per-partition and package manifests | `i4_output.py` |
| R7 input/output/tool/run identity, reconciliation, unresolved-state evidence | `GOVERNED_INPUTS.json`, `RUN_RECORD.json`, `RECONCILIATION.jsonl`, `w2/unresolved.jsonl` |
| R8 runner identity in the run-level envelope | `i4_identity.py` (`runner_fingerprint()`) |

The runner contains **no** parsing, header-tolerance, field-mapping, numeric, flag, calendar,
identity, continuity, overlay, metric or serialization semantics. Every such transformation is
performed by `src/nse_engine/`, unmodified and fingerprinted.

---

## 2. Commands

```
python tools/i4_runner/i4_runner.py run     --legacy-root <dir> --udiff-root <dir> ...
python tools/i4_runner/i4_runner.py verify  --package <run dir>
python tools/i4_runner/i4_runner.py replay  --a <run dir> --b <run dir> [--verdict <file>]
```

Exit codes: `0` pass · `1` usage error · `2` governing failure (fail-closed).

### 2.1 Governed I4 run (Windows, operator command line)

```
python tools\i4_runner\i4_runner.py run ^
  --legacy-root "C:\IIPS_Data\NSE_Legacy_Acquisition\archives" ^
  --udiff-root  "C:\IIPS_Data\NSE_CM_UDiFF_10Y\archives" ^
  --inventory   evidence\inventory\file_inventory.json ^
  --labels      evidence\d04\DEC2_CAL_LABELS.json ^
  --d01-metrics evidence\d03\windows_run\FIX-SEM-DEF-01__metrics.csv ^
  --d01-verdict evidence\d03\windows_run\FIX-SEM-DEF-01__d01_definition_verdict.json ^
  --out         "D:\I4_RUNS\i4-<declared-token>" ^
  --run-id      "i4-<declared-token>" ^
  --expect-records 2462 ^
  --expect-inventory-lf-sha256 336b9531cd34f48e9a2e7e7593cc4e9c2736b3864d8213bc65d6ab8b488729d2 ^
  --expect-tool-fingerprint d3269b731008a0d544eaa7e96d6c6b75cf94dfd6ce31d8fb5e1f23fdf10a80e9 ^
  --expect-runner-fingerprint f3ebf62488716ea3f4fff76b104760dfee7df45c81af253a4faf352beb624c4a ^
  --min-free-bytes <bytes>
```

Notes.

* `--out` must be **new or empty** and outside both corpus roots; it is created if absent.
* `--run-id` is required and clock-free. The same id is used again when intentionally replaying
  the same declared configuration; a different id must not be used for a replay comparison.
* `--expect-*` arguments are optional declarations; when supplied, a mismatch is a Tier A
  preflight failure. `--expect-runner-fingerprint` pins the declared runner module set
  (`RUNNER_MODULES`, RD-3): any edit to those six modules invalidates the value, which is the
  intended behaviour — publish the new fingerprint with the new runner bytes. The values shown
  above are the G-I4-M1 revision's; the pre-revision values were
  `7bee84902f8cb0e5c60703acbe1b17d6e85a9b9762289bab1741d9f003df5a52` (engine) and
  `618bfd4c4919f3224a3e0f64682c21617c356580ebccd807f8abce528302c904` (runner, as reported by
  `i4_identity.runner_fingerprint()`; this README previously printed a stale value). `--expect-tool-fingerprint` detects a CRLF-converted or edited engine
  (a Windows checkout with `core.autocrlf=true` changes engine bytes while `git status` stays
  clean) and the CRLF-invariant `lf_sha256` basis is used for the inventory.
* Declared paths are never written into the package (RD-8, clock-free/path-free package). The
  corpus is identified by its archive-set digest, not by a path.

### 2.2 Verification

```
python tools\i4_runner\i4_runner.py verify --package "D:\I4_RUNS\i4-<declared-token>"
```

Checks the package manifest, every artifact hash, unlisted artifacts, partition manifests, the
completion marker, artifact classes and the recorded engine/runner identity.

### 2.3 Deterministic replay (MD-03 #11, MD-11 #7)

```
python tools\i4_runner\i4_runner.py run  ... --out "D:\I4_RUNS\i4-token-a" --run-id "i4-token"
python tools\i4_runner\i4_runner.py run  ... --out "D:\I4_RUNS\i4-token-b" --run-id "i4-token"
python tools\i4_runner\i4_runner.py replay --a "D:\I4_RUNS\i4-token-a" ^
                                           --b "D:\I4_RUNS\i4-token-b" ^
                                           --verdict "D:\I4_RUNS\i4-token-replay-verdict.json"
```

The comparison is total: no exclusion list is consulted (`provenance.run_id` is the only
declared run-metadata field, and it is identical in both runs by construction). A mismatch is
`REPLAY-FAILED` and is never normalised away. The verdict file must be written **outside** both
packages.

---

## 3. Package layout

```
<run root>/
  PREFLIGHT.jsonl                        tier A / tier G preflight checks
  INPUT_MANIFEST.jsonl                   one record per consumed member (R7)
  RECONCILIATION.jsonl                   every tier A / G / C / E comparison (RD-4)
  GOVERNED_INPUTS.json                   input identity + hashes + bases + tool identity
  RUN_RECORD.json                        run identity, counts, partitions, boundaries
  w2/calendar.jsonl                      derived output (calendars days)
  w2/associations.jsonl                  derived output (identities + dated associations)
  w2/identity_summary.json               derived output (association totals, unkeyed groups)
  w2/metrics.json                        derived output (row metrics + optional D01 fold)
  w2/unresolved.jsonl                    unresolved-state evidence (never resolved)
  partitions/<family>/<year>/rows/<stem>.rows.jsonl
  partitions/<family>/<year>/evidence/<stem>.evidence.json
  manifests/<family>_<year>.sha256       per-partition manifest
  PACKAGE_MANIFEST.sha256                every retained artifact except itself and the marker
  RUN_COMPLETE.json                      completion marker, written LAST (RD-9)
```

A failed run additionally retains `RUN_FAILED.json` and **no** completion marker. When the
failure happens during preflight, `PREFLIGHT.jsonl` still holds every check performed up to and
including the failing one (the count is echoed in `RUN_FAILED.json` as
`preflight_checks_retained`); the package remains incomplete by construction because
`RUN_COMPLETE.json` is absent.

**No-write failure cases (F5).** Nothing at all is written — not even failure evidence — when the
declared output root (a) lies inside a corpus root, (b) exists but is not a directory, or
(c) already contains entries. The condition is reported on stderr and the exit code is `2`. A
pre-existing directory is never adopted as a run root and is never modified; its contents are
left exactly as they were found.

---

`PACKAGE_MANIFEST.sha256` uses the `<sha256>  <path>` convention and is therefore compatible
with `sha256sum -c` on the run directory.

---

## 4. Reconciliation tiers (RD-4, as authorized)

| Tier | Meaning | Disposition |
|---|---|---|
| **A** | authoritative input/expectation: archive sha256, archive-set identity, one archive per date, single CSV member, member identity, family mapping, governed header shape, `expected_source_date` | **gating** — a divergence aborts the complete run |
| **G** | governing cross-checks (engine-recorded member hashes vs runner hashes; D01 header list vs the engine's header view; frozen verdict vs recomputed fold) | declared per check: `gating` or `non-gating` |
| **C** | definition-dependent D01 counters (`row_count`, `bad_rows`, `isin_count`, `symbol_count`, `series_counts`, `date_values`) | **non-gating**, always recorded |
| **E** | evidence-only observations (size corroboration, flag census) | **non-gating** |

There is no tolerance, no expected-divergence list, no filename-derived identity, no date-text
mapping rule and no change to W1/W2 semantics anywhere in the reconciliation path.

---

## 5. Failure policy (RD-9)

The first governing failure halts the run. No completion marker is written; the additional
artifact is `RUN_FAILED.json` naming the stage, condition and (where applicable) the failed
check, plus any artifact already written for the work that did happen (a failed preflight keeps
its partial `PREFLIGHT.jsonl`). A failed output root is never repaired, appended to or
re-labelled, and must be discarded before a re-run into a **new/empty** directory.

**Read-only custody.** If the declared output root lies inside a corpus root, the run fails
closed *without writing anything at all* — not even `RUN_FAILED.json` — because creating files
inside the corpus would violate the read-only custody of the source archives (D03). The
comparison is case-folding on case-insensitive filesystems, so a differently-cased spelling of
the same directory cannot defeat the gate (F4). The same no-write rule applies to a pre-existing
non-empty or non-directory output root (F5, §3).

Failure classes handled explicitly: missing archive · unexpected archive · archive hash mismatch
· malformed archive · missing CSV member · multiple CSV members · member identity failure ·
format/header failure · parser/canonical rejection · governed reconciliation failure · manifest
failure · output hash failure · package assembly failure · replay mismatch.

---

## 6. Operational notes

* **Memory (G-I4-M1-CORRECTIVE).** The runner retains no `CanonicalBuild` and no per-row object:
  each member is processed exactly once — its rows are written, fed to the engine's bounded-memory
  W2 composition (`nse_engine.w2_stream.W2Accumulator`), and released. Everything the accumulator
  keeps is exact and packed: one `array('I')` with seven uint32 per row, one row index per row, one
  index per identity, and **one interned copy of each distinct value** shared with the D01 metric
  fold (normalized ISIN and symbol tables), plus one `array('Q')` for the D01 symbol/series pairs.
  Measured retained state (synthetic corpora; `tests/test_w2_stream_memory.py`):

  | Shape | rows | identities | retained | bytes/row | bytes/identity |
  |---|---|---|---|---|---|
  | A repeated identities/observations | 200,000 | 2,000 | 8.0 MB | 40.2 | 4,019.8 |
  | B identity-dominated (corpus worst case) | 200,000 | 200,000 | 63.8 MB | 319.2 | 319.2 |
  | C mixed | 200,000 | 50,000 | 14.9 MB | 74.4 | 297.6 |

  Corpus-shape projection (the authoritative acceptance model, worst case = one distinct ISIN
  **and** symbol per row, rows = 5,689,949 D01-exact; runner allowance = the measured single-member
  transient at the corpus's largest member, 3,704 rows, ×1.5): **≈1.82 GB accumulator + ≈0.08 GB
  runner ≈ 1.90 GB ≤ 2.5 GB**. Any realistic identity profile is smaller; the unresolved item is
  the corpus's true distinct-identity count, which the accessible evidence does not contain (the
  equity master is GATED). The pre-corrective revision measured ≈760 B/row and projected ≈4.33 GB;
  the pre-streaming design retained ≈7.1 kB/row and projected ≈40 GB — the failure the failed
  Windows run exhibited. Per-member transients (one member's parse + serialization) are bounded by
  the largest member (≈70 MB at 3,704 rows) and are released before the next member is read.
  A runtime identity-count/memory gate remains a separate fail-closed execution safeguard, not a
  substitute for this acceptance evidence.* **Time.** Preflight reads every archive once (hash + structure) and processing reads each
  archive again (member bytes + drift hash): roughly two full corpus passes, plus parsing.
* **Corpus is read-only.** No code path opens a corpus file for writing; the D03 read-only
  guarantee is preserved.
* **No clock.** The runner uses no clock, randomness or environment value; preflight PF-03
  enforces this by scanning the declared runner modules, and the retained package contains no
  timestamp, hostname, absolute path or environment value.

---

## 7. Fingerprint bases and CRLF (F6)

`runner_fingerprint()` is defined over the **source-controlled canonical bytes** of the six
declared `RUNNER_MODULES`: each module is hashed as a git blob (name `\x00` length `\x00` bytes
`\x00`, modules sorted by name), exactly as the engine's own `tool_fingerprint()` is. It depends
on no environment, path, clock or host value.

Three independent per-module bases are recorded in the run evidence, so a transfer can always be
verified on a basis that is stable across platforms:

| Basis | Field | Behaviour under a CRLF worktree |
|---|---|---|
| raw bytes as checked out | `raw_sha256` | changes (raw bytes change) |
| **line-ending-normalised** | `lf_sha256` | **unchanged — CRLF-invariant** |
| git blob id | `git_blob_sha1` | equals the repository blob only while the checkout keeps the committed line endings |

Consequence for a Windows operator: with `core.autocrlf=true` the worktree bytes differ from the
committed bytes, so `runner_fingerprint()` (and `tool_fingerprint()` for the engine) differ, and
`--expect-runner-fingerprint` / `--expect-tool-fingerprint` fail closed at PF-02 / PF-01. This is
the intended detection, not a defect — the two supported resolutions are:

1. transfer/checkout the modules with their committed line endings (verify each file against the
   published `lf_sha256`, or against the blob id in a checkout that preserves line endings), or
2. omit that declaration and record the fingerprint actually observed on the host.

The fingerprint is never adapted to the environment: a CRLF-specific or host-specific variant
would defeat its purpose.
