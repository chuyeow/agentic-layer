#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
mods_src="$repo_root/mods"
tmp_root="$(mktemp -d)"
trap 'rm -rf "$tmp_root"' EXIT

home="$tmp_root/home"
mkdir -p "$home"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

[[ -d "$mods_src" ]] || fail "missing mods source: $mods_src"

HOME="$home" CODEX_HOME="$tmp_root/codex" PI_CODING_AGENT_DIR="$tmp_root/pi" \
  "$repo_root/install-configs.sh" >/dev/null

while IFS= read -r -d '' src; do
  name="$(basename "$src")"
  dst="$home/.claude/skills/$name"
  [[ -L "$dst" ]] || fail "expected symlink: $dst"
  [[ "$(readlink "$dst")" == "$src" ]] || fail "wrong target: $dst -> $(readlink "$dst")"
  [[ -f "$src/.claude-plugin/plugin.json" ]] || fail "mod without plugin.json: $name"
  [[ ! -e "$home/.codex/skills/$name" && ! -e "$tmp_root/codex/skills/$name" ]] || \
    fail "mod leaked into Codex skills: $name"
done < <(find "$mods_src" -mindepth 1 -maxdepth 1 -type d -print0 | LC_ALL=C sort -z)

# Engine-generated editor types must stay out of git.
for m in "$mods_src"/*/; do
  git -C "$repo_root" check-ignore -q "${m}.claude-plugin/types/x.d.ts" || \
    fail "generated types not ignored: ${m}.claude-plugin/types"
done

printf '%s\n' "PASS: Claude Code mods install"
