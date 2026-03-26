import json
from dataclasses import dataclass

import anthropic

anthropic_client = anthropic.Anthropic()

JUDGE_PROMPT = """\
You are an expert code reviewer evaluating AI-generated code. Score the output on each dimension from 1 (very poor) to 10 (excellent).

## Task Acceptance Criteria
{criteria}

## Generated Code
{code_summary}

## Instructions
Score on each dimension, then provide a brief rationale. Be calibrated — a score of 10 is exceptional. Respond ONLY with valid JSON matching this schema:
{{
  "ac_completeness": <1-10>,
  "code_style": <1-10>,
  "code_quality": <1-10>,
  "security": <1-10>,
  "bugs": <1-10>,
  "rationale": "<2-3 sentence summary>"
}}

Scoring guide:
- ac_completeness: Did the output satisfy all acceptance criteria?
- code_style: Is the code idiomatic, consistent, well-named?
- code_quality: Is it maintainable, well-structured, not over-engineered?
- security: No obvious vulnerabilities (injection, exposed secrets, unsafe deps)?
- bugs: Does it appear functional? Would it run/compile without errors?
"""


@dataclass
class RubricScore:
    ac_completeness: float
    code_style: float
    code_quality: float
    security: float
    bugs: float
    rationale: str

    @property
    def overall(self) -> float:
        return (
            self.ac_completeness + self.code_style + self.code_quality
            + self.security + self.bugs
        ) / 5


def score_cell(
    artifact_files: dict[str, str],
    acceptance_criteria: list[str],
    judge_model: str = "claude-opus-4-6",
) -> RubricScore:
    """Score a cell's artifacts against the rubric using Claude as judge."""
    if not artifact_files:
        code_summary = "No files were generated."
    else:
        parts = [f"Files generated: {list(artifact_files.keys())}\n"]
        total_chars = 0
        for path, content in artifact_files.items():
            chunk = f"\n### {path}\n```\n{content[:2000]}\n```"
            if total_chars + len(chunk) > 8000:
                parts.append("\n[... additional files truncated ...]")
                break
            parts.append(chunk)
            total_chars += len(chunk)
        code_summary = "".join(parts)

    criteria_text = "\n".join(f"- {c}" for c in acceptance_criteria)
    prompt = JUDGE_PROMPT.format(criteria=criteria_text, code_summary=code_summary)

    response = anthropic_client.messages.create(
        model=judge_model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(b.text for b in response.content if b.type == "text")
    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text.strip())

    return RubricScore(
        ac_completeness=float(data["ac_completeness"]),
        code_style=float(data["code_style"]),
        code_quality=float(data["code_quality"]),
        security=float(data["security"]),
        bugs=float(data["bugs"]),
        rationale=data["rationale"],
    )
