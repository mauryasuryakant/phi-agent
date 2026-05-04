import requests
from tools import *
from parser import parse_response
from config import *

VALID_ACTIONS = {
    "open_youtube",
    "youtube_search",
    "open_url",
    "google_search",
    "create_file",
    "run_command",
    "finish"
}

def call_model(prompt):
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]


def execute(action, inputs):
    if action == "open_youtube":
        return open_youtube()

    elif action == "youtube_search":
        if isinstance(inputs, dict):
            query = (
                inputs.get("query")
                or inputs.get("search_query")
                or inputs.get("search_term")
            )
            if query:
                return youtube_search(query=query)

        if isinstance(inputs, str):
            return youtube_search(query=inputs)

        return "Error: Missing 'query' for youtube_search"

    elif action == "open_url":
        if isinstance(inputs, dict) and "url" in inputs:
            return open_url(inputs["url"])

        if isinstance(inputs, str):
            return open_url(inputs)

        return "Error: Missing 'url' for open_url"

    elif action == "google_search":
        if isinstance(inputs, dict):
            query = (
                inputs.get("query")
                or inputs.get("q")
                or inputs.get("search_query")
            )
            if query:
                return google_search(query=query)

        if isinstance(inputs, str):
            return google_search(query=inputs)

        return "Error: Missing 'query' for google_search"

    elif action == "create_file":
        if isinstance(inputs, dict):
            filename = inputs.get("filename") or inputs.get("file_name")
            content = inputs.get("content")

            if filename and content:
                return create_file(filename, content)

        return "Error: Missing filename/content"

    elif action == "run_command":
        return run_command(str(inputs))

    return "Unknown action"


def run_agent(task):
    prompt = f"""
You are a STRICT ReAct agent.

You have tools that can perform real actions. You MUST use them when appropriate.
You ARE capable of performing actions. NEVER say you cannot.

CORE RULES:
1. You MUST complete the FULL task.
2. You MUST output exactly ONE Action and ONE Action Input per step.
3. If the task contains multiple requests, COMPLETE them step-by-step across multiple steps.
4. Do NOT try to solve multiple tasks in a single step.
5. Prefer the most direct and efficient action (avoid unnecessary steps like searching if URL is known).
6. If a well-known website is requested (e.g., YouTube, GitHub), use open_url directly.
7. Do NOT repeat actions unnecessarily.
8. Only use finish when ALL parts of the task are completed.

BEHAVIOR RULES:
9. Do NOT simulate limitations or say you cannot perform actions.
10. Do NOT over-explain. Keep thoughts short and practical.
11. Your reasoning should focus only on selecting the correct next action.

SEARCH RULES:
12. If task asks to search on YouTube:
    - Use youtube_search
    - The query MUST exactly match the user input
    - Do NOT modify, shorten, or simplify the query

FORMAT RULES:
13. Action Input MUST be valid JSON.
14. Output STRICTLY in this format:

Thought: ...
Action: ...
Action Input: {{}}

AVAILABLE ACTIONS:
- open_youtube
- youtube_search
- open_url
- google_search
- create_file
- run_command
- finish

Task: {task}
"""

    for step in range(MAX_STEPS):
        print(f"\n--- Step {step+1} ---")

        response = call_model(prompt)
        print("\nMODEL:\n", response)

        action, inputs = parse_response(response)

        if not action:
            print("❌ Failed to parse action. Stopping.")
            break

        # 🔒 Block invalid actions
        if action not in VALID_ACTIONS:
            print(f"❌ Invalid action: {action}")
            prompt += f"\nObservation: Invalid action '{action}'. Use only valid tools.\n"
            continue

        if action == "finish":
            print("✅ Task completed.")
            break

        if CONFIRM_EXECUTION:
            confirm = input(f"Execute {action} with {inputs}? (y/n): ")
            if confirm.lower() != "y":
                print("⛔ Skipped.")
                break

        try:
            result = execute(action, inputs)
        except Exception as e:
            result = f"Execution error: {str(e)}"

        print("Result:", result)

        # ✅ Auto-stop only when real task completes
        if any(x in result for x in ["Searched YouTube", "Opened URL"]):
            print("✅ Auto-detected success. Finishing.")
            break

        prompt += f"\nObservation: {result}\n"


if __name__ == "__main__":
    user_task = input("Enter your task: ")
    run_agent(user_task)