export type Folded = boolean

declare module 'claude-code' {
  interface PluginState {
    'compact-diffs': { isFolded: Folded }
  }
}
