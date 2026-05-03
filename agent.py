import requests
from tools import *
from parser import parse_response
from config import *

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

    elif action == "google_search":
        return google_search(**inputs)

    elif action == "create_file":
        return create_file(**inputs)

    elif action == "run_command":
        return run_command(inputs.get("cmd", ""))

    return "Unknown action"

def run_agent(task):
    prompt = f"""
You are an AI agent using ReAct.

Available actions:
- open_youtube
- google_search
- create_file
- run_command
- finish

Format STRICTLY:

Thought: ...
Action: ...
Action Input: {{}}
"""

    prompt += f"\nTask: {task}\n"

    for step in range(MAX_STEPS):
        print(f"\n--- Step {step+1} ---")

        response = call_model(prompt)
        print("\nMODEL:\n", response)

        action, inputs = parse_response(response)

        if not action:
            print("Failed to parse action. Stopping.")
            break

        if action == "finish":
            print("Task completed.")
            break

        # 🔒 Confirmation layer
        if CONFIRM_EXECUTION:
            confirm = input(f"Execute {action} with {inputs}? (y/n): ")
            if confirm.lower() != "y":
                print("Skipped.")
                break

        result = execute(action, inputs)

        print("Result:", result)

        prompt += f"\nObservation: {result}\n"

if __name__ == "__main__":
    user_task = input("Enter your task: ")
    run_agent(user_task)