---
title: Relationship Explorer
status: idea
created: 2026-04-30
---

# Relationship Explorer

## Summary

Add a targeted practice mode that starts from relationships the student has
already made, then probes those relationships with analysis and evaluation
questions.

The student can provide a mind map, or the agent can infer a relationship map
from existing `solid_connections`, weak connections, failed probes, and recorded
weak spots. The session then focuses on the quality of links between concepts or
sub-concepts rather than only revising each concept in isolation.

## Motivation

The current study pipeline can already record individual concepts, weak spots,
solid connections, Bloom ratings, and probe history. Relationship Explorer would
use that stored evidence more aggressively.

Students often remember separate concepts but lose marks when they need to:

- compare two similar ideas
- explain how one concept causes, constrains, or modifies another
- judge which concept matters more in a scenario
- notice that a familiar relationship breaks under different conditions
- transfer a connection from one example to another

Those are mostly higher-Bloom tasks. Relationship Explorer is meant to expose
weak connective tissue between ideas and strengthen mastery by making the
student reason across what they already know.

## Intended Inputs

The mode could start from either student-provided or system-derived material.

Student-provided inputs:

- a mind map
- a list of concept pairs
- a short explanation of how two ideas connect
- a topic area where the student feels their understanding is fragmented

System-derived inputs:

- `solid_connections` from compiled concept files
- weak spots that mention another concept
- failed or mid `analyze` and `evaluate` probes
- concepts with good lower-Bloom ratings but weaker higher-Bloom ratings
- related concepts from the same week, source file, or syllabus area

## Proposed Workflow

1. Read `.claude/skills/deep-encoding/SKILL.md`.
2. If the student provides a mind map, parse the concepts, sub-concepts, and
   claimed relationships.
3. If no mind map is provided, read relevant `knowledge/concepts/` files and
   build a relationship map from existing evidence.
4. Identify relationship targets:
   - strong links worth stress-testing
   - weak links worth repairing
   - missing links suggested by source material or prior probes
   - concept pairs where lower-Bloom knowledge exists but higher-Bloom evidence
     is thin
5. Start the session with analysis and evaluation probes rather than basic
   recall.
6. Ask the student to explain, compare, challenge, apply, or judge the target
   relationship.
7. If the student struggles, step down briefly to repair the component concept,
   then return to the relationship.
8. Record the current-session evidence in `inbox/` without directly modifying
   `knowledge/`.

## Probe Types

### Relationship Explanation

Ask the student to explain how two ideas connect and why the connection matters.

Example:

```text
How does coupling affect modular complexity, and why is that relationship
important when judging a design?
```

### Direction And Dependency

Test whether the student can identify the direction of influence, dependency,
or causality between concepts.

Example:

```text
Does abstraction reduce complexity directly, or does it change what kind of
complexity the designer has to manage? Defend your answer.
```

### Boundary And Breakdown

Ask when a relationship stops holding or becomes misleading.

Example:

```text
When might a technique that improves cohesion fail to improve maintainability?
What condition breaks the usual relationship?
```

### Tradeoff Judgement

Ask the student to evaluate a relationship using explicit criteria.

Example:

```text
If two designs improve different relationships, one reducing duplication and one
reducing coupling, which would you prioritize in this scenario and why?
```

### Missing-Link Diagnosis

Give a partial map and ask what relationship is missing or under-explained.

Example:

```text
Your map links encapsulation to maintainability and testing to reliability. What
relationship between encapsulation and testing might be missing?
```

## Bloom Strategy

Relationship Explorer should emphasize `analyze` and `evaluate`.

Useful `analyze` evidence:

- breaks a relationship into meaningful parts
- explains direction, dependency, cause, consequence, or constraint
- compares two relationships using relevant criteria
- identifies where an example fits or breaks a claimed link

Useful `evaluate` evidence:

- chooses between competing relationships or priorities
- justifies the judgement with domain criteria
- weighs tradeoffs instead of giving a one-sided answer
- explains what evidence or scenario change would alter the judgement

Lower Bloom levels can still be repaired during the session, but they should not
be the main starting point unless the relationship probe shows that a component
concept is missing.

## Relationship To Existing Study Sessions

Relationship Explorer is closest to a stricter revision session.

It should build on the existing revise flow:

- read relevant `knowledge/concepts/<slug>.md` files
- re-use failed probes where they involve relationships
- target weak spots and weak or mid higher-Bloom levels
- record Q&A evidence with Bloom level, answer summary, outcome, and prompting

The difference is that the primary unit of practice is a relationship, not a
single concept.

## Recording Evidence

Until the schema changes, Relationship Explorer can be recorded as:

```yaml
session_type: revise
mode: relationship-explorer
```

Useful session evidence:

- concepts and sub-concepts involved
- source of the relationship map
- relationship claims tested
- questions asked at `analyze` and `evaluate`
- whether the student could explain direction, dependency, tradeoff, or
  breakdown
- weak connections exposed
- solid connections strengthened
- component concepts that had to be repaired before the relationship made sense

The notes should preserve the existing evidence rule: only rate Bloom levels
that were actually probed or clearly demonstrated in the current session.

## Possible Future Schema Change

A future schema could explicitly represent relationship evidence:

```yaml
relationships:
  - from: coupling
    to: modular_complexity
    relation_type: contributes_to
    bloom_levels_probed: [analyze, evaluate]
    outcome: mid
    weak_spots:
      - "could describe both ideas but struggled to explain direction of influence"
    probes:
      - bloom_level: analyze
        question: "How does coupling affect modular complexity?"
        answer_summary: "Identified that more coupling can raise complexity, but needed prompting to explain why."
        outcome: mid
        with_prompting: true
```

This would let the compiler distinguish concept mastery from relationship
mastery.

## Open Design Questions

- Should relationship evidence live inside each concept file or in a separate
  relationship graph?
- How should the system represent relationships between sub-concepts rather than
  full concepts?
- Should a student-provided mind map be stored as source evidence, session
  evidence, or a separate artifact?
- How should the compiler decide whether a weak relationship affects one
  concept, both concepts, or only the connection between them?
- What minimum evidence is needed before a connection counts as `solid`?
- How should the agent avoid over-testing relationships that are interesting but
  not important to the syllabus?

## Implementation Sketch

Add a documented protocol such as:

```text
Run Relationship Explorer for modularity and complexity.
```

The agent protocol could require:

1. Read `.claude/skills/deep-encoding/SKILL.md`.
2. Read the relevant concept files and source material.
3. Build a compact relationship map from mind map input or compiled evidence.
4. Select two or three high-value relationships to test.
5. Start with `analyze` or `evaluate` probes.
6. Step down only when the student lacks a component concept.
7. Return to the original relationship after repair.
8. Save evidence to `inbox/YYYY-MM-DD-revise-<topic>-relationship-explorer.md`.

## Acceptance Criteria For A Future Implementation

- The agent can build or accept a relationship map before questioning starts.
- The first substantive probes target `analyze` or `evaluate`, not simple
  recall.
- Questions focus on relationships between concepts or sub-concepts.
- Session notes distinguish weak concepts from weak relationships.
- Evidence is written to `inbox/` and compiled later rather than written
  directly to `knowledge/`.
- The mode helps identify and strengthen higher-Bloom connections using the
  student's pre-existing knowledge.
