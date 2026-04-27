---
title: Bloom Evaluative Workframe
status: idea
created: 2026-04-27
---

# Bloom Evaluative Workframe

## Summary

Develop an evaluative workframe that helps an LLM identify a user's domain
knowledge from study-session evidence, understand the quality of that knowledge,
and assign a defensible rating using a future assessment framework.

The workframe should use Bloom's Revised Taxonomy as the backbone. For each
Bloom level, it should define what evidence the LLM needs before assigning
`mid`, `good`, or `solid`, while preserving the existing rule that ratings are
based only on what the user actually demonstrated.

## Motivation

The current study pipeline records evidence from learn and revise sessions, then
lets later tooling compile that evidence into concept mastery. A future
evaluation framework could make this more consistent by giving the LLM clearer
criteria for judging what kind of knowledge the user has shown.

The goal is not to let the LLM guess mastery from confidence, fluency, or length
of answer. The goal is to make it identify specific evidence:

- what the user recalled
- what relationships they explained
- what procedures they applied
- what distinctions or causes they analyzed
- what tradeoffs, judgements, or criteria they evaluated

The framework should also make prompting visible. An answer reached only after
heavy prompting should not receive the same rating as an answer the user gave
independently and in their own words.

## Design Principles

- Rate evidence, not vibes.
- Do not infer untested Bloom levels from adjacent performance.
- Separate domain correctness from communication polish.
- Treat prompting as part of the evidence.
- Prefer lower ratings when evidence is thin or ambiguous.
- Record weak spots even when the final answer improves.
- Reward transfer, explanation, and judgement more than memorized phrasing.

## Proposed Rating Scale

The project already has these ratings:

- `weak`: struggled, wrong, or could not answer
- `mid`: partial answer, got there with prompting
- `good`: clear answer in own words, handles relationships
- `solid`: deep answer, spontaneous connection, teaching-back quality
- `untested`: not probed

This idea expands what `mid`, `good`, and `solid` should mean at each Bloom
level. `weak` still applies when the user is incorrect, cannot proceed, or only
produces fragments that do not show usable understanding.

## Bloom Criteria

### Remember

The user can retrieve relevant facts, terms, definitions, steps, symbols,
events, or examples from the domain.

`mid` criteria:

- Recalls some key terms or facts but misses important details.
- Recognizes the concept when prompted but struggles to produce it unaided.
- Gives a definition that is partly correct but incomplete or too vague.
- Confuses nearby terms until the agent narrows the question.

`good` criteria:

- Accurately states core definitions, facts, or steps in their own words.
- Can name important components without relying on multiple-choice cues.
- Avoids major confusion with similar concepts.
- Can provide a basic example that matches the definition.

`solid` criteria:

- Recalls the concept quickly and accurately across different phrasings.
- Can distinguish it from close alternatives without prompting.
- Supplies precise examples, counterexamples, or edge cases from memory.
- Can teach the basic facts back clearly enough that another student could
  recognize the concept.

### Understand

The user can explain meaning, relationships, causes, implications, and the
"why" behind the concept.

`mid` criteria:

- Explains the concept only at a surface level.
- Gets the main idea but needs prompting to explain why it matters.
- Uses examples correctly after the agent provides or heavily shapes them.
- Shows partial relationships but leaves gaps between cause, effect, and
  significance.

`good` criteria:

- Explains the concept clearly in their own words.
- Connects the concept to related ideas, examples, or course themes.
- Can explain why a definition or rule works, not only repeat it.
- Can restate the idea for a different audience or context without losing
  correctness.

`solid` criteria:

- Gives a coherent explanation that includes meaning, mechanism, and
  significance.
- Spontaneously connects the concept to prior knowledge, contrasting concepts,
  or real examples.
- Handles follow-up questions without collapsing into memorized wording.
- Identifies common misunderstandings and explains why they are wrong.

### Apply

The user can use the concept, method, rule, or procedure in a relevant task or
case.

`mid` criteria:

- Can apply the idea to a familiar example with guidance.
- Follows a procedure but makes errors in ordering, assumptions, or details.
- Needs reminders about which rule, formula, or concept is relevant.
- Gets to a workable answer after correction or scaffolding.

`good` criteria:

- Chooses and applies the relevant concept correctly in a familiar task.
- Explains the steps taken and why they fit the problem.
- Notices ordinary mistakes or checks the result against the original context.
- Can adapt the concept to a slightly different example.

`solid` criteria:

- Applies the concept independently in unfamiliar or mixed contexts.
- Selects among possible methods and justifies the choice.
- Anticipates constraints, edge cases, or failure modes while applying it.
- Can walk someone else through the task while explaining both action and
  reasoning.

### Analyze

The user can break material into parts, identify relationships, compare cases,
trace causes, and explain structure.

`mid` criteria:

- Identifies some parts or differences but misses important relationships.
- Can compare examples after the agent supplies the comparison frame.
- Notices a cause or dependency but cannot fully trace its consequences.
- Gives a partially correct structure that needs reorganization or prompting.

`good` criteria:

- Breaks the concept, argument, system, or problem into meaningful parts.
- Explains how parts relate, depend on each other, or create outcomes.
- Compares similar concepts using relevant criteria.
- Can diagnose where an example fits, fails, or changes category.

`solid` criteria:

- Builds a clear structural model of the concept or problem.
- Identifies hidden assumptions, dependencies, tensions, or boundary cases.
- Explains tradeoffs between different interpretations or designs.
- Transfers the analysis frame to a new case without being handed the frame.

### Evaluate

The user can make justified judgements using criteria, evidence, tradeoffs, and
domain values.

`mid` criteria:

- Gives an opinion or judgement but relies on limited criteria.
- Identifies one tradeoff but misses competing priorities.
- Can evaluate when the agent supplies the criteria or asks leading questions.
- Gives a conclusion that is plausible but weakly justified.

`good` criteria:

- Makes a clear judgement and supports it with relevant domain criteria.
- Weighs at least two tradeoffs, constraints, or competing values.
- Uses evidence from the concept, source material, or example rather than
  preference alone.
- Can explain what would change their judgement.

`solid` criteria:

- Develops or selects appropriate evaluation criteria independently.
- Weighs multiple tradeoffs and explains why one criterion matters more in the
  given context.
- Recognizes uncertainty, limitations, missing evidence, or context dependence.
- Can defend, revise, or qualify the judgement under challenge.

## Evidence Capture Requirements

For each rated Bloom level, the session note should preserve:

- the question or task
- the user's answer summary
- the level being probed
- the rating assigned
- whether prompting was needed
- what evidence supported the rating
- what misconception, gap, or strength was observed

This gives the future framework enough data to audit why a rating was assigned.

## Example Evaluation Pattern

For the `understand` level:

Question:

```text
Explain why modularity can reduce software complexity, and name one way it can
also introduce complexity.
```

Possible outcomes:

- `mid`: The user says modularity "makes things simpler" and, after prompting,
  mentions separation into parts, but cannot explain dependency or interface
  complexity clearly.
- `good`: The user explains that modularity separates responsibilities, reduces
  the amount of code a developer must reason about at once, and notes that poor
  interfaces or too many dependencies can add coordination complexity.
- `solid`: The user explains the above, connects it to coupling and cohesion,
  gives a concrete design example, and identifies the tradeoff between local
  simplicity and system-level integration cost without being prompted.

## Relationship To Existing Pipeline

This should not replace the evidence rule. It should make the evidence rule
more explicit.

- Agent-run sessions should still write raw evidence to `inbox/`.
- `knowledge/` should remain compiled output.
- The compiler should remain responsible for canonical mastery updates.
- The framework can guide agents when writing probes, session summaries, and
  rating observations.
- Future validation could check that each rating has a probe and evidence
  statement attached.

## Possible Implementation Sketch

Add a rubric file or prompt section that agents must consult before assigning
observed ratings. The framework could be used in three places:

1. During a session, to choose probes that target specific Bloom levels.
2. During session-note writing, to justify observed ratings.
3. During compile, to normalize evidence across sessions and agents.

Potential future files:

```text
docs/bloom-evaluation-workframe.md
docs/schemas/probe-evidence.schema.json
scripts/evaluate_evidence.py
```

## Open Design Questions

- Should the framework rate only the current concept, or also cross-concept
  transfer?
- How much prompting is allowed before a rating must drop from `good` to `mid`?
- Should `solid` require transfer to a new context, or can a deep explanation
  inside the original context be enough?
- How should contradictory evidence across sessions be reconciled?
- Should the evaluator distinguish factual accuracy, reasoning quality, and
  confidence calibration as separate dimensions?
- How should the framework handle domains where Bloom levels overlap, such as
  mathematical proof, programming, design critique, or essay argument?

## Acceptance Criteria For A Future Implementation

- Each Bloom level from `remember` through `evaluate` has explicit rating
  criteria.
- Agents can justify every non-`untested` rating with session evidence.
- The framework makes prompting visible in the rating decision.
- The framework avoids upgrading mastery from unprobed or inferred ability.
- The criteria work across factual, technical, analytical, and judgement-heavy
  concepts.
- The pipeline can compile the evidence without writing directly to
  `knowledge/` during the study session.
