import os
import subprocess
import logging
from google.adk.agents import Agent

# Setup logging
logging.basicConfig(level=logging.INFO)

# Store the repo path for the session
class RepoContext:
    path = None

repo_context = RepoContext()

# Universal Git runner
def run_git_command(*args: str) -> str:
    if not repo_context.path:
        return "[ERROR] Repository path not set. Use 'set_repo_path' first."
    try:
        logging.info(f"Running: git {' '.join(args)} in {repo_context.path}")
        result = subprocess.run(["git", *args], capture_output=True, text=True, check=True, cwd=repo_context.path)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"[ERROR] Git command failed:\n{e.stderr.strip()}"

# ---- Core Git Tools ----
def get_status() -> str:
    return run_git_command("status")

def add_data() -> str:
    return run_git_command("add", ".")

def commit_data(msg: str) -> str:
    return run_git_command("commit", "-m", msg)

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
    recs = ["Here’s what I suggest:\n"]

    if "Changes not staged" in status:
        recs.append("- You have unstaged changes. Use `add_data()`.\n")
    if "Changes to be committed" in status:
        recs.append("- You have staged changes. Use `commit_data()`.\n")
    if "Untracked files" in status:
        recs.append("- There are untracked files. You might want to stage them.\n")
    if "Your branch is ahead" in status:
        recs.append("- Your branch is ahead. Consider `push_changes()`.\n")
    if "working tree clean" in status:
        recs.append("- Everything looks clean. You can switch branches or pull changes.\n")

    return "".join(recs) if len(recs) > 1 else "Repo looks clean. Nothing to recommend."

# ---- Repo & File Management ----
def set_repo_path(path: str) -> str:
    if not os.path.exists(path):
        return "[ERROR] This path does not exist."
    repo_context.path = path

    if not os.path.isdir(os.path.join(path, ".git")):
        subprocess.run(["git", "init"], cwd=path)

    files = os.listdir(path)
    preview = "\n".join(f"- {f}" for f in files[:10]) if files else "(empty)"
    return f"✅ Repo set to: {path}\n📁 Preview:\n{preview}"

def git_init() -> str:
    return run_git_command("init")

def list_repo_files() -> str:
    if not repo_context.path:
        return "[ERROR] Repository path not set."
    try:
        files = os.listdir(repo_context.path)
        return "📁 Files:\n" + "\n".join(f"- {f}" for f in files)
    except Exception as e:
        return f"[ERROR] Failed to list files: {str(e)}"

def create_folder(folder_name: str) -> str:
    if not repo_context.path:
        return "[ERROR] Repository path not set."
    try:
        full_path = os.path.join(repo_context.path, folder_name)
        os.makedirs(full_path, exist_ok=True)
        return f"📁 Folder created: {folder_name}"
    except Exception as e:
        return f"[ERROR] Failed to create folder: {str(e)}"

# ---- Agent Definition ----
root_agent = Agent(
    name="git_control_agent",
    model="gemini-2.0-flash",
    description="An AI agent to help you manage Git operations in any local folder.",
    instruction=(
        "You are a helpful Git agent. Ask the user to set the repo folder before doing anything.Use the set_repo_path to set it "
        "Once set, you can use the tools below to help them:\n"
        "- Git basics: get_status, add_data, commit_data, push_changes, pull_changes, rollback_last_commit\n"
        "- Branching: create_branch, switch_branch, delete_branch\n"
        "- Stashing: stash_changes, apply_stash\n"
        "- Logs & tips: view_log, recommend_action\n"
        "- Folder tools: create_folder, list_repo_files\n"
        "Only do what the user asks you to do."
        "Do not mention tools name"
    ),
    tools=[
        set_repo_path,
        git_init,
        get_status,
        add_data,
        commit_data,
        push_changes,
        pull_changes,
        rollback_last_commit,
        create_branch,
        switch_branch,
        delete_branch,
        stash_changes,
        apply_stash,
        view_log,
        recommend_action,
        list_repo_files,
        create_folder
    ],
)
