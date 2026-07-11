# Bublee Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the current Conny-to-Bublee migration into a manageable, audited Bublee runtime where active agents, prompts, tokens, and public responses cannot regress to Conny or deceptive identities.

**Architecture:** Keep production running while adding guardrails first. Split active runtime from legacy artifacts, make identity/prompt rules explicit, and only then archive generated static/dump/patch files.

**Tech Stack:** Python 3.12, FastAPI runtime, PM2 process management, Telegram webhooks, shell scripts for audits.

---

## File Structure

- Modify: `/home/ubuntu/bublee/src/core/production_monitor.py` for production patient prompt identity.
- Modify: `/home/ubuntu/bublee/src/core/runtime.py` for emergency fallback prompt identity.
- Modify: `/home/ubuntu/bublee/bublee_core/prompt_ops.py` for reusable prompt builder identity language.
- Modify: `/home/ubuntu/bublee/v7/agents/captacion.py` for V7 agent identity language.
- Create: `/home/ubuntu/bublee/scripts/audit_runtime_cleanliness.py` for Conny/identity regression checks in active runtime.
- Keep: `/home/ubuntu/bublee/scripts/audit_agents.py` for Telegram/process role checks.
- Update: `/home/ubuntu/bublee/architecture/AGENT_MEMORY.md` with each cleanup pass.

## Task 1: Runtime Prompt Honesty Baseline

- [x] Replace prompt phrases that claim Bublee is a human/person/real receptionist.
- [x] Keep natural WhatsApp tone rules without identity deception.
- [x] Ensure direct IA questions are answered honestly and briefly.
- [x] Run `python3 -m compileall` on modified Python files.

## Task 2: Runtime Cleanliness Audit

- [x] Add `scripts/audit_runtime_cleanliness.py`.
- [x] Fail on `Conny` references in active Python runtime, excluding explicit migration memory/docs.
- [x] Fail on dangerous prompt phrases in active prompt files: `No eres un bot`, `recepcionista real`, `persona real`.
- [x] Run `python3 scripts/audit_runtime_cleanliness.py` and fix findings.

## Task 3: Agent Registry And Startup Guards

- [x] Create a small registry for active instances: base, production, melissa-x quarantine, ovni.
- [x] Extend `scripts/audit_agents.py` to validate registry instead of hardcoded constants.
- [x] Make startup or PM2 deploy docs require both audits before restart.

## Task 4: Legacy Archive Pass

- [x] Identify generated static files containing Conny logos or `conny_master_key`.
- [x] Move dumps like `recover.sql` and one-off patch scripts into `legacy/` with a manifest.
- [x] Do not delete files until audit confirms no runtime import references them.

## Task 5: Prompt Consolidation

- [x] Extract shared identity policy into a single module.
- [x] Replace duplicated hardcoded emergency prompts with that module.
- [x] Add smoke tests or audit assertions for the prompt strings.

## Verification Commands

```bash
python3 /home/ubuntu/bublee/scripts/audit_agents.py
python3 /home/ubuntu/bublee/scripts/audit_runtime_cleanliness.py
python3 -m compileall /home/ubuntu/bublee/src/core/production_monitor.py /home/ubuntu/bublee/src/core/runtime.py /home/ubuntu/bublee/bublee_core/prompt_ops.py /home/ubuntu/bublee/v7/agents/captacion.py
```

## Current Execution Choice

Inline execution is being used now because the user asked to continue and apply changes directly.
