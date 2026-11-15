---
name: tdd
description: Test-Driven Development (TDD) workflow. Use this skill when the user asks to implement features using TDD, write tests first, follow red-green-refactor cycle, or develop code with test-first approach. Also use when user mentions TDD, unit testing workflow, or wants to refactor code with test coverage.
---

# Test-Driven Development (TDD)

Work one behavior at a time: red → green → refactor.

1. **List scenarios first** – the basic case, then the what-ifs (timeouts, missing data, invalid input, boundaries). Keep it as a checklist and work through it.
2. **Red** – write one test for one scenario, run the whole suite, and confirm the new test fails for the right reason: an assertion on the missing behavior, not a NameError/ImportError or other structural failure.
3. **Green** – write the simplest code that passes, nothing more. A hard-coded return is acceptable at this stage; later tests force the real implementation.
4. **Refactor** – only on green, running the tests after each step. Remove duplication and any test-specific values left in production code.
5. **Commit after each green.** If a fix isn't quick, revert to the last passing commit rather than debugging at length.

Test behavior through public interfaces, not internals, so refactoring doesn't break tests. Use test doubles to keep unit tests fast, and cover the real connections with separate integration tests.
