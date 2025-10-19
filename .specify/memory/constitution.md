<!--
Sync Impact Report:
- Version Change: N/A → 1.0.0
- New Constitution: Initial ratification
- Principles Added:
  * I. Standard Library Only
  * II. Test-Driven Development (NON-NEGOTIABLE)
  * III. Code Quality & Readability
  * IV. Type Safety
  * V. Minimal Complexity
- Sections Added:
  * Core Principles
  * Quality Standards
  * Development Workflow
  * Governance
- Templates Requiring Updates:
  * ✅ plan-template.md (reviewed - Constitution Check section will auto-populate)
  * ✅ spec-template.md (reviewed - compatible with constitution requirements)
  * ✅ tasks-template.md (reviewed - test-first workflow aligned)
- Follow-up TODOs: None
-->

# Subrepo Constitution

## Core Principles

### I. Standard Library Only

**Rule**: All functionality MUST be implemented using only the Python standard library. No external dependencies are permitted except for development tooling (linting, formatting, testing frameworks).

**Rationale**: Eliminates dependency management complexity, security vulnerabilities from third-party code, version conflicts, and ensures long-term maintainability. Forces developers to deeply understand Python's capabilities and write more maintainable code.

**Allowed Exceptions**:
- Development tools: pytest, black, mypy, ruff (not shipped with application)
- Build tools: setuptools, wheel (not runtime dependencies)

**Enforcement**:
- `dependencies = []` in pyproject.toml MUST remain empty
- Code review MUST reject any `import` from non-standard-library packages
- CI MUST verify zero runtime dependencies

### II. Test-Driven Development (NON-NEGOTIABLE)

**Rule**: Tests MUST be written before implementation. The red-green-refactor cycle is strictly enforced:
1. Write test that captures requirement
2. Verify test fails (RED)
3. Implement minimal code to pass test (GREEN)
4. Refactor while keeping tests green (REFACTOR)

**Rationale**: Ensures code is testable by design, provides living documentation of intended behavior, prevents scope creep, and creates a safety net for refactoring. Non-negotiable because retrofitting tests is exponentially harder and produces lower-quality test coverage.

**Requirements**:
- Every public function/class MUST have corresponding tests
- Tests MUST be reviewed and approved before implementation begins
- Tests MUST fail before implementation (no false positives)
- Test coverage MUST be ≥90% for all new code
- Integration tests required for cross-module functionality
- Contract tests required for public APIs/CLIs

### III. Code Quality & Readability

**Rule**: Code MUST prioritize clarity over cleverness. Every module, class, and function MUST have clear purpose and documentation.

**Requirements**:
- Docstrings MUST follow Google style for all public APIs
- Function names MUST be descriptive verbs (e.g., `parse_git_status`, not `parse`)
- Class names MUST be descriptive nouns (e.g., `SubtreeManager`, not `Manager`)
- Magic numbers/strings MUST be named constants
- Functions MUST do one thing and do it well (single responsibility)
- Maximum function length: 50 lines (excluding docstrings)
- Maximum file length: 500 lines
- Comments MUST explain "why", not "what" (code should be self-documenting for "what")

**Rationale**: Code is read 10x more than written. Clarity reduces cognitive load, speeds onboarding, and prevents bugs.

### IV. Type Safety

**Rule**: All code MUST use Python type hints. Type checking MUST pass with mypy in strict mode.

**Requirements**:
- All function signatures MUST include parameter and return type hints
- No use of `Any` type except when truly unavoidable (requires justification)
- Type stubs MUST be provided for any dynamic code
- mypy MUST pass with `--strict` flag
- Type hints MUST be kept up-to-date with implementation

**Rationale**: Type hints serve as inline documentation, catch bugs at static analysis time, enable better IDE support, and make refactoring safer.

### V. Minimal Complexity

**Rule**: Start with the simplest solution. Additional complexity MUST be justified by concrete requirements.

**Requirements**:
- YAGNI (You Aren't Gonna Need It): Don't build features not yet required
- No premature optimization: Optimize only measured bottlenecks
- No premature abstraction: Extract patterns only after 3+ occurrences
- Prefer composition over inheritance
- Avoid metaprogramming unless absolutely necessary (requires explicit justification)

**Rationale**: Complexity is technical debt. Every abstraction layer, every design pattern, every line of code is a maintenance burden. The best code is code you don't write.

## Quality Standards

### Code Style
- Formatting: Black (default settings)
- Linting: Ruff with strict rules
- Line length: 100 characters maximum
- Import ordering: isort-compatible (standard lib → third-party → local)

### Error Handling
- Exceptions MUST be specific (no bare `except:`)
- Error messages MUST be actionable and user-friendly
- Errors MUST be logged with appropriate context
- Use custom exception classes for domain-specific errors

### Documentation
- README MUST explain: what, why, how to install, how to use, how to contribute
- API documentation MUST be generated from docstrings
- Breaking changes MUST be documented in CHANGELOG
- Complex algorithms MUST include references or explanation comments

### Testing Standards
- Tests MUST be isolated (no shared state between tests)
- Test names MUST describe what is being tested (e.g., `test_parse_returns_error_for_invalid_input`)
- Use pytest fixtures for test setup/teardown
- Integration tests MUST be in separate directory from unit tests
- Tests MUST run in <1 second for unit tests, <10 seconds for integration tests

## Development Workflow

### Before Writing Code
1. Clarify requirements - ensure you understand what and why
2. Write specification - document expected behavior
3. Write tests - capture requirements as executable tests
4. Review tests - ensure tests are correct and comprehensive
5. Verify tests fail - confirm test suite catches missing implementation

### During Development
1. Implement minimal code to pass one test
2. Run tests frequently (after each small change)
3. Refactor once green (improve design without changing behavior)
4. Keep commits small and focused
5. Write commit messages that explain why, not what

### Before Submitting Code
1. All tests MUST pass
2. Type checking MUST pass (mypy --strict)
3. Linting MUST pass (ruff check)
4. Formatting MUST be applied (black)
5. Documentation MUST be updated
6. Test coverage MUST meet threshold (≥90%)

### Code Review Requirements
- At least one approval required before merge
- Reviewers MUST verify constitution compliance
- Reviewers MUST verify tests were written first
- Reviewers MUST verify type safety
- Reviewers MUST verify documentation quality

## Governance

### Amendment Process
This constitution supersedes all other development practices. Amendments require:
1. Documented proposal explaining: what changes, why needed, impact analysis
2. Review by all active contributors
3. Consensus approval (no blocking objections)
4. Update version following semantic versioning
5. Migration plan for existing code if needed

### Version Semantics
- **MAJOR**: Backward-incompatible governance changes, principle removals/redefinitions
- **MINOR**: New principles added, materially expanded guidance
- **PATCH**: Clarifications, wording improvements, typo fixes

### Compliance Review
- All pull requests MUST be verified against this constitution
- Violations MUST be justified in writing or rejected
- Complexity violations require entry in plan.md Complexity Tracking table
- Constitution compliance is a blocking requirement for merge

### Complexity Justification
If a principle must be violated:
1. Document in plan.md Complexity Tracking table
2. Explain why needed and what alternatives were rejected
3. Get explicit approval from reviewer
4. Create follow-up task to revisit and simplify if possible

**Version**: 1.0.0 | **Ratified**: 2025-10-18 | **Last Amended**: 2025-10-18
