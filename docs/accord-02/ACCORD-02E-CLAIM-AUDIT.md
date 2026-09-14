# ACCORD-02E — Claim Audit

This audit classifies material claims in ACCORD-02A/B/C/D. It does not reopen
broad prior-art research and does not authorize any novelty conclusion.

## 1. Claim classes

| Claim family | Classification | Review result |
| --- | --- | --- |
| Linked-record identities and retry identity rules | Normative definition | Supported by A and reused by B/C/D. |
| Transport metadata is non-authoritative | Normative definition | Repeated consistently across A/B/C/D. |
| Authority validity and effect occurrence are orthogonal | Normative definition | Explicitly required by B/C/D. |
| Attenuation is component-wise and does not imply effective containment | Normative definition | Supported by B; composition remains profile-dependent. |
| Dispatch/transport acceptance/provider acceptance do not prove arbitrary downstream effect | Normative definition | Supported by A/C and tested by D scenarios. |
| Negative evidence requires explicit completeness | Normative definition | Supported by C and D. |
| Retry count is not logical-effect count | Normative definition | Supported by A/C/D. |
| Staged predicates are distinct | Normative definition | Supported by C; cross-schema binding remains ambiguous. |
| Evidence classes have no universal authority | Normative definition | Supported by A/C. |
| A verifier can operate from portable supplied inputs | Engineering contract/hypothesis | A/C define the intended contract; D must still remove catalog leakage. |
| Stronger evidence affordances improve the trade-off | Empirical hypothesis | Not demonstrated; H-EFFECT-2 only. |
| Accord improves false-confirmation/indeterminacy/duplicate trade-offs | Empirical hypothesis | Not demonstrated; H-BASELINE-1 only. |
| Multi-hop/sibling attenuation bounds effective authority under declared profiles | Empirical hypothesis | Not demonstrated; H-AUTH-2/H-AUTH-3 only. |
| Delegate assertion resistance | Empirical hypothesis | Testable by D, not an existing result. |
| External verifiability fraction | Empirical outcome | Must be measured in a future scored experiment. |
| A2A/MCP interoperability | Conformance target | Not evidence of settlement or authority. |
| `VERIFIED` and `CORROBORATED` labels | Normative A result vocabulary | Must not be silently equated with C `EFFECT_SUPPORTED`; see `E2E-MAJOR-001`. |
| `NO_EFFECT_OBSERVED` | Qualified observation label | Must not be silently equated with profile-bounded C non-occurrence; see `E2E-MAJOR-001`. |
| Exactly-once external effects | Explicit non-goal | Correctly prohibited. |
| Universal effect truth or perfect authority containment | Explicit non-goal | Correctly prohibited. |
| Distributed consensus or complete mediation | Explicit non-goal | Correctly prohibited. |
| Novelty of attenuated credentials, durable execution, receipts, or idempotency | Prior-art boundary | Not claimed by ACCORD-02E. |

## 2. Wording that needs containment

### `VERIFIED`

ACCORD-02A uses `VERIFIED` and `CORROBORATED` as result kinds, while
ACCORD-02C replaces a single overloaded success field with occurrence,
attribution, causality, freshness, duplication, completeness, sufficiency, and
profile compatibility axes. Without a normative translation, a future reader
could treat A `VERIFIED` as universal truth or as a direct synonym for C
`EFFECT_SUPPORTED`. The review records this as `E2E-MAJOR-001`.

### `AUTHORIZED`

ACCORD-02B defines an authority relation and an effective-authority analysis;
it explicitly does not authorize dispatch. ACCORD-02C/D include authority
validity statuses such as `AUTHORIZED` and `INVALID_AUTHORITY`. These labels must
identify their source and evaluation time rather than being inferred from
`ATTENUATED` or `CONTAINED`. The review records this as `E2E-MAJOR-002`.

### `independent` and `corroborated`

The prose correctly treats observer distinction, operator relationship, process
boundary, trust root, and causal independence as separate properties. No claim
that observer-distinct evidence proves non-collusion is made. This is a
non-issue, provided the future experiment retains the full property vector.

### `final` and `terminal`

ACCORD-02C correctly scopes finality to a profile, interval, and proposition.
`UNKNOWN_TERMINAL` in A is not automatically irreversible under C reopening
semantics. The missing label mapping remains a schema issue, not a claim that
terminal unknown is final truth.

### `idempotent` and `exactly-once`

The stack consistently distinguishes idempotent request handling from exactly-once
external occurrence. No exactly-once result is authorized without evidence.

## 3. Prior-art boundary

ACCORD-02E preserves the ACCORD-01 prior-art boundary. It does not claim novelty
for:

- attenuated delegated credentials or subsumption;
- finite delegation depth or bounded lifetime;
- idempotent retries;
- durable execution and reconciliation;
- transaction in-doubt states;
- signed receipts;
- portable action certificates;
- evidence classes or provider observations by themselves.

The proposed contribution remains a future empirical/system interaction among
authority binding, effect identity, evidence affordances, external verification,
composition, uncertainty, and realistic delegate behaviour. No novelty finding
is authorized by this review.

## 4. Claim conclusion

No existing empirical result was found in A–D. The material overclaim risk is
concentrated in vocabulary translation and the D scenario-catalog oracle
boundary, not in a claim that experiments have already demonstrated a benefit.
