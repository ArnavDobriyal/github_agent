import os
import subprocess
import logging
from google.adk.agents import Agent, LlmAgent
from google.adk.tools.agent_tool import AgentTool
import json
from pydantic import BaseModel
import json
import socket
# ——— Setup & Context ———
logging.basicConfig(level=logging.INFO)

class RepoContext:
    path: str | None = None
# Define the structure of the input
class DockerfileInput(BaseModel):
    file: str
    summary: str
    imports: list[str]
    requirements: list[str]
repo_context = RepoContext()

def run_git_command(*args: str) -> str:
    if not repo_context.path:
        return "[ERROR] Repo path not set. Call set_repo_path() first."
    try:
        logging.info(f"git {' '.join(args)} @ {repo_context.path}")
        out = subprocess.run(
            ["git", *args],
            capture_output=True, text=True, check=True,
            cwd=repo_context.path
        ).stdout.strip()
        return out or "[OK] Command succeeded."
    except subprocess.CalledProcessError as e:
        return f"[ERROR] {e.stderr.strip()}"

def run_shell_command(cmd: str) -> str:
    if not repo_context.path:
        return "[ERROR] Repo path not set."
    try:
        logging.info(f"shell: {cmd} @ {repo_context.path}")
        out = subprocess.run(
            cmd, shell=True,
            capture_output=True, text=True, check=True,
            cwd=repo_context.path
        ).stdout.strip()
        return out or "[OK] Command succeeded."
    except subprocess.CalledProcessError as e:
        return f"[ERROR] {e.stderr.strip()}"

def set_repo_path(path: str) -> str:
    if not os.path.exists(path):
        return "[ERROR] Path does not exist."
    repo_context.path = path
    if not os.path.isdir(os.path.join(path, ".git")):
        subprocess.run(["git", "init"], cwd=path, check=True)
    files = [f for f in os.listdir(path) if not f.startswith('.') and f not in {'.env', 'env', 'venv', '.venv'}]
    preview = "\n".join(f"- {f}" for f in files[:10]) or "(empty)"
    return f"✅ Repo set to: {path}\n📁 Preview:\n{preview}"

def get_status() -> str:
    return run_git_command("status")

def add_data() -> str:
    return run_git_command("add", ".")

def commit_data(msg: str) -> str:
    add_res = run_git_command("add", ".")
    commit_res = run_git_command("commit", "-m", msg)
    return f"{add_res}\n{commit_res}"

def push_changes() -> str:
    update_readme()
    return run_git_command("push")

def pull_changes() -> str:
    return run_git_command("pull")

def rollback_last_commit() -> str:
    return run_git_command("reset", "--soft", "HEAD~1")

def create_branch(branch_name: str) -> str:
    return run_git_command("checkout", "-b", branch_name)

def switch_branch(branch_name: str) -> str:
    return run_git_command("checkout", branch_name)

def delete_branch(branch_name: str) -> str:
    return run_git_command("branch", "-d", branch_name)

def stash_changes() -> str:
    return run_git_command("stash")

def apply_stash() -> str:
    return run_git_command("stash", "apply")

def view_log() -> str:
    return run_git_command("log", "--oneline", "-n", "5")

def recommend_action() -> str:
    status = run_git_command("status")
    recs = ["Here’s my recommendation:\n"]
    if "Changes not staged" in status: recs.append("- Stage changes: add_data()\n")
    if "Changes to be committed" in status: recs.append("- Commit staged: commit_data(msg)\n")
    if "Untracked files" in status: recs.append("- Stage untracked: add_data()\n")
    if "ahead of" in status: recs.append("- Push to remote: push_changes()\n")
    if "working tree clean" in status: recs.append("- Tree clean: maybe switch_branch() or pull_changes().\n")
    return "".join(recs) if len(recs) > 1 else "Nothing to recommend."

def list_repo_files() -> str:
    if not repo_context.path:
        return "[ERROR] Repo path not set."
    items = [f for f in os.listdir(repo_context.path)
             if not f.startswith('.') and f not in {'.env', 'env', 'venv', '.venv', 'README.md','__pycache__'}]
    return "📁 Files:\n" + "\n".join(f"- {i}" for i in items)

def list_folder_contents(subpath: str) -> str:
    if not repo_context.path:
        return "[ERROR] Repo path not set."
    full = os.path.join(repo_context.path, subpath)
    if not os.path.isdir(full):
        return f"[ERROR] {subpath} is not a directory."
    items = [i for i in os.listdir(full) if not i.startswith('.') and i not in {'.env', 'env', 'venv', '.venv','__pycache__'}]
    return f"📂 Contents of {subpath}:\n" + "\n".join(f"- {i}" for i in items)

def describe_structure() -> str:
    if not repo_context.path:
        return "[ERROR] Repo path not set."
    lines = []
    for root, dirs, files in os.walk(repo_context.path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'.env', 'env', 'venv', '.venv','__pycache__'}]
        level = root.replace(repo_context.path, '').count(os.sep)
        indent = '  ' * level
        folder = os.path.basename(root) or os.path.basename(repo_context.path)
        lines.append(f"{indent}- {folder}/")
        for f in files:
            if f.startswith('.') or f in {'README.md', '.env'}:
                continue
            lines.append(f"{indent}  - {f}")
    return "\n".join(lines)

def update_readme() -> str:
    if not repo_context.path:
        return "[ERROR] Repo path not set."
    readme_path = os.path.join(repo_context.path, 'README.md')
    content = '\n\n# Project Structure\n\n' + describe_structure() + '\n'
    try:
        with open(readme_path, 'a', encoding='utf-8') as f:
            f.write(content)
        return '✅ Appended project structure to README.md.'
    except Exception as e:
        return f"[ERROR] Failed to update README.md: {e}"

    
# ——— Tool: Get file content ————————————————————————————————
def get_file_content(file_name: str) -> str:
    try:
        file_path = os.path.join(repo_context.path, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"[ERROR] Could not read {file_name}: {e}"


# ——— Tool: Generate context.json ————————————————————————
def update_code_context(content: dict) -> str:
    context_path = os.path.join(repo_context.path, 'context.json')
    try:
        # Check if file exists and has valid JSON list
        if os.path.exists(context_path):
            with open(context_path, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
                except json.JSONDecodeError:
                    existing_data = []
        else:
            existing_data = []

        # Append new content
        existing_data.append(content)

        # Write updated list back to file
        with open(context_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2)

        return f"✅ Appended new context to context.json successfully."
    except Exception as e:
        return f"[ERROR] Failed to update context.json: {e}"

    
# Reads context.json and sends it to the LLM agent for Dockerfile generation
def generate_dockerfile_from_context(dockerfile_content: str) -> str:
    try:
        # Check if repo_context.path is set
        if repo_context.path is None:
            return "[ERROR] Repository path is not set in RepoContext."

        # Define path for Dockerfile inside the repo context
        dockerfile_path = os.path.join(repo_context.path, "Dockerfile")

        # Create the Dockerfile
        with open(dockerfile_path, "w", encoding="utf-8") as f:
            f.write(dockerfile_content.strip())
        
        return f"✅ Dockerfile successfully created at: {dockerfile_path}"

    except Exception as e:
        return f"[ERROR] Failed to write Dockerfile: {str(e)}"

def build_docker_image(tag: str = "my_app_image") -> str:
    try:
        result = subprocess.run(
            ["docker", "build", "-t", tag, "."],
            capture_output=True, text=True,
            cwd=repo_context.path
        )
        if result.returncode == 0:
            return f"✅ Docker image built successfully with tag: {tag}"
        else:
            return f"[ERROR] Docker build failed:\n{result.stdout}\n{result.stderr}"
    except Exception as e:
        return f"[ERROR] Exception during Docker build: {e}"


def get_available_port(start_port: int = 8000, end_port: int = 8100) -> int:
    """
    Return the first free TCP port in [start_port, end_port).
    Cross-platform method by attempting to bind each port.
    """
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No free ports found in range {start_port}-{end_port}")

def run_docker_container(tag: str) -> str:
    try:
        # Run container without manual port mapping
        result = subprocess.run(
            ["docker", "run", "-d", tag],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return f"[ERROR] Docker run failed:\n{result.stdout}\n{result.stderr}"

        container_id = result.stdout.strip()

        # Check container logs for crash
        logs = subprocess.run(["docker", "logs", container_id], capture_output=True, text=True)
        if "Traceback" in logs.stdout or "Exception" in logs.stdout:
            return f"[ERROR] Container log shows crash:\n{logs.stdout}"
        return f"🚀 Docker container running!\nContainer ID: {container_id}"

    except Exception as e:
        return f"[ERROR] Exception during Docker run: {e}"
# ——— Agent: Summarizer —————————————————————————————————————
summarizer = LlmAgent(
    name="Summarizer",
    model="gemini-2.0-flash",
    instruction=(
        ""
        "You are a code summarization assistant.\n"
        "Given the full contents of a source file, return a JSON object with:\n"
        "- file: the filename\n"
        "- summary: a 2–3 sentence description of its purpose and logic\n"
        "- imports: list of imports used\n"
        "- requirements: list of external packages needed for Docker or installation\n"
        "Do not ask user for validation of json directly call update_code_context"
        "Only respond with a JSON object to update_code_context.Do not show the Json to user\n"
        "If user selects to summarise all the files then use the describe_structure,list_folder_contents,list_repo_files as necessary to find all information\n"
        "the content will be sent back to you by get_file_content you need to summarise it into the json object and send to update_code_context "
    ),
    tools=[
        get_file_content,
        update_code_context,
        list_repo_files,
        list_folder_contents,
        describe_structure
    ]
)

# ——— Agent: Docker —————————————————————————————————————
dockerfile_agent = LlmAgent(
    name="DockerfileGenerator",
    model="gemini-2.0-flash",
    instruction=(
        "You are a Dockerfile generation expert and interactive deployment assistant.\n"
        "This will be a back-and-forth session to tailor the Dockerfile to user needs.\n"
        "The user will supply a JSON object (`context.json`) containing:\n"
        "- file: main entry file path (e.g., `api/main.py`, `server.js`, `main.go`)\n"
        "- summary: short description of the project\n"
        "- imports: list of project dependencies or modules\n"
        "- requirements: explicit packages or version pins\n"
        "\n"
        "**Interactive Steps**:\n"
        "1) **Clarify requirements**:\n"
        "   - Ask the user if they need environment variables, volume mounts, or custom build args.\n"
        "   - Confirm desired base image variants (slim vs alpine).\n"
        "2) **Reserve a port**:\n"
        "   - Call `get_available_port(8000, 8100)` and tell the user which port was reserved.\n"
        "3) **Generate Dockerfile draft**:\n"
        "   - Detect language by file extension.\n"
        "   - Use multi-stage builds for size optimization.\n"
        "   - Set `WORKDIR /app`.\n"
        "   - Copy only necessary files first to leverage layer caching.\n"
        "   - Install dependencies: use `requirements.txt` or infer from imports.\n"
        "   - Install system packages if needed (APT or APK).\n"
        "   - EXPOSE the reserved port.\n"
        "   - Set `CMD` to run the app on that port.\n"
        "4) **Review with user**:\n"
        "   - Present the generated Dockerfile and ask for edits (ports, env vars, healthchecks).\n"
        "   - Apply any user edits dynamically via follow-up instructions.\n"
        "5) **Save & deploy**:\n"
        "   - Call `generate_dockerfile_from_context` to write the file.\n"
        "   - Build with `build_docker_image`.\n"
        "   - Run with `run_docker_container`.\n"
        "6) **Report result**:\n"
        "   - Show only success messages or structured error outputs from each tool.\n"
        "\n"
    ),
    tools=[
        get_available_port,
        generate_dockerfile_from_context,
        build_docker_image,
        run_docker_container,
        get_file_content,
        list_repo_files,
        list_folder_contents,
        describe_structure,
        run_shell_command    ]
)





# ——— Agent Definition ———————————————————————————————
root_agent = Agent(
    name="git_control_agent",
    model="gemini-2.0-flash",
    description="AI assistant to manage Git repos and project structure.",
    instruction=(
        "First ask the user to set the repository path then set it using set_repo_path. Do not mention names of functions\n"
        "Available tools:\n"
        "- Git basics: get_status, add_data, commit_data, push_changes, pull_changes, rollback_last_commit\n" 
        "- Branching: create_branch, switch_branch, delete_branch\n"
        "- Stash: stash_changes, apply_stash\n"
        "- Logs & tips: view_log, recommend_action\n"
        "- File/Folder: list_repo_files, list_folder_contents, describe_structure, update_readme\n"
        "- Shell execution: run_shell_command(cmd)\n"
        "update_readme should be run when new data is added\n"
        "Always present most of the structure or data in highly redable format \n"
        "**If there is a requirement that are not in tools then directly tell the user the commands to do it from cmd and if user accepts then run the command using run_shell_command**\n"
        "Use only what the user asks, in the right order (e.g., add_data() before commit_data())."
    ),
    tools=[
        set_repo_path,
        run_shell_command,
        # Git tools
        get_status, add_data, commit_data, push_changes, pull_changes,
        rollback_last_commit, create_branch, switch_branch, delete_branch,
        stash_changes, apply_stash, view_log, recommend_action,
        # File/Folder
        list_repo_files, list_folder_contents, describe_structure, update_readme,
        # Summarization
    ],
    sub_agents=[summarizer,dockerfile_agent]
)