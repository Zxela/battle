import asyncio
import json
from dataclasses import dataclass

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

# Maximum time (seconds) for a judge evaluation
JUDGE_TIMEOUT = 300

JUDGE_PROMPT = """\
You are an expert code reviewer evaluating AI-generated code. You are in the directory containing the generated code. Use your tools to explore the files and understand what was built.

## Task Acceptance Criteria
{criteria}

## Instructions
Explore the code in this directory thoroughly, then score it on each dimension from 1 (very poor) to 10 (excellent). Be calibrated — a score of 10 is exceptional.

Respond ONLY with valid JSON matching this schema:
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


async def score_cell(
    artifact_dir: str,
    acceptance_criteria: list[str],
    judge_model: str = "claude-opus-4-6",
) -> RubricScore:
    """Score a cell's artifacts by running Claude Code in the artifact directory."""
    criteria_text = "\n".join(f"- {c}" for c in acceptance_criteria)
    prompt = JUDGE_PROMPT.format(criteria=criteria_text)

    # If no artifact dir or empty, short-circuit with minimum scores
    if not artifact_dir:
        return RubricScore(
            ac_completeness=1, code_style=1, code_quality=1,
            security=1, bugs=1, rationale="No artifact directory provided.",
        )

    output_schema = {
        "type": "object",
        "properties": {
            "ac_completeness": {"type": "number"},
            "code_style": {"type": "number"},
            "code_quality": {"type": "number"},
            "security": {"type": "number"},
            "bugs": {"type": "number"},
            "rationale": {"type": "string"},
        },
        "required": ["ac_completeness", "code_style", "code_quality", "security", "bugs", "rationale"],
    }

    options = ClaudeAgentOptions(
        cwd=artifact_dir,
        model=judge_model,
        permission_mode="bypassPermissions",
        allowed_tools=["Read", "Glob", "Grep", "Bash"],
        output_format={"type": "json_schema", "schema": output_schema},
    )

    text = ""
    structured = None

    async def _run_judge() -> None:
        nonlocal text, structured
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
                text = message.result or ""
                structured = message.structured_output

    await asyncio.wait_for(_run_judge(), timeout=JUDGE_TIMEOUT)

    # Prefer structured output from SDK if available
    if structured and isinstance(structured, dict):
        data = structured
    else:
        # Fallback: parse text response
        text = text.strip()
        if not text:
            raise ValueError("Judge returned empty response")
        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]
                if text.lower().startswith("json"):
                    text = text[4:]
        data = json.loads(text.strip())

    def clamp(val: float) -> float:
        return max(1.0, min(10.0, val))

    return RubricScore(
        ac_completeness=clamp(float(data["ac_completeness"])),
        code_style=clamp(float(data["code_style"])),
        code_quality=clamp(float(data["code_quality"])),
        security=clamp(float(data["security"])),
        bugs=clamp(float(data["bugs"])),
        rationale=str(data["rationale"]),
    )
