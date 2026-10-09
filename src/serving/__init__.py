"""First-release serving layer — initial vertical slice (D24, under D23 authority).

Read-only consumer of the qualified M2 baseline (D16-07 durable state class (1)).

Boundary (D16-09, D23 §§8/10/11/12):

* serving is a read-only consumer of the baseline; it never invokes or schedules
  historical processing and never treats derived state as a source of truth;
* the engine remains the owner of the write path;
* serving state is durable class (4) — always a pure derivation of the baseline,
  rebuildable at any time; deleting it is never a data event (D16-07);
* this slice implements exactly one query category: Q3 instrument query (D16-10),
  with row-level D05 §8 provenance, over a deterministic, rebuildable read model.

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
from .query import QUERY_ID, QueryError, partitions_listing, query_instrument
from .rebuild import rebuild_state

__all__ = [
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
    "QueryError",
    "partitions_listing",
    "query_instrument",
    "rebuild_state",
]
