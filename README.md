# Session 6 - Streamlit Chat UI

Part of the **AI Engineering Course** — a hands-on course for software engineers transitioning into AI engineering.

## Goal

Convert the reliable puzzle agent from Session 4 (terminal-based) into a browser-based chat UI using Streamlit. No changes to agent logic — only the UI layer changes.

## Programs

### `streamlit_agent.py`
The main puzzle agent with a Streamlit chat interface. Features:
- Agent loop with tool calling (get puzzles, validate, retrieve)
- Retry with exponential backoff and non-retryable error handling
- Token/cost tracking per conversation turn
- Max iteration guard and wall-clock timeout
- Input validation

### `demo_streamlit.py`
A standalone Streamlit demo for exploring basic Streamlit concepts.

## Key Concepts

- **Streamlit rerun model** — the entire script reruns top-to-bottom on every user action
- **`st.session_state`** — persists data across reruns (replaces global variables)
- **Two separate state lists:**
  - `messages` — full LLM conversation history including tool calls (what the agent needs)
  - `chat_history` — user and assistant text only (what the UI renders)
- **Rendering order:** capture input → append to `chat_history` → render history → run agent loop → append response → `st.rerun()`
- **`st.spinner("Thinking...")`** for visual feedback during agent processing

## Tech Stack

- Python
- Streamlit
- LiteLLM (with `gpt-4o-mini`)
- python-dotenv

## How to Run

```bash
pip install streamlit litellm python-dotenv
streamlit run streamlit_agent.py
```

Make sure you have a `.env` file with your OpenAI API key and `C:\puzzle\puzzle.txt` with puzzle data.

## Course Arc

| Session | Topic |
|---------|-------|
| Session 1 | Making Calls to LLM |
| Session 2 | AI Agents — Tool Calling + Agent Loop |
| Session 4 | Reliability |
| **Session 6** | **Streamlit Chat UI** |
| Session 7 | OpenAI Agents SDK — Foundations |
| Session 8 | OpenAI Agents SDK — Handoffs |
| Session 9 | OpenAI Agents SDK — Guardrails & Tripwires |
