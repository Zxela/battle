import pytest
from unittest.mock import MagicMock, patch
from battle.evaluators.llm_judge import RubricScore, score_cell


def make_mock_anthropic_response(json_text: str):
    block = MagicMock()
    block.type = "text"
    block.text = json_text
    msg = MagicMock()
    msg.content = [block]
    msg.stop_reason = "end_turn"
    return msg


def test_score_cell_returns_rubric_score():
    mock_response = make_mock_anthropic_response("""{
        "ac_completeness": 8,
        "code_style": 7,
        "code_quality": 7,
        "security": 9,
        "bugs": 8,
        "rationale": "Good overall implementation"
    }""")

    with patch("battle.evaluators.llm_judge.anthropic_client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        score = score_cell(
            artifact_files={"index.tsx": "export default function App() {}"},
            acceptance_criteria=["App renders without errors"],
            judge_model="claude-opus-4-6",
        )

    assert isinstance(score, RubricScore)
    assert score.ac_completeness == 8
    assert score.overall == pytest.approx((8 + 7 + 7 + 9 + 8) / 5, rel=0.01)


def test_score_cell_handles_empty_artifacts():
    mock_response = make_mock_anthropic_response("""{
        "ac_completeness": 1, "code_style": 1, "code_quality": 1,
        "security": 1, "bugs": 1, "rationale": "No code produced"
    }""")
    with patch("battle.evaluators.llm_judge.anthropic_client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        score = score_cell(
            artifact_files={},
            acceptance_criteria=["Build completes"],
            judge_model="claude-opus-4-6",
        )
    assert score.overall < 5


def test_score_cell_strips_markdown_fences():
    json_in_fences = """```json
{
    "ac_completeness": 7,
    "code_style": 7,
    "code_quality": 7,
    "security": 7,
    "bugs": 7,
    "rationale": "Average"
}
```"""
    mock_response = make_mock_anthropic_response(json_in_fences)
    with patch("battle.evaluators.llm_judge.anthropic_client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        score = score_cell(
            artifact_files={"app.py": "print('hello')"},
            acceptance_criteria=["Runs without errors"],
        )
    assert score.ac_completeness == 7


def test_rubric_score_overall():
    score = RubricScore(
        ac_completeness=10, code_style=8, code_quality=6, security=9, bugs=7,
        rationale="test"
    )
    assert score.overall == pytest.approx(8.0, rel=0.01)
