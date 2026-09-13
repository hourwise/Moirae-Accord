# Moirae Accord Architecture Appendix

Read this appendix only after freezing the independent analysis requested in [ACCORD-01-BLIND-BRIEF.md](ACCORD-01-BLIND-BRIEF.md).

This is a hypothesis, not accepted architecture and not an implementation commitment.

## Current hypothesis

```text
                   Moirae Accord
                         |
               +---------+---------+
               |                   |
           A2A adapter          MCP adapter
               |                   |
               +---------+---------+
                         |
                    The Fates
                         |
       +-----------------+-----------------+
       |                 |                 |
   Adrasteia           Ananke             Horae
   contracts           authority          durable execution
                                             +
                                        reconciliation
```

The hypothesis places a framework-independent synthesis layer above portable contracts, authority/policy, and durable execution. It treats A2A and MCP as possible transport boundaries and defers governed memory. The diagram is intentionally subject to rejection, replacement, or decomposition.

## Proposed core invariants

```text
CHILD_AUTHORITY <= PARENT_AUTHORITY

REMOTE_COMPLETED != VERIFIED_SUCCESS

UNKNOWN != SUCCESS

UNKNOWN != FAILURE

NO_VALID_AUTHORITY -> NO_EFFECT

NO_ACCEPTABLE_EFFECT_EVIDENCE -> NO_VERIFIED_SUCCESS
```

These are proposed research invariants, not claims that the current ecosystem implements all of them for nested delegation or remote agents.

## Questions for the red-team comparison

Compare the independent design against this hypothesis rather than accepting its vocabulary or decomposition.

### Boundary and ownership

- Is Accord a necessary control plane, or an unnecessary integration layer?
- Which concerns belong in a portable contract, an authority runtime, a durable workflow runtime, a transport adapter, or an application?
- Does the proposed boundary create a second policy engine or a second source of execution truth?
- Can an existing authority/durable-execution pair expose the required protocol without Accord?

### Trust and authority

- Which process is trusted to issue, attenuate, revoke, and attest to a child authority?
- Can Accord itself be bypassed, confused, replayed, or induced to overstate authority?
- Is a formal partial order sufficient to define `CHILD_AUTHORITY <= PARENT_AUTHORITY`?
- What are the semantics of scope, capability, deadline, approval, budget, audience, and representation attenuation?
- What happens when a parent is revoked after a child is reserved or after the effect boundary begins?

### Completion and effect truth

- What makes an effect receipt independent?
- Who is allowed to attest to `VERIFIED_SUCCESS`?
- Can the system distinguish “task completed,” “agent returned,” “provider accepted,” “effect occurred,” and “effect was independently observed”?
- Is `UNKNOWN` a meaningful terminal state, a reconciliation state, or both?
- When is `VERIFIED_NO_EFFECT` defensible?
- Do idempotency keys prevent duplicate effects, or merely make duplicate attempts recognizable?

### Interoperability

- Is A2A the correct boundary, or should the research remain protocol-neutral?
- Does MCP need a separate adapter if governance is transport-independent?
- Does the architecture accidentally make transport metadata authoritative?
- What minimum wire-level contract is needed to test the hypothesis without implementing an entire protocol ecosystem?

### Methodology and claims

- Which experiment could falsify the hypothesis?
- What failure cases must be demonstrated: authority widening, replay, duplicate dispatch, crash after effect, lost response, forged receipt, provider ambiguity, revocation race, or task/effect confusion?
- Are the proposed claims limited to the accepted local single-host evidence?
- What would count as a negative result and cause a pivot or rejection?
