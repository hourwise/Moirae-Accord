# ACCORD-02E-R3 — Claim Audit

| Claim pattern | Classification | Finding |
|---|---|---|
| JSON Schemas close object shapes and discriminated variants | Normative/engineering claim | Supported for the inspected schemas; cross-record properties still need rules. |
| R3 supplies a self-contained validation scope | Normative claim | Not established; active profile and schema-contract resolution is incomplete. |
| External verifier needs no Accord-private state | Design limitation/target | Not supported until the missing scope records are supplied. |
| Unknown extensions cannot strengthen results | Normative limitation | Supported conditional on a resolved extension registry. |
| Normalization precedes truth comparison | Normative scoring rule | Supported by the declared pipeline; not empirically executed. |
| Two implementations will agree | Future interoperability hypothesis | Not demonstrated by static review. |
| Evidence proves external truth | Prohibited overclaim | Not made and not implied by this review. |
| `VERIFIED` means universal truth or exactly-once effect | Prohibited overclaim | Not permitted by A/C mapping. |
| Authority validity proves occurrence, or occurrence proves authority | Prohibited overclaim | Orthogonality preserved. |
| Passing conformance vectors proves research benefit | Prohibited empirical claim | Not made. |
| Scenario IDs are opaque to expected results | Experimental requirement | Still partly declarative; the catalog flag is not a proof of semantic opacity. |

The review therefore does not claim empirical interoperability, provider trust,
ground truth, exactly-once effects, complete mediation, or research success.
