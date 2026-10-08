"""Tools the agent can call: a safe calculator and web search."""
import ast
import operator

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


# Registry used by the agent to look up tools by name
TOOLS = {t.name: t for t in (calculator, web_search)}


# ---------- Quick test: run `python tools.py` ----------
if __name__ == "__main__":
    print("Calculator test:", calculator.invoke({"expression": "(120 * 1.18) / 4"}))
    print("Search test:", web_search.invoke({"query": "capital of Japan"})[:200])