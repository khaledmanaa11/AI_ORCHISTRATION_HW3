def test_researcher_has_web_search_tool(api_key):
    from reasearch_crew.crew import ReasearchCrew

    crew_obj = ReasearchCrew().crew()
    researcher = next(a for a in crew_obj.agents if "Research" in a.role)
    tool_names = [t.name for t in researcher.tools]
    assert "web_search" in tool_names


def test_research_task_demands_sourced_figures(api_key):
    from reasearch_crew.crew import ReasearchCrew

    crew_obj = ReasearchCrew().crew()
    research = next(
        t for t in crew_obj.tasks if "research" in t.description.lower()
    )
    out = research.expected_output.lower()
    assert "figures" in out
    assert "source" in out
    assert research.output_file == "output/research.md"
