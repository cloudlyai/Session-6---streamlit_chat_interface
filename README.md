# Session 6: Streamlit Chat UI

Part of the **AI Engineering Course**, a hands-on course for software engineers
transitioning into AI engineering.

## Goal

Take the puzzle agent from Session 5 and give it a browser chat UI using Streamlit.
The agent logic stays the same - only the UI layer changes.

## Programs

### `streamlit_agent.py`

The puzzle agent with a Streamlit chat interface:

- Agent loop with tool calling (get puzzles, validate, retrieve)
- Retry with exponential backoff and non-retryable error handling
- Token and cost tracking per conversation turn
- Max iteration guard and wall-clock timeout
- Input validation

### `demo_streamlit.py`

A standalone Streamlit demo for exploring core Streamlit concepts before
looking at the full agent.

## Key Concepts

- **Streamlit rerun model:** the entire script reruns top-to-bottom on every
  user action
- **`st.session_state`:** persists data across reruns, replacing global variables
- **Two separate state lists:**
  - `messages` - full LLM conversation history including tool calls (what the
    agent needs)
  - `chat_history` - user and assistant text only (what the UI renders)
- **Rendering order:** capture input, append to `chat_history`, render history,
  run agent loop, append response, `st.rerun()`
- **`st.spinner("Thinking...")`** for visual feedback while the agent is running

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

Make sure you have a `.env` file with your OpenAI API key and a
`C:\puzzle\puzzle.txt` file with puzzle data.

## Course Arc

| Session | Topic |
|---------|-------|
| Session 1 | Introduction |
| Session 2 | LLM Orchestration - Raw API Calls |
| Session 3 | Basic AI Agents - Tool Calling |
| Session 4 | Intermediate AI Agents - Agent Loop and State |
| Session 5 | Reliable Agents - Retries, Timeouts, Cost Tracking |
| **Session 6** | **Streamlit Chat UI** <- you are here |
| Session 7 | OpenAI Agents SDK - Foundations |
| Session 8 | OpenAI Agents SDK - Multi-Agent Handoffs |
| Session 9 | OpenAI Agents SDK - Guardrails and Tripwires |
