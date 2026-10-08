"""Tools the agent can call: calculator, web search, and a safe file reader."""
import ast
import operator
from pathlib import Path

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

# ---------- Safe calculator (no eval(), so no code-injection risk) ----------
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")


@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression, for example '(120 * 1.18) / 4'."""
    try:
        return str(_eval(ast.parse(expression, mode="eval").body))
    except Exception as e:
        return f"Calculator error: {e}"


# ---------- Web search ----------
_search = DuckDuckGoSearchRun()


@tool
def web_search(query: str) -> str:
    """Search the web for current information."""
    try:
        return _search.run(query)
    except Exception as e:
        return f"Search error: {e}"


# ---------- File reader (restricted to the workspace folder) ----------
WORKSPACE = (Path(__file__).parent / "workspace").resolve()
WORKSPACE.mkdir(exist_ok=True)
ALLOWED_TYPES = {".txt", ".md", ".csv", ".json", ".py", ".pdf"}
MAX_CHARS = 6000  # keeps long files from flooding the LLM context


@tool
def read_file(filename: str) -> str:
    """Read a file from the workspace folder (txt, md, csv, json, py, pdf).
    Pass only the file name, for example 'sales.csv'."""
    try:
        path = (WORKSPACE / filename).resolve()

        # Block path tricks like '../.env'
        if WORKSPACE not in path.parents:
            return "Access denied: only files inside the workspace folder can be read."

        if not path.exists():
            available = [p.name for p in WORKSPACE.iterdir() if p.is_file()]
            return f"File not found. Available files: {available}"

        if path.suffix.lower() not in ALLOWED_TYPES:
            return f"Unsupported file type. Allowed: {sorted(ALLOWED_TYPES)}"

        if path.suffix.lower() == ".pdf":
            from pypdf import PdfReader

            text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")

        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + "\n...[truncated]"
        return text or "File is empty."
    except Exception as e:
        return f"File read error: {e}"


# Registry used by the agent to look up tools by name
TOOLS = {t.name: t for t in (calculator, web_search, read_file)}


# ---------- Quick test: run `python tools.py` ----------
if __name__ == "__main__":
    print("Calculator test:", calculator.invoke({"expression": "(120 * 1.18) / 4"}))
    print("Search test:", web_search.invoke({"query": "capital of Japan"})[:200])
    print("File test:", read_file.invoke({"filename": "sales.csv"}))
    print("Security test:", read_file.invoke({"filename": "../.env"}))