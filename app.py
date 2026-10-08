"""Streamlit UI for the Autonomous AI Task Agent."""
import json
from pathlib import Path

import streamlit as st

from agent import MODEL, run
from tools import WORKSPACE

st.set_page_config(page_title="Autonomous AI Task Agent", page_icon="🤖", layout="wide")

st.title("🤖 Autonomous AI Task Agent")
st.caption("Plans a goal, calls tools, self-corrects, and writes a final answer.")

# ---------- sidebar ----------
with st.sidebar:
    st.header("Settings")
    max_retries = st.slider("Max self-correction retries", 0, 3, 2)
    st.markdown(f"**Model:** `{MODEL}`")
    st.markdown("**Tools:** web search, calculator, file reader")

    st.divider()
    st.subheader("Files for the agent")
    uploaded = st.file_uploader(
        "Upload a file", type=["txt", "md", "csv", "json", "py", "pdf"]
    )
    if uploaded:
        (WORKSPACE / Path(uploaded.name).name).write_bytes(uploaded.getvalue())
        st.success(f"Saved {uploaded.name}")
    files = [p.name for p in WORKSPACE.iterdir() if p.is_file()]
    st.caption("Available: " + (", ".join(files) or "none"))

    st.divider()
    st.markdown(
        "**How it works**\n\n"
        "1. Planner splits the goal into sub-tasks\n"
        "2. Executor calls tools for each sub-task\n"
        "3. Critic checks the result and triggers retries\n"
        "4. Memory carries results between steps"
    )

# ---------- example goals ----------
examples = [
    "Find the current population of India and Japan, then calculate how many times larger India's population is",
    "Find the height of Mount Everest in meters and convert it to feet",
    "Read sales.csv and calculate the total revenue (units times price for each product, then add them up)",
    "Read sales.csv, calculate revenue per product, and tell me which product earns the most",
]
choice = st.selectbox("Try an example (or type your own below)", [""] + examples)
goal = st.text_area("Your goal", value=choice, height=100)

# ---------- run ----------
if st.button("Run agent", type="primary"):
    if not goal.strip():
        st.warning("Please enter a goal first.")
    else:
        with st.status("Agent is working...", expanded=True) as status:
            try:
                answer = run(goal, max_retries=max_retries, log=st.write)
                status.update(label="Agent finished", state="complete")
            except Exception as e:
                status.update(label="Agent failed", state="error")
                st.error(f"Error: {e}")
                st.stop()

        st.subheader("Final answer")
        st.markdown(answer)

        mem_file = Path("memory.json")
        if mem_file.exists():
            with st.expander("View agent memory (memory.json)"):
                st.json(json.loads(mem_file.read_text(encoding="utf-8")))