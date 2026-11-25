import { expect, test } from 'claude-code/testing'
import { SUNSET, frame, width } from '../hooks/draw'

const COLS = 60

const msg = (kind: string) => ({
  plugin: 'highlight-me', component: 'UserMessage', requestId: 'm-' + kind, surface: 'terminal',
  viewport: { columns: COLS, rows: 40 },
  props: { text: 'hi', origin: { kind }, isExpanded: false },
}) as any

const engine = (on: any) =>
  on('ui.render', ($: any, e: any) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine row</Text>
  })

const flat = (text: string) => frame(text, 58).map(l => l.map(s => s.text).join(''))
const LONG = 'a prompt long enough to wrap onto a second line and then a third line of text'

test('the box is round, one width, YOU in the top edge, prompt on the next row', () => {
  for (const text of ['hi', LONG]) {
    const lines = flat(text)
    expect(new Set(lines.map(width)).size).toBe(1)
    expect(lines[0]).toMatch(/^╭─┤ ★ YOU ★ ├─+╮$/)
    expect(lines[1]).toMatch(/^│ ❯ (hi|a prompt)/)
    expect(lines.at(-1)).toMatch(/^╰─+╯$/)
  }
  expect(flat('hi').length).toBe(3)
})

test('the YOU tag is sunset yellow', () => {
  const top = frame('hi', 58)[0] ?? []
  expect(top.find(s => s.text.includes('YOU'))?.bg).toBe(SUNSET.accent)
})

test('my prompt draws its own sunset box; the engine row is not used', async ($, on) => {
  engine(on)
  const ui = await $.ui.mount(msg('composer'))
  expect(await ui.find({ type: 'Text', text: /❯ hi/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /engine row/ })).toBeUndefined()
  expect(JSON.stringify(await ui.drawn())).toContain(`"backgroundColor":"${SUNSET.accent}"`)
  await ui.unmount()
})

test('a task notification is left alone', async ($, on) => {
  engine(on)
  const ui = await $.ui.mount(msg('task-notification'))
  expect(await ui.find({ type: 'Text', text: /engine row/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /YOU/ })).toBeUndefined()
  await ui.unmount()
})
