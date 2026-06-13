from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from dotenv import load_dotenv

from .gateway import GatekeptLLM, load_llm_config, resolve_key
from .tools.search import web_search_tool
from .tools.typeset import render_and_compile_tool

load_dotenv()

_llm_cache: dict[str, GatekeptLLM] = {}


def _get_llm(phase: str) -> GatekeptLLM:
    cached = _llm_cache.get(phase)
    if cached is not None:
        return cached
    cfg = load_llm_config()
    _, api_key = resolve_key(phase)
    llm = GatekeptLLM(
        model=cfg["model"],
        base_url=cfg["base_url"],
        api_key=api_key,
    )
    _llm_cache[phase] = llm
    return llm


@CrewBase
class ReasearchCrew():
    """ReasearchCrew crew"""
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],  # type: ignore[index]
            llm=_get_llm("research"),
            tools=[web_search_tool],
            verbose=True,
        )

    @agent
    def typesetter(self) -> Agent:
        return Agent(
            config=self.agents_config['typesetter'],  # type: ignore[index]
            llm=_get_llm("typeset"),
            tools=[render_and_compile_tool],
            verbose=True,
        )

    def get_llm(self, phase: str) -> GatekeptLLM:
        """Expose a phase-scoped GatekeptLLM for SDK composition."""
        return _get_llm(phase)

    @task
    def research_task(self) -> Task:
        Path("output").mkdir(exist_ok=True)
        return Task(
            config=self.tasks_config['research_task'],  # type: ignore[index]
        )

    @task
    def typeset_task(self) -> Task:
        return Task(
            config=self.tasks_config['typeset_task'],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ReasearchCrew crew (research + typeset only)."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

    def research_crew(self) -> Crew:
        """Single-task crew for Phase 1 (research only)."""
        return Crew(
            agents=[self.researcher()],
            tasks=[self.research_task()],
            process=Process.sequential,
            verbose=True,
        )

    def typeset_crew(self) -> Crew:
        """Single-task crew for Phase 3 (typeset only)."""
        return Crew(
            agents=[self.typesetter()],
            tasks=[self.typeset_task()],
            process=Process.sequential,
            verbose=True,
        )
