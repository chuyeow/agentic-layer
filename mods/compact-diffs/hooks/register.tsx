import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

type Hunk = { lines: string[] }

const STORE_KEY = 'isFolded'
const isFolded = atom({ plugin: 'compact-diffs', key: 'isFolded' } as const, true)

// Pure: count added/removed lines across hunks.
export const countLines = (hunks: readonly Hunk[]) => {
  let added = 0
  let removed = 0
  for (const h of hunks) {
    for (const l of h.lines) {
      if (l.startsWith('+')) added += 1
      else if (l.startsWith('-')) removed += 1
    }
  }
  return { added, removed }
}

export const summary = (hunks: readonly Hunk[], path?: string) => {
  const { added, removed } = countLines(hunks)
  return `${path ? `${path} ` : ''}+${added} −${removed}`
}

// Pure: the status-line cue for a fold state.
export const cue = (folded: boolean) => (folded ? '⊟ diffs folded' : '⊞ diffs shown')

const HINT = ' · ctrl+alt+d to unfold'

const show = ($: EngineInterface, folded: boolean) => $.ui.status(cue(folded))

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'diffs',
      description: 'Toggle folding of file diffs in the transcript (compact-diffs)',
    })
    const stored = await $.store.get(STORE_KEY)
    const folded = typeof stored === 'boolean' ? stored : true
    await update($, isFolded, () => folded)
    show($, folded)
    return next(e)
  })

  on('command.run', { command: 'diffs' }, async $ => {
    let folded = true
    await update($, isFolded, v => (folded = !v))
    await $.store.set(STORE_KEY, folded)
    show($, folded)
    return { isTextDisplayOnly: true }
  })

  on('ui.render', { component: 'ToolResult' }, async ($, e, next) => {
    if (e.props.isExpanded || e.props.isErrored || !(await read($, isFolded))) {
      return next(e)
    }

    const out = e.props.output as Record<string, unknown> | undefined
    if (!out || typeof out !== 'object') {
      return next(e)
    }

    const { Box, Text } = $.ui.resolve(e)

    // Edit / Write: replace the diff block with one line.
    if ((e.props.tool === 'Edit' || e.props.tool === 'Write') && Array.isArray(out.structuredPatch)) {
      const hunks = out.structuredPatch as Hunk[]
      if (hunks.length === 0) {
        return next(e)
      }
      return (
        <Text dimColor>
          {'  ⎿  '}
          {summary(hunks)}
          {HINT}
        </Text>
      )
    }

    // Bash that edited files: keep stdout/stderr, swap its diff for one line per file.
    const diff = out.bashEditDiff as
      | { files?: { filePath: string; hunks: Hunk[] }[]; moreFiles?: number }
      | undefined
    if (e.props.tool === 'Bash' && diff?.files?.length) {
      const { bashEditDiff: _drop, ...rest } = out
      const row = await next({ ...e, props: { ...e.props, output: rest } })
      const more = diff.moreFiles ? ` (+${diff.moreFiles} more files)` : ''
      return (
        <Box flexDirection="column">
          {row}
          {diff.files.map(f => (
            <Text key={f.filePath} dimColor>
              {'  ⎿  Updated '}
              {summary(f.hunks, f.filePath)}
            </Text>
          ))}
          <Text dimColor>
            {'     '}
            {more}
            {HINT.slice(3)}
          </Text>
        </Box>
      )
    }

    return next(e)
  })
}
