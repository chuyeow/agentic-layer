import type { Register } from 'claude-code'
import { boxWidth, frame } from './draw'
import type { Seg } from './draw'

// Prompts typed by the person: the local composer, or Remote Control (bridge).
const MINE = new Set(['composer', 'bridge'])

const textProps = (s: Seg) => ({
  ...(s.color ? { color: s.color } : {}),
  ...(s.bg ? { backgroundColor: s.bg } : {}),
  ...(s.bold ? { bold: true } : {}),
})

export const register: Register = on => {
  // Draws the whole row itself: the engine's row carries a blank top line
  // that a wrapper cannot remove.
  on('ui.render', { component: 'UserMessage' }, async ($, e, next) => {
    if (!MINE.has(e.props.origin.kind)) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    const lines = frame(e.props.text, boxWidth(e.viewport?.columns ?? 80))
    return (
      <Box flexDirection="column" marginTop={1}>
        {lines.map(line => (
          <Text>
            {line.map(s => (
              <Text {...textProps(s)}>{s.text}</Text>
            ))}
          </Text>
        ))}
      </Box>
    )
  })
}
