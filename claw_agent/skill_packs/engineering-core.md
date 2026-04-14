# Engineering Core Skill Pack

## Coding Standards
- Use consistent naming: camelCase (JS/TS), snake_case (Python/Rust), PascalCase (C#/Go types)
- Prefer immutability. Use `const`, `final`, `readonly`, frozen dataclasses
- Functions do ONE thing. If the name needs "and", split it
- No magic numbers — extract to named constants
- Fail fast: validate at boundaries, trust internals

## Architecture Patterns
- **Hexagonal/Ports-and-Adapters**: Domain core with no framework imports. Adapters at edges
- **Repository Pattern**: Abstract data access behind interfaces. Swap storage without touching business logic
- **CQRS**: Separate read models from write models when query patterns diverge from mutation patterns
- **Event-Driven**: Decouple via events when temporal coupling isn't required

## Code Review Checklist
1. Does it compile/lint clean? No warnings treated as TODOs
2. Are edge cases handled? Empty lists, null/None, zero, negative, unicode, concurrent access
3. Is error handling specific? No bare `except:` or `catch (Exception e)` swallowing everything
4. Are tests covering the change? Unit for logic, integration for boundaries
5. Is the public API surface minimal? Don't expose internal state

## Refactoring Discipline
- Make it work → Make it right → Make it fast (in that order)
- Extract method when a comment explains "what" — the method name IS the comment
- Replace conditional with polymorphism when switch/if chains grow past 3 branches
- Dead code gets deleted, not commented out. Git remembers

## Git Workflow
- Conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
- One logical change per commit. Atomic, revertable
- Rebase feature branches, merge to main
- Never force-push shared branches
