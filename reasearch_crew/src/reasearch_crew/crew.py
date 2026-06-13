import json
import os
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from dotenv import load_dotenv

from .gateway import GatekeptLLM
from .tools.search import web_search_tool
from .tools.typeset import render_and_compile_tool

load_dotenv()

_CONFIG_DIR = Path(__file__).parent / "config"
_LLM_CONFIG_PATH = _CONFIG_DIR / "llm.json"
_llm_singleton: GatekeptLLM | None = None


def _load_llm_config() -> dict:
    return json.loads(_LLM_CONFIG_PATH.read_text(encoding="utf-8"))


def _get_llm() -> GatekeptLLM:
    global _llm_singleton
    if _llm_singleton is None:
        cfg = _load_llm_config()
        api_key = os.getenv(cfg["api_key_env"])
        if not api_key:
            raise RuntimeError(
                f"Missing environment variable: {cfg['api_key_env']}"
            )
        _llm_singleton = GatekeptLLM(
            model=cfg["model"],
            base_url=cfg["base_url"],
            api_key=api_key,
        )
    return _llm_singleton


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
            llm=_get_llm(),
            tools=[web_search_tool],
            verbose=True,
        )

    @agent
    def typesetter(self) -> Agent:
        return Agent(
            config=self.agents_config['typesetter'],  # type: ignore[index]
            llm=_get_llm(),
            tools=[render_and_compile_tool],
            verbose=True,
        )

    def get_llm(self) -> GatekeptLLM:
        """Expose the shared GatekeptLLM for the compose phase."""
        return _get_llm()

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
