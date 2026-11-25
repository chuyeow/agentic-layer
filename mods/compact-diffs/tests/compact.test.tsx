import { expect, test } from 'claude-code/testing'

const HUNKS = [{ oldStart: 1, oldLines: 2, newStart: 1, newLines: 2, lines: [' a', '-b', '+B', '+C'] }]

const engine = (on: any) =>
  on('ui.render', ($: any, e: any) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine-diff</Text>
  })

test('Edit diff folds to one line', async ($, on) => {
  engine(on)
  const ui = await $.ui.mount({
    plugin: 'compact-diffs', component: 'ToolResult', requestId: 't1', surface: 'terminal',
    props: { tool_use_id: 't1', tool: 'Edit', isErrored: false, isExpanded: false,
      output: { filePath: '/x.html', structuredPatch: HUNKS } },
  } as any)
  expect((await ui.find({ type: 'Text', text: /\+2 −1/ }))?.text).toContain('ctrl+alt+d')
  expect(await ui.find({ type: 'Text', text: /engine-diff/ })).toBeUndefined()
  await ui.unmount()
})

test('ctrl+o shows the full diff', async ($, on) => {
  engine(on)
  const ui = await $.ui.mount({
    plugin: 'compact-diffs', component: 'ToolResult', requestId: 't2', surface: 'terminal',
    props: { tool_use_id: 't2', tool: 'Edit', isErrored: false, isExpanded: true,
      output: { filePath: '/x.html', structuredPatch: HUNKS } },
  } as any)
  expect((await ui.find({ type: 'Text', text: /engine-diff/ }))?.text).toBe('engine-diff')
  await ui.unmount()
})

test('Bash keeps stdout, swaps its diff for a per-file line', async ($, on) => {
  engine(on)
  const ui = await $.ui.mount({
    plugin: 'compact-diffs', component: 'ToolResult', requestId: 't3', surface: 'terminal',
    props: { tool_use_id: 't3', tool: 'Bash', isErrored: false, isExpanded: false,
      output: { stdout: '2', stderr: '', interrupted: false,
        bashEditDiff: { files: [{ filePath: 'reports/t.html', hunks: HUNKS }], moreFiles: 0 } } },
  } as any)
  expect(await ui.find({ type: 'Text', text: /engine-diff/ })).toBeDefined()
  expect((await ui.find({ type: 'Text', text: /Updated reports\/t\.html \+2 −1/ }))).toBeDefined()
  await ui.unmount()
})

test('/diffs unfolds, then folds again', async ($, on) => {
  engine(on)
  on('command.register', () => ({ value: { command: 'diffs' } }))
  on('session.start', (_: any, e: any) => ({ cwd: e.cwd }))
  const store: Record<string, unknown> = {}
  on('store.get', (_: any, e: any) => ({ value: store[e.key] }))
  on('store.set', (_: any, e: any) => ((store[e.key] = e.value), { value: undefined }))
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const mount = () => $.ui.mount({
    plugin: 'compact-diffs', component: 'ToolResult', requestId: 't4', surface: 'terminal',
    props: { tool_use_id: 't4', tool: 'Edit', isErrored: false, isExpanded: false,
      output: { filePath: '/x.html', structuredPatch: HUNKS } },
  } as any)

  await $.command.run({ command: 'diffs', args: '' } as any)
  let ui = await mount()
  expect(await ui.find({ type: 'Text', text: /engine-diff/ })).toBeDefined()
  await ui.unmount()

  await $.command.run({ command: 'diffs', args: '' } as any)
  ui = await mount()
  expect(await ui.find({ type: 'Text', text: /\+2 −1/ })).toBeDefined()
  await ui.unmount()
})
