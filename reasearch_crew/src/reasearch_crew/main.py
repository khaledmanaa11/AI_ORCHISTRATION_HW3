#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from reasearch_crew import settings
from reasearch_crew.crew import ReasearchCrew
from reasearch_crew.gateway import flush
from reasearch_crew.report.outline import section_outline

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def _book_inputs() -> dict:
    cfg = settings.book_config()
    return {
        "topic": cfg["topic"],
        "current_year": str(datetime.now().year),
        "outline": "; ".join(section_outline()),
    }


def run():
    """
    Run the crew on the ALYASMEEN book, then report token totals (§11).
    """
    try:
        ReasearchCrew().crew().kickoff(inputs=_book_inputs())
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
    finally:
        flush()


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        ReasearchCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        ReasearchCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        ReasearchCrew().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = ReasearchCrew().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
