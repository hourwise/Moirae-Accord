# ACCORD-01 External Review Template

Return one primary verdict and complete every section. A rejection or pivot is an acceptable successful result.

## A. PRIMARY VERDICT

Choose exactly one:

```text
CONTINUE
CONTINUE_WITH_CHANGES
PIVOT
REJECT
```

Rationale:

## B. PROBLEM VALIDITY

Is the problem real, useful, and operationally precise? Which actors, effects, and trust boundaries are in scope?

## C. PRIOR ART / NOVELTY

What already solves this? What remains genuinely open? What terminology, research communities, standards, or systems are missing from the framing?

## D. BLIND ARCHITECTURE

What would you build independently before seeing the architecture appendix? Include the minimum experiment and its failure modes.

## E. COMPARISON TO ACCORD HYPOTHESIS

Where do the two designs converge? Where do they diverge? Which design elements should be removed, moved, or replaced?

## F. TRUST-MODEL ATTACK

Where is trust actually located? Can Accord itself lie, be bypassed, be replayed, or be confused? Which trust roots are assumed rather than evidenced?

## G. AUTHORITY-MODEL ATTACK

Is `CHILD_AUTHORITY <= PARENT_AUTHORITY` sufficiently defined? What formal semantics, data model, partial order, or proof obligations are required?

## H. COMPLETION / EFFECT ATTACK

Can the proposed system actually know what happened? Who is allowed to attest to effects? How are task completion, provider acceptance, effect occurrence, and independent verification distinguished?

## I. METHODOLOGY ATTACK

Can the planned experiment falsify the claim? What observations would constitute failure? What evidence would justify `VERIFIED_SUCCESS`, `VERIFIED_NO_EFFECT`, and `UNKNOWN`?

## J. TERMINOLOGY ATTACK

Evaluate the terms:

- truth
- verified
- independent
- completion
- effect
- exactly-once
- authority
- delegation

Recommend replacements where needed.

## K. REMOVE-A-COMPONENT TEST

Evaluate each:

- Accord without Adrasteia;
- Accord without Ananke;
- Accord without Horae;
- Ananke + Horae without Accord;
- the research question without A2A.

## L. REQUIRED CHANGES BEFORE IMPLEMENTATION

List blockers only. Do not include optional improvements here.

## M. OPTIONAL IMPROVEMENTS

List non-blocking recommendations separately.

## N. FINAL RECOMMENDED RESEARCH QUESTION

Rewrite the research question if necessary. If no rewrite is needed, explain why.

## Evidence basis

List sources consulted, search date, relevant versions/SHAs, and any uncertainty or limitation in the review.
