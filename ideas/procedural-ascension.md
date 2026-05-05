---
title: Procedural Ascension
status: idea
created: 2026-05-05
---

# Procedural Ascension

## Summary

Create a practice-generation system for procedural skills, especially
programming. Procedural Ascension is not a single skill lesson. It is a full
practice framework that helps a student turn newly learned programming concepts
into usable competence through repeated, increasingly demanding exercises.

The system should start with small, quick tasks that reinforce basic usage and
fight the forgetting curve. It should then ascend toward larger, more
integrated projects that require the student to combine concepts, make design
choices, debug their own work, and explain tradeoffs.

Examples of target concepts include:

- defining and calling functions in JavaScript or Python
- using directories and file organization
- working with lists, dictionaries, sets, arrays, and objects
- understanding mutable and immutable values
- writing loops and conditionals
- decomposing code into smaller units
- using imports, modules, packages, and project structure
- reading errors and debugging simple failures
- building small command-line, web, or data-processing applications

## Motivation

The existing study pipeline is strong at recording conceptual understanding:
what the student can recall, explain, apply, analyze, and evaluate. Programming
also requires procedural fluency. A student can understand a concept in words
but still struggle to use it when writing code.

Procedural Ascension should close that gap. After the student learns an initial
concept, the agent should generate practice tasks that force the student to use
the concept repeatedly across varied contexts. The goal is not only to check
whether the student remembers the idea, but whether they can produce working
outputs with it.

The system should treat projects and code artifacts as evidence. A student's
solution can reveal:

- whether they can select the right construct without being told
- whether they understand edge cases and data flow
- whether they can combine multiple concepts in one program
- whether their code is brittle, overcomplicated, or well structured
- whether they can debug and revise from feedback
- whether they can explain why their implementation works

## Core Idea

Procedural Ascension generates practice ladders from the student's current
knowledge web.

Instead of asking only:

```text
What does the student know about functions?
```

it asks:

```text
What can the student build with functions right now, and what exercise would
raise that capability one level?
```

The system should use stored knowledge, weak spots, prior session notes, and
source material to create exercises that are neither random nor generic. A
student weak on mutable data structures should receive tasks that make mutation
visible. A student who understands loops but struggles with decomposition should
receive tasks where repeated logic must be extracted into functions. A student
who can complete isolated snippets should be moved toward small integrated
programs.

## Practice Ladder

Procedural Ascension should organize exercises by increasing procedural demand.

### Level 1: Immediate Repetition

Short tasks completed soon after learning the concept.

Purpose:

- build initial motor memory
- make syntax and basic usage less fragile
- expose obvious misconceptions early
- create enough repetition to resist quick forgetting

Example tasks:

- write five functions that each transform one input into one output
- convert repeated code into a function
- create and update a list of values
- choose whether a set or list better fits a small task
- predict whether mutating a value changes another reference

### Level 2: Variation And Transfer

Small exercises that use the same concept in different contexts.

Purpose:

- prevent rote pattern matching
- force the student to recognize when the concept applies
- vary data types, input shapes, and constraints
- reveal shallow understanding hidden by familiar examples

Example tasks:

- write a function that filters numbers, then adapt it to filter strings
- use a dictionary/object to count frequencies in text
- rewrite a loop-based solution using helper functions
- build a small directory scanner or file organizer
- compare two implementations and explain which is easier to modify

### Level 3: Integrated Micro-Projects

Tasks that combine several recently learned concepts into a small useful
program.

Purpose:

- move from isolated technique to working program
- require planning, decomposition, and debugging
- surface relationships between concepts
- create more meaningful output for evaluation

Example tasks:

- build a command-line flashcard quiz
- create a grocery list manager using lists and dictionaries
- write a small script that organizes files by extension
- build a text statistics tool that counts words, unique words, and repeated
  terms
- create a tiny expense tracker with add, list, summarize, and delete commands

### Level 4: Constraint-Based Projects

Projects with explicit design constraints, tradeoffs, and review criteria.

Purpose:

- develop judgement rather than only completion
- force the student to make implementation choices
- reveal whether they can reason about structure and maintainability
- produce stronger evidence for higher Bloom levels

Example tasks:

- build the same tool twice, once using lists and once using dictionaries, then
  compare the designs
- implement a task without mutating input data
- refactor a working script so each function has a single responsibility
- add error handling to a program that currently assumes perfect input
- explain which data structure would become painful if the project grew

### Level 5: Personalized Ascension Projects

Larger exercises generated from the student's knowledge web and recent weak
spots.

Purpose:

- consolidate multiple concepts into durable competence
- target the student's actual weaknesses
- produce rich artifacts for evaluation
- create a path from beginner exercises toward independent project work

Example tasks:

- build a study-session note parser using files, functions, lists, dictionaries,
  and validation rules
- create a small habit tracker that persists data to a local file
- make a mini static-site generator from markdown files
- build a command-line todo application with tags, filtering, and summaries
- create a data-cleaning script that reads messy input and produces structured
  output

## Research Role

The agent should perform deep exercise research before generating a practice
ladder. The research goal is not to copy generic tutorials. It is to identify
creative, useful, varied task patterns that help the student practice the
specific concept.

Useful research targets:

- beginner programming exercise collections
- kata-style practice tasks
- project-based learning prompts
- language-specific idioms and common mistakes
- spaced repetition and deliberate practice patterns
- debugging exercises and code-reading prompts
- small projects that combine one new concept with older concepts

The output of research should be transformed into original exercises tailored
to the student's current knowledge state. The agent should avoid blindly
reusing tasks that do not match the student's level, language, or goals.

## Relationship To The Existing Knowledge System

Procedural Ascension should preserve the evidence rule. It should not mark a
student as competent because an exercise was assigned. It should update evidence
only when the student actually completes, explains, debugs, or improves an
output.

Existing Bloom-style evidence still applies, but the evidence source changes:

- `remember`: recalls syntax, terms, steps, and rules without constant cues
- `understand`: explains how the code works and why the construct matters
- `apply`: writes working code using the concept in a relevant task
- `analyze`: diagnoses bugs, traces data flow, compares designs, and identifies
  structure
- `evaluate`: judges tradeoffs, chooses data structures, defends design choices,
  and explains what should change as requirements grow

Procedural Ascension should also track procedural indicators that are not fully
captured by conceptual notes:

- independence level
- number and type of errors
- whether the student needed hints
- whether the final code runs
- whether the student can explain their own code
- whether the student can revise after feedback
- whether the solution transfers to a varied task

## Proposed Workflow

1. Student selects a programming concept, language, and rough difficulty.
2. Agent reads existing `knowledge/concepts/` entries, relevant session notes,
   and source material when available.
3. Agent identifies current strengths, weak spots, and adjacent concepts.
4. Agent researches creative exercise patterns for the target concept.
5. Agent builds a procedural ascension ladder:
   - quick repetition tasks
   - variation tasks
   - micro-projects
   - constraint-based extensions
   - optional personalized project
6. Student chooses a task or asks the agent to choose the best next task.
7. Student completes the exercise in their own environment or shared workspace.
8. Agent reviews the output for correctness, structure, concept use, and
   explanation quality.
9. Agent asks follow-up questions that probe understanding and judgement.
10. Agent records evidence to `inbox/` without directly editing compiled
    `knowledge/`.

## Exercise Generation Principles

Exercises should be:

- specific enough that the student knows what to build
- small enough to finish at the intended level
- varied enough to avoid memorized templates
- constrained enough to reveal the target concept
- open enough to require actual decisions at higher levels
- reviewable through code, output, explanation, or tests
- connected to the student's known weak spots

Exercises should avoid:

- vague prompts such as "practice functions"
- large projects before the student has basic fluency
- tasks where the target concept is optional or incidental
- over-scaffolded prompts that remove all decision-making
- hidden requirements that make evaluation unfair
- treating polished UI or cleverness as evidence of concept mastery

## Evaluation Criteria

The agent should evaluate submitted work using evidence from the artifact and
the student's explanation.

Useful criteria:

- correctness: does the program do what the prompt asked?
- concept targeting: does the solution actually use the intended concept?
- independence: how much prompting or correction was needed?
- transfer: can the student adapt the pattern to a related task?
- debugging: can the student find and fix issues?
- structure: is the solution decomposed appropriately for the level?
- readability: can the student or another beginner understand the code?
- judgement: can the student explain tradeoffs and limitations?

The evaluation should distinguish between:

- syntax mistakes
- conceptual misunderstanding
- weak procedural fluency
- poor problem decomposition
- missing edge-case reasoning
- incomplete explanation

## Recording Evidence

Until the schema supports a dedicated practice type, Procedural Ascension could
record sessions as:

```yaml
session_type: other
```

or as `revise` when the main purpose is targeted practice of an existing
concept. The session body should clearly identify the mode as
`procedural-ascension`.

Useful evidence to record:

- target language
- target concept or concept cluster
- practice ladder generated
- chosen exercise
- student's submitted code or output summary
- errors encountered
- hints or scaffolding provided
- final working state
- follow-up probes and answers
- observed Bloom ratings
- procedural weak spots
- next recommended exercise

Possible future schema fields:

```yaml
session_type: practice
mode: procedural-ascension
target_language: python
artifact_type: code
exercise_level: 3
artifact_status: runs
independence: partial-hints
```

Adding a dedicated `practice` session type would require updates to validation,
ingest, compile behavior, and documentation.

## Example Procedural Ascension Ladder

Target concept: functions in Python.

Level 1:

- Write a function `double(n)` that returns twice the input.
- Write a function `is_even(n)` that returns `True` or `False`.
- Write a function `greet(name)` that returns a greeting string.

Level 2:

- Write a function that takes a list of numbers and returns only the even ones.
- Write a function that takes a list of names and returns the longest name.
- Rewrite a repeated block of code into one reusable function.

Level 3:

- Build a command-line quiz where each question is checked by a helper
  function.

Level 4:

- Refactor the quiz so question loading, answer checking, scoring, and summary
  output are separate functions. Explain why each function boundary exists.

Level 5:

- Build a small spaced-repetition flashcard tool. Use functions to separate
  loading cards, selecting due cards, checking answers, updating scores, and
  saving results. After building it, explain which parts would need to change if
  the data moved from a text file to a database.

## Open Design Questions

- Should Procedural Ascension become a separate session type or remain a mode
  under `revise` or `other`?
- How should submitted code artifacts be stored: copied into inbox notes,
  linked from workspace paths, or summarized?
- Should the compiler derive concept mastery from code artifacts directly, or
  only from agent-written evidence summaries?
- How should the system distinguish language-specific syntax weakness from
  general programming-concept weakness?
- Should generated exercises include automated tests by default?
- How should the agent calibrate difficulty when the student has knowledge in
  one programming language but is learning another?
- How should spaced practice be scheduled across multiple procedural concepts?

## Acceptance Criteria For A Future Implementation

- The agent can generate a multi-level practice ladder for a selected
  programming concept and language.
- Exercises are tailored to existing knowledge, weak spots, and adjacent
  concepts.
- The system can evaluate student-produced code or project outputs as evidence.
- Notes record what the student actually demonstrated, including prompting and
  errors.
- The flow writes agent-run evidence to `inbox/` and does not directly modify
  compiled `knowledge/`.
- The framework supports both quick repetition exercises and larger personalized
  projects.
- Future compile behavior can distinguish conceptual understanding from
  procedural fluency without inventing mastery.
