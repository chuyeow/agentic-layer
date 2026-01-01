---
name: tdd
description: Comprehensive guide for Test-Driven Development (TDD) methodology. Use this skill when the user asks to implement features using TDD, write tests first, follow red-green-refactor cycle, or develop code with test-first approach. Also use when user mentions TDD, unit testing workflow, or wants to refactor code with test coverage.
---

# Test-Driven Development (TDD)

Test-Driven Development is a software development approach where tests are written before the actual code. This skill guides you through the TDD process, from writing your first failing test to refactoring production code.

## Core TDD Cycle: Red-Green-Refactor

The fundamental TDD cycle consists of three phases:

1. **Red**: Write a failing test
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Clean up code while keeping all tests passing

This cycle repeats for each new piece of functionality.

## The Six-Step TDD Process

Follow these steps for each feature or behavior you implement:

### 1. List Scenarios for the New Feature

Before writing any code, enumerate the expected behaviors and edge cases:

- Start with the basic case
- Add "what-if" scenarios: timeouts, missing data, invalid inputs, boundary conditions
- Consider use cases and user stories
- Document these as a checklist to work through

**Example scenarios for a calculator's add function:**
- Basic addition: 2 + 3 = 5
- Adding negative numbers: -5 + 3 = -2
- Adding zero: 5 + 0 = 5
- Large numbers: 1000000 + 2000000 = 3000000

### 2. Write a Test for One Item on the List

Select one scenario from your list and write an automated test that would pass if that behavior is correctly implemented.

**Key principles:**
- Test only one behavior per test
- Keep tests small and focused
- Use descriptive test names that explain the scenario
- Follow the test structure: Setup → Execution → Validation → Cleanup

**Example test structure:**

```python
def test_add_positive_numbers():
    # Setup: Arrange the test state
    calculator = Calculator()

    # Execution: Act on the unit under test
    result = calculator.add(2, 3)

    # Validation: Assert the expected outcome
    assert result == 5

    # Cleanup: (if needed) restore state
```

### 3. Run All Tests - The New Test Should Fail

Execute your entire test suite. The new test must fail for the right reason (not due to syntax errors or missing imports).

**Why this matters:**
- Validates the test actually tests something and the harness works
- Confirms new code is genuinely needed

**What "fail for the right reason" means:**
- ✅ Good: Test fails with assertion error because expected behavior is missing
- ❌ Bad: Test fails due to NameError, ImportError, or other structural issues

### 4. Write the Simplest Code That Passes the New Test

Implement just enough code to make the failing test pass. Nothing more.

**Example:**

```python
# First test: add(2, 3) should return 5
def add(a, b):
    return 5  # Hard-coded - perfectly acceptable at this stage!

# After more tests, evolve to:
def add(a, b):
    return a + b
```

This "fake it till you make it" approach is intentional and valuable.

### 5. Run All Tests - Everything Should Pass

Execute the full test suite again. All tests, including the new one, must pass.

**If tests fail:**
- Make minimal changes to fix them
- Don't add new functionality while fixing
- If you can't fix quickly, consider reverting and starting over
- Keep commits small so reverting is easy

### 6. Refactor While Ensuring All Tests Continue to Pass

Now improve the code quality without changing behavior. Run tests after each refactoring step to ensure nothing breaks.

Remove duplication, extract methods, improve naming, eliminate hard-coded test data, and simplify logic.

### 7. Repeat

Return to step 1 or 2 with the next scenario on your list. Continue until all scenarios are implemented and tested.

## Test Structure Best Practices

Structure each test consistently for clarity and maintainability:

### Four-Phase Test Pattern

1. **Setup (Arrange)**: Prepare the system and test data
2. **Execution (Act)**: Invoke the behavior being tested
3. **Validation (Assert)**: Verify the results are correct
4. **Cleanup (Teardown)**: Restore pre-test state

### Test Organization Tips

- **Extract common setup/teardown**: Use test fixtures, setUp/tearDown methods, or before/after hooks
- **Keep tests independent**: Each test should work in isolation and in any order
- **Focus assertions**: Each test should verify one logical outcome
- **Name tests descriptively**: `test_add_returns_sum_of_two_positive_integers` is better than `test_add`
- **Treat test code with respect**: Test code deserves the same quality standards as production code

## Core TDD Principles

### KISS (Keep It Simple, Stupid)

Write the simplest code that makes tests pass. Complexity emerges from refactoring, not from initial implementation.

### YAGNI (You Aren't Gonna Need It)

Only implement features that are needed right now for passing tests. Don't add functionality for hypothetical future requirements.

### Test Units, Not Implementation Details

Test behavior through public interfaces, not internal implementation. This allows refactoring without breaking tests.

**Example:**

```python
# ❌ Bad: Testing implementation details
def test_internal_cache_structure():
    obj = MyClass()
    assert obj._cache == {}  # Fragile - breaks if implementation changes

# ✅ Good: Testing behavior
def test_caching_improves_performance():
    obj = MyClass()
    first_call_time = time_function_call(obj.get_data)
    second_call_time = time_function_call(obj.get_data)
    assert second_call_time < first_call_time * 0.1
```

## Working with External Dependencies

### Use Test Doubles for Isolation

When code depends on external systems (databases, APIs, file systems), use test doubles to maintain fast, isolated unit tests:

- **Mock objects**: Verify interactions (was this method called?)
- **Stub objects**: Provide canned responses
- **Fake objects**: Working implementations with shortcuts (e.g., in-memory database)
- **Spy objects**: Record information about interactions

### Supplement with Integration Tests

Test doubles don't prove real connections work. Write integration tests separately to verify actual component interactions, but run them less frequently than unit tests.

### Testing Pyramid Strategy

- **Base (most tests)**: Fast unit tests with test doubles
- **Middle**: Moderate integration tests with real components
- **Top (fewest tests)**: Slow end-to-end tests of full system

## Anti-Patterns to Avoid

### Dependent Tests

❌ Tests that rely on execution order or state from other tests

**Why it's bad:** Creates fragile test suites where one failure cascades into many false negatives

**Solution:** Make each test independent with its own setup and teardown

### Testing Implementation Details

❌ Tests that verify internal structure rather than external behavior

**Why it's bad:** Tests break whenever you refactor, even if behavior is unchanged

**Solution:** Test only through public interfaces

### Slow-Running Tests

❌ Tests that take seconds or minutes to run

**Why it's bad:** Developers won't run them frequently, defeating TDD's rapid feedback loop

**Solution:** Use test doubles for external dependencies; move slow tests to separate integration suite

### All-Knowing Oracles

❌ Tests that verify every possible detail of output

**Why it's bad:** Expensive to maintain, brittle, and time-consuming

**Solution:** Verify only the aspects relevant to the behavior being tested

### Hard-Coded Test Data in Production Code

❌ Leaving test-specific values in production code after making tests pass

**Why it's bad:** Production code becomes polluted with test concerns

**Solution:** Refactor during the "Refactor" phase to remove test data

### Precise Timing Tests

❌ Tests that assert exact execution times or timestamps

**Why it's bad:** Flaky tests that fail randomly based on system load

**Solution:** Allow tolerance ranges (e.g., 5-10% margin) or test relative timing

## Commit Strategy

- Make small, frequent commits
- Commit after each green phase (tests passing)
- Write descriptive commit messages that reference the test
- If stuck, revert to last passing commit rather than debugging extensively

## TDD in Practice: Example Workflow

Let's implement a `UserValidator` class using TDD:

### Iteration 1: Empty email should be invalid

```python
# Test (Red)
def test_empty_email_is_invalid():
    validator = UserValidator()
    assert validator.is_valid_email("") == False

# Implementation (Green)
class UserValidator:
    def is_valid_email(self, email):
        return False  # Simplest implementation

# Refactor
# Nothing to refactor yet

# ✅ Test passes
```

### Iteration 2: Valid email should pass

```python
# Test (Red)
def test_valid_email_is_valid():
    validator = UserValidator()
    assert validator.is_valid_email("user@example.com") == True

# Implementation (Green)
class UserValidator:
    def is_valid_email(self, email):
        return "@" in email and len(email) > 0  # Simple implementation

# Refactor
class UserValidator:
    def is_valid_email(self, email):
        if not email:
            return False
        return "@" in email

# ✅ Both tests pass
```

### Iteration 3: Email without domain should be invalid

```python
# Test (Red)
def test_email_without_domain_is_invalid():
    validator = UserValidator()
    assert validator.is_valid_email("user@") == False

# Implementation (Green)
import re

class UserValidator:
    def is_valid_email(self, email):
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

# Refactor
# Extract pattern to class constant
class UserValidator:
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    def is_valid_email(self, email):
        if not email:
            return False
        return bool(re.match(self.EMAIL_PATTERN, email))

# ✅ All three tests pass
```

Continue this cycle for remaining scenarios (special characters, maximum length, etc.).

## Quick Reference Checklist

Before starting TDD session:
- [ ] List all scenarios for the feature
- [ ] Set up test framework and ensure tests run
- [ ] Prepare to commit frequently

For each scenario:
- [ ] Write one focused test
- [ ] Run tests - verify new test fails for right reason
- [ ] Write simplest code to pass
- [ ] Run tests - verify all pass
- [ ] Refactor for quality (run tests after each change)
- [ ] Commit with descriptive message

Common reminders:
- [ ] Keep tests independent
- [ ] Test behavior, not implementation
- [ ] Use test doubles for external dependencies
- [ ] Remove hard-coded test data during refactoring
- [ ] Make small commits
- [ ] Resist the urge to write untested code

## Troubleshooting

**Problem:** Test is always passing even before implementation
- Verify test actually invokes the code under test
- Check assertions are correct
- Ensure test framework is detecting the test

**Problem:** Can't get test to pass
- Is the test testing the right thing?
- Are you trying to do too much at once? Break into smaller steps
- Consider reverting and starting over with a simpler test

**Problem:** Tests are brittle and break often
- Are you testing implementation details instead of behavior?
- Are tests too tightly coupled to structure?
- Refactor tests to use public interfaces only

**Problem:** Tests are slow
- Are you hitting real databases/APIs? Use test doubles
- Move slow tests to separate integration suite
- Profile tests to find bottlenecks

**Problem:** Lost in refactoring
- Revert to last passing commit
- Refactor in smaller steps
- Keep running tests after each micro-refactoring
