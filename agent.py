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
    # phi4-mini - If the task is completed, DO NOT take another action.
    # gemma4:e2b - You have tools that can perform actions. You MUST use them when appropriate. Do not simulate inability.
    # gemma4:e2b - If the URL is well-known (e.g., github.com, youtube.com), directly use open_url without searching.
    prompt = f"""
You are a STRICT ReAct agent.
You have tools that can perform actions. You MUST use them when appropriate. Do not simulate inability.
If the URL is well-known (e.g., github.com, youtube.com), directly use open_url without searching.
RULES:
1. ALWAYS use available tools to complete the task.
2. You ARE capable of performing actions using tools. NEVER say you cannot.
3. NEVER use finish unless the FULL task is completed.
4. Prefer completing the task in the MINIMUM number of steps.
5. If task asks to search on YouTube:
   - Use youtube_search directly
   - DO NOT use open_youtube
   - The query MUST exactly match the user's search phrase
   - Do NOT remove or shorten any words
6. DO NOT explain limitations.
7. DO NOT overthink.
8. Action Input MUST be valid JSON. Example: {{"query": "cats"}}
9. Do NOT repeat actions unnecessarily. Choose the best single action if possible.
10. You MUST output exactly ONE Action and ONE Action Input.
11. You MUST use the FULL user query for search without modification.
12. Do NOT simplify or shorten search queries. Use them exactly as given by the user.
Available actions:
13. If the task contains a direct URL, ALWAYS use open_url.
- open_youtube
- youtube_search
- open_url
- google_search
- create_file
- run_command
- finish

Format STRICTLY:

Thought: ...
Action: ...
Action Input: {{}}

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

    # extra prompts
    # DO NOT open YouTube separately before searching.
    # Prefer the most direct tool that completes the task in one step.