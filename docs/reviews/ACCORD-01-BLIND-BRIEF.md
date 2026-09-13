# Moirae Accord Independent Review Brief

## Review purpose

You are not being asked to validate this project.

Your first responsibility is to determine whether it should exist at all.

This is a blind, adversarial review of a proposed research direction. You may conclude `CONTINUE`, `CONTINUE_WITH_CHANGES`, `PIVOT`, or `REJECT`. A rejection is a valid successful outcome.

Complete this brief before reading `ACCORD-01-ARCHITECTURE-APPENDIX.md`. The appendix contains a preferred design hypothesis and is intentionally withheld during the first phase so that your initial framing is independent.

## Research question

Principal question:

> When one AI agent delegates work to another, can an independent deterministic control plane prevent both privilege escalation and false completion — ensuring that a child never gains more authority than its parent, and that a task is never reported as successfully complete until its real-world effects are independently evidenced or explicitly classified UNKNOWN?

Technical formulation:

> Can interoperable agents be composed through a framework-independent control plane that binds delegated authority, task identity, effect identity, human approval, retries, reconciliation and evidence into one durable execution record without trusting an agent's own claim that it finished?

These are questions, not conclusions. No novelty claim is being made here.

## Existing evidence

The underlying ecosystem audit was completed as ACCORD-00 using isolated snapshots of eight named repositories. The audit was read-only and the accepted local evidence is preserved at the ACCORD-00 commit/tag.

Evidence-backed findings include:

- canonical human, service, agent, and runtime principal representations already exist;
- authenticated, acting, and represented-principal context already exists;
- delegation request and descriptor foundations exist;
- bounded resource scope and purpose fields exist;
- durable human approval, approval binding, expiry, revocation, and dispatch reservation exist in the accepted approval lineage;
- durable execution identity, action hashes, authority-instance binding, and execution reservations exist;
- local cross-process claims and arbitration exist;
- effect receipts with binding and provenance exist;
- `CONFIRMED`, `ABSENT`, and `UNKNOWN` effect states exist in the accepted durable-execution lineage;
- crash-after-effect reconciliation exists for the accepted local single-host scope;
- MCP discovery/execution adapter foundations exist;
- no A2A implementation was found in the inspected ecosystem;
- portable nested delegation is not currently complete;
- monotonic child-authority validation is not currently complete;
- remote task lifecycle supervision is not currently complete;
- distributed consensus, multi-host exactly-once execution, and production effect verification are not established by the accepted evidence.

These findings distinguish accepted runtime behavior from proposals, candidates, evidence-only repositories, and hackathon material. They do not establish that the research question is novel, important, or unsolved.

## Existing components

The inspected ecosystem contains components with these broad responsibilities:

**Adrasteia** — portable identity, runtime, capability, correlation, delegation-shape, and resource-scope contracts.

**Ananke** — authority, policy, approval, governed admission, authority reservation, and effect-oriented outcomes.

**Horae** — durable execution intent, claims, lifecycle state, recovery, and effect reconciliation.

**Mnemosyne** — governed memory, source provenance, reliability, classification, and qualified retrieval; deferred from the current v0.1 boundary.

**Fates Integration** — compatibility locks, conformance material, and acceptance evidence; not a runtime.

This responsibility summary is descriptive. It does not prescribe that a future Accord system must use all of these components.

## Current proposed v0.1 constraints

These are provisional constraints supplied for review, not conclusions:

- one parent;
- one child;
- maximum delegation depth 1;
- maximum children 1;
- deterministic capability, resource, deadline, and approval attenuation;
- no arbitrary recursion;
- no provider-specific token or cost accounting;
- no Firecracker requirement;
- no distributed exactly-once claim;
- no production external-provider effect.

The reviewer should decide whether these constraints are coherent, sufficient, artificial, or premature.

## Prior-art warning

Existing work already covers substantial pieces of delegated authorization, capability attenuation, A2A task protocols, durable queues, idempotency, effect reconciliation, and capability-security models.

Perform an independent, current prior-art search. Do not rely on the earlier ecosystem audit or on the terminology used in this brief. Search adjacent fields as well as direct competitors, including authorization/delegation systems, workflow engines, distributed-systems failure semantics, capability security, agent protocols, and formal methods.

Do not assume that combining familiar mechanisms makes the research novel. Identify what is genuinely open, what is merely an integration problem, and what is already solved under different terminology.

## Required adversarial questions

Answer each question directly, with evidence or an explicit uncertainty:

1. Is the research question meaningful, operationally precise, and useful?
2. Is the problem already solved under different terminology?
3. Are delegated authority and effect verification actually one problem or two separable problems?
4. Is “completion truth” the correct framing, or would another framing be more rigorous?
5. Is “independent verification” defensible? Independent from which principal, process, provider, or trust root?
6. Does `UNKNOWN` create useful semantics, or merely expose unavoidable uncertainty?
7. Is a new Accord component justified?
8. Could existing authorization systems plus durable workflow engines solve the same problem without Accord?
9. Could the existing authority and durable-execution components directly expose the necessary protocol without a new layer?
10. Is A2A the correct interoperability boundary?
11. Does the trust model simply relocate trust into Accord?
12. Can the proposed experiment falsify the hypothesis?
13. What result would count as failure?
14. What evidence would justify `VERIFIED_SUCCESS`?
15. Would a formal authority partial order be required?
16. Would property-based or model-based testing be necessary?
17. Are the proposed claims stronger than the single-host evidence supports?

## Required blind-design exercise

Before reading the architecture appendix, answer:

> If you had the existing components described above, but had never seen our proposed Accord architecture, what system would you build to investigate the research question?

Produce an independent architecture, threat model, experiment plan, and falsification criteria. Do not optimize your design to resemble the authors’ preferred direction.

## Evidence discipline

Separate:

- observed implementation from documentation;
- accepted evidence from implementation candidates;
- local single-host guarantees from distributed claims;
- agent reports from independently corroborated effects;
- a useful research hypothesis from a product roadmap.

When evidence is missing, say so. Do not fill gaps by assuming that a type, document, test name, or successful process return proves an external effect.
