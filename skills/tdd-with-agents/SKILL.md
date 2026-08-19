---
name: tdd-with-agents
description: Decide whether and how to use test-driven development when a coding agent is writing the code, and run the workflow that replaces it. Use this skill when someone asks for TDD, test-first, or red-green work from an agent, when writing a prompt or instruction file that tells an agent how to test, when refactoring or extending existing or legacy code that an agent will change, when deciding where a human review checkpoint belongs in an agent coding loop, or when judging whether agent-written tests are a real regression safety net using coverage or mutation testing.
---

# TDD with Agents

TDD is a set of mechanisms for reaching goals, not a goal. When a human runs the
loop, the mechanisms and the goals are tightly coupled, so "did we follow TDD"
is a decent proxy for "did we get the benefits." Inside an agent loop that
coupling breaks. The agent can perform every step of red-green-refactor and
deliver none of what the ritual exists to produce, because most of what TDD
produces is produced by a human experiencing friction.

So stop asking whether the agent followed TDD. Ask whether you got the three
things TDD was for:

1. A design that was thought through, rather than accreted from whatever the
   first test happened to lock in.
2. A test suite that will actually catch a regression, rather than one that
   executes lines without asserting anything meaningful.
3. A human who understands and agrees with the specified behavior.

Each of those needs its own mechanism in an agent loop. Test-first ordering
delivers none of them reliably, and the up-front design step it displaces is
the one the available evidence tentatively credits.

- Sources, findings, sample sizes, and what would change this guidance:
  [references/evidence.md](references/evidence.md). Read this before overriding
  anything here, and before repeating a claim from this skill to someone else.
- Mutation testing, tautology smells, and the review checklist for
  agent-written tests: [references/verifying-tests.md](references/verifying-tests.md).

## Pick a route

The right route is set by how well the behavior is already known and by whether
there is existing code to protect. It is not set by team policy or by how much
you like TDD.

| Situation | Route |
|---|---|
| Greenfield feature, design still open | **Design-first.** Full design and behavior list before any code or test, then tests, then implementation. |
| Behavior precisely known, high stakes, or contested | **Human specifies the tests.** You write the scenarios or the assertions. The agent implements against them and may not edit them. |
| Bug fix or regression | **Failing test first, for real.** The red step is a reproduction, so it is diagnostic rather than ceremonial. This is the one place in-loop red-green earns its cost. |
| Refactoring existing code | **Characterization tests first.** Pin current behavior, verify the pins are honest, then refactor under them. |
| Exploration or throwaway prototype | **No test discipline yet.** Backfill tests once the shape stabilizes, then run a mutation check on what the agent wrote. |

Strict incremental red-green-refactor inside the agent loop is not on this list.
It is available, but it needs a specific justification beyond "it is our
practice," because the evidence available says it costs prompt budget and
attention while producing no measurable improvement in design quality or
regression effectiveness.

## The default: design-first

For new functionality, this is the workflow. It inverts the TDD ordering
deliberately.

**1. Design before anything executable.** Have the agent produce the data types,
the interfaces and contracts, the module boundaries, and the error and edge
cases, as a written artifact and before it writes a single test or line of
implementation. This is the step the trace analysis tentatively credited for the
difference. Runs that did it tended to produce better data models, better
cross-cutting edge-case handling, and more complete functionality than runs that
grew a design one test at a time.

**2. Enumerate behavior exhaustively, then review it.** Get the full list of
behaviors, including edge cases, error paths, and boundary conditions, before
tests exist. This matters more than it sounds: in the incremental TDD runs
observed, behavior the agent never thought to write a test for was never
implemented at all. The behavior list is the artifact you review, not the test
file. Reviewing a list of sentences is fast; reviewing thirty test methods is
not, and you will not actually do it.

**3. Then tests, then implementation.** Writing the tests before the
implementation at this point is fine and costs nothing, and it keeps assertions
from being reverse-engineered from code the agent just wrote. Just be clear that
the ordering is not what is doing the work. The design step already did it.

**4. Verify the tests as artifacts, not the process as a ritual.** See
"Trusting the tests" below. This replaces watching the red step.

Two adjustments are worth making if you want to keep TDD ordering. Force an
explicit design-and-review step at the start and an explicit
refactor-and-design-review step at the end. In the source experiment, the only
strict-TDD run that ranked first was the one run after the prompt was
strengthened with exactly that. It was not reproducible within the same batch,
so treat it as a lead rather than a result.

Then enumerate the behavior list up front anyway, even though staging it into
the tests one at a time is the whole point of the ordering. Incremental TDD's
sharpest failure mode is silent omission: behavior nobody thought to write a
test for is behavior that never gets built, and unlike a wrong design it leaves
no trace to review. Enumerating first costs nothing and is compatible with
working through the list one red-green cycle at a time.

Neither adjustment is a measured improvement, and neither should be presented as
one. The first rests on a single run that did not reproduce. The second is a
mitigation for a failure mode the traces showed, not something anyone tested.

## Why the red step does not transfer

An agent watching its own test go red proves that it ran the test and saw a
failure. It does not prove the failure was for the right reason. Red-green is
evidence only when someone checks *why* it went red, and in a closed agent loop
nobody does.

Agents are also unreliable at the ritual itself. Across sessions they implement
before writing the test, skip or fabricate the red confirmation, and
over-implement past the current test so the next one passes without ever going
red. That last one is not really cheating: the agent can see the whole
requirement, so building only what the current test demands is artificial. You
can push against this with prompt effort, but you are paying tokens and
attention to enforce a ceremony whose downstream benefit did not show up in the
measurements.

The same reasoning retires the other classic arguments inside the loop:

- **YAGNI through small steps.** The restraint comes from a human sitting in the
  friction of not knowing what comes next. An agent has the full spec and feels
  nothing. Minimal-implementation instructions did not reliably stop agents from
  over-building. If you want restraint, cut the spec, do not stage the tests.
- **Confidence and momentum.** Kent Beck's core rationale for TDD is managing
  *human* fear, one locked-in step at a time. There is no fear in the loop to
  manage, and watching an agent's progress bar is not the same reassurance as
  earning each green yourself.
- **Design pressure and testability.** These are real benefits when a human
  writes the test, because specifying usage before implementation is genuinely
  hard. An agent can emit the test and the implementation in the same breath
  from the same internal representation, so no pressure is applied.
- **Avoiding tautological assertions.** Test-first makes this less likely but
  does not prevent it. Agents still write tests that recompute the expected
  value using the implementation's own logic, even when the test came first.

## Trusting the tests

If the human is out of the write loop, something has to establish that the test
suite would actually catch a regression. Coverage does not do this. Coverage
tells you a line executed, not that its behavior was verified. A file can report
100% statement coverage, have zero unit tests of its own, and be fully exercised
only incidentally by one broad acceptance test that asserts almost nothing about
it.

Mutation testing is the sensor that closes that gap. It perturbs the code and
reports which perturbations the suite failed to notice, which is a direct
measure of assertion strength rather than execution. Run it incrementally on
changed files rather than across the whole suite, because it is expensive.

Two limits to hold onto. First, mutation testing assumes the implementation is
correct and only asks whether the tests would notice it changing, so it says
nothing about whether the specified behavior was the *right* behavior. That
remains a human question, and it is the one the behavior-list review above
answers. Second, a mutation score is a sensor reading, not a target; driving it
up mechanically produces assertions that pin implementation details.

Notably, mutation scores did not differ meaningfully between TDD and non-TDD
runs. This is the sharpest single argument against in-loop TDD: the mechanism
that supposedly guarantees test effectiveness did not produce more effective
tests. Measure the property you want instead of prescribing the ritual that was
supposed to imply it.

See [references/verifying-tests.md](references/verifying-tests.md) for tooling,
tautology smells, and what to look at in a review.

## Existing code changes the calculus

The evidence behind this skill is greenfield-only, so treat this section as
reasoned extrapolation rather than a finding. Two things shift.

**The design-first advantage shrinks.** Existing types, boundaries, and
conventions already constrain the design, so there is much less for an up-front
design step to get right or wrong. Replace it with a *read-first* step: have the
agent state where the change belongs, which existing contracts it touches, and
what it will not change, before it writes anything.

**The regression risk grows, so the sensor matters more.** In greenfield work a
weak test suite means you might ship a bug. In existing code it means the agent
can silently break behavior that used to work, and the suite will not tell you.
This is where the failing-test-first and characterization-test routes earn their
place, and where an incremental mutation check on the changed files is worth the
runtime.

Bug fixes are the strongest case for genuine red-green anywhere in this skill. A
test that reproduces the reported failure is a real specification, its red state
is diagnostic evidence that you understood the bug, and it is small enough that
a human can actually read it. Insist on seeing the failure before the fix, and
insist the fix does not touch the test.

## Where the human goes

Agent TDD removes the human from the loop and then keeps the ceremony that only
made sense because the human was there. Put the human back at the two points
that carry information:

1. **The design and behavior list, before any code exists.** This is cheap to
   read, it is where the expensive mistakes are made, and it is the checkpoint
   the TDD ordering actively destroys by deferring design into a sequence of
   local decisions.
2. **The assertions for behavior you actually care about.** Not every test. Pick
   the handful encoding real business rules and read those closely. Let mutation
   testing cover the rest.

Watching a red bar is not one of these points.

## Anti-patterns

- **"Always use TDD" in an always-loaded instruction file.** It applies a
  ritual with an unclear payoff to every task regardless of whether behavior is
  known or code already exists, and it suppresses the up-front design step on
  exactly the greenfield work where that step helps most.
- **A coverage threshold as the quality gate.** Every run in the source
  experiment was instructed to reach at least 80% coverage, including the ones
  that produced weak assertions. It constrains execution, not verification.
- **Asking the agent to self-report TDD adherence.** You get a confident
  narrative of a workflow that partially did not happen. If adherence genuinely
  matters, judge it from the session transcript with a separate agent, which is
  what the source experiment had to do.
- **Treating a green suite the agent wrote as the safety net for a refactor the
  same agent proposed.** Both sides came from one internal representation. Get
  an independent signal before relying on it.
- **Spending prompt budget policing red-green while spending none on mutation
  testing.** That is enforcement aimed at the proxy instead of the property.

## Answering "should the agent use TDD here?"

Give the route and the single reason in one line, then the one checkpoint that
matters for it. Do not present the table unless asked, and do not hedge into
"it depends" when the situation determines the route. For example:

> Design-first, because the data model here is the hard part and incremental
> tests would lock it in before you see the shape. Review the behavior list
> before it writes anything.

If the request explicitly asks for strict in-loop TDD, do not silently
substitute something else. Say what the evidence shows, offer the design-first
route, and follow the user's decision. Their context may include reasons this
skill does not model, such as a team practice, an audit requirement, or a
codebase where the tests are the spec of record.

## Confidence and limits

This skill is more opinionated than its evidence base, deliberately, because the
prevailing default is unexamined in the other direction. The honest summary:
one small exploratory experiment found no benefit from in-loop TDD and a slight
edge to non-TDD runs, judged by an LLM, on small greenfield business-logic
tasks. That is a reason to stop treating in-loop TDD as the obvious default. It
is not proof that TDD is harmful.

Do not repeat the findings as established. Read
[references/evidence.md](references/evidence.md), which records the sample
sizes, the caveats, and the specific results that would overturn this guidance.

## Refreshing this skill

Durable (leave alone unless the underlying reasoning changed): the reframe from
ritual to the three goals, the route table, the design-first workflow, the
human-checkpoint placement, and the anti-patterns. These follow from the
structure of an agent loop rather than from any measurement.

Volatile (recheck): everything in
[references/evidence.md](references/evidence.md), the specific mutation-testing
tooling in [references/verifying-tests.md](references/verifying-tests.md), and
the claim that agents are unreliable at the red step. That last one is a model
capability claim and is the single most likely thing here to become false.

1. Re-check whether newer models follow TDD instructions faithfully without
   heavy prompting. If they do, the cost side of the argument weakens, though
   the "red proves nothing without a human reading it" argument survives.
2. Watch for a larger or better-controlled replication in either direction. The
   source is explicit that its sample is too small to conclude from, and asks
   for someone to run it at scale.
3. Watch for evidence on non-greenfield and larger tasks, which nothing here
   covers. A finding that TDD helps on large or legacy codebases would not
   contradict the source and would change the route table.
4. Re-check the mutation-testing tooling, which moves faster than the reasoning.
5. Re-run the evals after any change to the route table.
