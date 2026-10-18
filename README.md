# Correction Cascade

## Propagation map

A correction can reach the original article and still fail everywhere readers actually encounter the claim. Correction Cascade freezes that publication topology before checking it.

The owner records one canonical correction, two to eight named publication URLs, their dependency edges, and a bounded number of observation rounds. Any caller may trigger a round. GenLayer validators fetch the correction and every publication, bind all byte digests, and classify each node as `INCORPORATED`, `STALE`, or `UNREADABLE`.

Contract code then finds the stale frontier: stale nodes that do not sit below another stale node. That boundary identifies where propagation first broke. The model cannot edit the graph, select the frontier, or declare completion.

Each round is retained with its source digests, status vector, stale indexes, and frontier. The cascade closes `COMPLETE` only when every node incorporates the correction. It becomes `EXHAUSTED` when the check budget ends without complete propagation. An unreadable node is recorded as `INCONCLUSIVE`, never silently treated as corrected.

Checks are permissionless so a missing owner cannot stop observation. The owner may cancel only before the first check.

## Local verification

```text
python -m pytest -q
set PYTHONUTF8=1
genvm-lint contracts/contract.py
```

The direct suite covers partial and complete rounds, deterministic frontier calculation, exhausted and unreadable outcomes, cycle rejection, duplicate IDs and source slots, cancellation authorization, terminal replay, and forged validator output.
