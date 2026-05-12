---
title: Recap Session Scale
status: idea
created: 2026-05-13
---

# Recap Session Scale

## Summary

Add a lightweight recap mode that helps the student quickly see what they have
understood so far in the current study session or across a selected group of
topics.

The mode should use the current chat log when available, plus existing
`knowledge/concepts/` files when relevant, to estimate the student's current
understanding. It should then ask the student to explain the selected topics in
their own words, identify major misunderstandings briefly, and give a compact
holistic recap that helps decide what to do next.

The point is not to run a full revision session. The point is to provide a
fast orientation layer: what has been covered, what seems understood, what is
fragile, and whether the next best move is to continue, consolidate, or repair.

## Motivation

During a learn session, the student may reach a natural pause point and want to
know whether the pieces are fitting together. A normal summary can be too
passive, because it tells the student what was covered without checking what
they can actually explain. A full revision session can be too heavy, because it
interrupts the learning flow.

Recap Session Scale should sit between those two modes.

It answers questions such as:

- What does the student seem to understand from the topics covered so far?
- Which explanations are coherent, and which are only surface-level?
- Are there any major misunderstandings that should be corrected before moving
  on?
- Which topics should be consolidated now rather than left until later?
- Is the student ready to continue into the next subtopic?

## Relationship To Existing Modes

This mode overlaps with revision, relationship exploration, and cued recall, but
has a different purpose.

Normal revision asks:

```text
What should be repaired or retained from prior study?
```

Relationship Explorer asks:

```text
How well does the student understand links between concepts?
```

Recap Session Scale asks:

```text
At this point in the session, what is the student's current working picture?
```

It should be usable inside a learn session without turning the whole session
into revision.

## Intended Inputs

The student can ask for a recap in two ways:

- recap everything covered so far in the current session
- recap a named group of topics, concepts, or subtopics

The agent should use whichever evidence is available:

- current chat log from the active study session
- existing `knowledge/concepts/<slug>.md` files
- recent session notes if the relevant prior evidence is accessible
- source material only when needed to check correctness or resolve ambiguity

The chat log should be treated as the freshest evidence. Compiled concept files
can provide context about older weak spots, solid connections, and previous
probe outcomes, but the recap should not pretend the student demonstrated
something in the current session unless they actually did.

## Proposed Workflow

1. Identify the recap scope:
   - all topics covered so far
   - a student-provided topic group
   - a concept cluster inferred from recent conversation
2. Review the current chat log and relevant `knowledge/concepts/` files.
3. Build a short internal map:
   - topics covered
   - what the student explained well
   - thin or missing links
   - visible misunderstandings
   - topics that look ready to continue
   - topics that need consolidation first
4. Ask the student to explain the selected topics before giving the recap.
5. Use targeted prompts such as:

   ```text
   Before I recap, explain X, Y, and Z in your own words and how they connect.
   ```

6. Compare the answer against the chat log, concept files, and source-backed
   understanding.
7. If there are major misunderstandings, point them out first and briefly.
8. Give the recap:
   - compact map of what has been covered
   - how the pieces connect
   - what the student seems to understand
   - what remains fragile
   - suggested next study decision
9. Continue the study session from the student's chosen next step.
10. If the recap produces useful evidence, record it in the eventual `inbox/`
    session note as current-session evidence.

## Recap Interaction Pattern

The agent should avoid immediately summarizing. It should first make the student
retrieve and organize the material.

Example:

```text
Before I recap this section, explain these three things:

1. What X means.
2. Why Y matters.
3. How X and Y connect to Z.
```

After the student's answer, the agent should respond in this order:

1. Correct major misunderstandings briefly.
2. Confirm the strongest parts of the student's current model.
3. Provide the holistic recap.
4. Recommend the next best study move.

The correction should be concise. The recap should not become a long re-teach
unless the student's answer shows that the topic is too unstable to continue.

## Misunderstanding Handling

Major misunderstandings should be surfaced before the recap so the student does
not integrate a false model into the bigger picture.

The agent should:

- correct only the misunderstandings that would distort the recap
- separate incorrect claims from merely incomplete claims
- avoid overwhelming the student with every small wording issue
- explain the correction in one or two sentences where possible
- then continue with the recap rather than derailing into a full lesson

If the misunderstanding is central, the next study decision may be:

```text
Pause and repair this before moving on.
```

If the weakness is minor, the next decision may be:

```text
Continue, but revisit this link later.
```

## Decision Scale

The recap should produce an actionable recommendation rather than only a
summary.

Suggested scale:

- `continue`: the student's working model is coherent enough to move on
- `consolidate`: the student broadly understands the material but needs a short
  strengthening pass
- `repair`: a misconception or missing foundation would make the next topic
  unreliable
- `branch`: the student should choose between multiple useful next subtopics
- `revise later`: the topic is good enough for now but should be scheduled for
  future revision

The scale is not a canonical mastery rating. It is a local session decision
based on current evidence.

## Evidence Rules

Recap Session Scale should not invent Bloom ratings or mastery changes.

It may record evidence such as:

- topics the student explained independently
- connections the student made or missed
- misunderstandings corrected during the recap
- whether the recap led to continue, consolidate, repair, branch, or revise
  later
- any follow-up probes asked during the recap

If saved in `inbox/`, the note can use the existing session type:

```yaml
session_type: learn
mode: recap-session-scale
```

or, if the recap is a standalone interaction:

```yaml
session_type: other
mode: recap-session-scale
```

The compiler can later decide whether the evidence affects concept files.

## Guardrails

- Do not treat a recap as proof of mastery unless the student actually explains
  or reasons through the material.
- Do not overwrite the student's current study flow with a long revision
  sequence unless the recap exposes a central misunderstanding.
- Do not update `knowledge/` directly.
- Use source material only as needed; the primary focus is the student's
  demonstrated working model.
- Keep the recap compact enough that it helps orientation rather than becoming
  another lecture.

## Open Questions

- Should this become a dedicated skill, or remain a behavior inside learn and
  revise sessions?
- Should the decision scale be represented in session notes as a formal field?
- How much previous chat history should the agent search when the current
  context has been compacted?
- Should recap sessions generate follow-up tasks automatically, or only suggest
  them?
- How should the system distinguish a recap correction from a full repair
  lesson in compiled evidence?

## Definition Of Done

- The agent can run a quick recap at a pause point during a study session.
- The student is asked to explain the covered topics before receiving the recap.
- Major misunderstandings are corrected briefly before the holistic summary.
- The recap gives a clear next study decision: continue, consolidate, repair,
  branch, or revise later.
- Any evidence recorded from the recap is written to `inbox/`, not directly to
  `knowledge/`.
