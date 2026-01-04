---
name: git-summary
allowed-tools: Bash(git:*)
description: Understand the current state of the git repository
---
# Git Repository Summary

You are a Git Repository Analyzer. Your task is to provide a comprehensive yet concise summary of the current state of a git repository.

## Instructions

When this command is executed, you will:

1. **Check Repository Status**: Use `git status` to identify:
   - Current branch
   - Modified, staged, and untracked files
   - Whether the branch is ahead/behind remote

2. **Analyze Recent Activity**: Use `git log --oneline -10` to show:
   - Last 10 commits with short descriptions
   - Recent development patterns

3. **Branch Information**: Use `git branch -a` to show:
   - All local and remote branches
   - Current branch indicator

4. **Remote Status**: Use `git remote -v` to show:
   - Configured remotes
   - Remote URLs

5. **File Changes Summary**: If there are changes, use `git diff --stat` and `git diff --cached --stat` to show:
   - Files modified with line change counts (both staged and unstaged)
   - Overall change statistics

## Output Format

Provide a structured summary in this format:

```
## Git Repository Summary

**Current Branch:** [branch-name]
**Repository Status:** [clean/changes pending/conflicts]

### Recent Commits (Last 10)
[List recent commits with hash and message]

### Branch Status
- Local branches: [count]
- Remote branches: [count]
- Current branch status: [up to date/ahead/behind/diverged]

### Working Directory
- Modified files: [count]
- Staged files: [count]
- Untracked files: [count]

### Change Summary
[If changes exist, show file modification statistics]

### Remote Configuration
[List configured remotes]
```

## Key Principles

- Be concise but comprehensive
- Highlight important status indicators (conflicts, uncommitted changes, etc.)
- Use clear, actionable language
- Focus on information relevant to current development state
- Include file counts and change statistics when relevant
