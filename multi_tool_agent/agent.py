import os
import subprocess
import logging
from google.adk.agents import Agent

# ——— Setup & Context —————————————————————————————
logging.basicConfig(level=logging.INFO)

class RepoContext:
    path: str | None = None

repo_context = RepoContext()

def run_git_command(*args: str) -> str:
    """Run a git command in the selected repo and return output or error."""
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
    """Run any shell command (from a pre-approved list/file)."""
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

# ——— Path & Initialization —————————————————————————
def set_repo_path(path: str) -> str:
    """Set the working directory and auto-init if needed."""
    if not os.path.exists(path):
        return "[ERROR] Path does not exist."
    repo_context.path = path
    # auto-init git if missing
    if not os.path.isdir(os.path.join(path, ".git")):
        subprocess.run(["git", "init"], cwd=path, check=True)
    files = os.listdir(path)
    preview = "\n".join(f"- {f}" for f in files[:10]) or "(empty)"
    return f"✅ Repo set to: {path}\n📁 Preview:\n{preview}"

# ——— Core Git Tools ———————————————————————————————
def get_status() -> str:
    return run_git_command("status")

def add_data() -> str:
    return run_git_command("add", ".")

def commit_data(msg: str) -> str:
    """Auto-add then commit."""
    add_res = run_git_command("add", ".")
    commit_res = run_git_command("commit", "-m", msg)
    return f"{add_res}\n{commit_res}"

def push_changes() -> str:
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

# ——— File & Folder Tools ———————————————————————————
def list_repo_files() -> str:
    if not repo_context.path:
        return "[ERROR] Repo path not set."
    items = [f for f in os.listdir(repo_context.path)
             if not f.startswith('.') and f != 'README.md']
    return "📁 Files:\n" + "\n".join(f"- {i}" for i in items)

def list_folder_contents(subpath: str) -> str:
    """List files inside a named folder within the repo."""
    if not repo_context.path:
        return "[ERROR] Repo path not set."
    full = os.path.join(repo_context.path, subpath)
    if not os.path.isdir(full):
        return f"[ERROR] {subpath} is not a directory."
    items = [i for i in os.listdir(full) if not i.startswith('.')]
    return f"📂 Contents of {subpath}:\n" + "\n".join(f"- {i}" for i in items)

def describe_structure() -> str:
    """Produce a recursive tree of the project structure, skipping hidden and irrelevant files."""
    if not repo_context.path:
        return "[ERROR] Repo path not set."
    lines = []
    for root, dirs, files in os.walk(repo_context.path):
        # filter out hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        level = root.replace(repo_context.path, '').count(os.sep)
        indent = '  ' * level
        folder = os.path.basename(root) or os.path.basename(repo_context.path)
        lines.append(f"{indent}- {folder}/")
        for f in files:
            if f.startswith('.') or f == 'README.md' or f == '.env':
                continue
            lines.append(f"{indent}  - {f}")
    return "\n".join(lines)

def update_readme() -> str:
    """Write a filtered README.md that reflects current structure."""
    if not repo_context.path:
        return "[ERROR] Repo path not set."
    readme_path = os.path.join(repo_context.path, 'README.md')
    content = '# Project Structure\n\n```\n' + describe_structure() + '\n```'
    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return '✅ README.md updated with current structure.'
    except Exception as e:
        return f"[ERROR] Failed to write README.md: {e}"

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
        "update_readme should be run when you think it is appropriate or some major change occur dont ask user to do it\n"
        "Use only what the user asks, in the right order (e.g., add_data() before commit_data())."
    ),
    tools=[
        set_repo_path,
        run_shell_command,

        # Git
        get_status, add_data, commit_data, push_changes, pull_changes, rollback_last_commit,
        create_branch, switch_branch, delete_branch,
        stash_changes, apply_stash, view_log, recommend_action,

        # FS
        list_repo_files, list_folder_contents, describe_structure, update_readme,
    ],
)
