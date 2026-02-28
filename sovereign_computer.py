"""Sovereign Computer — Local AI Orchestration Conductor
Version 1.0 | Aetherhaven / Mellowambience
Runs entirely on local hardware. No APIs. No subscriptions.
"""

import os
import yaml
from pathlib import Path
from typing import TypedDict, List

from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from crewai import Agent, Task, Crew

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.1:70b")
OUTPUT_DIR      = Path(os.getenv("OUTPUT_DIR", "./output"))
OUTPUT_DIR.mkdir(exist_ok=True)

llm = ChatOllama(model=OLLAMA_MODEL, temperature=0.2, base_url=OLLAMA_BASE_URL)

# ── State Schema ──────────────────────────────────────────────────────────────
class SovereignState(TypedDict):
    goal: str
    tasks: List[str]
    results: dict
    artifacts: List[str]
    reflection: str

# ── Load Agents from YAML ─────────────────────────────────────────────────────
def load_agents() -> dict:
    agent_file = Path("agents/agents.yaml")
    if not agent_file.exists():
        return {}
    with open(agent_file) as f:
        configs = yaml.safe_load(f) or []
    agents = {}
    for cfg in configs:
        agents[cfg["name"]] = Agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg.get("backstory", ""),
            llm=llm,
            verbose=False,
        )
    return agents

agents = load_agents()

# ── Graph Nodes ───────────────────────────────────────────────────────────────
def decompose(state: SovereignState) -> SovereignState:
    """Router: break the goal into subtasks."""
    prompt = (
        f"Break this goal into 3-5 parallel subtasks.\n"
        f"Return ONLY a Python list of short task names, e.g. [\"research\", \"write\", \"compile\"].\n"
        f"Goal: {state['goal']}"
    )
    response = llm.invoke(prompt)
    try:
        tasks = eval(response.content.strip())
        if not isinstance(tasks, list):
            raise ValueError
    except Exception:
        tasks = ["research", "write", "compile"]
    state["tasks"] = tasks
    return state


def execute_crew(state: SovereignState) -> SovereignState:
    """Dispatch tasks to CrewAI agents."""
    if not agents:
        state["results"] = {t: f"[placeholder: run {t} task]" for t in state["tasks"]}
        return state

    crew_tasks = []
    agent_list = list(agents.values())
    for i, task_name in enumerate(state["tasks"]):
        agent = agent_list[i % len(agent_list)]
        crew_tasks.append(
            Task(
                description=f"For the goal '{state['goal']}', complete subtask: {task_name}",
                agent=agent,
                expected_output=f"Result of: {task_name}",
            )
        )

    crew = Crew(agents=agent_list, tasks=crew_tasks, verbose=False)
    result = crew.kickoff()
    state["results"] = {"crew_output": str(result)}
    return state


def reflect(state: SovereignState) -> SovereignState:
    """Self-evaluation: did the goal get met?"""
    summary = "\n".join(f"- {k}: {v}" for k, v in state["results"].items())
    prompt = (
        f"Goal: {state['goal']}\nResults:\n{summary}\n\n"
        f"Was the goal fully achieved? What's missing? Reply in 2-3 sentences."
    )
    response = llm.invoke(prompt)
    state["reflection"] = response.content.strip()
    return state


def save_artifacts(state: SovereignState) -> SovereignState:
    """Persist results to ./output."""
    out = OUTPUT_DIR / "results.md"
    with open(out, "w") as f:
        f.write(f"# Goal\n{state['goal']}\n\n# Results\n")
        for k, v in state["results"].items():
            f.write(f"\n## {k}\n{v}\n")
        f.write(f"\n# Reflection\n{state['reflection']}\n")
    state["artifacts"] = [str(out)]
    print(f"\n✓ Artifacts saved to {out}")
    return state


# ── Build Graph ───────────────────────────────────────────────────────────────
graph = StateGraph(SovereignState)
graph.add_node("decompose",      decompose)
graph.add_node("execute_crew",   execute_crew)
graph.add_node("reflect",        reflect)
graph.add_node("save_artifacts", save_artifacts)

graph.set_entry_point("decompose")
graph.add_edge("decompose",      "execute_crew")
graph.add_edge("execute_crew",   "reflect")
graph.add_edge("reflect",        "save_artifacts")
graph.add_edge("save_artifacts", END)

app = graph.compile()

# ── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🛸 Sovereign Computer v1.0")
    print("Everything runs on your machine. No cloud. No leaks.\n")
    goal = input("Your goal: ").strip()
    if not goal:
        goal = "Create a 7-day local marketing campaign: research trends, write copy, compile PDF, save to ./output"
    result = app.invoke({"goal": goal, "tasks": [], "results": {}, "artifacts": [], "reflection": ""})
    print("\n── Reflection ──")
    print(result["reflection"])
    print("\n── Artifacts ──")
    for a in result["artifacts"]:
        print(f"  {a}")
