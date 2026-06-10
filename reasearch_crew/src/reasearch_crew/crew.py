import json
import os
from pathlib import Path

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from dotenv import load_dotenv

load_dotenv()

_CONFIG_DIR = Path(__file__).parent / "config"
_LLM_CONFIG_PATH = _CONFIG_DIR / "llm.json"
_llm_singleton: LLM | None = None


def _load_llm_config() -> dict:
    return json.loads(_LLM_CONFIG_PATH.read_text(encoding="utf-8"))


def _get_llm() -> LLM:
    global _llm_singleton
    if _llm_singleton is None:
        cfg = _load_llm_config()
        api_key = os.getenv(cfg["api_key_env"])
        if not api_key:
            raise RuntimeError(
                f"Missing environment variable: {cfg['api_key_env']}"
            )
        _llm_singleton = LLM(
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
            config=self.agents_config['researcher'], # type: ignore[index]
            llm=_get_llm(),
            verbose=True,
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config['writer'], # type: ignore[index]
            llm=_get_llm(),
            verbose=True,
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'], # type: ignore[index]
        )

    @task
    def writing_task(self) -> Task:
        return Task(
            config=self.tasks_config['writing_task'], # type: ignore[index]
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ReasearchCrew crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
