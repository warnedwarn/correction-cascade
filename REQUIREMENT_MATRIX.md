# Requirement matrix

| Requirement | Code path | Targeted proof | Status |
|---|---|---|---|
| Unique normalized cascade IDs | `ident`, `open_cascade` | duplicate-ID test | PASS |
| Distinct HTTPS evidence slots | `https_url`, `open_cascade` | duplicate-slot test | PASS |
| Frozen acyclic dependency topology | `clean_edges` | cycle rejection test | PASS |
| Every round independently refetches all nodes | `_observe` | strict web mocks and digest assertions | PASS |
| All state-driving statuses validator-bound | strict equality over rows and digests | forged status and digest test | PASS |
| Frontier derived outside the model | `_derive` | partial-frontier test | PASS |
| Permissionless progress with bounded exhaustion | `check_propagation` | complete and exhausted tests | PASS |
| Unreadable evidence cannot become complete | `check_propagation` | inconclusive test | PASS |
| Cancellation and replay boundaries | `cancel_unchecked`, `check_propagation` | authorization and terminal replay tests | PASS |
| Live deployment and transaction | pending deployment | StudioNet receipt | UNVERIFIED |
