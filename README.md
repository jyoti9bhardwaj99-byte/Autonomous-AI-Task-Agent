# 🤖 Autonomous AI Task Agent

A multi-step autonomous agent built with **LangChain** that takes a high-level goal, decomposes it into sub-tasks, calls external tools, and **self-corrects** based on intermediate results.

## Features

- **Task decomposition**: a planner breaks a goal into 2-5 ordered sub-tasks
- **Tool calling**: the agent decides when to use web search or a calculator
- **Self-correction**: a critic reviews each result and triggers retries with feedback
- **Memory layer**: results carry across steps and every run is saved to `memory.json`
- **Streamlit UI**: watch the plan, tool calls, and retries live

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

## Tech stack

Python · LangChain · Groq LLM API (`openai/gpt-oss-120b`) · Streamlit · DuckDuckGo Search · Prompt Engineering

## Project structure

| File | Purpose |
|---|---|
| `agent.py` | Planner, executor, critic, and orchestration loop |
| `tools.py` | Safe calculator (no `eval`) and web search tools |
| `agent_memory.py` | Short-term context and JSON persistence |
| `app.py` | Streamlit web interface |

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/task-agent.git
cd task-agent
python -m venv venv
venv\Scripts\activate        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`) with your free [Groq API key](https://console.groq.com/keys):

```
GROQ_API_KEY=your_key_here
```

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

## Design notes

- The calculator parses expressions with Python's `ast` module instead of `eval()` to avoid code injection.
- The critic is a separate LLM call with a strict reviewer prompt, so the agent catches incomplete answers instead of accepting its first attempt.
- Retries and tool iterations are capped, so the agent can't loop forever.

## Future improvements

- Add more tools (file reader, Python REPL)
- Migrate orchestration to LangGraph
- Add an evaluation set to measure success rate with and without the critic
