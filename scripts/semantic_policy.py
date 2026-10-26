"""Validate the messages used by both squash and rebase merges."""
import re


def errors(title, commits, files, renovate=False):
    messages = [title, *commits]
    problems = []
    pattern = r"^(?:feat|fix|perf|revert|docs|style|refactor|test|build|ci|chore)(?:\([^()\r\n]+\))?!?: \S[^\r\n]*$"
    for index, message in enumerate(messages):
        subject = message.splitlines()[0] if message else ""
        if not re.fullmatch(pattern, subject):
            problems.append(f"{'PR title' if index == 0 else f'Commit {index}'} must use Conventional Commit syntax")
    if not commits:
        problems.append("No commits found; refusing an incomplete validation")
    workflow_only = bool(files) and all(path.startswith(".github/") for path in files)
    if workflow_only:
        for message in messages:
            subject = message.splitlines()[0] if message else ""
            if not re.match(r"^ci(?:\([^)]*\))?: ", subject):
                problems.append("Workflow-only PRs and all their commits must use ci: or ci(scope):")
    if renovate and workflow_only and any(not message.startswith("ci(deps): ") for message in messages):
        problems.append("Workflow-only Renovate updates must use ci(deps):")
    return problems
