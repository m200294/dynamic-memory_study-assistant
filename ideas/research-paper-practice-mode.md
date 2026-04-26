---
title: Research Paper Practice Mode
status: idea
created: 2026-04-26
---

# Research Paper Practice Mode

## Summary

Add a study/practice mode where an LLM reads a research paper alongside the
student's existing course knowledge, then uses the paper to probe, extend, and
stress-test previously studied concepts.

The paper should not be treated as ordinary source material at first. Instead,
it should act as an advanced context for practice: a way to expose new angles,
examples, tradeoffs, terminology, and research-level implications connected to
concepts the student has already encountered.

## Motivation

Some courses introduce a concept in lectures, then recommend a research paper
for deeper reading. For example, a software development and design class may
teach modular complexity, then point students toward a paper that expands the
idea in a more technical or research-oriented way.

The student wants a different reading workflow:

1. The LLM reads the research paper.
2. The LLM identifies ideas in the paper that connect to concepts already
   studied.
3. The LLM tests the student's current understanding before explaining too much.
4. The LLM uses the paper to introduce new extensions, complications, and
   examples.
5. The session produces evidence about what the student understood, what was
   weak, and which paper-linked ideas should be revisited.

## Intended Workflow

1. Student provides or selects a research paper from `extra-resources/`.
2. Student identifies the relevant studied concept, or asks the agent to infer
   it from `knowledge/concepts/`.
3. Agent reads the concept file, relevant source material, and the research
   paper.
4. Agent builds a short concept-to-paper bridge map:
   - familiar concepts from existing knowledge
   - new terms or claims introduced by the paper
   - tensions, tradeoffs, or research questions raised by the paper
   - likely misconceptions or weak spots to probe
5. Agent runs a practice session:
   - starts with diagnostic questions about pre-existing knowledge
   - asks paper-context questions before giving full explanations
   - probes Bloom levels, especially `analyze` and `evaluate`
   - asks the student to connect paper claims back to lecture concepts
6. Agent writes evidence to `inbox/` as a normal external study note.
7. Existing ingest and compile steps decide how, if at all, concept mastery
   should change.

## Example

Concept: modular complexity

Paper context: a recommended software engineering research paper discussing
modularity, design structure, dependencies, or complexity metrics.

Possible probes:

- "Before using the paper's terminology, how would you explain why modularity
  can reduce complexity?"
- "What kind of complexity might modularity reduce, and what kind might it
  accidentally introduce?"
- "The paper treats dependencies as evidence of design structure. How does that
  connect to what you already know about coupling and cohesion?"
- "If two systems have the same external behavior but different module
  structures, what would the paper likely care about, and why?"
- "Do you agree with the paper's implicit judgement about what makes a design
  better? What tradeoff might it understate?"

## Relationship To Existing Pipeline

This mode should preserve the current evidence rule.

- Research papers can live in `extra-resources/`.
- Agent-run sessions should still write notes to `inbox/`.
- The mode should not write directly to `knowledge/`.
- The compiler should remain responsible for updating concept mastery.
- Paper-derived ideas should only affect mastery when the student actually
  demonstrates understanding during the session.

## Possible Session Type

This could use the existing `revise` session type if the main goal is to test
and deepen an existing concept.

If this becomes distinct enough, a future schema change could add:

```yaml
session_type: paper-practice
```

However, that would require updating validation, ingest, compile behavior, and
documentation. Until then, using `revise` with clear notes is safer.

## Open Design Questions

- How should the agent choose which existing concepts are relevant to a paper?
- Should the paper be summarized first, or should the student encounter its
  ideas through questions before summary?
- Should paper-specific claims become new concepts, weak spots, or extra
  resources attached to existing concepts?
- How should citations or page references be recorded in session notes?
- Should there be a dedicated folder for paper notes, or is `extra-resources/`
  enough?
- How much of the paper should the LLM reveal before probing the student's own
  reasoning?

## Implementation Sketch

Add a documented command or protocol such as:

```text
Let's practice modular complexity through the paper in extra-resources/...
```

The agent protocol could require:

1. Read `.claude/skills/deep-encoding/SKILL.md`.
2. Read `knowledge/concepts/<slug>.md` if it exists.
3. Read relevant lecture/source files.
4. Read the selected research paper.
5. Produce a brief bridge map.
6. Run a question-led practice session.
7. Save evidence to `inbox/YYYY-MM-DD-revise-<concept>-paper-practice.md`.

## Acceptance Criteria For A Future Implementation

- The agent can run a paper-based practice session without changing compiled
  knowledge directly.
- Session notes include the paper, source material, concept files, and probes
  consulted.
- Notes distinguish between what the paper claims and what the student
  demonstrated.
- Bloom ratings are only recorded for levels actually probed.
- The flow works with the current compile pipeline or has explicit schema
  changes with validation updates.
