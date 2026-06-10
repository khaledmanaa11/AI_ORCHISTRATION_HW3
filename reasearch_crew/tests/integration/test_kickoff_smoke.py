from crewai.agent import Agent

from reasearch_crew.crew import ReasearchCrew


CANNED_PAPER = (
    "# Abstract\n\n"
    "Mocked smoke-test paper. No live network was touched.\n\n"
    "## Introduction\n\nCanned content.\n\n"
    "## Conclusion\n\nThe wiring is alive.\n"
)


def test_paper_written_to_output_dir(api_key, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        Agent,
        "execute_task",
        lambda self, task, context=None, tools=None: CANNED_PAPER,
    )

    ReasearchCrew().crew().kickoff(
        inputs={"topic": "Smoke Test", "current_year": "2026"}
    )

    paper = tmp_path / "output" / "paper.md"
    assert paper.exists(), f"missing {paper}; tmp contents: {list(tmp_path.iterdir())}"
    content = paper.read_text(encoding="utf-8")
    assert "Abstract" in content
    assert "Conclusion" in content
