import json
import re

def parse_response(text):
    action = None
    action_input = {}

    # Extract Action
    action_match = re.search(r"Action:\s*(\w+)", text)
    if action_match:
        action = action_match.group(1)

    # Extract JSON safely
    input_match = re.search(r"Action Input:\s*(\{.*\})", text, re.DOTALL)
    if input_match:
        try:
            action_input = json.loads(input_match.group(1))
        except:
            action_input = {}

    return action, action_input