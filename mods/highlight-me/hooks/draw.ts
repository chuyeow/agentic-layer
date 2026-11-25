// Pure drawing: prompt text + width + palette in, coloured lines out.

export type Seg = { text: string; color?: string; bg?: string; bold?: boolean }
export type Line = Seg[]
export type Palette = { name: string; edge: string; accent: string; ink: string; well: string }

// Sunset: orange-red edge, yellow YOU tag, dark ember well.
export const SUNSET: Palette = { name: 'sunset', edge: '#ff7043', accent: '#ffca28', ink: '#000000', well: '#2b1206' }

const isWide = (c: number) =>
  c >= 0x1100 &&
  (c <= 0x115f ||
    (c >= 0x2e80 && c <= 0xa4cf) ||
    (c >= 0xac00 && c <= 0xd7a3) ||
    (c >= 0xf900 && c <= 0xfaff) ||
    (c >= 0xfe30 && c <= 0xfe4f) ||
    (c >= 0xff00 && c <= 0xff60) ||
    (c >= 0xffe0 && c <= 0xffe6) ||
    (c >= 0x1f300 && c <= 0x1faff))

export const width = (s: string) =>
  Array.from(s).reduce((n, ch) => n + (isWide(ch.codePointAt(0) ?? 0) ? 2 : 1), 0)

const pad = (s: string, cols: number) => s + ' '.repeat(Math.max(0, cols - width(s)))
const lineWidth = (line: Line) => line.reduce((n, s) => n + width(s.text), 0)

export const wrap = (text: string, cols: number): string[] => {
  const out: string[] = []
  for (const para of text.split('\n')) {
    let line = ''
    for (const word of para.split(' ')) {
      let w = word
      while (width(w) > cols) {
        if (line) {
          out.push(line)
          line = ''
        }
        const chars = Array.from(w)
        let head = ''
        while (chars.length && width(head + chars[0]) <= cols) head += chars.shift()
        out.push(head)
        w = chars.join('')
      }
      const joined = line ? `${line} ${w}` : w
      if (width(joined) <= cols) line = joined
      else {
        out.push(line)
        line = w
      }
    }
    out.push(line)
  }
  return out
}

const tag = (p: Palette): Line => [
  { text: '┤', color: p.edge },
  { text: ' ★ YOU ★ ', bg: p.accent, color: p.ink, bold: true },
  { text: '├', color: p.edge },
]

// A round-cornered box with the YOU tag in its top edge; the prompt starts on
// the first row inside.
export const box = (content: readonly string[], w: number, p: Palette): Line[] => {
  const e = (text: string): Seg => ({ text, color: p.edge })
  const t = tag(p)
  return [
    [e('╭─'), ...t, e(`${'─'.repeat(Math.max(0, w - 3 - lineWidth(t)))}╮`)],
    ...content.map(l => [e('│'), { text: pad(` ${l}`, w - 2), bg: p.well }, e('│')]),
    [e(`╰${'─'.repeat(w - 2)}╯`)],
  ]
}

export const boxWidth = (columns: number) => Math.max(24, columns - 2)

// w: the box's own width in cells.
export const frame = (text: string, w: number, p: Palette = SUNSET): Line[] => {
  const lines = wrap(text.trim(), w - 6).map((l, i) => (i ? `  ${l}` : `❯ ${l}`))
  return box(lines, w, p)
}
