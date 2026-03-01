
import json
import re
import random
import time

import litellm

import streamlit as st

from dotenv import load_dotenv
from litellm import completion

load_dotenv()

PUZZLE_FILE_PATH = r"C:\puzzle\puzzle.txt"



# ======================validate puzzle before retrieval===

def validate_puzzle(puzzle_number: int) -> str:
    """Returns a random score that's always below 7 """
    score = random.randint(7, 9)
    return f"Puzzle {puzzle_number} quality score: {score}/10. above minimum threshold of 7/10."

def get_available_puzzles() -> str:
    """Get list of puzzles that haven't been used yet."""
    try:
        with open(PUZZLE_FILE_PATH, "r", encoding="utf-8") as file:
            content = file.read()

        # Parse all puzzles from file
        puzzles = re.split(r'(?=Puzzle \d+)', content)
        puzzles = [p.strip() for p in puzzles if p.strip()]

        # Filter out used puzzles
        available = []
        for puzzle in puzzles:
            # Extract puzzle name (e.g., "Puzzle 1")
            match = re.match(r'(Puzzle \d+)', puzzle)
            if match:
                puzzle_name = match.group(1)
                if puzzle_name not in st.session_state.used_puzzles:
                    # Get first line as title
                    first_line = puzzle.split('\n')[0]
                    available.append(first_line)

        if not available:
            return "NO_PUZZLES_LEFT"

        return "Available puzzles:\n" + "\n".join(f"- {p}" for p in available)

    except FileNotFoundError:
        return "Error: puzzle.txt not found."
    except Exception as e:
        return f"Error: {str(e)}"
    

def get_puzzle(puzzle_number: int) -> str:
    """Get a specific puzzle by its number and mark it as used."""
  

    try:
        with open(PUZZLE_FILE_PATH, "r", encoding="utf-8") as file:
            content = file.read()

        # Parse puzzles from file
        puzzles = re.split(r'(?=Puzzle \d+)', content)
        puzzles = [p.strip() for p in puzzles if p.strip()]

        # Find the requested puzzle
        puzzle_name = f"Puzzle {puzzle_number}"

        for puzzle in puzzles:
            if puzzle.startswith(puzzle_name):
                # Mark as used
                st.session_state.used_puzzles.add(puzzle_name)
                return puzzle

        return f"Puzzle {puzzle_number} not found in file."

    except FileNotFoundError:
        return "Error: puzzle.txt not found."
    except Exception as e:
        return f"Error: {str(e)}"
    
tool_functions = {
    "get_available_puzzles": get_available_puzzles,
    "get_puzzle": get_puzzle,
    "validate_puzzle": validate_puzzle
}

# ==Tool Schema for LLM - describes what the tool does and its parameters==

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_available_puzzles",
            "description": "Get a list of puzzles that are still available (not yet used). Returns 'NO_PUZZLES_LEFT' if all puzzles have been used.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_puzzle",
            "description": "Get a specific puzzle by its number. This marks the puzzle as used.",
            "parameters": {
                "type": "object",
                "properties": {
                    "puzzle_number": {
                        "type": "integer",
                        "description": "The puzzle number to retrieve (e.g., 1, 2, or 3)"
                    }
                },
                "required": ["puzzle_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_puzzle",
            "description": "Validate a puzzle's quality score before presenting it. Returns a score out of 10.",
            "parameters": {
                "type": "object",
                "properties": {
                    "puzzle_number": {
                        "type": "integer",
                        "description": "The puzzle number to validate"
                    }
                },
                "required": ["puzzle_number"]
            }
        }
    }
]


# ======================
# System Prompt
# ======================

system_prompt = """
You are a puzzle delivery agent that gives users puzzles one at a time.

Your workflow:
1. First, check what puzzles are available using get_available_puzzles
2. Before retrieving, validate the puzzle using validate_puzzle
3. Only retrieve (get_puzzle) and present puzzles scoring 7/10 or above
4. If puzzles are available, pick one and retrieve it using get_puzzle
5. Present the puzzle to the user
6. If user asks for another puzzle, repeat the process
7. If no puzzles are left (NO_PUZZLES_LEFT), inform the user that all puzzles have been used.
8. Quality scores can change between checks, so retry puzzles that previously scored low

Rules:
- Always check available puzzles first before retrieving one
- Never make up puzzles - only use ones from the file
- When all puzzles are exhausted, clearly tell the user
- Don't answer anything except puzzles from the file
- In context of puzzles also, if user ask anything except puzzle content, for e.g. count , hint, etc, respond with "I can only provide puzzles, that too one at a time. Please ask for a puzzle."
"""

NON_RETRYABLE_ERRORS = (
    litellm.AuthenticationError,   # 401 - bad API key
    litellm.BadRequestError,       # 400 - malformed request
    litellm.NotFoundError,         # 404 - wrong model name
)

def call_llm_with_retry(messages, tools, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = completion(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                max_tokens=1024,
            )
            return response

        except NON_RETRYABLE_ERRORS as e:
            # No point retrying these - they'll fail every time
            print(f"  [Fatal Error]: {e}")
            return None

        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # 1s, 2s, 4s
                print(f"  Error: {e}")
                print(f"  Retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait)
            else:
                print(f"  All {max_retries} attempts failed: {e}")
                return None


# gpt-4o-mini pricing per 1M tokens
COST_PER_1M_INPUT = 0.15
COST_PER_1M_OUTPUT = 0.60

def print_cost_summary(llm_calls, prompt_tokens, completion_tokens):
    total_tokens = prompt_tokens + completion_tokens
    cost = (prompt_tokens * COST_PER_1M_INPUT + completion_tokens * COST_PER_1M_OUTPUT) / 1_000_000
    print(f"  [Cost] LLM calls: {llm_calls} | Prompt: {prompt_tokens} | Completion: {completion_tokens} | Total: {total_tokens} | ${cost:.6f}")

MAX_INPUT_LENGTH = 100

def validate_input(user_input):
    if len(user_input) > MAX_INPUT_LENGTH:
        return f"Input too long ({len(user_input)} chars). Max {MAX_INPUT_LENGTH} allowed."
    return None


#======================
# Agent Loop Function
# ======================

def run_agent_loop(user_input: str, messages: list) -> str:
    """
    Run the agent loop until LLM decides to stop calling tools.
    Returns the final response from the agent.
    """
    # Validate input before doing anything
    validation_error = validate_input(user_input)
    if validation_error:
        return validation_error

    # Add user message
    messages.append({"role": "user", "content": user_input})

    iteration = 0
    max_iterations = 10  # Safety cap to prevent infinite loops during testing

    llm_calls = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0

    start_time = time.time()
    timeout_seconds = 10 

    while True:

        iteration += 1
        if iteration > max_iterations:
            print(f"Agent loop exceeded max iterations ({max_iterations}). Stopping.")
            messages.append({"role": "assistant", "content": "Error: Agent loop exceeded maximum iterations."})
            return "Sorry, I'm having trouble retrieving a puzzle right now. Please try again later."
        
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout_seconds:
            print(f"Agent loop timed out after {elapsed_time:.1f}s (limit: {timeout_seconds}s). Stopping.")
            print_cost_summary(llm_calls, total_prompt_tokens, total_completion_tokens)
            return "Error: Agent loop timed out."

        # Call LLM
        response = call_llm_with_retry(messages, tools)
        if response is None:
            if llm_calls > 0:
                print_cost_summary(llm_calls, total_prompt_tokens, total_completion_tokens)
                return "Sorry, I'm having trouble retrieving a puzzle right now. Please try again later."
        
        llm_calls += 1
        if response.usage:
            total_prompt_tokens += response.usage.prompt_tokens
            total_completion_tokens += response.usage.completion_tokens

        message = response.choices[0].message



        # If no tool calls, LLM is done - return the response
        if not message.tool_calls:
            # Add assistant response to history
            messages.append({"role": "assistant", "content": message.content})
            print_cost_summary(llm_calls, total_prompt_tokens, total_completion_tokens)
            return message.content

        # Process each tool call
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments or "{}")

            print(f"  [Tool Called]: {tool_name}")
            if tool_args:
                print(f"  [Arguments]: {tool_args}")

            # Execute the tool
            result = tool_functions[tool_name](**tool_args)

            print(f"  [Tool Result]: {result[:100]}..." if len(str(result)) > 100 else f"  [Tool Result]: {result}")
            print()

            # Add assistant message with tool call to history
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [tool_call]
            })

            # Add tool result to history so LLM can see it
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })


# ======================
# Streamlit UI
# ======================

st.title("Puzzle Agent")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

if "used_puzzles" not in st.session_state:
    st.session_state.used_puzzles = set()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.chat_input("Ask for a puzzle...")


if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = run_agent_loop(st.session_state.chat_history[-1]["content"], st.session_state.messages)
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    st.rerun()


