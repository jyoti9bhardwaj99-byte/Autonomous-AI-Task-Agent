"""Autonomous AI Task Agent: Planner -> Executor -> Critic -> Synthesizer."""
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq

from agent_memory import Memory
from tools import TOOLS

load_dotenv(Path(__file__).parent / ".env", override=True)

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
llm = ChatGroq(model=MODEL, temperature=0)


# ------------------------------------------------------------------ helpers
def extract_json(text: str, opener: str, closer: str):
    """Pull the first JSON array/object out of an LLM reply."""
    match = re.search(re.escape(opener) + r".*" + re.escape(closer), text, re.S)
    return json.loads(match.group(0))


# ------------------------------------------------------------------ planner
def plan(goal: str) -> list:
    """Break the goal into 2-5 ordered sub-tasks."""
    reply = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are a planner. Break the user's goal into 2-5 concrete, "
                    "ordered sub-tasks. The available tools are web_search and "
                    "calculator. Respond with ONLY a JSON array of strings."
                )
            ),
            HumanMessage(content=goal),
        ]
    )
    try:
        return extract_json(reply.content, "[", "]")
    except Exception:
        return [goal]  # fallback: treat the whole goal as one task


# ----------------------------------------------------------------- executor
def execute(task, memory, feedback="", max_iters=5, log=print) -> str:
    """Do one sub-task, calling tools in a loop until the LLM gives an answer."""
    agent_llm = llm.bind_tools(list(TOOLS.values()))

    prompt = task
    if feedback:
        prompt += f"\n\nYour previous attempt was rejected because: {feedback}\nFix this."

    messages = [
        SystemMessage(
            content=(
                "Complete the sub-task. Use tools when you need facts or math. "
                "Give a concise final answer.\n\n"
                "Results of earlier sub-tasks:\n" + memory.context()
            )
        ),
        HumanMessage(content=prompt),
    ]

    for _ in range(max_iters):
        try:
            ai = agent_llm.invoke(messages)
        except Exception as e:
            return f"LLM error: {e}"
        messages.append(ai)

        if not ai.tool_calls:  # no more tools needed -> final answer
            return ai.content

        for call in ai.tool_calls:
            log(f"Tool call: `{call['name']}({call['args']})`")
            tool = TOOLS.get(call["name"])
            output = tool.invoke(call["args"]) if tool else "Unknown tool"
            messages.append(ToolMessage(content=str(output), tool_call_id=call["id"]))

    return "Stopped: maximum tool iterations reached."


# ------------------------------------------------------------------- critic
def critique(task: str, result: str) -> dict:
    """Judge whether the result really completes the sub-task."""
    reply = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are a strict reviewer. Decide whether the result fully "
                    "and correctly completes the sub-task. Reply ONLY with JSON: "
                    '{"ok": true or false, "feedback": "what is missing or wrong"}'
                )
            ),
            HumanMessage(content=f"Sub-task: {task}\n\nResult: {result}"),
        ]
    )
    try:
        return extract_json(reply.content, "{", "}")
    except Exception:
        return {"ok": True, "feedback": ""}


# ------------------------------------------------------------- orchestrator
def run(goal: str, max_retries: int = 2, log=print) -> str:
    memory = Memory(goal)

    tasks = plan(goal)
    log("**PLAN**")
    for i, t in enumerate(tasks, 1):
        log(f"{i}. {t}")

    for i, task in enumerate(tasks, 1):
        log(f"**Step {i}/{len(tasks)}:** {task}")
        feedback = ""
        attempt = 1
        result = ""

        for attempt in range(1, max_retries + 2):
            result = execute(task, memory, feedback, log=log)
            verdict = critique(task, result)
            if verdict.get("ok"):
                break
            feedback = verdict.get("feedback", "")
            log(f"Self-correcting (attempt {attempt}): {feedback}")

        memory.add(task, result, attempt)
        log(f"Result: {result[:300]}")

    final = llm.invoke(
        [
            SystemMessage(content="Write a clear final answer to the goal using the results."),
            HumanMessage(content=f"Goal: {goal}\n\nResults:\n{memory.context()}"),
        ]
    )
    return final.content


# ---------- run from terminal: python agent.py ----------
if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) or input("Enter your goal: ")
    answer = run(goal)
    print("\n=== FINAL ANSWER ===")
    print(answer)