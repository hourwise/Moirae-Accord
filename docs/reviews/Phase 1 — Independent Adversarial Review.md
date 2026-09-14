Phase 1 — Independent Adversarial Review
0. Method and what I actually tested

I treated the brief as two separable hypotheses joined by an assertion of unity, and attacked each independently:

H-AUTH: a child never gains more authority than its parent.
H-EFFECT: a task is never reported complete until effects are independently evidenced or classified UNKNOWN.

My test for whether these are one problem: can each be falsified without the other? They can. H-AUTH is falsifiable by model-checking a derivation relation with zero external effects. H-EFFECT is falsifiable with a single agent, a single tool, and no delegation at all. Two independent falsifiers means two hypotheses. I return to this in §3.

1. Is the claimed problem real?

Partly yes, and the evidence is stronger than the brief claims — but only for one half.

False completion is empirically documented and large. From Confident Closing to Silent Failure (arXiv 2606.09863) measures 9,876 tau2-bench trajectories across 8 model families and 1,879 AppWorld trajectories: agent claims of completion contradicted by environment ground truth account for 45–48% of all failures in single-control domains and 75.8% of failures in AppWorld coding trajectories. That is a real, measured, expensive failure mode. The brief understates its own strongest evidence by not citing anything like this.

But the same paper contains the finding most dangerous to this project: in the dual-control telecom domain, where an independent simulator can observe state, false success collapses to 3%. And a TF-IDF detector reaches 0.83–0.95 AUROC at ~3,300× lower latency than an LLM judge. Two implications:

Independent state observation is the mechanism that works — which supports the premise.
Most of the available benefit appears to be reachable by reading the environment and a cheap classifier. Not by a control plane.

Privilege escalation across agent delegation is also real but is a predicted risk with far thinner incident evidence than false completion, and it is the half with the most mature countermeasures.

Finding: the problem is real. The two halves are not equally real, not equally open, and not equally hard.

2. Prior art
2.1 Monotonic child authority / capability attenuation — ALREADY_SOLVED
Layer	Status
Theory	Solved since Dennis & Van Horn (1966); Miller, Robust Composition (2006); Capability Myths Demolished (2003)
Mechanism	Solved: macaroons (2014), Biscuit (public-key offline attenuation), UCAN, SPKI/SDSI, ZCAP-LD
Agent-specific standardisation	In flight and explicit: draft-niyikiza-oauth-attenuating-agent-tokens-01 defines Invariant I4, Capability Monotonicity — "a derived token MUST NOT authorize tools that the parent did not authorize" — with deterministic subsumption rules over typed constraints (exact, range, one_of, subset, …) and offline chain verification from the root trust anchor alone. Also draft-araut-oauth-transaction-tokens-for-agents, draft-liu-oauth-chain-delegation, RFC 8693 act, RFC 9396 RAR. OAuth Identity Chaining reached Proposed Standard in 2026.
Recent academic	Bounded Agents (2608.15888) proves Blast Radius Monotonicity and Composition Soundness, evaluated on 3,154 instances across InjecAgent/AgentDojo/ASB. Five-Plane Reference Architecture (2606.12320) implements "composite principals with capability attenuation" and reports "attenuation correctness and evidence reconstructability hold on every trial." AgentFlow (2608.22868) proves privilege-escalation resistance and delegation safety over a label lattice. Overlaying Governance (2606.03518) handles recursive delegation chains with resource-scope attenuation.

In 2026, "a child never gains more authority than its parent" is a conformance test, not a research contribution. At depth 1 with one child, it is an afternoon of property-based testing.

What genuinely remains open in this area — and the v0.1 constraints delete all of it:

Aggregation/composition: two individually-valid attenuated grants combining into effective authority neither parent intended. Bounded Agents addresses this only "under a complete restriction set and serialized admission," which is a strong and unrealistic assumption. OPEN_PROBLEM.
Cross-vocabulary subsumption: deciding ⊑ when parent and child express scope in different resource models. OPEN_PROBLEM.
Revocation propagation through a chain with offline verifiers. Explicitly out of scope in the IETF draft. OPEN_PROBLEM.
Non-monotonic dimensions — budget, quota, rate — across concurrent siblings. This is distributed counting, not a partial order. PARTIALLY_SOLVED.
2.2 UNKNOWN — TERMINOLOGY_DIFFERENCE / ALREADY_SOLVED

The in-doubt state is X/Open XA, circa 1991, formalised in Gray & Reuter (1993), including the full vocabulary of heuristic-commit, heuristic-rollback, heuristic-mixed, heuristic-hazard. The underlying impossibility is older: Two Generals (Akkoyunlu et al., 1975) and FLP (1985). A2A itself carries TASK_STATE_UNSPECIFIED described as "unknown or indeterminate."

There is nothing novel about a three-valued outcome. See §4.6 for what is potentially novel about it.

2.3 Durable execution, reconciliation, crash-after-effect — ALREADY_SOLVED (single-host)

Temporal, Restate, DBOS, Cadence, Step Functions, Durable Functions. Every one of them journals steps before the result is observed, replays completed steps, and documents the exact residual honestly: "Neither DBOS nor Temporal gives you exactly-once against arbitrary external APIs — that still requires idempotency keys on your side." The crash-after-effect-before-journal window is textbook, not frontier. Rebuilding it single-host is engineering.

Critically: durable execution engines treat the activity's return value as truth. A Temporal activity that returns ok is believed. That is exactly the gap — and it is closed by a wrapper pattern ("re-read the effect surface instead of trusting the return"), not by a platform.

2.4 Effect receipts and evidence — PARTIALLY_SOLVED, crowded
Notarized Agents (2606.04193): receiver-attested receipts, HPKE-encrypted to the owner, published to witness-cosigned Merkle logs, bound to the authorization token. This is substantially the same idea, already built, and it names its own open residue precisely: suppression attack, service collusion, adoption incentive.
draft-marques-asqav-compliance-receipts-06, draft-chueayen-attestation-receipts-00.
AP2 (donated to FIDO Alliance, April 2026): SD-JWT Verifiable Credential Mandates binding human intent → agent → cart → settlement, verifiable without trusting the issuer.
RAILS (2606.08790): "no financially material settlement is supported by evidence below the obligation's admissibility floor" — an admissibility-graded verification model with a formal Clearing Decision. This is the brief's H-EFFECT, with better vocabulary, in the commerce vertical.
TessPay (2602.00213): verify-then-pay.
2.5 Governance control planes — ALREADY_SOLVED as a genre

Five-Plane (2606.12320), Proof-Carrying Agent Actions (2606.04104, action certificates binding envelope + runtime/approval receipts + replay proof, with an explicit outcome closure checkpoint and externality-awareness), Sovereign Execution Broker (2606.20520), Deterministic Control Plane for LLM Coding Agents (2606.26924), Deontic Policies (2606.19464), Authenticated Workflows (2602.10465). Plus commercial: Auth0 for GenAI, Descope, Arcade, WorkOS, Scalekit, Snowflake Agentic Control Plane.

"A new agent control plane" has approximately zero differentiation in 2026. It is the most crowded slot in the entire space.

2.6 The observability limit — OPEN_PROBLEM, but not solvable by a control plane

Effect verification is the oracle problem under a new name. A closed deterministic system cannot verify the correctness of external information; oracles "relay off-chain data but do not prove it is accurate; they ask you to trust the source." Decentralising the relay distributes the trust assumption; it does not produce proof.

This is the hard ceiling on the entire H-EFFECT programme and the brief does not acknowledge it.

3. One problem or two?

Two. The unity claim does not survive contact.

H-AUTH is a safety property over a static, decidable derivation relation. Closed-world. Offline-checkable. Provable. It is about before.
H-EFFECT is an epistemic property over an open world, bounded by the honesty and observability of systems you do not control. Undecidable in general. It is about after.

They share one artifact: a task identity in a durable record. Sharing a correlation ID is integration, not a research unity.

Worse, coupling them is actively harmful to the work. H-AUTH is provable and boring. H-EFFECT is valuable and unprovable. Binding them means no reader can accept the rigorous half without swallowing the unfalsifiable half, and the project inherits the weakest epistemics of its two components.

The strongest case for unity — the provenance join: binding effect receipt → authority instance → approval, so you can answer "was this effect produced under a live, unrevoked, attenuated grant?" That is a real property. But AP2 already joins mandate→settlement, Notarized Agents already binds receipt→auth token, and PCAA already binds certificate→approval receipts. The join is PARTIALLY_SOLVED and, where open, is a record format, not a runtime.

4. The seventeen questions, answered

1. Meaningful, operationally precise, useful? Meaningful and useful; not operationally precise. "Successfully complete," "real-world effects," "independently evidenced" and "authority" are all undefined against a measurement procedure. No falsification threshold is stated anywhere in the brief.

2. Already solved under different terminology? H-AUTH: yes (capability attenuation / capability monotonicity / monotonic narrowing). UNKNOWN: yes (in-doubt / heuristic outcome). Durable reconciliation: yes. H-EFFECT in full generality: no — and it is not solvable, only boundable (oracle problem). The narrow slice between those is the only real territory.

3. One problem or two? Two. See §3.

4. Is "completion truth" defensible? No. Drop it. Three objections:

It imports a correspondence-theory claim the system cannot make. The system certifies evidence admissibility, never truth.
It is unfalsifiable as phrased.
It conflates three predicates that must be kept apart: (a) effect occurrence — did external state change; (b) effect attribution — was that change caused by this task instance (requires a client idempotency key the provider echoes); (c) goal satisfaction — does the change constitute what was wanted. The False Success paper's ground truth is (a)+(b) only. "Truth" implies (c), which is semantic, underdetermined, and frequently a human judgement. An agent that drops a table to update one row achieved the effect.

Better framing: evidenced-effect settlement with a graded evidence class, i.e. RAILS' admissibility floor. Or corroborated attributed effect state. Every outcome should be a tuple: ⟨state, evidence_class, observer, trust_root⟩ — never a bare word.

5. Is "independent verification" defensible? Independent from whom? Only if you answer the question explicitly, which the brief does not. Honestly enumerated:

Independent of the child's claim — achievable, cheap, and where the 45%→3% benefit lives. ✅
Independent of the child's process/host — achievable. ✅
Independent of the provider — not achievable. The provider is the sole authority on its own state. Receipts make it accountable; they do not make it checkable. Notarized Agents names exactly this: suppression and collusion. ❌
Independent of the control plane itself — only if the verifier can be run by a third party against the record with no access to plane-private state, over a witnessed append-only log (RFC 9162-style). Otherwise the answer is no. ⚠️

6. Does UNKNOWN create useful semantics? The state is not novel and by itself creates nothing. Its value is entirely a function of the obligations attached to it, and the sign of that value is not obvious:

UNKNOWN → caller retries: actively harmful without fencing. An LLM caller that reads UNKNOWN as "try again" produces duplicate external effects — worse than a false SUCCESS.
UNKNOWN → block and escalate: valuable, but its value is capped by human review throughput, which then becomes the system bottleneck.

The genuinely open and falsifiable question is therefore not "is UNKNOWN meaningful" but: what is the operating curve of UNKNOWN rate against human escalation capacity and duplicate-effect rate, and do autonomous callers behave better or worse when handed indeterminacy? I found no paper on this. OPEN_PROBLEM — and it is the most interesting thing in the brief.

7. Is a new component justified? As a runtime, no. New SPOF, new trust root, new adoption barrier, in the most crowded architectural slot of 2026, at a scope that cannot demonstrate the properties claimed. As a specification + independently runnable verifier library, defensibly yes — the join record plus a verifier anyone can execute is the one thing that answers Q11 rather than dodging it.

8. Would conventional auth + durable workflow suffice? Largely yes. Temporal/Restate + Biscuit or AAT tokens + provider idempotency keys + a reconciliation activity that re-reads the effect surface reproduces essentially everything in the brief at depth 1. Two residues survive: (i) offline, third-party-checkable proof that a specific effect was authorised by a specific attenuated grant; (ii) a portable semantics of indeterminacy that survives crossing framework boundaries. Those two are the only defensible deltas, and both are formats, not platforms.

9. Could existing authority + durable-execution components expose this directly? Yes, and they should. The needed change to a durable-execution engine is a wrapper: do not trust the activity's return value; obtain an independent observation of the effect surface and record its evidence class. That is a library on top of existing primitives.

10. Is A2A the right boundary? A2A is one transport, not the contribution. A2A v1.0 defines no delegation, no attenuation, and — confirmed against the specification — no independent completion verification whatsoever: clients learn completion solely from the remote agent's own state transitions. TASK_STATE_UNSPECIFIED is a protobuf default, not a semantic indeterminate outcome. So A2A is precisely the thing that lacks these semantics. That makes it a good venue and a bad foundation. Note that a2aproject/A2A discussion #1404, "SEP: Capability-based authorization," is already debating signed delegation chains with parent linkage and offline reconstruction. Contributing a monotonicity conformance suite to that SEP is higher-leverage than a private control plane, and would produce external validation the project otherwise cannot get. Any design must demonstrate on ≥2 unrelated transports to prove A2A is not load-bearing.

11. Does the trust model just relocate trust into Accord? As described, yes. The only escape is that the control plane is trusted for non-repudiation and ordering, not for truth, and that a lying plane is detectable by the principal via an externally runnable verifier over a witnessed append-only log. If the design cannot state that in one sentence, the objection lands and the project is a trust-laundering exercise.

12. Can the proposed experiment falsify the hypothesis? No — the v0.1 constraints make falsification impossible for every interesting claim. Specifically:

Depth 1 + max 1 child removes transitive attenuation, sibling aggregation, revocation propagation, and cycles: every place escalation actually occurs.
"No production external-provider effect" removes the entire object of study. You cannot study effect verification with no effects. A mock provider you also wrote will confirm whatever you designed it to confirm. This is the largest methodological flaw in the brief.
Single host removes partition, crash-partition interleaving, and the duplicate-effect race that makes UNKNOWN interesting.

The constraints are internally coherent, but they are the scope of an engineering v0.1, not of an experiment. They are scoped to exclude the research question.

There is also a direct internal contradiction: the brief claims to prevent privilege escalation while stating no Firecracker requirement. Prevention requires complete mediation. An unisolated child retains its own credentials, its own network, and its own prompt-injection surface. You cannot claim prevention while declining to isolate. The honest claim is "prevents escalation via mediated channels" — which is much weaker and must be stated.

13. What counts as failure? See §6.

14. What evidence would justify VERIFIED_SUCCESS? Only: a provider-attributable artifact, bound to a client-chosen idempotency key, observed by a principal other than the executing agent, at a stated evidence class, with the trust root named. Absent attribution, the strongest honest verdict is OBSERVED_CONSISTENT, not VERIFIED.

15. Is a formal authority partial order required? Necessary, cheap, and insufficient — and the insufficiency must be stated or the work overclaims.

You need a decidable subsumption relation ⊑ with derive(g) ⊑ g. AAT's constraint subsumption already gives this; do not reinvent it.
It is a preorder, not a partial order, unless you quotient by semantic equivalence — two syntactically distinct grants can be equi-powerful. Claiming "partial order" without the quotient is sloppy and a reviewer will catch it.
Monotonicity of the grant lattice does not imply monotonicity of effective authority. The object-capability literature established that syntactic capability monotonicity is insufficient in the presence of object capabilities. Confused deputy via the parent, sibling aggregation, and timing all break the implication.
Budgets, rates and deadlines are non-monotonic and need resource accounting, not a lattice.

16. Property-based / model-based testing required? Yes, and it is the cheapest credible thing in the project.

Attenuation layer: property-based testing is ideal — generate random grants, derive random attenuations, assert ⊑, assert transitivity, metamorphic test that any attenuation sequence composes to something ⊑ root. Plus a small Alloy or TLA+ model of authority-instance × approval × reservation × effect-state, checked for: no CONFIRMED without a matching authorised reservation; no two CONFIRMED for one action hash; UNKNOWN never transitions to CONFIRMED without new evidence.
Execution/reconciliation: deterministic simulation testing in the FoundationDB / Antithesis / TigerBeetle tradition, with crash injection at every point, especially crash-after-effect-before-journal. Well-established method; using it well is a genuine strength but is not itself a contribution.
Full mechanised proof (Lean/Rocq): not justified at v0.1. AgentFlow and Bounded Agents already publish theorems; marginal credibility per unit cost is poor.

17. Are the claims stronger than single-host evidence supports? Yes, substantially. Unsupportable at this scope: exactly-once, guarantee, distributed, consensus, prevents, never, truth, production, and unqualified independent. What is supportable: "on a single host, under injected fault model F, against providers of evidence class E, we observed zero false confirmations in N trials at an UNKNOWN rate of p."

5. The system I would build, blind

Form: not a runtime; not one project. A test harness and a thin specification, contributed as a profile of existing standards.

P1 — Evidence-Bound Delegation Record (specification + independently runnable verifier)

A signed, append-only, per-task record with three linked chains and no runtime of its own:

Authority chain — root grant → attenuated child grant, offline-verifiable via AAT-style typed subsumption. Reuse draft-niyikiza or Biscuit. Do not invent a token format.
Intent chain — human approval bound to an action hash, with expiry, revocation, and dispatch reservation. AP2 mandate shape.
Effect chain — per attempt: ⟨idempotency_key, provider_echo, receipt_or_absence_proof, observer_identity, observation_time, evidence_class⟩.

Plus a verifier binary a third party runs with only (record, trust anchors), emitting {VERIFIED_SUCCESS | NOT_DONE | UNKNOWN | INVALID} together with the list of trust assumptions it had to discharge. The verifier being independently executable is the entire answer to Q11. If it needs plane-private state, the project has failed by construction.

P2 — The experiment harness (the actual research instrument, and the more valuable output)

A provider simulator bank classifying effect surfaces by evidence affordance:

Class	Affordance
E0	No observable state (fire-and-forget)
E1	Observable but unattributable (row exists; author unknown)
E2	Attributable via client idempotency key echoed back
E3	Provider-signed receipt
E4	Receipt + third-party transparency log / witness

Crossed with fault injection — crash before/after effect, duplicate delivery, delayed receipt, provider lies, provider silently drops, partition at the observation step — and with adversarial child agents: honest, optimistic-liar, lazy-liar, crashed, slow, and a prompted-to-lie LLM child, since that is the actual threat rather than a byzantine abstraction.

This harness is reusable whichever architecture wins, and it is what makes any claim in this space falsifiable. It is the contribution I would defend.

P3 — Conformance profile, not new mechanism

Publish H-AUTH as a conformance test suite against draft-niyikiza-oauth-attenuating-agent-tokens and A2A SEP #1404. External adoption of a test suite is achievable; external adoption of a new runtime is not.

Discard: new runtime; new token format; distributed consensus; Firecracker; governed memory (correctly already deferred).
Reuse: Temporal/Restate/DBOS for durability; Biscuit/AAT for attenuation; MCP 2026-07-28 Tasks extension + elicitation for async lifecycle and human-in-the-loop; A2A as one of ≥2 transports, precisely to demonstrate it is not load-bearing.

Threat model I would state

In scope: lying child, lazy child (partial work claimed complete), crashed child, replaying child, over-reaching child, prompt-injected child, colluding siblings; buggy or unavailable provider; crash-after-effect; duplicate effect.
Out of scope but named, not hidden: colluding provider (unverifiable by construction); compromised control plane (mitigated by external verifiability + witnessed log, never by assumption); compromised approver; the gap between "effect occurred" and "goal met."

One-sentence honest statement of what the system does: it converts an unverifiable claim into a verifiable evidence chain with an explicit trust root; it does not create truth.

6. Falsification criteria for my own design

Pre-registered, with baselines, or none of it counts.

#	Hypothesis	Falsifier
H1	No reachable state grants a child authority ⊄ parent	One counterexample from PBT or the model checker. Note: this will pass, and passing is weak evidence of value.
H1′	Effective authority — including composition across a session and laundering via the parent — never exceeds the parent's	A counterexample. I expect this to fail, and the failure would be the most interesting result in the project.
H2	False-confirm rate ≈ 0 while UNKNOWN rate stays operationally usable	Either false confirms occur, or UNKNOWN exceeds ~20–30% on honest providers, at which point callers ignore or auto-retry it. (b) is the likely failure and the one to fear.
H3	The mechanism beats the cheap baseline: post-hoc state read + TF-IDF detector (0.83–0.95 AUROC, 3,300× faster)	Improvement below a pre-registered margin. If 200 lines of TF-IDF plus one state read captures most of the benefit, no control plane is justified. This baseline must be in the experiment from day one.
H4	Exposing UNKNOWN to an autonomous caller improves end-to-end outcomes vs. mapping it to FAILED or to retry	No difference, or worse via duplicate effects. Genuinely open.
H5	The record verifies across ≥2 unrelated runtimes and ≥2 unrelated providers, by a third party with no plane-internal access	Verification requires plane-private state ⇒ trust was merely relocated ⇒ project rejected.

Decision rule: H1 passing alone is not a result. The project is justified only if H3 clears its margin and H5 holds. If H2(b) or H5 fails, stop.

A copy of this review is at phase1-review.md if you want it verbatim in the repo.

PHASE_1_FROZEN
Provisional verdict

PIVOT

The underlying pain — agents confidently reporting completion that did not happen — is real, large, and empirically documented at 45–76% of failures depending on domain. The proposed vehicle does not survive review. Specifically: the delegated-authority half is already solved and standardising; "completion truth" is indefensible terminology; a new control plane is the most crowded architectural slot in the field; the single-host, depth-1, no-real-effects constraints exclude every phenomenon that could falsify the hypothesis; and the trust model, as stated, relocates trust rather than reducing it.

The surviving research question is narrower and better: given effect surfaces of varying evidence affordance and delegates of varying honesty, what is the achievable frontier between false confirmation, indeterminacy rate, and duplicate effects — and does exposing indeterminacy to an autonomous caller help or hurt?

If the team reads the changes below as amendments rather than redirection, CONTINUE_WITH_CHANGES is defensible. I am calling PIVOT because the changes are load-bearing: split the problem, drop the runtime, drop the terminology, permit real effects, lift depth-1.

Independently proposed architecture
Experiment harness first — provider simulator bank graded E0–E4 by evidence affordance, crossed with fault injection and adversarial child agents including a prompted-to-lie LLM child. This is the primary deliverable and the only reusable one.
Evidence-Bound Delegation Record — a format joining authority chain, intent/approval chain, and per-attempt effect chain, plus a verifier any third party can run against (record, trust anchors) with zero plane-private state, emitting a verdict and the trust assumptions it discharged.
Conformance profile, not new mechanism — H-AUTH published as a test suite against draft-niyikiza-oauth-attenuating-agent-tokens and A2A SEP #1404.
No new runtime. Durability from Temporal/Restate/DBOS; attenuation from Biscuit/AAT; async lifecycle and HITL from MCP Tasks + elicitation; ≥2 transports so A2A is demonstrably not load-bearing.
Two projects, one shared artifact. Authority and effect verification ship separately and are falsified separately; they share only the record format.
Strongest argument against proceeding

The measurable benefit appears reachable without the system. Independent state observation alone takes false success from ~45% to ~3%, and a TF-IDF detector reaches 0.83–0.95 AUROC at 3,300× lower latency than an LLM judge. Meanwhile the authority half is a solved conformance test, the durability half is commodity, and the verification half runs into the oracle problem — a provider that will not emit attributable evidence cannot be made to, by any control plane. What remains is an integration with a crowded competitor set, evaluated at a scope that structurally cannot falsify its own central claims.

Strongest argument for proceeding

Nobody has characterised the trade-off surface, and it is the thing practitioners will actually need. Every existing system either asserts a binary outcome (RAILS' admissibility floor, AP2's mandates, PCAA's outcome closure) or ignores indeterminacy entirely (A2A trusts the remote agent's own status; Temporal trusts the activity's return value). No one has measured what happens to an autonomous caller when handed UNKNOWN, whether the resulting retry behaviour manufactures duplicate external effects, or where the usable frontier sits between indeterminacy rate and human escalation capacity. That is a genuinely open, genuinely falsifiable empirical question, the harness needed to answer it is valuable independent of any architecture, and the team already holds the durable-execution and approval primitives to build it quickly.

Unresolved questions that must be answered before implementation
Which half are you doing? Committing to both is the failure mode. My recommendation: effect verification, with authority reduced to a conformance suite.
What is the trust root of a VERIFIED_SUCCESS, in one sentence, without the word "truth"? If it cannot be written, stop.
Can a third party run the verifier with no plane-private state? If no, Q11 lands and the project is trust laundering.
What replaces "no production external-provider effect"? Effect verification cannot be studied without effects. Sandbox/test-mode APIs from ≥2 real independent providers at ≥2 distinct evidence classes are the minimum credible substitute.
What is the pre-registered margin over the TF-IDF + state-read baseline below which the project is abandoned?
Is depth 1 defensible given that aggregation, transitive attenuation and revocation propagation — the only open parts of H-AUTH — all require depth ≥ 2 and siblings ≥ 2?
How is "prevents escalation" reconciled with declining isolation? Either weaken the claim to "via mediated channels," or accept a sandbox requirement.
Is the ⊑ relation a partial order or a preorder, and if the former, what is the semantic-equivalence quotient?
Is the target an A2A SEP contribution or a private system? The former yields external validation the latter cannot obtain.
What is the abandonment criterion, written before any code, and who is empowered to invoke it?