---
title: Ascension Revision Mode
status: idea
created: 2026-04-27
---

# Ascension Revision Mode

## Summary

Add an advanced revision mode that uses the student's existing knowledge record
to find the boundary of their current understanding, then deliberately pushes
just beyond that boundary.

The mode should behave like a stricter form of revision. Instead of only
repairing known weak spots, it should probe toward the edge of the student's
current mastery, introduce nearby module-relevant concepts when useful, and aim
to move each Bloom level toward `solid` evidence.

## Motivation

Normal revision is good for checking memory, revisiting weak spots, and
repairing previously failed probes. Ascension revision has a different purpose:
it should stretch the student's knowledge to the highest useful level within the
scope of the module.

The mode is based on the idea of comprehensible input. Questions should not be
randomly difficult or outside the course. They should sit just beyond what the
student already knows: close enough that the student can reason toward the
answer, but difficult enough to reveal the limit of their understanding.

The aim is not arbitrary trivia, premature specialization, or testing unrelated
content. The aim is high mastery of the knowledge the student actually needs.

## Relationship To Existing Revision Mode

The current `revise` flow already supports part of this:

- read the existing concept file
- revisit weak spots
- re-ask useful failed probes
- probe weak or mid Bloom levels
- record evidence without inventing mastery

Ascension revision should build on that foundation, not replace it.

Normal revision asks:

```text
What does the student still need to repair or retain?
```

Ascension revision asks:

```text
Where is the student's current ceiling, and what question would raise it?
```

## Proposed Workflow

1. Read the relevant `knowledge/concepts/<slug>.md`.
2. Identify current Bloom ratings, weak spots, solid connections, and unresolved
   weak or mid probes.
3. Read the relevant `source-material/week-NN/` files and `syllabus.md` so the
   stretch questions stay within module scope.
4. Build a short ascension map:
   - already solid areas
   - repair targets
   - likely ceiling points
   - adjacent module-relevant concepts
   - Bloom levels that can still be pushed higher
5. Start with diagnostic probes to verify the recorded mastery still holds.
6. Ask progressively harder questions:
   - first inside the known concept
   - then across related concepts
   - then in unfamiliar examples
   - then in judgement, tradeoff, or design scenarios
7. When the student reaches a limit, give enough explanation to make the next
   step reachable, then probe again.
8. Stop when the session has clear evidence of the current ceiling, not when the
   student has simply answered a fixed number of questions.
9. Save evidence to `inbox/` or canonical session logs using the existing
   `revise` session type until the schema supports a dedicated mode.

## Bloom-Level Ascension Strategy

### Remember

Push from basic recall toward fast, precise, flexible recall.

Ascension probes should ask the student to:

- recall definitions without cues
- distinguish close terms
- retrieve important components in varied order
- produce examples and counterexamples from memory

Target `solid` evidence:

- accurate recall across different phrasings
- precise distinction from nearby ideas
- independent examples or counterexamples

### Understand

Push from explanation toward relational understanding.

Ascension probes should ask the student to:

- explain why the concept matters
- connect it to prior knowledge
- explain causes, mechanisms, and consequences
- identify common misconceptions

Target `solid` evidence:

- coherent explanation of meaning, mechanism, and significance
- spontaneous links to related concepts
- ability to explain why a misconception is wrong

### Apply

Push from familiar use toward independent transfer.

Ascension probes should ask the student to:

- apply the concept in new but module-relevant cases
- choose between possible methods
- justify the selected approach
- notice constraints, edge cases, or failure modes

Target `solid` evidence:

- correct independent use in unfamiliar contexts
- justified method selection
- anticipation of ordinary mistakes or limitations

### Analyze

Push from comparison toward structural reasoning.

Ascension probes should ask the student to:

- break a case into meaningful parts
- trace dependencies, causes, or consequences
- compare similar concepts using explicit criteria
- identify hidden assumptions or tensions

Target `solid` evidence:

- clear structural model of the problem or concept
- transfer of the analysis frame to a new case
- recognition of assumptions, tradeoffs, or boundary cases

### Evaluate

Push from opinion toward justified judgement.

Ascension probes should ask the student to:

- make a judgement using domain criteria
- weigh competing tradeoffs
- defend or revise a position under challenge
- explain what evidence would change the judgement

Target `solid` evidence:

- independent selection of evaluation criteria
- justified prioritization among tradeoffs
- calibrated judgement that accounts for uncertainty or context

## Comprehensible-Input Guardrails

Ascension should be hard, but not arbitrary.

The agent should:

- stay within the module, syllabus, source material, or clearly relevant
  adjacent concepts
- avoid advanced content that does not improve course mastery
- introduce a new concept only when it helps explain or extend the current one
- mark any introduced idea as adjacent or extension material
- return to evidence from the student's answer before assigning a rating
- avoid treating confusion with brand-new material as failure of the original
  concept unless the link was clearly in scope

## Recording Evidence

Until the schema changes, ascension sessions can be recorded as:

```yaml
session_type: revise
```

The session body should explicitly state that the revision style was
`ascension`.

Useful evidence to record:

- the starting mastery state
- the ascension map
- the hardest successful probe
- the first probe that exposed the ceiling
- any adjacent concepts introduced
- whether the student reached the answer independently or with prompting
- which Bloom levels showed `solid` evidence
- which Bloom levels still need another ascension pass

## Possible Future Schema Change

Instead of adding a new top-level session type immediately, the cleaner future
change may be to keep `session_type: revise` and add a mode field:

```yaml
session_type: revise
mode: ascension
```

This avoids treating ascension as a completely separate kind of study evidence.
It is still revision, but with a more aggressive goal and protocol.

If a dedicated type is later preferred, validation would need to allow:

```yaml
session_type: ascension
```

That would require updates to validation, schemas, ingest, compile prompts,
documentation, and any progress summaries that group sessions by type.

## Relationship To Bloom Evaluative Workframe

This mode should use the future Bloom evaluative workframe as its rating guide.
The workframe defines what `mid`, `good`, and `solid` mean at each Bloom level.
Ascension revision defines how to generate the probes that can produce that
evidence.

In short:

```text
Bloom workframe = how to judge evidence
Ascension mode = how to create stronger evidence
```

## Open Design Questions

- Should ascension target one concept deeply or a cluster of related concepts?
- How many failed stretch probes are useful before the session becomes
  demoralizing or inefficient?
- Should the agent reveal the ascension map to the student before probing, or
  keep some of it implicit?
- How should the system distinguish a productive ceiling from a simple lack of
  prerequisite knowledge?
- Should introduced adjacent concepts become new concepts, weak spots, or just
  notes in the session body?
- Should progress dashboards track concepts that are `solid` at every Bloom
  level?

## Acceptance Criteria For A Future Implementation

- The mode starts from existing concept mastery, weak spots, and probe history.
- Stretch questions stay within the module or clearly useful adjacent material.
- The session identifies the student's current ceiling rather than only
  retesting old questions.
- The mode can produce evidence for `solid` ratings across Bloom levels.
- Prompting is recorded and prevents unsupported promotion to `good` or `solid`.
- Adjacent concepts are marked clearly and are not confused with required
  mastery unless source material supports them.
- The implementation works with the current evidence rule and does not write
  directly to `knowledge/` during the session.
