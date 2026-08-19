# Verifying agent-written tests

Read this when you need to decide whether a test suite an agent wrote would
actually catch a regression. Tooling here is volatile; the smells and the
checklist are not.

## What each technique can tell you

| Technique | Answers | Cost | Blind spot |
|---|---|---|---|
| Coverage | Which lines the tests execute | Cheap | Says nothing about whether anything was asserted |
| Mutation testing | Whether the tests would notice the code changing | Expensive | Assumes the current behavior is the wanted behavior |
| Property-based testing | Whether logical cases are missing | Moderate | Needs properties you can state, which is the hard part |
| Fuzz testing | Whether input handling is resilient | Moderate | Only useful where malformed input is a real risk |

Coverage is a floor, not a signal. Use it to find code the tests never touch,
then stop drawing conclusions from it.

## Mutation testing

Mutation testing introduces small changes to the code (flipping a comparison,
removing a call, changing a boundary) and reports which ones the test suite
failed to catch. A surviving mutant is a change no assertion noticed, which is
exactly the shape of an undetected regression.

**How to run it without it becoming unaffordable.** Run incrementally against
changed files rather than the whole suite. Trigger it deliberately at review
time or on a schedule rather than continuously, because full runs are slow
enough to break the feedback loop they exist to serve.

**How to feed results to an agent.** Mutation tools emit large machine-readable
reports that will flood a context window if pasted in whole. Wrap the report in
a small query script that answers specific questions (summary, worst files,
hotspot lines, weak tests) and give the agent the script rather than the report.
Agents are good at reading mutation output and proposing a prioritized plan for
where to strengthen assertions, once they can query it.

**Tooling, as of 2026-08.** Stryker for JavaScript and TypeScript, Stryker.NET
for C#, PIT for the JVM, mutmut or cosmic-ray for Python, cargo-mutants for
Rust, go-mutesting for Go. Check current maintenance status before adopting;
this is the fastest-moving content in this skill.

**Do not turn the score into a target.** A mutation score is a sensor reading.
Optimizing it directly produces assertions that pin implementation details and
make the suite brittle in exactly the way you were trying to avoid. Use it to
find the files with nothing meaningful asserted, fix those, and move on.

## Tautology smells

A tautological test derives its expected value from the same logic it claims to
check, so it cannot fail when the implementation is wrong. Agents produce these
even when the test was written first. Mutation testing catches some of them;
these are the patterns to look for by eye.

- The expected value is computed rather than written down. If the assertion
  recalculates the answer, it is restating the implementation.
- The test calls the code under test, or a helper that shares its logic, to
  produce the value it then compares against.
- The expected value is a constant that was clearly copied from a failing run
  rather than derived from the requirement. Snapshot and approval tests are the
  legitimate form of this, but only when the snapshot was reviewed once by a
  human who knew what it should say.
- The assertion checks structure rather than value: that a result is non-null,
  has the right type, or has some number of elements, with nothing about
  content.
- The test name describes a behavior the assertions do not actually check.
- A mock is configured with the exact value the assertion then verifies, so the
  test proves only that the mock works.

## Review checklist

You will not read every test. Read these.

1. **Tests for the business rules you actually care about.** Pick the handful
   encoding real domain decisions and read the assertions closely. Ask what
   would have to break for each one to fail.
2. **Whatever mutation testing flags as weakest.** Go to the files with the most
   survivors first, since that is where assertions are missing rather than
   merely thin.
3. **Tests that changed alongside an implementation change.** A test edited in
   the same change as the code it covers is the highest-risk pattern in an agent
   workflow, because the agent may have moved the goalpost rather than met it.
   For bug fixes, the test must not change at all after it goes red.
4. **The behavior list, against the tests.** The failure mode is silent absence:
   behavior nobody wrote a test for is behavior that may never have been
   implemented. Compare the test names to the specified behaviors and look for
   what is missing, not for what is wrong.
5. **Anything the agent suppressed.** Skipped tests, disabled assertions,
   loosened tolerances, widened lint thresholds. Suppressions are a good place
   to start a review because they mark where the agent chose not to comply.

## The limit worth remembering

Everything here measures test *effectiveness*: given that the implementation
does what was intended, would the tests notice it changing. None of it measures
test *correctness*: whether what was intended was right. That remains a human
judgment, which is why the design and behavior review before any code is the
checkpoint that carries the most information.
