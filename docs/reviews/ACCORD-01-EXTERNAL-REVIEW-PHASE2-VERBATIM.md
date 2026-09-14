ACCORD-01 External Review — Phase 2
A. PRIMARY VERDICT
PIVOT

Rationale.

Phase 1 concluded PIVOT before seeing this appendix. The appendix does not overturn that conclusion; it supplies the mechanism for it, and adds two defects I could not have predicted.

What the appendix gets right is substantial and I want to credit it before attacking: the invariant set is the correct shape for this problem, REMOTE_COMPLETED != VERIFIED_SUCCESS is the single most important sentence in either document, and the red-team questions are — with one exception — the questions I would have asked. "Does the proposed boundary create a second policy engine or a second source of execution truth?" and "Does the architecture accidentally make transport metadata authoritative?" are both self-identified fatal risks. An architecture document that names its own fatal risks is unusual and good.

But the answer to both of those self-posed questions is yes, as drawn. And three further findings drive the pivot:

The diagram places a non-runtime in the runtime path. The brief's accepted evidence states plainly: "Fates Integration — compatibility locks, conformance material, and acceptance evidence; not a runtime." The appendix diagram places The Fates between the transport adapters and all three runtimes. Either Fates silently becomes a fourth runtime — uncosted, unevidenced, and contradicting the accepted audit — or the diagram is wrong. This is not a nitpick: it is the load-bearing junction of the entire stack.
Three of the six invariants are tautologies, one is false as stated, and one is empty. Detail in §G/§H. Only CHILD_AUTHORITY <= PARENT_AUTHORITY is both testable and true, and it is the half Phase 1 classified ALREADY_SOLVED.
The invariant set is aimed at the wrong half of the empirical problem. Every invariant governs the unauthorized child. The measured failure mode — 45–48% of tau2-bench failures, 75.8% of AppWorld failures — is the lying or mistaken child, which is fully authorized and simply reports work it did not do. NO_VALID_AUTHORITY -> NO_EFFECT does nothing about that agent. Only NO_ACCEPTABLE_EFFECT_EVIDENCE -> NO_VERIFIED_SUCCESS engages it, and that invariant's entire content sits inside an undefined word.

The pivot is not "abandon this." It is: the invariants are close to a good specification; the layer they are drawn inside is not justified. Keep the invariants, repair them, relocate them to their natural owners, add an externally runnable verifier, and build the harness. Delete the box labelled Accord.

B. PROBLEM VALIDITY

Real, useful, not operationally precise — unchanged from Phase 1, and the appendix does not add the missing precision.

The appendix's most valuable contribution to precision is its own question: "Can the system distinguish 'task completed,' 'agent returned,' 'provider accepted,' 'effect occurred,' and 'effect was independently observed'?" That five-term chain is the right decomposition and it is better posed than anything in the brief. It is also missing a sixth term, and the missing one is where real systems actually fail:

1. agent returned                    (process fact)
2. task completed                    (agent's claim)          ← what A2A reports
3. provider accepted                 (provider's ack)
4. effect occurred                   (external state changed)
5. effect attributed to THIS attempt (the missing term)       ← where systems fail
6. effect independently observed     (by a non-delegate principal)

Step 5 is the hard one. You can see the row; you cannot prove you wrote it. Every design that jumps from 4 to 6 without 5 has a correlation bug waiting in it. The appendix's chain, uncorrected, licenses exactly that jump.

Actors in scope: parent agent, child agent, human approver, external provider, the control plane itself. Missing from scope: the observer as a distinct principal. Someone must read the effect surface, and the entire independence claim rests on who that is. The appendix never names them.

Trust boundaries in scope: parent↔child, agent↔plane, plane↔provider. Missing: plane↔auditor. Without it, "independent" has no referent.

C. PRIOR ART / NOVELTY

Frozen from Phase 1. Restated in compressed form against the appendix's specific claims:

Appendix element	Classification	Nearest prior art
CHILD_AUTHORITY <= PARENT_AUTHORITY	ALREADY_SOLVED	draft-niyikiza-oauth-attenuating-agent-tokens-01 Invariant I4 Capability Monotonicity, with typed subsumption and offline chain verification from the root anchor alone; Biscuit; macaroons; Bounded Agents (2608.15888) Blast Radius Monotonicity; Five-Plane (2606.12320) composite principals with attenuation
UNKNOWN != SUCCESS, UNKNOWN != FAILURE	TERMINOLOGY_DIFFERENCE	X/Open XA in-doubt, c. 1991; heuristic-commit/rollback/mixed/hazard; Gray & Reuter 1993
REMOTE_COMPLETED != VERIFIED_SUCCESS	PARTIALLY_SOLVED	Notarized Agents (2606.04193) receiver-attested receipts; PCAA (2606.04104) outcome closure; False Success (2606.09863) dual-control state verification
NO_ACCEPTABLE_EFFECT_EVIDENCE -> NO_VERIFIED_SUCCESS	PARTIALLY_SOLVED	RAILS (2606.08790) — admissibility floor, Evidence Envelope, Clearing Decision. This is the same invariant with the floor actually specified.
NO_VALID_AUTHORITY -> NO_EFFECT	ALREADY_SOLVED in principle, false as stated here	Complete mediation, Saltzer & Schroeder 1975. Requires isolation the brief declines.
A2A/MCP adapters over a governance core	ALREADY_SOLVED as a genre	Authenticated Workflows (2602.10465); Sovereign Execution Broker (2606.20520); Auth0 for GenAI; Arcade; Descope; WorkOS
Reconciliation / crash-after-effect	ALREADY_SOLVED single-host	Temporal, Restate, DBOS, Step Functions

Missing from the framing — communities and vocabulary the appendix should be speaking and is not:

Atomic commitment and heuristic outcomes. Everything about UNKNOWN was settled vocabulary thirty years ago. Not citing it will read as unawareness.
Clearing and settlement. RAILS, TessPay, AP2 mandates. "Admissibility floor" is the term of art for the undefined word "acceptable."
The oracle problem. The hard ceiling on the whole completion programme. Unacknowledged.
Compensating transactions / sagas. Entirely absent, and §F shows it is required by the revocation race the appendix itself raises.
Complete mediation. The concept that makes NO_VALID_AUTHORITY -> NO_EFFECT either true or false.

Genuinely open, still: the trade-off surface between false-confirmation rate, UNKNOWN rate, duplicate-effect rate and human escalation capacity, on effect surfaces graded by evidence affordance, against adversarial delegates. Nobody has measured it. The appendix does not target it.

D. BLIND ARCHITECTURE

Frozen. Summarised for comparison:

P1 — Evidence-Bound Delegation Record: a signed, append-only, per-task record with three linked chains (authority / intent-approval / per-attempt effect), plus a verifier any third party can run against (record, trust anchors) with zero plane-private state, emitting a verdict and the trust assumptions it discharged.
P2 — Experiment harness (the primary deliverable): provider simulator bank graded E0–E4 by evidence affordance, crossed with fault injection (crash before/after effect, duplicate delivery, delayed receipt, lying provider, silent drop, partition at observation) and adversarial child agents including a prompted-to-lie LLM child.
P3 — Conformance profile, not new mechanism: H-AUTH as a test suite against the IETF attenuating-token draft and A2A SEP #1404.
No new runtime. Durability from Temporal/Restate/DBOS; attenuation from Biscuit/AAT; async lifecycle and HITL from MCP Tasks + elicitation; ≥2 transports so no single one is load-bearing.

Minimum experiment and its failure modes: H1/H1′/H2/H3/H4/H5 as frozen in Phase 1 §6, with the decision rule "H1 passing alone is not a result; the project is justified only if H3 clears its pre-registered margin and H5 holds."

E. COMPARISON TO ACCORD HYPOTHESIS
Convergence

Genuine and worth stating: the two designs agree on the semantics almost completely.

Shared commitment	Appendix	My blind design
Agent's claim is not evidence	REMOTE_COMPLETED != VERIFIED_SUCCESS	"Don't trust the activity's return value"
Success must be evidence-gated	NO_ACCEPTABLE_EFFECT_EVIDENCE -> NO_VERIFIED_SUCCESS	Evidence-class floor
Three-valued outcome	UNKNOWN != SUCCESS/FAILURE	{VERIFIED_SUCCESS, NOT_DONE, UNKNOWN, INVALID}
Authority narrows downward	CHILD_AUTHORITY <= PARENT_AUTHORITY	AAT-style subsumption chain
Transport should not be the contribution	"possible transport boundaries"	≥2 transports, A2A as venue
Memory deferred	deferred	discarded from v0.1

The disagreement is not about what should be true. It is entirely about where those statements live and who can check them.

Divergence
Axis	Accord hypothesis	Independent design	Severity
Form	A runtime layer with adapters and a facade beneath it	A record format + externally runnable verifier + an experiment harness	Fatal to the layer
Fates in the call path	Present, between adapters and runtimes	Absent; Fates stays conformance material per accepted evidence	Fatal / contradiction
External verifiability	Nothing in the appendix lets a third party check a claim without trusting Accord	Verifier takes (record, anchors), no plane-private state	Fatal to "independent"
Definition of "acceptable"	Undefined	E0–E4 evidence-class taxonomy	Blocker
Threat model	Unauthorized child	Lying, lazy, crashed, replaying, injected, colluding children	Aimed at the wrong half
Effect attribution	Absent from the five-term chain	Explicit sixth term, idempotency-key echo required	Blocker
Compensation	Absent	Required by the revocation race	Blocker
Baseline	None	State re-read + TF-IDF detector, pre-registered margin	Blocker
Testability without a wire protocol	Both adapters sit between Accord and the core	Loopback transport; wire protocols are conformance targets	Major
Policy decisions	Accord appears to enforce authority invariants above Ananke	Accord never decides; requests derivation, verifies result	Major
Remove, move, replace

Remove

The box labelled Accord as a runtime layer. Its three claimed gaps (portable nested delegation, monotonic child-authority validation, remote task lifecycle supervision) each have a natural existing owner — see §K.4.
The Fates from the runtime path. It is conformance material; keep it there.
The adapter stack as a dependency. Adapters become optional conformance targets; the core must be exercisable over loopback.

Move

CHILD_AUTHORITY <= PARENT_AUTHORITY → Ananke, as a derivation rule, not a check performed by a layer above it.
REMOTE_COMPLETED != VERIFIED_SUCCESS, NO_ACCEPTABLE_EFFECT_EVIDENCE -> NO_VERIFIED_SUCCESS, and all effect-state semantics → Horae, which per the accepted evidence already owns CONFIRMED/ABSENT/UNKNOWN and reconciliation. There must be exactly one home for the record of what happened.
The join — authority instance ↔ approval ↔ task identity ↔ effect evidence, as one portable, signed, externally verifiable record → Adrasteia, which already owns portable contracts and correlation. This is the single genuinely novel artifact and it is a type, not a runtime.

Replace

"Acceptable evidence" → a published evidence-class taxonomy with per-class trust assumptions.
NO_VALID_AUTHORITY -> NO_EFFECT → NO_VALID_AUTHORITY -> NO_MEDIATED_DISPATCH, plus an explicit statement that unmediated channels exist.
The three tautological invariants → either testable properties or an explicitly-labelled definitions section.
F. TRUST-MODEL ATTACK

Where trust actually sits, as drawn: entirely inside Accord, and nowhere else. Accord derives or validates the child grant, mediates dispatch, receives the receipt, decides whether evidence is "acceptable", writes the record, and is the only reader of that record. There is no witness, no external verifier, and no principal who can contradict it. Accord is the sole author and sole judge of its own evidence. That is trust relocation, precisely as Phase 1 Q11 anticipated, and the appendix supplies no escape.

The escape exists and is cheap: Accord is trusted for non-repudiation and ordering, not for truth, with an append-only witnessed log and a verifier a third party can run. Until the appendix says that in one sentence, the word "independent" in the research question is unsupported.

Can Accord lie?

Yes, undetectably. It authors the record it is judged by. Mitigation: witnessed append-only log (RFC 9162-shaped), verifier runnable by the principal. Cost: low. Currently absent.

Can Accord be bypassed?

Yes, trivially. A child agent holding its own provider credentials, its own network egress, or carrying a prompt injection produces effects Accord never observes. The brief's "no Firecracker requirement" removes the isolation that complete mediation needs. NO_VALID_AUTHORITY -> NO_EFFECT is therefore false in the deployed configuration, and this is an internal contradiction between the two documents, not merely a scoping choice.

Can Accord be replayed?

Yes, at the evidence boundary. Harvest a receipt from run 1, present it as evidence for run 2. Defence requires the provider to echo a plane-chosen nonce bound to the action hash before dispatch. Most providers will not. Consequence: for low-evidence providers, receipt replay is unpreventable and the evidence class must be downgraded rather than the receipt accepted. This is exactly why the undefined word "acceptable" is a blocker and not a detail.

Can Accord be confused?

Yes, and the appendix asks the right question — "Does the architecture accidentally make transport metadata authoritative?" As drawn, with both adapters between Accord and the core, the answer is yes by default. If an A2A task id, an MCP session, or an auth header is mapped into the authority binding or the effect correlation, a malicious peer controls that binding.

Rule that must be adopted: no transport-supplied identifier may be load-bearing for authority or for effect attribution. Authority binds to a plane-issued action hash and nonce; transport identifiers are correlation hints with no evidential weight. One sentence, removes a whole attack class.

Can Accord be induced to overstate authority?

Yes, via interpretation drift. If Accord derives a child grant by interpreting a parent scope, and its interpretation is looser than Ananke's, Accord mints a grant Ananke would have refused. Mitigation: Accord must never mint. It requests derivation from Ananke and verifies the returned grant. Note what this rule implies — under it, Accord holds no authority logic at all, which is itself an argument for demoting it to a library.

The revocation race

The appendix's sharpest question: "What happens when a parent is revoked after a child is reserved or after the effect boundary begins?" The answer breaks an invariant.

Once the effect boundary is crossed you are in the in-doubt window. Revocation cannot retract an in-flight effect. Either you evaluate authority at dispatch — in which case the true invariant is NO_VALID_AUTHORITY_AT_DISPATCH -> NO_DISPATCH and a revoked-mid-flight effect still happens — or you require prepare/commit from the provider, which essentially no real provider offers.

So revocation must be redefined as: revocation prevents new dispatch and creates a compensation obligation for in-flight effects. That obligation requires a compensation/saga model. The appendix has none. This is a missing component of real size, surfaced by the appendix's own question.

Trust roots assumed rather than evidenced
That the provider's receipt means what the plane thinks it means.
That the provider is not colluding or buggy. Notarized Agents names this exactly — suppression and collusion — as unsolved.
That the log is not rewritten.
That the approving human is not compromised.
That "effect occurred" implies "goal met." It does not.
G. AUTHORITY-MODEL ATTACK

CHILD_AUTHORITY <= PARENT_AUTHORITY is not sufficiently defined, in five specific ways. Frozen Phase 1 findings, now applied to the concrete invariant:

<= is undefined. It needs a decidable subsumption relation over typed constraints. The IETF attenuating-token draft already supplies one (exact, range, one_of, not_one_of, contains, subset, wildcard, with subsumption rules). Adopt it; do not invent one.
It is a preorder, not a partial order, unless you quotient by semantic equivalence. Two syntactically distinct grants can be equi-powerful. Antisymmetry fails without the quotient. Claiming "partial order" without it will not survive review.
Grant monotonicity does not imply effective-authority monotonicity. The object-capability literature established that syntactic capability monotonicity is insufficient in the presence of object capabilities. Sibling aggregation, confused-deputy laundering via the parent, and timing all break the implication. The invariant as written says grants; the research question's word "escalation" means effective authority. These are different claims and the document uses one to assert the other.
Non-monotonic dimensions do not fit. Budget, quota, rate and deadline under clock skew are resource accounting across concurrent holders, not lattice meets. The appendix's own list — "scope, capability, deadline, approval, budget, audience, and representation attenuation" — mixes at least three different algebras under one <=. Specifically:
scope/capability/audience — set-like, genuine meet-semilattice ✅
deadline — total order on time, but requires a trusted clock and a skew bound ⚠️
budget — additive, consumable, needs distributed counting; <= is the wrong operator ❌
approval — not a quantity at all; a binding to a specific action hash with expiry and revocation, which composes by conjunction not by narrowing ❌
representation — a substitution, not a restriction; acting-as can change the resource set non-monotonically ❌
Three of seven dimensions are not attenuation in the lattice sense. Publishing them under one <= is the most likely source of a real soundness bug.
Depth 1 with one child removes every case where the invariant is interesting. Transitive attenuation, sibling aggregation, and revocation propagation all require depth ≥ 2 or siblings ≥ 2. Phase 1 §4.12 stands: the constraints are scoped to exclude the phenomenon.

Proof obligations required: reflexivity, transitivity, antisymmetry-up-to-equivalence on the quotient, derive(g) ⊑ g for every derivation rule, and a separate — and I predict failing — statement about effective authority under composition. Property-based testing covers 1–3 cheaply; a small Alloy or TLA+ model covers the lifecycle state machine; full mechanised proof is not justified at v0.1.

H. COMPLETION / EFFECT ATTACK

Can the system know what happened? No — and it should stop implying it can. It can record attributed observations at a stated evidence class with a named trust root. That is a weaker and completely respectable claim.

The invariants, audited individually
Invariant	Status
CHILD_AUTHORITY <= PARENT_AUTHORITY	Testable and true, once <= is defined. Also the half that is already solved.
NO_VALID_AUTHORITY -> NO_EFFECT	False as deployed. Requires complete mediation; the brief declines isolation. Rewrite to NO_MEDIATED_DISPATCH.
NO_ACCEPTABLE_EFFECT_EVIDENCE -> NO_VERIFIED_SUCCESS	True but empty until "acceptable" is a published taxonomy. All the content is in that word.
REMOTE_COMPLETED != VERIFIED_SUCCESS	A type distinction, not an invariant. It asserts two labels differ. No implementation can violate it; therefore no experiment can test it. Correct principle, wrong grammar.
UNKNOWN != SUCCESS	Same — definitional.
UNKNOWN != FAILURE	Same — definitional.

Three of six are tautologies. One is false. One is empty. One is genuine, and it is the already-solved one. An invariant set with this profile cannot carry a research claim.

Who may attest VERIFIED_SUCCESS?

Never the executing agent. Never Accord alone. The attestation subject must be an observer principal distinct from the delegate, and the record must name it. Accord's role is to record that attestation, not to make it. Phase 1's honest ladder:

delegate-independent → achievable, and where the measured benefit is (45–48% → 3%)
process/host-independent → achievable
provider-independent → not achievable; the provider is the sole authority on its own state
plane-independent → only via an externally runnable verifier over a witnessed log
VERIFIED_NO_EFFECT

The template asks when this is defensible. Almost never, and this is a bigger problem than it looks. Absence of evidence at time T is not evidence of absence: a delayed provider write can land after your observation. Defensibility requires either a linearizable read plus a fence, or a monotonic "this idempotency key was never accepted" assertion. Essentially no commercial provider offers either.

Consequence: VERIFIED_NO_EFFECT mostly collapses into UNKNOWN. That drives the UNKNOWN rate up — which is precisely Phase 1's H2(b), the failure mode I flagged as most likely. The appendix introduces the state without noticing that introducing it makes its own hardest problem worse.

Recommended form: NO_EFFECT_OBSERVED(as_of T, read_semantics R) — a timestamped, qualified observation, never a verdict.

Do idempotency keys prevent duplicate effects?

No. They make duplicate attempts recognisable at the provider, if and only if the provider implements them, with the right scoping, within a retention window. Three concrete failures:

Provider doesn't implement them → no protection at all.
Semantic duplicates under different keys → two attempts that mean the same thing but were keyed differently are invisible to the mechanism.
Retention window expiry — the important one. Reconcile after the provider's window (commonly 24h) and you can no longer distinguish "already done" from "never done." That is an UNKNOWN that never resolves, and it is a permanent one. Any reconciliation design must carry a deadline shorter than the shortest provider retention window, or accept unresolvable indeterminacy. Nothing in the appendix acknowledges this.
Is UNKNOWN terminal, reconciliation, or both?

Both, and the distinction must be in the type. UNKNOWN_PENDING(retry_until T) and UNKNOWN_TERMINAL(reason) are different obligations. Collapsing them is how an autonomous caller ends up retrying a terminal indeterminacy and manufacturing a duplicate effect — Phase 1's harmful case. The value of UNKNOWN is not in the state; it is in the obligations attached to it, and unqualified UNKNOWN attaches none.

I. METHODOLOGY ATTACK

As scoped, the experiment cannot falsify the hypothesis. Phase 1 §4.12, unchanged and now reinforced: depth 1 + one child deletes every case where escalation occurs; single-host deletes partition and the interleavings that make UNKNOWN interesting; and "no production external-provider effect" deletes the object of study. A mock provider you also wrote will confirm whatever you designed it to confirm.

The appendix's failure-case list is good and I would keep all of it: authority widening, replay, duplicate dispatch, crash after effect, lost response, forged receipt, provider ambiguity, revocation race, task/effect confusion. Three must be added:

lying child — the empirically dominant case, entirely absent
partially-lying child (real work, overstated completeness) — the hardest to detect
idempotency-window expiry — the unresolvable UNKNOWN

What would count as failure (frozen from Phase 1 §6, applied here):

H1 passes trivially — it will — and therefore contributes nothing.
H3: the mechanism fails to beat state re-read + a cheap detector by a pre-registered margin. The False Success paper's TF-IDF detector reaches 0.83–0.95 AUROC at ~3,300× lower latency than an LLM judge. If 200 lines plus one state read captures most of the benefit, no control plane is justified. This baseline is not optional and is currently absent.
H2(b): UNKNOWN exceeds ~20–30% on honest providers, so callers ignore or auto-retry it. VERIFIED_NO_EFFECT's collapse (§H) makes this more likely, not less.
H5: verification requires plane-private state ⇒ trust merely relocated ⇒ reject.

Evidence justifying each verdict:

Verdict	Required evidence
VERIFIED_SUCCESS	Provider-attributable artifact bound to a plane-chosen key/nonce, observed by a principal other than the delegate, at evidence class E3+, trust root named. Below E3: CORROBORATED, not VERIFIED.
VERIFIED_NO_EFFECT	Linearizable read past a fence, or a provider assertion that the key was never accepted, within the retention window. Otherwise → UNKNOWN.
UNKNOWN	Default. Must carry {PENDING(retry_until) | TERMINAL(reason)}, the obligation it imposes, and why the stronger verdicts were unreachable.

Claims permissible at single-host scope: "on a single host, under injected fault model F, against providers of evidence class E, with delegate behaviours B, we observed zero false confirmations in N trials at an UNKNOWN rate of p." Nothing containing exactly-once, guarantee, distributed, consensus, prevents, never, truth, or unqualified independent.

J. TERMINOLOGY ATTACK
Term	Verdict	Replacement
truth	Reject. Correspondence claim the system cannot make; unfalsifiable; collides with commit/durability in transaction systems.	evidence, attested observation, record. Kill "completion truth" entirely.
verified	Keep, never bare. verified alone is meaningless.	VERIFIED(evidence_class, observer, trust_root). Reserve VERIFIED for E3+; use CORROBORATED below.
independent	Keep only when qualified by principal.	delegate-independent (achievable and where the benefit is). Never use unqualified — it currently implies provider-independence, which is unachievable.
completion	Reject as an invariant term. Ambiguous across the appendix's own five-term chain.	Use the six-term chain explicitly (§B). Never write "completion" in an invariant.
effect	Split. Hides the attribution problem, which is where systems fail.	attempt / effect occurrence / effect attribution / effect observation.
exactly-once	Reject at any scope. Not achievable against arbitrary external providers; every durable-execution vendor says so in their own docs.	at-most-once mediated dispatch + duplicate-recognisable attempts.
authority	Keep, but disambiguate. The invariant constrains grants; readers hear effective authority. §G.3.	grant vs effective authority, used consistently and never interchanged.
delegation	Keep, but split. The project conflates delegation of authority (grant derivation) with delegation of work (task assignment).	Two terms. This conflation is the linguistic root of why the two research halves got fused — Phase 1 §3.

Additional: VERIFIED_NO_EFFECT → NO_EFFECT_OBSERVED(as_of, read_semantics). UNKNOWN → UNKNOWN_PENDING / UNKNOWN_TERMINAL. And drop mythological code names from technical prose entirely — "The Fates" appearing as a box in a call graph is exactly how a non-runtime ended up in the runtime path.

K. REMOVE-A-COMPONENT TEST
1. Accord without Adrasteia

Accord must then define its own principal, capability, correlation and resource-scope types — becoming a competing portable-contract layer alongside the one that already exists. Strictly worse: two vocabularies, a translation layer between them, and drift.

Adrasteia survives and should be promoted. It is the most defensible component in the stack, and it is the natural home for the one genuinely novel artifact — the portable, signed, externally verifiable join record. Adrasteia + a verifier ≈ my entire blind design. Verdict: load-bearing; keep and expand.

2. Accord without Ananke

Accord must then decide authority itself. The "second policy engine" risk resolves by Accord becoming the only policy engine — i.e. Accord is renamed Ananke. Nothing is removed.

The informative resolution runs the other way: adopt the §F rule that Accord never mints, only requests derivation and verifies. Under that rule Accord holds no authority logic, so "Accord without Ananke" is incoherent — which proves Accord's authority role is a function call, not a component. Verdict: Ananke load-bearing; Accord's authority role is not a layer.

3. Accord without Horae

Accord must then journal, reserve, recover and reconcile — becoming a durable-execution engine competing from scratch with Temporal, Restate and DBOS. Catastrophic and unnecessary.

The follow-on matters more: Horae already owns CONFIRMED/ABSENT/UNKNOWN and crash-after-effect reconciliation per the accepted evidence. So Accord's completion invariants restate, one layer up, semantics that already have a home. That is the second source of execution truth the appendix asks about, and the answer is yes. Verdict: Horae (or a commodity equivalent) load-bearing; Accord's completion role is duplication.

4. Ananke + Horae without Accord — the decisive test

What is actually lost? The brief names three gaps:

Gap	Natural owner without Accord
Portable nested delegation	An Ananke feature — grant derivation across a serialization boundary
Monotonic child-authority validation	An Ananke derivation rule; conformance-tested against the IETF draft
Remote task lifecycle supervision	A Horae activity wrapping an A2A/MCP client poll loop
The join — authority ↔ approval ↔ task ↔ effect evidence, externally verifiable	An Adrasteia record type + a standalone verifier binary

Ananke + Horae + three features + one Adrasteia record type + a verifier ≈ Accord, with no new runtime, no fourth layer, no second policy engine, and no second source of execution truth.

This is the strongest single argument in the review. The remove-a-component test fails for Accord itself: removing it and assigning its four responsibilities to their natural owners loses nothing except a box on a diagram. Verdict: Accord is an unnecessary integration layer as drawn. Answering the appendix's own first question — "Is Accord a necessary control plane, or an unnecessary integration layer?" — the honest answer from its own decomposition is the latter.

5. The research question without A2A

Loses nothing scientifically. Gains three things: testability today via loopback, external validity via ≥2 transports, and a publication venue.

A2A v1.0 defines no delegation, no attenuation, and no completion verification whatsoever — clients learn completion solely from the remote agent's own state transitions, and TASK_STATE_UNSPECIFIED is a protobuf default, not a semantic indeterminate outcome. A2A is therefore the thing that lacks these semantics: a good venue, a bad foundation.

On the appendix's related question — "Does MCP need a separate adapter if governance is transport-independent?" — no. You need a per-transport evidence mapping, which is a table, not an adapter stack. And the answer to "What minimum wire-level contract is needed?": four fields.

action_hash + nonce     (plane-issued; the only authority binding)
idempotency_key         (plane-chosen; must be echoed by the provider)
receipt_or_echo         (provider artifact; determines evidence class)
task_correlation_id     (hint only; NEVER load-bearing)

That is the whole wire contract. It fits in a header. It does not require implementing a protocol ecosystem — which is precisely what the appendix suspected and is right to suspect.

Verdict: A2A is a conformance target and a publication venue (SEP #1404), not a dependency.

L. REQUIRED CHANGES BEFORE IMPLEMENTATION

Blockers only.

Remove The Fates from the runtime path, or reclassify it against the accepted evidence and cost it as a fourth runtime. The current diagram contradicts ACCORD-00.
Resolve the call-direction ambiguity in the diagram. It admits both a layer-stack and a call-graph reading, which yield different attack surfaces. An architecture that cannot be read unambiguously cannot be red-teamed. I attacked the layer-stack reading; state which is meant.
Adopt the rule: Accord never mints authority. It requests derivation from Ananke and verifies the result. Eliminates the second policy engine and the interpretation-drift escalation path.
Single source of execution truth. Effect state lives in Horae. Accord may not maintain a parallel one.
Rewrite NO_VALID_AUTHORITY -> NO_EFFECT to -> NO_MEDIATED_DISPATCH, or adopt isolation. As written it is false in the deployed configuration.
Define "acceptable" as a published evidence-class taxonomy with per-class trust assumptions and per-class permitted verdicts.
Ship an externally runnable verifier taking (record, trust anchors) with zero plane-private state, emitting a verdict and the trust assumptions discharged. Without this the word "independent" in the research question is unsupported.
Add the lying and partially-lying child to the threat model, with adversarial child agents in the experiment. The invariant set currently addresses only the unauthorized child — the smaller half of the measured problem.
Add effect attribution as an explicit sixth term and require idempotency-key echo for any verdict above UNKNOWN.
Add a compensation model for revoked-in-flight effects, or explicitly remove revocation-after-dispatch from scope. Surfaced by the appendix's own question.
Replace or relabel the three tautological invariants. Definitions belong in a definitions section, not an invariant set.
Bound reconciliation deadlines below the shortest provider idempotency retention window, and define the verdict when that window expires.
Real external effects from ≥2 independent providers at ≥2 evidence classes, or the completion half is untestable and should not be claimed.
Pre-register a baseline (state re-read + cheap detector) and an abandonment margin, before any code.
Provide a loopback transport so the core is exercisable with zero wire protocol.
Rule: no transport-supplied identifier is load-bearing for authority or effect attribution.
M. OPTIONAL IMPROVEMENTS
Split the seven attenuation dimensions into their three real algebras (set-like / temporal / consumable) rather than one <=.
Quotient the grant relation by semantic equivalence so "partial order" is literally true.
Deterministic simulation testing (FoundationDB/Antithesis/TigerBeetle style) for the crash-after-effect window.
A small Alloy or TLA+ model of authority-instance × approval × reservation × effect-state, checked for: no CONFIRMED without a matching authorized reservation; no two CONFIRMED per action hash; UNKNOWN never reaching CONFIRMED without new evidence.
Contribute the monotonicity conformance suite to a2aproject/A2A SEP #1404 — external validation the project cannot otherwise obtain.
Evidence-class advertisement in agent cards / tool manifests, so callers can decline E0/E1 surfaces for material actions.
Drop mythological code names from technical prose.
Cite the atomic-commitment and clearing literature explicitly; not doing so will read as unawareness of thirty-year-old and current-year prior art respectively.
N. FINAL RECOMMENDED RESEARCH QUESTION

The current question must be split, because — frozen from Phase 1 §3 — each half is falsifiable without the other, and fusing them means the provable half cannot be accepted without the unprovable one.

Primary (keep, retarget, fund):

For external effect surfaces of varying evidence affordance, and delegates of varying honesty, what is the achievable frontier between false-confirmation rate, indeterminacy rate, duplicate-effect rate and human escalation load — and does a portable, externally verifiable record binding attenuated authority to attributed effect evidence improve that frontier over a durable-workflow baseline that simply re-reads provider state?

This is falsifiable, unaddressed in the literature, targets the empirically dominant failure mode, and produces a reusable instrument regardless of outcome.

Secondary (small, cheap, publish as conformance):

Does grant-level monotonic attenuation bound effective authority under sibling composition and parent-mediated laundering, at delegation depth ≥ 2?

Phase 1 predicted this one fails. A negative result here would be the most interesting finding the project could produce, and it costs a property-based test suite and a model checker — not a runtime.

Removed from both: truth, independent unqualified, exactly-once, prevent, and control plane.

Evidence basis

Search date: 14 September 2026. Documents read: ACCORD-01-BLIND-BRIEF.md, ACCORD-01-ARCHITECTURE-APPENDIX.md, ACCORD-01-EXTERNAL-REVIEW-TEMPLATE.md only. No repository code, no other ACCORD-* file, no commit history inspected in either phase.

Standards / specifications: A2A Protocol Specification (v1.0, Agentic AI Foundation / Linux Foundation) · MCP Specification 2026-07-28 and release notes · draft-niyikiza-oauth-attenuating-agent-tokens-01 · draft-araut-oauth-transaction-tokens-for-agents · draft-liu-oauth-chain-delegation-00 · draft-marques-asqav-compliance-receipts-06 · draft-chueayen-attestation-receipts-00 · A2A SEP #1404, capability-based authorization · Summer 2026 identity standards recap · AP2 announcement

Papers: False Success in LLM Agents (2606.09863) — the load-bearing empirical citation · Notarized Agents (2606.04193) · Proof-Carrying Agent Actions (2606.04104) · Five-Plane Reference Architecture (2606.12320) · Bounded Agents (2608.15888) · Overlaying Governance (2606.03518) · RAILS (2606.08790) · AgentFlow (2608.22868) · Authenticated Workflows (2602.10465) · Sovereign Execution Broker (2606.20520) · Identity Management for Agentic AI (2510.25819) · Governance Gaps in Agent Interoperability Protocols (2606.31498)

Systems / background: Restate — What is Durable Execution · Demystifying Determinism in Durable Execution · DBOS vs Temporal · Oracle two-phase commit / in-doubt transactions · Antithesis — deterministic simulation testing · TigerBeetle — protocol-aware DST · Ethereum — the oracle problem

Uncertainty and limitations, stated plainly:

Several arXiv items were assessed from abstract-level fetches, not full texts. Where a paper's precise scope matters to a classification — Bounded Agents' composition-soundness conditions, Five-Plane's attenuation evaluation — treat my reading as directional. Two of my ALREADY_SOLVED classifications could soften to PARTIALLY_SOLVED on full reading. None would move to OPEN_PROBLEM.
I attacked the layer-stack reading of the appendix diagram. A call-graph reading changes the trust-surface analysis in §F, though not the Fates contradiction or the two-sources-of-truth finding.
I have not seen Adrasteia, Ananke or Horae. All component-boundary reasoning derives from the brief's one-line responsibility summaries. If Horae's UNKNOWN semantics or Ananke's derivation rules differ materially from those summaries, §K.2–4 should be re-run against the real interfaces.
I could not verify the ACCORD-00 findings themselves; I took them as given and reasoned about their internal consistency, which is how the Fates contradiction surfaced.
My prior-art sweep was English-language, web-indexed, and conducted in one session. Vendor-internal and enterprise-proprietary systems in this space are numerous and invisible to it. Treat "no prior art found" as "none found," never as "none exists."