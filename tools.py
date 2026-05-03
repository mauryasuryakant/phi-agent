import webbrowser
import subprocess

def open_youtube():
    webbrowser.open("https://www.youtube.com")
    return "Opened YouTube"

def google_search(query):
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)
    return f"Searched Google for {query}"

def create_file(filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return f"File '{filename}' created"

# ⚠️ restrict commands
ALLOWED_COMMANDS = ["dir", "echo"]

def run_command(cmd):
    if not any(cmd.startswith(c) for c in ALLOWED_COMMANDS):
        return "Command not allowed"

    result = subprocess.getoutput(cmd)
    return result