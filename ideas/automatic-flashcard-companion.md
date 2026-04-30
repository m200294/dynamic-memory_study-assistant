---
title: Automatic Flashcard Companion
status: idea
created: 2026-04-30
---

# Automatic Flashcard Companion

## Summary

Add a supplementary system that automatically identifies course details,
concept fragments, definitions, terms, distinctions, examples, facts, formulas,
or other information that benefits from rote memorization, then turns them into
flashcards for spaced practice.

The flashcards should support the main learn and revise sessions rather than
replace them. They would preserve memory of layer 3 and layer 4-ish knowledge:
details that matter, but that are easy to forget unless they are rehearsed
directly.

## Motivation

The current study pipeline is strongest at deep encoding: concept explanation,
relationships, Bloom-level probing, weak-spot detection, and evidence-based
mastery tracking.

Some knowledge also needs a lighter memorization loop. Examples include:

- key terminology and definitions
- small but important distinctions
- named methods, models, or principles
- formula parts or procedural steps
- examples and counterexamples
- dates, authors, labels, acronyms, or classifications
- facts that support analysis but are not themselves deep concepts

These details can weaken a student's performance even when their conceptual
understanding is otherwise good. A flashcard companion would keep that memory
fresh without turning every revision session into recall drilling.

## Intended Behavior

The system should:

1. Scan source material, session notes, and compiled concept files for
   memorization-worthy items.
2. Decide whether each item is better suited to flashcard practice, deep
   questioning, or both.
3. Generate concise flashcards with clear prompts and answer criteria.
4. Attach cards to relevant concepts, weeks, sources, and weak spots.
5. Surface useful cards before, during, or after main revision sessions.
6. Record practice evidence separately from deep Bloom evidence.

The goal is not to reduce concepts to flashcards. The goal is to offload
maintenance of precise recall so revision sessions can spend more time on
understanding, application, analysis, and evaluation.

## Candidate Card Types

- Definition card: "What does X mean?"
- Distinction card: "How is X different from Y?"
- Cloze card: "The three parts of X are ..., ..., and ...."
- Example card: "Give an example of X."
- Counterexample card: "What would not count as X, and why?"
- Procedure card: "What is the next step after X?"
- Formula card: "What does each symbol in this formula mean?"
- Source-anchor card: "Which concept does this quoted phrase point to?"

## Relationship To Existing Study Sessions

During a learn session, the agent could flag details that look important but
too recall-heavy to spend much Socratic time on. At the end of the session,
those details could become candidate flashcards.

During a revise session, the agent could:

- warm up with a small number of relevant cards
- use failed cards as prompts for deeper conceptual questions
- recommend new cards when a weak spot is caused by missing recall
- keep flashcard performance separate from Bloom ratings unless the answer also
  demonstrates understanding or higher-level reasoning

## Evidence Rules

Flashcard success should not automatically imply conceptual mastery.

Possible evidence distinctions:

- Recall evidence: the student remembered the item correctly.
- Prompting evidence: the student needed hints or recognition cues.
- Concept evidence: the answer also showed understanding, relationship,
  application, analysis, or evaluation.

A student may remember a definition without understanding it. They may also
understand a concept but forget a label. The system should preserve that
difference.

## Open Design Questions

- Should generated flashcards live in a new `flashcards/` folder, in `inbox/`,
  or as compiled artifacts under a separate pipeline?
- What schema should represent cards, reviews, ease, due dates, and source
  links?
- Should flashcard generation happen during ingest, compile, or a separate
  command?
- How should duplicate cards be detected when the same detail appears in
  multiple sources?
- How can the system avoid generating low-value trivia cards?
- Should card scheduling be built into the pipeline or exported to an external
  tool such as Anki?

## Implementation Sketch

Add a flashcard generation pass that produces candidate cards from:

- `source-material/`
- `extra-resources/`
- `syllabus.md`
- `inbox/` session notes
- `knowledge/concepts/` compiled concept files

Each generated card could include:

```yaml
concept_slug: recursion
week: 1
source: source-material/week-01/lecture-notes.md
card_type: distinction
prompt: "How is recursion different from iteration?"
answer: "Recursion solves a problem through self-calls; iteration repeats using loops or repeated control flow."
tags: [recall, distinction, supplementary]
```

Future study sessions could then request:

```text
Revise recursion and include its flashcard warm-up.
```

## Acceptance Criteria For A Future Implementation

- The system can identify memorization-heavy details without treating every
  sentence as a card.
- Generated cards are linked back to source material and concepts.
- Flashcard practice can be used alongside normal revision sessions.
- Flashcard results do not directly overwrite Bloom ratings.
- Failed cards can create useful weak-spot evidence for later deep revision.
