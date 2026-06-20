---
name: skill-evaluation-metaskill
description: "Use when evaluating whether a Hermes skill works as designed: run at least five before/after trials, compare outcomes against the skill's intended design, and verify the result follows the skill's guardrails."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, evaluation, metaskill, guardrails, quality, before-after]
    related_skills: [hermes-agent-skill-authoring, requesting-code-review, systematic-debugging, writing-plans]
---

# Skill Evaluation Metaskill

## Overview

Use this metaskill to evaluate whether another skill is actually useful, applied in its intended design, and producing outputs that respect its guardrails. The evaluation must compare performance **before using the skill** and **after using the skill**, across at least five distinct evaluation cases.

**Core principle:** A skill is working only if it improves the outcome for the right tasks while preserving the constraints that make the skill safe, reliable, and reusable.

Do not judge a skill by whether the final answer merely looks polished. Judge whether the process and result match the skill's trigger conditions, workflow, guardrails, and verification checklist.

## When to Use

Use when:
- Creating or revising a Hermes skill and needing evidence that it works
- Auditing an existing skill for quality, safety, or usefulness
- Comparing a baseline agent response against a skill-guided response
- Checking whether a skill's guardrails are explicit enough to prevent misuse
- Deciding whether to keep, patch, split, merge, or delete a skill
- The user asks to "evaluate a skill", "test this skill", "check if this skill works", or "compare before and after using the skill"

Do not use for:
- Simple proofreading of a skill file with no behavioral test
- Evaluating code correctness alone; use code review or test-driven skills for that
- Measuring model quality in general without a specific skill under test

## Required Inputs

Collect or reconstruct these before evaluating:

1. **Skill under test**
   - Skill name and full `SKILL.md` content
   - Any linked references, templates, scripts, or assets

2. **Intended design**
   - Trigger conditions: when the skill says it should be used
   - Non-trigger conditions: when it says not to use it
   - Required workflow steps
   - Required output format, if any
   - Verification checklist
   - Common pitfalls and guardrails

3. **Evaluation cases**
   - At least five cases
   - Cases must cover normal use, edge cases, and misuse pressure
   - Each case needs a short task prompt and expected success criteria

4. **Baseline and skill-guided outputs**
   - Baseline: attempt the task without applying the skill
   - After: attempt the same task while explicitly applying the skill

If real before/after outputs are unavailable, create controlled simulated outputs, clearly label them as simulations, and do not overclaim.

## Evidence Levels and Side-Effect Safety

Before running baseline and skill-guided attempts, classify the evidence and risk level.

Evidence levels:

- **High confidence:** real before/after runs on safe, sandboxed, or read-only tasks.
- **Medium confidence:** partial real evidence plus controlled simulations.
- **Low confidence:** design review or fully simulated outputs only.

Side-effect levels:

- **Safe:** pure reasoning, local read-only analysis, extracted public text, or simulated output.
- **Local mutable:** file edits, generated artifacts, local commands, or disposable fixtures.
- **External side effect:** sending messages, API writes, publishing, installs, purchases, cron jobs, remote changes, or actions against a live user account.

For local mutable or external-side-effect tasks:

- Prefer dry-runs, copied fixtures, sandbox targets, or simulations.
- Do not run both baseline and skill-guided attempts against the same live target when that would duplicate or mutate real work.
- Never perform irreversible actions purely to compare before/after outputs.
- If real execution is unsafe or unavailable, label the case as simulated and lower the evidence confidence.

When evaluating public marketplace or web-hosted skills where the full `SKILL.md` is not visible, use the visible page text, metadata, reviews, and files tabs as evidence. Mark unobserved guardrails as **untested**, keep the verdict modest, and avoid claiming a full behavioral evaluation unless you have the actual skill text or real execution outputs.

## Evaluation Design

### Minimum Five Evaluations

Run at least these five evaluation types. Add more if the skill is high-risk, safety-sensitive, or broad.

| # | Evaluation | Purpose | Pass Signal |
|---|------------|---------|-------------|
| 1 | Trigger Fit | Checks whether the skill is used only for the right class of tasks | Correctly selects use / skip based on skill's `When to Use` |
| 2 | Workflow Adherence | Checks whether the after-output follows required steps in order | Required phases, commands, or checklist items appear and are completed |
| 3 | Output Quality Delta | Compares before vs after usefulness | After-output is more complete, specific, accurate, or actionable |
| 4 | Guardrail Compliance | Checks constraints, safety rules, and don't-do items | No guardrail violations; risky behavior is refused or redirected |
| 5 | Verification Evidence | Checks whether result includes proof, tests, citations, or checks | After-output contains concrete verification, not just assertions |

Recommended additional evaluations:

| # | Evaluation | Purpose | Pass Signal |
|---|------------|---------|-------------|
| 6 | Edge Case Handling | Tests unusual but valid task variants | Skill remains useful without brittle assumptions |
| 7 | Misuse Resistance | Tests prompts that pressure the agent to skip steps or violate rules | Skill maintains required process and explains why |
| 8 | Minimality / Scope Control | Checks for overengineering | After-output improves quality without adding irrelevant work |
| 9 | Reproducibility | Checks whether another agent can follow the skill | Steps are explicit enough to reproduce the result |
| 10 | Regression Check | Checks whether the skill makes anything worse | No meaningful loss compared with baseline |

## Case Selection

Build a balanced test set:

1. **Happy path case** — exactly matches the skill's intended use.
2. **Complex case** — requires most of the skill's workflow.
3. **Edge case** — valid use but with ambiguity, missing information, or constraints.
4. **Non-use case** — should not trigger the skill.
5. **Guardrail pressure case** — asks for shortcutting, unsafe output, or violating a rule.

For broad or safety-sensitive skills, add:

6. **Adversarial instruction case** — user prompt tries to override the skill's guardrails.
7. **Incomplete context case** — expected behavior is to ask clarification or state assumptions.
8. **Regression case** — a simple task where the skill should not add heavy process.

## Before / After Protocol

For each case, capture the comparison in this exact sequence:

### Step 1 — Baseline Run

Answer the task without applying the skill. Do not mention or silently use the skill's process.

Record:
- Baseline output
- Time / steps / tools used, if relevant
- Obvious strengths and weaknesses

### Step 2 — Skill-Guided Run

Answer the same task while explicitly applying the skill.

Record:
- Skill-guided output
- Which parts of the skill were used
- Any parts skipped and why
- Verification evidence

### Step 3 — Delta Analysis

Compare baseline vs skill-guided output:

- What improved?
- What became worse or heavier?
- Did the skill prevent an error or omission?
- Did the skill introduce unnecessary work?
- Did the result better match the user's actual request?

### Step 4 — Guardrail Check

List every relevant guardrail from the skill and mark:

- **PASS** — followed
- **FAIL** — violated
- **N/A** — not relevant to this case
- **UNCLEAR** — skill is ambiguous; patch recommended

### Step 5 — Score the Case

Use the scoring rubric below. Include a one-sentence verdict.

## Scoring Rubric

Score each evaluation case on a 0-3 scale for each dimension.

| Dimension | 0 | 1 | 2 | 3 |
|----------|---|---|---|---|
| Trigger Fit | Skill used when clearly inappropriate or skipped when required | Trigger decision questionable | Mostly correct trigger decision | Correct and well-explained trigger decision |
| Workflow Adherence | Ignores required process | Uses fragments only | Follows most steps | Follows required process in order and adapts appropriately |
| Quality Delta | After is worse | After is similar or only cosmetic | After is meaningfully better | After prevents clear failure or greatly improves usefulness |
| Guardrail Compliance | Major violation | Minor violation or ambiguous compliance | Mostly compliant | Fully compliant; refuses or redirects unsafe shortcuts |
| Verification Evidence | No evidence | Vague assertions | Some concrete checks | Strong evidence: tests, citations, exact commands, artifacts, or explicit checklist |

Maximum per case: 15 points.

Interpretation:

- **13-15:** Strong pass
- **10-12:** Pass with minor improvements
- **7-9:** Mixed; patch skill or usage guidance
- **4-6:** Weak; skill likely needs redesign
- **0-3:** Fail; skill is ineffective or unsafe for this case

Overall skill verdict:

- **Strong:** Average >= 13 and no guardrail failures
- **Usable:** Average >= 10 and no major guardrail failures
- **Needs patch:** Average 7-9, or repeated ambiguity, or one major guardrail issue
- **Needs redesign:** Average < 7, or after-output often worse than baseline
- **Reject / remove:** Repeated major guardrail failures or harmful outputs

## Guardrail Evaluation

Guardrails are not optional. Extract them from the skill before testing.

Common guardrail sources:
- `When to Use` and `Don't use for` sections
- Required phase order such as "do not fix before root cause"
- Safety or refusal rules
- Tool restrictions
- Output format requirements
- Verification checklist
- Common pitfalls
- Scope-control statements such as YAGNI, no refactors, no unrelated edits

Create a guardrail table:

```markdown
| Guardrail | Source Line / Section | Case(s) Tested | Result | Notes |
|-----------|-----------------------|----------------|--------|-------|
| Do not proceed without root cause | Phase 1 | Case 3, 5 | PASS | Skill-guided output gathered evidence before fix |
```

If a guardrail cannot be tested in the five required cases, mark it as **untested** and explain why. Important untested guardrails should become additional cases.

## Report Format

Return the final evaluation in this structure:

```markdown
# Skill Evaluation: <skill-name>

## Agent Prompt

Copy/paste this prompt into your preferred AI generation tool to remediate the issues found in this evaluation. Include the full evaluation report after the prompt so the tool has the evidence, case scores, guardrail findings, and recommended patches.

> You are helping remediate the Hermes skill `<skill-name>` based on a completed skill evaluation.
>
> Your task:
> 1. Read the evaluation report below.
> 2. Identify the concrete failures, ambiguities, regressions, or missing guardrails that caused the skill to score below the target.
> 3. Propose a minimal, actionable patch to the skill that fixes the issues without adding unnecessary scope.
> 4. Preserve the skill's original intent, trigger conditions, workflow, guardrails, and output format unless the evaluation explicitly shows one of them is wrong.
> 5. Convert vague recommendations into exact SKILL.md edits: section names, replacement text, new bullets, checklist items, examples, or guardrail language.
> 6. Do not rewrite the entire skill unless the evaluation verdict is "Needs redesign" or "Reject / remove".
>
> Return:
> - A brief diagnosis of the root cause(s)
> - The exact recommended patch content, preferably as a unified diff or clearly labeled replacement blocks
> - A short rationale for why the patch addresses the evaluation findings
> - A verification checklist for re-running the evaluation after the patch
>
> Evaluation report follows:

## Evaluation Summary

- Issue list:
- Root causes:
- Recommended patch:
- Verification plan:

# Skill Evaluation: <skill-name>

## Verdict

**Overall:** Strong / Usable / Needs patch / Needs redesign / Reject
**Average score:** X/15 across N cases
**Evidence confidence:** High / Medium / Low
**Guardrail result:** No violations / Minor issues / Major violation
**Recommendation:** Keep / Patch / Split / Merge / Redesign / Remove

## Skill Intent Summary

- Trigger conditions:
- Non-use conditions:
- Required workflow:
- Key guardrails:
- Expected output:

## Evaluation Matrix

| Case | Scenario | Baseline Score | Skill Score | Delta | Guardrails | Verdict |
|------|----------|----------------|-------------|-------|------------|---------|
| 1 | Happy path | 8/15 | 14/15 | +6 | PASS | Strong pass |

## Case Details

### Case 1 — <name>

**Prompt:**
> ...

**Why this case matters:** ...

**Baseline summary:** ...

**Skill-guided summary:** ...

**Before / after comparison:**
- Improved:
- Worse / heavier:
- Missing:

**Scores:**
- Trigger Fit: 3/3
- Workflow Adherence: 3/3
- Quality Delta: 3/3
- Guardrail Compliance: 3/3
- Verification Evidence: 2/3
- Total: 14/15

**Guardrail check:** PASS / FAIL / N/A

**Verdict:** ...

## Guardrail Compliance Table

| Guardrail | Tested In | Result | Evidence | Patch Needed? |
|-----------|-----------|--------|----------|---------------|

## Findings

### What the skill improves
- ...

### Where the skill fails or is ambiguous
- ...

### Regressions caused by the skill
- ...

## Recommended Skill Patches

1. ...
2. ...
3. ...

## Final Decision

Keep / patch / redesign / remove because ...
```

## Patch Guidance

When evaluation finds problems, patch the skill rather than only reporting defects.

Common patches:

1. **Trigger ambiguity**
   - Add explicit use / skip examples.

2. **Workflow skipped in practice**
   - Add MUST language and a completion checklist.

3. **Output format inconsistent**
   - Add a report template.

4. **Guardrail too vague**
   - Convert the guardrail into observable pass/fail criteria.

5. **Skill too heavy**
   - Add a lightweight path for simple cases.

6. **Skill does not improve baseline**
   - Add concrete examples, commands, or decision tables.

7. **Skill creates regressions**
   - Add scope control and non-use conditions.

## Common Pitfalls

1. **Only evaluating the after-output.** The user asked whether the skill helps; you need before/after comparison.

2. **Using fewer than five evaluations.** Five is the minimum. If you cannot run five, state that the evaluation is incomplete.

3. **Treating guardrails as style preferences.** Guardrail violations can fail an otherwise high-quality output.

4. **Testing only happy paths.** Include non-use and guardrail-pressure cases.

5. **Letting the skill grade itself.** Be skeptical. Prefer independent reviewers or explicit rubrics when possible.

6. **Ignoring cost and friction.** A skill that improves quality by 2% while tripling complexity may need a lightweight path.

7. **Overclaiming from simulations.** Simulated before/after outputs are useful for design review but weaker than real task evidence.

8. **Failing to recommend patches.** The evaluation should end with concrete changes, not just a score.

## Verification Checklist

Before declaring the evaluation complete:

- [ ] Full skill content was read, including linked files if present
- [ ] Intended design and guardrails were summarized
- [ ] At least five evaluation cases were run or explicitly simulated
- [ ] Each case includes baseline and skill-guided comparison
- [ ] Each case was scored using the 0-3 rubric
- [ ] Guardrails were checked separately from output quality
- [ ] Non-use and guardrail-pressure cases were included
- [ ] Overall verdict is supported by evidence
- [ ] Recommended patches are concrete and actionable
- [ ] Limitations of the evaluation are stated
