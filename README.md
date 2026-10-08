# 🤖 Autonomous AI Task Agent

A multi-step autonomous agent built with **LangChain** that takes a high-level goal, decomposes it into sub-tasks, calls external tools, and **self-corrects** based on intermediate results.

## Features

- **Task decomposition**: a planner breaks a goal into 2-5 ordered sub-tasks
- **Tool calling**: the agent decides when to use web search, a calculator, or a file reader
- **Self-correction**: a critic reviews each result and triggers retries with feedback
- **Memory layer**: results carry across steps and every run is saved to `memory.json`
- **File reader**: reads txt, md, csv, json, py, and pdf files from a sandboxed `workspace` folder
- **Streamlit UI**: upload files and watch the plan, tool calls, and retries live

## Architecture

```
User goal
   │
   ▼
Planner ──► [sub-task 1, sub-task 2, ...]
   │
   ▼
For each sub-task:
   Executor (LLM + tools) ──► Critic ──► OK? ──► Memory
        ▲                        │ no
        └──── feedback ──────────┘ (retry, up to N times)
   │
   ▼
Synthesizer ──► Final answer
```

## Tools

| Tool | What it does |
|---|---|
| `web_search` | Searches the web with DuckDuckGo for current information |
| `calculator` | Evaluates math safely by parsing expressions with `ast` (no `eval`) |
| `read_file` | Reads files from the `workspace` folder; blocks path tricks like `../.env` |

## Tech stack

Python · LangChain · Groq LLM API (`openai/gpt-oss-120b`) · Streamlit · DuckDuckGo Search · pypdf · Prompt Engineering

## Project structure

| File | Purpose |
|---|---|
| `agent.py` | Planner, executor, critic, and orchestration loop |
| `tools.py` | Calculator, web search, and sandboxed file reader |
| `agent_memory.py` | Short-term context and JSON persistence |
| `app.py` | Streamlit web interface with file upload |
| `workspace/` | Files the agent is allowed to read (includes sample `sales.csv`) |

## Setup

```bash
git clone https://github.com/jyoti9bhardwaj99-byte/Autonomous-AI-Task-Agent.git
cd Autonomous-AI-Task-Agent
python -m venv venv
venv\Scripts\activate        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`) with your free [Groq API key](https://console.groq.com/keys):

```
GROQ_API_KEY=your_key_here
```

To use a different Groq model, set `GROQ_MODEL` in `.env`.

## Run

Web app:

```bash
streamlit run app.py
```

Command line:

```bash
python agent.py "Find the height of Mount Everest in meters and convert it to feet"
```

## Example goals

- Find the current population of India and Japan, then calculate how many times larger India's is
- Find the height of Mount Everest in meters and convert it to feet
- Read sales.csv and calculate the total revenue (units times price for each product, then add them up)
- Read sales.csv, calculate revenue per product, and tell me which product earns the most

## Design notes

- The calculator parses expressions with Python's `ast` module instead of `eval()` to avoid code injection.
- The file reader resolves every path and refuses anything outside `workspace/`, so the agent can't read secrets such as `.env`.
- The critic is a separate LLM call with a strict reviewer prompt, so the agent catches incomplete or unsupported answers instead of accepting its first attempt.
- Prompts tell the agent to use only facts from tool results, which reduces hallucinated details such as invented units or currency symbols.
- Retries and tool iterations are capped, so the agent can't loop forever.

## Future improvements

- Evaluation set to measure success rate with and without the critic
- More tools (Python REPL, API calls)
- Migrate orchestration to LangGraph
- Deploy on Streamlit Community Cloud
