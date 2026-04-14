# Testing & QA Skill Pack

## Test-Driven Development (TDD)
- Red → Green → Refactor. Write the failing test FIRST
- Test behavior, not implementation. "When X happens, Y should result"
- One assertion per test (logical assertion — multiple `expect` lines for one concept is fine)
- Test names describe the scenario: `it("returns 404 when user does not exist")`

## Testing Pyramid
- **Unit Tests (70%)**: Fast, isolated, test single functions/methods. Mock external dependencies
- **Integration Tests (20%)**: Test component boundaries — DB queries, API calls, service interactions
- **E2E Tests (10%)**: Test critical user paths. Playwright/Cypress. Keep minimal — they're slow and flaky

## Testing Patterns
- **Arrange-Act-Assert**: Setup → Execute → Verify. Clear separation
- **Factories**: `createUser({...overrides})` over raw fixtures. Flexible, readable
- **Test isolation**: Each test creates its own data. No shared state between tests. `beforeEach` cleanup
- **Snapshot testing**: Sparingly. Good for serialized output, bad for UI (breaks on every style change)
- **Property-based testing**: For parsers, serializers, mathematical functions. Fast-check / Hypothesis

## Framework-Specific
- **Jest/Vitest**: `describe/it/expect`. Mock with `vi.fn()` or `jest.fn()`. Module mocks for imports
- **Pytest**: Fixtures for setup, parametrize for data-driven. `conftest.py` for shared fixtures
- **Playwright**: Page Object Model. Locators over selectors. Auto-wait. Parallel by default
- **React Testing Library**: Test as user sees it. `getByRole` > `getByTestId` > `querySelector`

## Coverage & Quality
- Coverage target: 80%+ for business logic. 100% for critical paths (auth, payments, data mutations)
- Mutation testing: Verify tests actually catch bugs, not just execute code
- Flaky test policy: Quarantine → Fix → Un-quarantine. Never ignore
- CI gate: Tests must pass before merge. No exceptions. No `--skip-tests`

## Performance Testing
- Load testing: k6, Artillery, or Locust for API endpoints
- Benchmarking: Measure before optimizing. Compare against baselines
- Stress testing: Find the breaking point. Document it. Set alerts before it
