---
title: Declarative-Procedural Bridging
status: idea
created: 2026-05-09
---

# Declarative-Procedural Bridging

## Summary

Create a study skill that deliberately bridges the gap between declarative
understanding and procedural performance.

The student may first discuss the concepts behind a procedural topic, such as
mathematics, programming, problem solving, proof writing, debugging, or
algorithm design. Once the agent has gauged the student's conceptual
understanding, it should immediately create targeted procedural exercises that
force the student to use the concept in practice.

The core principle is:

```text
Explain the idea, then attempt the action while the explanation is still fresh.
```

This is similar to watching instructions about swimming fast or riding a bike.
The instruction may be useful, but real competence only appears when the
student tries to swim, ride, calculate, code, prove, debug, or solve. The skill
should therefore pair conceptual discussion with immediate action so the
student can discover the distance between understanding the topic and being
able to perform it.

## Motivation

The existing study pipeline can help a student explain concepts, compare ideas,
and reason about why something works. For procedural subjects, this is not
enough. A student can understand an explanation of a derivative, recursion, a
data structure, or a proof technique, then still freeze when asked to use it
without guidance.

Declarative-Procedural Bridging should make that gap visible and trainable.
Rather than treating explanation and practice as separate sessions, the agent
should move fluidly between them:

- discuss the concept
- check what the student appears to understand
- create a small exercise that uses exactly that concept
- observe where the student hesitates, misapplies, or succeeds
- repair the conceptual model if needed
- generate another exercise that tests the repaired understanding

The goal is not only to teach a concept. The goal is to test whether the
student can operationalize it.

## Core Idea

Declarative knowledge answers questions such as:

- What does this concept mean?
- Why does this method work?
- When should this technique apply?
- What are the steps or rules?
- How does this concept relate to nearby concepts?

Procedural knowledge answers questions such as:

- Can the student execute the steps without being led?
- Can they choose the method when it is not named in the question?
- Can they recover from mistakes?
- Can they translate the concept into code, equations, diagrams, proofs, or
  decisions?
- Can they complete the task under realistic constraints?

This skill should keep both forms of knowledge connected. A conceptual
discussion should naturally produce a next action:

```text
You explained the concept. Now use it.
```

Likewise, a procedural failure should lead back to the concept:

```text
The attempt failed here. What part of the concept did the procedure depend on?
```

## Intended Workflow

1. Select a procedural topic or concept.
2. Ask the student to explain the idea, method, rule, or intuition in their own
   words.
3. Probe the explanation enough to identify the current declarative model:
   - what the student understands
   - what they only recognize
   - what they confuse with nearby concepts
   - what steps or conditions they omit
   - what examples they can or cannot generate
4. Create an immediate procedural exercise targeted at the exact conceptual
   state observed.
5. Have the student attempt the exercise before receiving a full worked
   solution.
6. Compare the attempt against the earlier explanation:
   - Did the student use the concept they described?
   - Did the explanation contain a hidden gap?
   - Did the student know what to do but fail in execution?
   - Did they execute mechanically without understanding why?
7. Give focused feedback that connects the procedural error back to the
   concept.
8. Generate a second exercise that isolates the repaired gap or increases
   transfer demand.
9. Record evidence about both the conceptual understanding and the procedural
   performance.

## Exercise Design Rules

The exercises should be small enough to attempt immediately, but specific
enough to reveal whether the student can bridge from concept to action.

Good bridging exercises should:

- target one recently discussed concept or relationship
- require the student to perform, not only explain
- avoid naming the exact procedure when transfer is being tested
- include enough variation to prevent rote copying
- expose common mistakes linked to the concept
- create observable evidence, such as code, calculations, proof steps, traces,
  diagrams, or decisions
- lead naturally into a next repair question or follow-up exercise

The agent should avoid generic practice that does not depend on the preceding
discussion. If the student just discussed recursion termination, the next
exercise should make termination matter. If the student just explained why a
matrix operation is valid, the next exercise should require them to decide
whether a concrete operation is allowed and then perform it.

## Example Domains

### Programming

Conceptual discussion:

```text
Explain why a function should have a clear input and output.
```

Immediate procedural bridge:

```text
Here is repeated code that calculates three different totals. Extract the
shared logic into a function, choose its parameters, and call it in each case.
```

Follow-up repair:

```text
Your explanation mentioned clear outputs, but your function prints instead of
returning. What changes if another part of the program needs to reuse the
result?
```

### Mathematics

Conceptual discussion:

```text
Explain what the chain rule is trying to account for.
```

Immediate procedural bridge:

```text
Differentiate three composed functions. For each one, mark the outer function,
the inner function, and where the derivative of the inner function appears.
```

Follow-up repair:

```text
You identified the composition correctly but omitted the inner derivative in
the second problem. What part of your explanation predicts that missing step?
```

### Proof Writing

Conceptual discussion:

```text
Explain why proving a universal statement usually requires an arbitrary
element.
```

Immediate procedural bridge:

```text
Write the first five lines of a proof for a universal statement without using a
specific example as the main object.
```

Follow-up repair:

```text
Your proof started with one example. How does that differ from the arbitrary
object your explanation described?
```

### Debugging

Conceptual discussion:

```text
Explain the difference between a syntax error, a runtime error, and a logic
error.
```

Immediate procedural bridge:

```text
Classify these three broken snippets, predict what will happen, and fix each
one.
```

Follow-up repair:

```text
You described logic errors as code that runs but gives the wrong result. Which
snippet matched that description, and why did your first fix treat it like a
syntax problem?
```

## Bridging Patterns

The skill can use several repeatable patterns.

### Explain Then Execute

The student explains a method, then immediately performs it on a fresh example.

Use when the agent needs to test whether the explanation is actionable.

### Predict Then Attempt

The student predicts what should happen before doing the procedure.

Use when the concept involves cause and effect, code execution, algebraic
transformation, proof strategy, or system behavior.

### Diagnose Then Repair

The student uses a concept to identify an error, then fixes it.

Use when misconceptions are visible through buggy code, invalid algebra,
incorrect proof steps, or flawed reasoning.

### Choose Then Perform

The student chooses which method applies, then carries it out.

Use when the main gap is method selection rather than mechanical execution.

### Compare Then Implement

The student compares two conceptual options, then implements or applies the one
they selected.

Use when the topic involves tradeoffs, design choices, data structures,
algorithm selection, or proof approaches.

## Evidence Rules

The session should record both sides of the bridge.

Declarative evidence:

- what the student could explain
- which terms, distinctions, or conditions they recalled
- whether their explanation was accurate, partial, or misleading
- whether they could connect the concept to examples

Procedural evidence:

- what the student attempted
- whether they selected the right procedure
- whether they executed the steps correctly
- where they needed prompting
- whether the error came from conceptual confusion, execution weakness, or both
- whether a repaired explanation improved the next attempt

The agent should not mark procedural competence from explanation alone. It
should also avoid treating one failed attempt as proof that the student lacks
all conceptual understanding. The useful evidence is the relationship between
what the student said and what they could do.

## Relationship To Procedural Ascension

Declarative-Procedural Bridging is a session-level interaction pattern.
Procedural Ascension is a broader practice ladder.

The bridge can happen inside a single explanation or revision session:

```text
Discuss a concept, then immediately test the ability to use it.
```

Procedural Ascension can then take the evidence from that bridge and turn it
into a longer sequence of increasingly demanding exercises.

In other words:

- Declarative-Procedural Bridging reveals the gap.
- Procedural Ascension trains the gap over time.

## Implementation Sketch

This could become a documented skill or mode for agent-led study sessions.

Possible command:

```text
Let's bridge the concept and procedure for <topic>.
```

Agent protocol:

1. Read the relevant source material and concept files.
2. Ask for or elicit a conceptual explanation.
3. Summarize the student's apparent declarative model.
4. Generate one immediate targeted exercise.
5. Let the student attempt it with minimal scaffolding.
6. Evaluate the attempt against the concept just discussed.
7. Repair the concept or procedure.
8. Generate a second bridge exercise.
9. Save the session note to `inbox/` with explicit declarative and procedural
   evidence.

Possible note fields:

```yaml
session_type: revise
mode: declarative-procedural-bridge
topic: "<topic>"
declarative_summary: "<what the student could explain>"
procedural_task: "<exercise attempted>"
attempt_summary: "<what the student did>"
bridge_gap: "<gap between explanation and execution>"
repair: "<feedback or re-teaching given>"
follow_up_task: "<next targeted exercise>"
evidence:
  declarative: "<rating or notes>"
  procedural: "<rating or notes>"
```

## Acceptance Criteria For A Future Implementation

- The agent can move from conceptual explanation to targeted procedural
  exercise in the same session.
- Exercises are generated from the student's demonstrated conceptual state, not
  from a generic worksheet.
- Session notes distinguish declarative understanding from procedural
  performance.
- The bridge gap is explicitly recorded when explanation and execution diverge.
- Follow-up exercises target the observed gap rather than repeating the same
  task blindly.
- The existing evidence rule is preserved: competence is updated only from what
  the student actually demonstrates.

## Open Design Questions

- Should this be a standalone skill or a mode inside existing revision and
  procedural practice skills?
- How many bridge attempts should happen before moving into a longer practice
  ladder?
- Should the agent always ask for a conceptual explanation first, or can it
  infer the concept from a failed procedure?
- How should the compiler represent a gap where declarative evidence is strong
  but procedural evidence is weak?
- Should procedural evidence use the same Bloom levels, a separate fluency
  scale, or both?
