# D09 — BOUNDED-MEMORY W2 REVISION: ENGINE RETAINED-STATE RECORD (G-I4-M1-CORRECTIVE)

**Status:** implemented in the engine and runner (Arena branch, non-production). This note records
the retained-state representation and the memory acceptance evidence for the corrective revision.
It does not itself execute anything, does not authorize a corpus run, and does not select a storage
technology.

## 1. What changed and why

The failed Windows corpus attempt (`G:\My Engines\I4_RUNS\i4-20261007`, preserved untouched)
exhausted memory because the runner retained every member's `CanonicalBuild` (≈7.1 kB per canonical
row, ≈40 GB projected at 5,689,949 rows). The first bounded-memory revision removed that retention
but its accumulator still used object-per-identity state (≈760 B/row, ≈4.33 GB projected), which
exceeded the ≤2.5 GB acceptance ceiling. This corrective revision compacts the retained state.

## 2. Retained state (representation only — no semantic change)

| Structure | Purpose | Cost |
|---|---|---|
| `AssociationAccumulator._data` — one `array('I')` | packed rows: `YYYYMMDD` date, line, symbol id, series id, member id, validity id, verbatim-symbol exception id | 28 B/row |
| `AssociationAccumulator._next` — one `array('i')` | next-row link of the identity's intrusive list (arrival order restored on reconstruction) | 4 B/row |
| `AssociationAccumulator._head` — one `array('i')` | first row of each identity (`-1` = keyed rows exist only in excluded/unkeyed contexts) | 4 B/identity |
| `RowTokens.isin` — intern of normalized ISINs | **is** the identity key space and the D01 `distinct_nonblank_isin` source | ≈116 B/identity |
| `RowTokens.symbol` + `raw_symbol` | symbol tokens; a verbatim symbol is stored only when it differs from its normalized form | ≈100 B/identity |
| `RowMetricAccumulator._pairs` — `Uint64Set` (`array('Q')`) | D01 `distinct_symbol_series_pairs` as `(symbol_id, series_id)` key | ≈16 B/pair worst case, 0 for repeated pairs |

Every quantity that was removed or compressed was proven unnecessary to the governed output before
removal: the per-identity `array` object (one per identity) and the four duplicate string tables are
representation, not information — the identity documents, association runs, intervals, provenance
dedup, unkeyed groups, overlay accounting and D01 metric values are all byte-identical to the
pre-revision engine modulo the fingerprint field (§4).

Exactness is preserved: `Uint64Set` stores the full 64-bit key and compares it on probe (no
probabilistic membership, no collision-based false positives); the D01 distinct counts are lengths
and counters of the shared intern tables; every metric name, definition, normalization and
distinct-value rule is unchanged.

## 3. Measured retained state (synthetic corpora; no corpus access)

`tracemalloc`/`sys.getsizeof` over the accumulator; `resource.getrusage` for RSS; one shape per
process so each RSS figure belongs to that phase.

| Shape | rows | identities | retained | bytes/row | bytes/identity | peak traced |
|---|---|---|---|---|---|---|
| A — repeated identities/observations | 200,000 | 2,000 | 8.0 MB | 40.2 | 4,019.8 | 137.5 MB |
| B — identity-dominated (one ISIN and symbol per row) | 200,000 | 200,000 | 63.8 MB | 319.2 | 319.2 | 70.9 MB |
| B — identity-dominated, scaling control | 1,000,000 | 1,000,000 | 295.5 MB | 295.5 | 295.5 | 312.0 MB |
| C — mixed | 200,000 | 50,000 | 14.9 MB | 74.4 | 297.6 | 19.8 MB |

The per-row cost **falls** with scale (319.2 → 295.5 B/row), so the projection below uses the
smaller-scale, higher value.

## 4. Acceptance projection (worst case, explicit model)

* rows = 5,689,949 (D01 exact); members = 2,462; rows/member 1,660–3,704 (mean 2,311);
* identity profile = **worst case**: one distinct ISIN and one distinct symbol per row — the maximum
  any corpus can reach, so the model does not depend on the unresolved real profile;
* accumulator = 319.2 B/row × 5,689,949 = **1.82 GB**;
* runner allowance = measured single-member transient at the corpus's largest member (3,704 rows,
  ≈70 MB) × 1.5 safety = **≈0.08 GB** (bounded per member, released before the next member);
* **total ≈ 1.90 GB ≤ 2.5 GB.**

At the 1M-row measured constant (295.5 B/row) the projection is ≈1.76 GB. Any realistic identity
profile is smaller than the worst case; the sensitivity table in
`tests/test_w2_stream_memory.py` records the fall-off.

## 5. Unresolved evidence (recorded, not resolved)

The corpus-wide distinct-identity count is **not** available from the accessible evidence: the
per-file D01 metrics give only per-file distinct counts (summing them yields 5,686,592, an upper
bound that counts a security once per file), and the equity security master is `GATED`
(`FIX-SECMASTER-01`). The acceptance model therefore uses the worst case rather than an assumed
count. A runtime identity-count/memory preflight gate for a future execution is a separate
fail-closed safeguard; it is not a substitute for this evidence and is not implemented here.
