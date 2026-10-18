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

## StudioNet record

- Contract: [`0x652b02682f2f980AecA42aa0B3aAfb6F2cAbB5E6`](https://explorer-studio.genlayer.com/address/0x652b02682f2f980AecA42aa0B3aAfb6F2cAbB5E6)
- Reviewed source: [`7e7ccf4`](https://github.com/warnedwarn/correction-cascade/tree/7e7ccf4401d9df43c40627269a77b9c7d5a63135)
- Deployment: [`0x91d5...a4bf`](https://explorer-studio.genlayer.com/transactions/0x91d5942ec90b5e606fdbe6702bc6ea9439125259c5b2ae9797ebccea3e47a4bf)
- Open cascade: [`0xe83c...794f`](https://explorer-studio.genlayer.com/transactions/0xe83c65f8d4fbd20eba7f15cc2e894c412aa935fb83aa97ace0d9a9f1e2a5794f)
- Check propagation: [`0x01e0...b3c6`](https://explorer-studio.genlayer.com/transactions/0x01e0a6cded28234709f3fd50baed0f71b2b39918a0669d4489292382648bb3c6)
- Live record: `CASCADE-1792287556`, terminal state `COMPLETE`

The deployment and both workflow transactions reached `FINALIZED / MAJORITY_AGREE / SUCCESS`. The deployed contract bytes match the reviewed source SHA-256. The correction and publication pages are operator-authored fixtures used to demonstrate the mechanism, not independent newsroom records.
