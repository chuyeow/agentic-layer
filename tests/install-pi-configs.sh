#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
pi_src="$repo_root/configs/pi"
tmp_root="$(mktemp -d)"
trap 'rm -rf "$tmp_root"' EXIT

home="$tmp_root/home"
codex_home="$tmp_root/codex"
mkdir -p "$home" "$codex_home"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_link() {
  local path="$1"
  local expected="$2"

  [[ -L "$path" ]] || fail "expected symlink: $path"
  [[ "$(readlink "$path")" == "$expected" ]] || \
    fail "wrong target: $path -> $(readlink "$path"), expected $expected"
}

[[ -d "$pi_src" ]] || fail "missing Pi config source: $pi_src"

HOME="$home" CODEX_HOME="$codex_home" "$repo_root/install-configs.sh" >/dev/null

while IFS= read -r -d '' src; do
  rel="${src#"$pi_src"/}"
  assert_link "$home/.pi/agent/$rel" "$src"
done < <(find "$pi_src" -type f ! -name '.gitkeep' -print0 | LC_ALL=C sort -z)

HOME="$home" CODEX_HOME="$codex_home" "$repo_root/install-configs.sh" >/dev/null

override_home="$tmp_root/override-home"
override_codex_home="$tmp_root/override-codex"
override_pi_agent_dir="$tmp_root/pi-agent"
mkdir -p "$override_home" "$override_codex_home"
HOME="$override_home" \
  CODEX_HOME="$override_codex_home" \
  PI_CODING_AGENT_DIR="$override_pi_agent_dir" \
  "$repo_root/install-configs.sh" >/dev/null
assert_link \
  "$override_pi_agent_dir/settings.json" \
  "$pi_src/settings.json"

for excluded in auth.json trust.json models-store.json calm; do
  [[ ! -e "$pi_src/$excluded" ]] || fail "runtime file must not be tracked: $excluded"
done

if grep -q '"lastChangelogVersion"' "$pi_src/settings.json"; then
  fail "lastChangelogVersion is generated state"
fi

printf '%s\n' "PASS: Pi config install"
