---
title: Cued Recall Revision Skill
status: idea
created: 2026-05-01
---

# Cued Recall Revision Skill

## Summary

Create a dedicated revision-session skill for cued recall. The skill should
gauge how much of a topic the student can retrieve from memory by asking
questions that demand recall before recognition, explanation, or re-teaching.

When the student cannot recall the answer accurately, the agent should provide
graduated hints that help retrieval without giving the full answer away too
early. The goal is to strengthen memory retrieval while still preserving useful
evidence about what the student remembered independently, what required cues,
and what was not available even with support.

## Motivation

Normal revision often mixes recall, explanation, application, and repair. That
is useful, but it can hide a specific problem: the student may understand a
concept once it is visible, yet fail to retrieve the key facts, structure, or
terminology without cues.

This skill would make retrieval itself the object of practice. It should help
answer questions such as:

- Can the student recall the concept without being shown the answer?
- Which part of the concept disappears first?
- Does a small cue unlock the memory, or does the agent need to re-explain?
- Is the weakness a recall failure, a conceptual misunderstanding, or both?

The mode should be separate from ordinary revision so the agent does not
accidentally over-explain before testing recall.

## Relationship To Existing Revision Mode

The existing `revise` protocol already asks the agent to read the relevant
compiled concept, revisit weak spots, and probe weak or mid Bloom levels.

Cued recall revision should build on that protocol, but change the interaction
style:

- ask recall-heavy questions before giving summaries
- avoid leading questions at the start of each probe
- use hints only after a failed or incomplete retrieval attempt
- record how much prompting was required
- separate recall strength from deeper conceptual mastery

The session can still use:

```yaml
session_type: revise
mode: cued-recall
```

if the schema later supports a `mode` field. Until then, the mode can be noted
in the body of an `inbox/` revision note.

## Proposed Workflow

1. Read `.claude/skills/deep-encoding/SKILL.md`.
2. Read the relevant `knowledge/concepts/<slug>.md` if it exists.
3. Read relevant source material when the concept file is missing, thin, or
   ambiguous.
4. Identify recall targets:
   - definitions
   - named parts or steps
   - distinctions between nearby concepts
   - examples and counterexamples
   - cause-effect chains
   - common errors or misconceptions
5. Ask an initial free-recall prompt:

   ```text
   Without looking anything up, tell me everything you remember about X.
   ```

6. Read the student's answer and infer the highest-value recall targets that
   seem most likely to be retrievable with a cue.
7. Follow with targeted recall probes, starting with the least cued form and
   prioritizing likely-retrievable targets before unrelated missing material.
8. If the student struggles, move through a hint ladder.
9. Only reveal or re-teach the answer after the hint ladder shows that recall
   is not available.
10. Record each probe with the recall target, answer summary, hint level reached,
   outcome, and whether the issue looked like recall, understanding, or both.

## Likely-Retrievable Targeting

After the initial free-recall answer, the agent should not immediately quiz the
student on every missing item. It should first inspect what the student already
mentioned, half-mentioned, implied, confused, or approached indirectly.

The next probes should target the material the student is most likely to
recover with a small cue. This helps pull as much knowledge as possible out of
memory before the agent moves to colder, less connected gaps.

Signals that a target may be likely retrievable:

- the student used a nearby term but missed the exact term
- the student described a function but not the label
- the student gave one part of a pair, list, process, or contrast
- the student remembered an example but not the principle
- the student remembered a cause but not the consequence, or the reverse
- the student showed partial structure but left a named step blank
- the student's wording suggests familiarity even when the answer is incomplete

Suggested targeting order:

1. Ask about items the student explicitly mentioned but left incomplete.
2. Cue adjacent items that naturally pair with what they recalled.
3. Probe structures they partly reconstructed, such as missing steps in a
   process or missing sides of a distinction.
4. Use source-backed recall targets that were not mentioned only after the
   likely-retrievable material has been exhausted.
5. Move to answer reveal or re-teaching when repeated cues do not unlock recall.

The agent should make a judgement call after each answer:

```text
What is the most likely next thing this student can still retrieve if I give
one small, non-answer hint?
```

This rule is meant to maximize retrieval before teaching. It should not become
guesswork detached from the course material; the agent should still use concept
files and source material to decide which recalled fragments matter.

## Hint Ladder

The agent should use the smallest useful cue first.

Suggested hint levels:

- Level 0: no hint; pure recall.
- Level 1: broad context cue, such as the week, topic area, or problem type.
- Level 2: structural cue, such as the number of parts or the kind of relation.
- Level 3: partial cue, such as the first term, an example, or a contrast.
- Level 4: recognition cue, such as choosing between plausible options.
- Level 5: answer reveal and short re-teach.

The agent should not jump straight to the answer unless the student asks to
stop the recall attempt or the answer is needed to unblock the session.

## Example Interaction Pattern

Concept: recursion

1. "Without looking anything up, what do you remember about recursion?"
2. If the student says "it keeps calling itself" but misses termination, ask:
   "Good, you remembered the self-call part. What has to exist so it does not
   continue forever?"
3. "What are the two things a recursive solution usually needs?"
4. If the student struggles: "One part stops the process; the other part moves
   the problem toward that stopping point. What are they called?"
5. If still incomplete: "The first term starts with `base`. What is the full
   phrase, and what does it do?"
6. After the answer: "Now explain why missing that part causes a failure."

This preserves recall pressure first, then uses cues to rebuild access to the
memory.

## Evidence Rules

The session note should distinguish:

- independent recall
- recall after broad cue
- recall after structural cue
- recall after partial cue
- recognition only
- no recall, required answer reveal

Possible rating interpretation:

- `solid`: recalled accurately with no cue and connected it to meaning.
- `good`: recalled accurately with no cue or only a broad cue.
- `mid`: recalled with structural or partial cues.
- `weak`: recognition only, incorrect recall, or required answer reveal.

These ratings should only apply to the probed recall target or Bloom level. A
failed recall probe should not automatically downgrade higher-level conceptual
understanding unless the student's answer also showed misunderstanding.

## Recording Evidence

Useful fields to include in the session body:

- concept and source files consulted
- recall targets selected
- free-recall summary
- likely-retrievable targets inferred from the free-recall answer
- each targeted probe
- hint level reached
- answer summary
- recall outcome
- whether prompting was needed
- whether the weakness looked like memory access, concept confusion, or both
- recommended follow-up flashcards or revision targets

Example probe note:

```yaml
- bloom_level: remember
  recall_target: "base case and recursive case"
  question: "What are the two things a recursive solution usually needs?"
  answer_summary: "Remembered recursive case but missed base case until a partial cue."
  hint_level_reached: 3
  outcome: mid
  with_prompting: true
  weakness_type: recall
```

## Implementation Sketch

Add a new skill file, for example:

```text
.claude/skills/cued-recall-revision/SKILL.md
```

The skill should define:

- when to use cued recall revision
- how to select recall targets from concept files and source material
- how to infer likely-retrievable targets from the student's free-recall answer
- how to run the hint ladder
- how to avoid giving away answers too early
- how to distinguish recall evidence from understanding evidence
- how to write final notes to `inbox/`

The user could invoke it with prompts such as:

```text
Revise recursion using cued recall mode.
```

or:

```text
Run a cued recall revision session for week 2 core ideas.
```

## Acceptance Criteria For A Future Implementation

- The mode is clearly separate from ordinary revision sessions.
- The agent asks low-cue recall questions before explanation.
- The agent targets likely-retrievable material from the student's own answer
  before moving to cold gaps.
- Hints are graduated and do not reveal the full answer too early.
- Session notes record the highest hint level needed for each probe.
- Recall weakness is not confused with conceptual weakness unless the answer
  shows both.
- The output stays compatible with the existing inbox-first study pipeline.
