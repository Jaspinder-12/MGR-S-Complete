# GPU Linking Project - Safety Guidelines

## OVERVIEW
This document outlines strict safety protocols for development on the GPU Linking project. These rules are non-negotiable and designed to protect the user's system and personal data from accidental damage or loss.

## ABSOLUTE SAFETY RULES (NON-NEGOTIABLE)

1. **ASSUME DATA IS IRREPLACEABLE** - Every action must assume the host system contains irreplaceable personal data.

2. **STRICTLY FORBIDDEN ACTIONS**
   - Deleting files
   - Overwriting files
   - Moving files
   - Renaming files
   - Cleaning, pruning, optimizing, compacting, or deduplicating
   - Using recursive operations
   - Using wildcards
   - Using absolute paths
   - Touching home directories, system directories, mounted drives, or cloud folders
   - Requesting admin or root privileges
   - Operating outside the defined workspace

3. **WORKSPACE ISOLATION**
   - ALL operations are restricted to the `./PROJECT_ROOT/` directory
   - Approved structure:
     - `src/` - Human-written code ONLY
     - `gen/` - AI-generated code ONLY
     - `docs/` - Architecture, design, research
     - `logs/` - Text-only logs of decisions and steps
     - `scratch/` - Disposable experiments (can be deleted safely)
     - `backups/` - Timestamped snapshots
     - `tools/` - Scripts that NEVER self-execute

4. **VERSION CONTROL ENFORCEMENT**
   - Git must remain initialized and functional
   - Every AI-assisted change requires:
     1. Snapshot
     2. Explanation
     3. Commit
   - No rebasing
   - No force pushes
   - No history rewriting
   - Assume recovery WILL be needed one day

## DEVELOPMENT PHILOSOPHY

- Prefer boring, reliable engineering over clever tricks
- Every complex idea must have:
  - A simple baseline version
  - A cheaper alternative
  - A clear "why this exists"
- Experimental features must be clearly labeled EXPERIMENTAL
- If something is speculative or not currently feasible, say so directly
- Never hallucinate hardware availability or performance claims

## BEFORE ANY ACTION

- Explain what you intend to do
- Explain why it is safe
- Specify exact file paths (relative only)
- Wait for approval before executing

## FAILURE & AMBIGUITY HANDLING

- If unsure, STOP
- If something is risky, REFUSE and explain
- Never guess or hallucinate system state
- Never assume lost data can be recreated

## PROJECT EXPECTATIONS

For each major component:
- High-level architecture
- Data flow
- Failure modes
- Hardware assumptions
- Software dependencies
- Open-source alternatives
- Cost-aware options (India-friendly)
- Clear separation between:
  - What is real today
  - What is experimental
  - What is future research

## TRUST & VERIFICATION

- All commands must be visible and auditable
- No silent actions
- No hidden operations
- Everything must be documented

## CONSEQUENCES OF VIOLATION

Violation of these safety rules will result in immediate termination of the current task and a full review of the project state.
