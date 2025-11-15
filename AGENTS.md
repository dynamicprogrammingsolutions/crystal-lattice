# Functional Programming Guidelines

Follow functional programming principles for new code, refactor existing code to functional style when feasible.

## Core Principles
- **Pure functions**: Same input → same output, no side effects
- **Immutability**: Never mutate data, create new versions instead
- **First-class functions**: Pass functions as arguments, return them as values

## Architecture Structure
- **Functional Core, Imperative Shell**: Business logic pure, I/O at boundaries
- **Push side effects to edges**: Keep them in presentation/database layers
- **Layer separation**: Presentation → Application (pure) → Infrastructure (effects)

## Side Effect Management
- **Isolate effects**: Contain them in specific modules/files
- **Dependency injection**: Pass effect handlers as function parameters
- **Effect tagging**: Explicitly label/structure side effect operations
- **Centralized handling**: Use effect buses or interpreters

## Code Organization
- **Pure logic first**: Business rules as pure functions
- **Composition over inheritance**: Build complex behavior from simple functions
- **Recursion over loops**: Prefer recursive patterns for data processing
- **Declarative style**: Focus on what, not how

## Testing & Maintenance
- **Pure core testable**: Business logic easily unit tested
- **Effects swappable**: Mock effects for testing different scenarios
- **Explicit boundaries**: Clear separation between pure and impure code

## Practical Patterns
- Separate data transformation from I/O operations
- Use function composition for complex workflows
- Model effects as data structures when possible
- Keep effect handlers thin and focused