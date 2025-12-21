# Parliament (Governance Core) v0.1

## Purpose
A shared, industry-agnostic decision forum that supports multi-agenda concurrency.

## Non-goals (v0.1)
- No EventBus integration
- No execution / trading / dispatching
- No AI inference
- No global mutable state

## Core Concepts
- **Agenda**: independent decision context (first-class)
- **Proposal**: what to do + constraints
- **Vote**: role stance + confidence + rationale
- **Decision**: institutional outcome, not execution

## Concurrency Model
- Parliament is stateless.
- State exists only inside an Agenda’s Proposal/Votes.
- Parallelism is achieved by running multiple agendas independently.

## Output Guarantee
- Same input (proposal+votes+rules) => same decision output.
