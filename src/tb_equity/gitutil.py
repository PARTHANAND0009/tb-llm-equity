"""Git helpers used when writing manifests (RULE 1 requires a commit sha)."""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def git_commit_sha(repo_root: Path = REPO_ROOT) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"
