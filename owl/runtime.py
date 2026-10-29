"""Local-first runtime: no autonomous shell, browser or filesystem execution."""

from __future__ import annotations
import os
from owl.providers import create_model


def run_task(prompt: str, provider: str | None = None,
             model: str | None = None, mode: str | None = None) -> str:
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 16000:
        raise ValueError("Task length must be between 1 and 16,000 characters.")
    selected_mode = (mode or os.getenv("OWL_MODE", "assistant")).strip().lower()
    if selected_mode not in ("assistant", "workforce"):
        raise ValueError("Mode must be assistant or workforce.")
    from camel.agents import ChatAgent

    llm = create_model(provider=provider, model=model)
    if selected_mode == "assistant":
        agent = ChatAgent(
            "Respond in English. Be clear about uncertainty. You have no filesystem, "
            "browser, or shell tools; do not claim to have executed actions.",
            model=llm,
            tools=[],
        )
        response = agent.step(prompt)
        if response.terminated or response.msg is None:
            raise RuntimeError("The selected model did not return a response.")
        return str(response.msg.content)

    from camel.societies import Workforce
    from camel.tasks.task import Task

    workforce = Workforce(
        "OWL",
        task_agent=ChatAgent(
            "Decompose the request into reasoning tasks using only provided evidence. "
            "Respond in English.",
            model=llm,
        ),
        coordinator_agent=ChatAgent(
            "Coordinate analysis and verification. Report unknowns. Respond in English.",
            model=llm,
        ),
    )
    tools = []
    if os.getenv("OWL_ENABLE_WEB_SEARCH", "0") == "1":
        from camel.toolkits import FunctionTool, SearchToolkit
        tools = [FunctionTool(SearchToolkit().search_duckduckgo)]

    workforce.add_single_agent_worker(
        "Analyze the request and gather evidence within the allowed tools.",
        worker=ChatAgent(
            "Analyze the request; distinguish supplied facts from assumptions. Respond in English.",
            model=llm, tools=tools,
        ),
    )
    workforce.add_single_agent_worker(
        "Independently verify claims and identify errors.",
        worker=ChatAgent(
            "Audit the reasoning; identify unsupported claims. Respond in English.",
            model=llm, tools=[],
        ),
    )
    output = workforce.process_task(Task(content=prompt))
    if output is None or output.result is None:
        raise RuntimeError("The workforce did not produce a result.")
    return str(output.result)
