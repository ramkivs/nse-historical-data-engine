"""First-release serving layer — initial vertical slice (D24, under D23 authority).

Read-only consumer of the qualified M2 baseline (D16-07 durable state class (1)).

Boundary (D16-09, D23 §§8/10/11/12):

* serving is a read-only consumer of the baseline; it never invokes or schedules
  historical processing and never treats derived state as a source of truth;
* the engine remains the owner of the write path;
* serving state is durable class (4) — always a pure derivation of the baseline,
  rebuildable at any time; deleting it is never a data event (D16-07);
* this slice implements the Q1 dataset/partition summaries, the Q2 date-range
  query, the Q3 instrument query (D16-10), the Q9 archive inventory query
  (per-archive INPUT_MANIFEST + D01 facts with the explicit M2-only registry
  absence), the Q7 record-detail query (one canonical row plus its archive
  and reconciliation facts), and the Q8 data-quality views (flag censuses,
  quarantine count, unresolved-state records, reconciliation aggregates,
  and the explicit D21 CHANGED absence), each with row-level D05 §8
  provenance where rows are served, over a deterministic, rebuildable read model.

Technology (D23 §13 delegated selection, recorded in the D24 implementation record):
Python 3 standard library only; a plain canonical-JSON index file on local disk;
in-process streaming query; CLI consumer. No database server, no network listener,
no authentication, no multi-user architecture.

Nothing in this package mutates the baseline, reinterprets canonical rows, selects
any technology beyond the recorded class-(4) file, or implements any other query
category, the processing trigger, or any changed-content mechanism (D21/D23).
"""

from .baseline import (
    Baseline,
    BaselineError,
    BaselineSpec,
    DEFAULT_M2_SPEC,
    open_baseline,
)
from .index import (
    ServingIndexError,
    build_index,
    index_state,
    load_index,
    write_index,
)
from .archive import (
    ARCHIVE_QUERY_ID,
    D01_INVENTORY_PATH,
    D01_INVENTORY_RECORD_COUNT,
    D01_INVENTORY_SHA256,
    D01InventoryError,
    load_d01_inventory,
    parse_input_manifest,
    query_archive_inventory,
)
from .detail import (
    RECORD_DETAIL_QUERY_ID,
    parse_reconciliation,
    query_record_detail,
)
from .quality import (
    DATA_QUALITY_QUERY_ID,
    parse_unresolved,
    query_data_quality,
)
from .query import (
    DATE_RANGE_QUERY_ID,
    DATASET_QUERY_ID,
    QUERY_ID,
    QueryError,
    partitions_listing,
    query_date_range,
    query_dataset_summary,
    query_instrument,
)
from .rebuild import rebuild_state

__all__ = [
    "ARCHIVE_QUERY_ID",
    "D01_INVENTORY_PATH",
    "D01_INVENTORY_RECORD_COUNT",
    "D01_INVENTORY_SHA256",
    "D01InventoryError",
    "load_d01_inventory",
    "parse_input_manifest",
    "query_archive_inventory",
    "RECORD_DETAIL_QUERY_ID",
    "parse_reconciliation",
    "query_record_detail",
    "DATA_QUALITY_QUERY_ID",
    "parse_unresolved",
    "query_data_quality",
    "Baseline",
    "BaselineError",
    "BaselineSpec",
    "DEFAULT_M2_SPEC",
    "open_baseline",
    "ServingIndexError",
    "build_index",
    "index_state",
    "load_index",
    "write_index",
    "QUERY_ID",
    "DATASET_QUERY_ID",
    "DATE_RANGE_QUERY_ID",
    "QueryError",
    "partitions_listing",
    "query_instrument",
    "query_dataset_summary",
    "query_date_range",
    "rebuild_state",
]
