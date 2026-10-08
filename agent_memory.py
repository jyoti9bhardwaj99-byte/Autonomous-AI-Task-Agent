"""Memory layer: remembers results of completed sub-tasks and saves them to disk."""
import json
from datetime import datetime
from pathlib import Path


class Memory:
    def __init__(self, goal: str, path: str = "memory.json"):
        self.goal = goal
        self.path = Path(path)
        self.steps = []  # list of dicts: task, result, attempts

    def add(self, task: str, result: str, attempts: int = 1):
        """Store a completed sub-task and save everything to disk."""
        self.steps.append(
            {"task": task, "result": result, "attempts": attempts}
        )
        self.save()

    def context(self) -> str:
        """Return past results as text, so the LLM can use them in later steps."""
        if not self.steps:
            return "(none yet)"
        return "\n".join(f"- {s['task']} -> {s['result']}" for s in self.steps)

    def save(self):
        data = {
            "goal": self.goal,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "steps": self.steps,
        }
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------- Quick test: run `python agent_memory.py` ----------
if __name__ == "__main__":
    m = Memory("test goal", path="test_memory.json")
    m.add("Find population of India", "About 1.4 billion")
    m.add("Find population of Japan", "About 124 million", attempts=2)
    print(m.context())
    print("\nSaved file exists:", m.path.exists())