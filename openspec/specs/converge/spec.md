# Capability: `converge` (the converge loop)

## Purpose

The end-of-plan converge loop drives open **blocking** review findings to clean by looping
*fix → gate → scoped re-verify*, or halts. Pure deterministic control flow — **no LLM in the loop**:
it re-reads the findings files from disk each round and gates convergence on the verifier-owned
`verdict` signal, never on the fixer's word. This spec captures the behavior shipped in
`orchestrator/converge.py`; each scenario declares `Layers: unit` and is bound to its proving test.

## Requirements

### Requirement: Converge blocking findings to clean

The converge loop SHALL return `CONVERGED` as soon as every findings file reads clean, and while any
finding is still blocking SHALL spawn the fixer, run the gate, and re-verify — looping until the
findings clear.

#### Scenario: Already-clean findings converge without a fix
- **Key:** `converge:converge-to-clean:already-clean-zero-rounds`
- **Layers:** unit
- **WHEN** the first read of the findings reports every file clean
- **THEN** the loop returns `CONVERGED` after zero rounds, having spawned no fixer

#### Scenario: A fix that clears the findings converges in one round
- **Key:** `converge:converge-to-clean:fix-then-verified-clean`
- **Layers:** unit
- **WHEN** the findings are blocking, then read clean after one fixer spawn and re-verify
- **THEN** the loop returns `CONVERGED` after one round, having spawned the fixer once and run the
  re-verify once

#### Scenario: Reopened findings drive another round until clean
- **Key:** `converge:converge-to-clean:reopen-then-clears`
- **Layers:** unit
- **WHEN** the re-verify reopens the findings once before a later round reads them clean
- **THEN** the loop runs another fix + re-verify round and returns `CONVERGED` (two rounds)

### Requirement: Bounded, gate-guarded termination

The converge loop SHALL terminate by construction — halting at the round cap when the findings never
clear, and halting on a red gate after a fix (before re-verifying) — so it can never loop unbounded.

#### Scenario: The round cap halts a never-clearing loop
- **Key:** `converge:bounded-termination:round-cap-halts`
- **Layers:** unit
- **WHEN** the findings stay blocking through `max_rounds` fix attempts
- **THEN** the loop halts with reason `round cap exceeded` at `max_rounds` rounds

#### Scenario: A red gate after a fix halts before re-verifying
- **Key:** `converge:bounded-termination:red-gate-halts`
- **Layers:** unit
- **WHEN** the gate is red after a fixer spawn
- **THEN** the loop halts with reason `gate red after fix` and does not run the re-verify
