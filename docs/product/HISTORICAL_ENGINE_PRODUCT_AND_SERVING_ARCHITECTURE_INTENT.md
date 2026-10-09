# I4 Historical Data Engine --- Target Product & Serving Architecture Intent

**Status:** Proposed / Targeted Architecture Intent\
**Date:** 2026-10-09\
**Scope:** Post-I5 serving, consumption, incremental ingestion, and
presentation direction\
**Authoritative implementation status:** Not authorized by this
document\
**Product type:** Single-user, personal-use application

------------------------------------------------------------------------

## 1. Purpose

This document preserves the intended product and architectural direction
for the I4 Historical Data Engine after completion of the initial
10-year historical baseline.

Its purpose is to prevent later implementation work from drifting away
from the agreed mental model.

This is a **target/intent artifact**, not an implementation
authorization and not a technology-selection decision.

Future implementation must still pass the applicable governance and
authority decisions.

------------------------------------------------------------------------

## 2. Product Scope & Non-Goals

### Product Scope

This is a **single-user, personal-use application**.

The product is intended for the owner's personal use to:

-   process and maintain NSE historical market-data archives;
-   expose the resulting canonical historical dataset for exploration
    and analysis;
-   provide a presentation/query experience based on the demonstrated I4
    application;
-   incrementally incorporate newly arriving archives without
    unnecessarily reprocessing the historical corpus;
-   expose provenance, identity, data-quality, reconciliation,
    determinism/replay, reports, and related evidence where supported by
    the underlying contracts.

### Explicit Non-Goals

Do **not** introduce any of the following unless a future scope decision
explicitly requires them:

-   authentication;
-   RBAC;
-   multi-user support;
-   PostgreSQL;
-   enterprise deployment architecture;
-   enterprise identity infrastructure;
-   tenant isolation;
-   organization/team administration;
-   enterprise-scale distributed architecture.

The application should remain appropriately simple for its
**single-user, personal-use** purpose.

**Important:** Technical complexity must not be introduced merely
because it is a common enterprise pattern.

------------------------------------------------------------------------

## 3. Initial 10-Year Baseline

The current I4 M2 run is treated conceptually as the **initial
historical baseline/backfill**.

The baseline consists of the already processed historical corpus,
including:

-   2,462 archives;
-   approximately 10 years of NSE historical coverage;
-   canonical processing;
-   identity/association information;
-   trading-calendar information;
-   reconciliation/evidence;
-   determinism/replay qualification;
-   durable evidence supporting the completed qualification.

The initial baseline should be generated once and then made available to
the future serving/query layer.

### Critical principle

The UI must **not** regenerate the entire 10-year corpus simply because
a user opens the application or performs a query.

The historical processing engine and the presentation/query layer are
separate concerns.

------------------------------------------------------------------------

## 4. Target High-Level Architecture

The intended conceptual architecture is:

``` text
                         INITIAL LOAD
                              │
                    2,462 historical archives
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ Historical Data Engine   │
                 │ Canonical Processing    │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ Authoritative Durable   │
                 │ Historical Dataset      │
                 └────────────┬────────────┘
                              │
                         Query / API
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ Presentation / UI       │
                 └─────────────────────────┘


                     FUTURE ARCHIVE ARRIVAL
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ Archive Discovery       │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ Identity / Fingerprint  │
                 │ / Deduplication         │
                 └────────────┬────────────┘
                              │
                     ┌────────┴─────────┐
                     │                  │
                Already seen         New / changed
                     │                  │
                     ▼                  ▼
                   Skip          Incremental Process
                                        │
                                        ▼
                              Validation / Evidence
                                        │
                                        ▼
                              Durable Publication
                                        │
                                        ▼
                                Query / API / UI
```

------------------------------------------------------------------------

## 5. Separation of Responsibilities

### Historical / Ingestion Engine

Responsible for:

-   archive discovery;
-   archive identity;
-   content fingerprinting;
-   duplicate detection;
-   determining whether processing is necessary;
-   canonical processing;
-   validation;
-   evidence generation;
-   incremental publication.

### Serving / Query Layer

Responsible for:

-   exposing the durable canonical dataset;
-   query/filter operations;
-   retrieving canonical records;
-   exposing provenance and quality information;
-   serving data to the UI;
-   supporting reports and exploration.

### Presentation / UI

Responsible for:

-   visualization;
-   navigation;
-   filtering/query construction;
-   displaying results;
-   displaying status and evidence;
-   presenting reports;
-   user interaction.

### Critical boundary

**The UI must not become the historical processing engine.**

The UI may expose an operation such as "Process New Archives" in the
future, but the actual discovery, qualification, processing, and durable
publication belong to the ingestion/engine side.

------------------------------------------------------------------------

## 6. Incremental Processing Model

Future archive arrival should follow this conceptual flow:

``` text
New archive arrives
       │
       ▼
Archive discovery
       │
       ▼
Identity + content fingerprint
       │
       ├────────────── Already processed ──────────────► SKIP
       │
       ▼
New / changed archive
       │
       ▼
Canonical processing
       │
       ▼
Validation / evidence
       │
       ▼
Durable publication
       │
       ▼
Dataset/index update
       │
       ▼
UI automatically sees available data
```

### Existing archives

Existing archives should **not be regenerated unnecessarily**.

The system should recognize an archive that has already been
successfully processed.

### Duplicate handling

If the same archive is encountered again, it should be recognized using
the applicable identity/content contract rather than blindly creating
duplicate data.

### Changed content

If an archive with the same apparent identity has different content, it
must **not** be silently treated as an ordinary duplicate.

The precise disposition for changed content remains a future
contract/governance question. Possible outcomes could include explicit
conflict, reprocessing, replacement/versioning, or quarantine, but this
document does not select one.

------------------------------------------------------------------------

## 7. Processing Contract / Version Awareness

Archive identity alone may not be sufficient forever.

Future incremental processing should consider whether an already
processed archive was processed under the applicable:

-   engine version;
-   canonical contract;
-   processing rules;
-   evidence contract;
-   other governing qualification/version identifiers.

A future implementation must not silently assume that "seen before"
always means "permanently valid under every future contract."

The exact requalification/versioning policy is intentionally left for a
future authority decision.

------------------------------------------------------------------------

## 8. Serving Model

The intended serving model is:

``` text
Durable canonical dataset
          │
          ▼
     Query / API
          │
     ┌────┴────┐
     │         │
     ▼         ▼
    UI       Reports
```

The API/query layer should be a **consumer of the durable dataset**, not
the owner of historical computation.

Queries should not cause a full historical reprocessing run.

------------------------------------------------------------------------

## 9. Presentation / UI Target

The supplied I4 application mockups establish the target presentation
direction.

The future presentation layer should remain **close to the demonstrated
application** rather than being redesigned into an unrelated product.

### Dashboard direction

The demonstrated dashboard establishes concepts including:

-   10-Year NSE Historical Data;
-   run identity and completion status;
-   archive count;
-   canonical row count;
-   identity-record count;
-   trading-calendar count;
-   error count;
-   rows by year;
-   archives by exchange segment;
-   data coverage;
-   archive inventory;
-   archive details;
-   canonical data access;
-   identity/association access;
-   calendar-overlay access;
-   reconciliation access;
-   engine logs;
-   processing/run status.

### Data Explorer direction

The demonstrated Data Explorer establishes concepts including:

-   dataset selection;
-   date-range query;
-   instrument selection;
-   segment;
-   series/market type;
-   trading status;
-   exchange segment;
-   optional filters;
-   quick filters;
-   query results;
-   saved queries;
-   query history;
-   canonical-record details;
-   source evidence;
-   related records;
-   data-quality status;
-   provenance;
-   source archive;
-   source row;
-   archive path;
-   raw record access;
-   archive access;
-   reconciliation access;
-   price/chart views;
-   yearly summaries;
-   data-quality summaries.

These are **presentation/product reference points**, not a claim that
every element is already contractually defined for the future serving
layer.

------------------------------------------------------------------------

## 10. Data Flow Principle

The preferred conceptual separation is:

``` text
                    WRITE / INGEST PATH

New archives
    │
    ▼
Discovery
    │
    ▼
Identity / Deduplication
    │
    ▼
Historical Engine
    │
    ▼
Validation / Evidence
    │
    ▼
Durable Dataset
    │
    └──────────────────────────┐
                               │
                               ▼
                         READ / SERVE PATH
                               │
                         Query / API
                               │
                         ┌─────┴─────┐
                         ▼           ▼
                        UI         Reports
```

This separation should be preserved even if the eventual application
runs locally as a single-user application.

------------------------------------------------------------------------

## 11. What Must Not Be Assumed Yet

This document intentionally does **not** decide:

-   concrete persistence technology;
-   database product;
-   storage engine;
-   API framework;
-   hosting model;
-   deployment model;
-   ingestion scheduler;
-   archive-watcher mechanism;
-   changed-archive resolution policy;
-   requalification/version migration policy;
-   exact API endpoints;
-   exact query schema;
-   exact UI implementation technology.

Those require future investigation and explicit authority where
applicable.

In particular, **PostgreSQL is not a target requirement**.

------------------------------------------------------------------------

## 12. Single-User Simplicity Principle

Because this is a personal-use application, future architecture should
prefer the simplest design that satisfies:

-   durability;
-   correctness;
-   deterministic processing;
-   incremental updates;
-   queryability;
-   provenance;
-   evidence;
-   reliability;
-   the demonstrated UI experience.

Do not introduce enterprise infrastructure merely because it is familiar
or conventional.

The architecture should remain proportionate to the product's actual
scope.

------------------------------------------------------------------------

## 13. Relationship to I5

I5 is already closed as the formal 10-year qualification determination.

This document does **not** reopen I5.

The 10-year corpus processing is already complete and qualified.

The target described here concerns the **future consumption, serving,
incremental-ingestion, and presentation architecture built on top of
that qualified baseline**.

No I5 rerun is implied.

------------------------------------------------------------------------

## 14. Future Questions That Must Be Answered Before Implementation

When the post-I5 serving/consumption phase is formally authorized, the
following should be explicitly resolved:

1.  What is the authoritative durable serving dataset?
2.  What persistence mechanism is appropriate for a single-user personal
    application?
3.  What is the canonical archive identity/fingerprint contract?
4.  How are new archives discovered?
5.  How is a changed archive handled?
6.  How is processing/version compatibility determined?
7.  What constitutes successful incremental publication?
8.  What API/query contract exposes canonical data?
9.  Which UI operations are read-only versus processing operations?
10. How are provenance and evidence exposed?
11. How are incremental failures and partial publication handled?
12. What backup/recovery expectations apply to the personal-use dataset?
13. What exact subset of the demonstrated UI becomes the first serving
    release?

These questions should be answered from the existing engine
contracts/evidence where possible rather than reinvented.

------------------------------------------------------------------------

## 15. Non-Drift Rules

Future work should preserve these principles unless an explicit future
decision changes them:

1.  **10-year backfill is a baseline operation, not a recurring UI
    operation.**
2.  **Do not reprocess existing archives unnecessarily.**
3.  **Process genuinely new archives incrementally.**
4.  **Use archive identity/content fingerprinting for duplicate
    recognition.**
5.  **Do not silently accept changed content as a duplicate.**
6.  **Keep ingestion/processing separate from presentation.**
7.  **UI reads through the serving/query layer.**
8.  **Serving reads from authoritative durable data.**
9.  **Do not introduce authentication, RBAC, multi-user support,
    PostgreSQL, or enterprise architecture without explicit scope
    authorization.**
10. **Do not invent an M/N gate or other future gate merely from this
    document.**
11. **Do not treat this intent artifact as implementation authority.**
12. **Preserve the demonstrated I4 UI/application model as the target
    presentation reference.**
13. **Do not reopen or rerun I5.**
14. **Any material architectural deviation requires an explicit future
    decision and durable record.**

------------------------------------------------------------------------

## 16. Intended Lifecycle

The target product lifecycle is:

``` text
I4 historical processing
        │
        ▼
10-year qualified baseline
        │
        ▼
Future serving / consumption authority
        │
        ├──────────────────────┐
        │                      │
        ▼                      ▼
Initial dataset serving   Incremental ingestion
        │                      │
        ▼                      ▼
       UI              New archives only
        │                      │
        └──────────┬───────────┘
                   ▼
          Continuously usable
          personal historical
             data application
```

The future serving/consumption phase should build on the existing
qualified baseline rather than repeating the baseline-generation
process.

------------------------------------------------------------------------

## 17. Status of This Artifact

**This document is a target/intent record only.**

It is intended to preserve product expectations and prevent
architectural drift.

It does **not**:

-   authorize implementation;
-   select technology;
-   establish a persistence authority;
-   establish an API authority;
-   establish a UI implementation gate;
-   reopen I5;
-   authorize production deployment.

A future governance decision should explicitly adopt, modify, or
supersede this intent before substantive post-I5 implementation begins.
