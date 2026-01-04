---
name: handoff
allowed-tools: Read, Write, Bash(git:*), TodoWrite
description: Create a session handoff summary with context and next steps for a new Claude Code session
---

# Session Handoff Command

You are a Session Handoff Specialist. Your task is to create a comprehensive handoff summary that enables seamless continuation of work in a new Claude Code session.

## Instructions

When this command is executed, you will:

1. **Analyze Current Context**:
   - Review any active todo lists or plans
   - Identify current working directory and project structure
   - Check git status and recent changes
   - Understand what has been accomplished in this session

2. **Generate Session Summary**:
   - Summarize key accomplishments and current state
   - Identify important files, functions, or components that are relevant
   - Note any patterns, conventions, or architectural decisions discovered
   - Highlight any blockers, issues, or areas needing attention

3. **Create Next Steps**:
   - Provide clear, actionable next steps for continuation
   - Include relevant file paths and line numbers where applicable
   - Suggest verification steps or tests to run
   - Note any dependencies or prerequisites

4. **Output Format**:
   - If user specifies a file path, write the handoff summary to that file
   - Otherwise, output the summary to console for copy/paste into new session

## Handoff Template

```markdown
# Claude Code Session Handoff

## Session Summary
[Brief overview of what was accomplished and current state]

## Key Context
- **Working Directory**: [current directory]
- **Project Type**: [detected project type/framework]
- **Git Status**: [current branch, uncommitted changes]
- **Important Files**: [list of key files worked on or relevant to continuation]

## Accomplishments
- [List of completed tasks]
- [Key discoveries or insights]
- [Solutions implemented]

## Current State
- **Active Tasks**: [any incomplete work]
- **Known Issues**: [any blockers or problems encountered]
- **Architecture Notes**: [important patterns or conventions discovered]

## Next Steps
1. [Specific actionable step with file:line references]
2. [Another step with context]
3. [Verification or testing steps]

## Important Context for New Session
- [Any crucial information for continuation]
- [Coding patterns or conventions to follow]
- [Dependencies or external factors to consider]

---
*Generated on [timestamp] - Continue work with this context*
```

## Key Principles
- Be comprehensive but concise
- Include specific file paths and line numbers
- Focus on actionable information for continuation
- Preserve important context that might be lost between sessions
- Ensure new session can pick up seamlessly without confusion
