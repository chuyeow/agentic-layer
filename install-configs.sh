#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bin/install-configs [--force] [--dry-run]

Symlink repo `configs/codex/**` into `~/.codex/**` (or `$CODEX_HOME/**`).

Options:
  --force    move conflicting targets aside (adds `.bak.<epoch>`)
  --dry-run  print actions only
EOF
}

force=0
dry_run=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --force) force=1; shift ;;
    --dry-run) dry_run=1; shift ;;
    *) echo "unknown arg: $1" >&2; usage >&2; exit 2 ;;
  esac
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
src_root="$repo_root/configs/codex"
dst_root="${CODEX_HOME:-$HOME/.codex}"

if [[ ! -d "$src_root" ]]; then
  echo "missing: $src_root" >&2
  exit 1
fi

mkdirp() {
  [[ $dry_run -eq 1 ]] && echo "mkdir -p $1" || mkdir -p "$1"
}

move_aside() {
  local target="$1"
  local backup="${target}.bak.$(date +%s)"
  [[ $dry_run -eq 1 ]] && echo "mv $target $backup" || mv "$target" "$backup"
}

link_file() {
  local src="$1"
  local dst="$2"

  mkdirp "$(dirname "$dst")"

  if [[ -L "$dst" ]]; then
    local existing
    existing="$(readlink "$dst" || true)"
    if [[ "$existing" == "$src" ]]; then
      [[ $dry_run -eq 1 ]] && echo "ok $dst -> $src"
      return 0
    fi
    if [[ $force -eq 1 ]]; then
      move_aside "$dst"
    else
      echo "conflict (symlink): $dst -> $existing (want $src)" >&2
      return 1
    fi
  elif [[ -e "$dst" ]]; then
    if [[ $force -eq 1 ]]; then
      move_aside "$dst"
    else
      echo "conflict (exists): $dst" >&2
      return 1
    fi
  fi

  [[ $dry_run -eq 1 ]] && echo "ln -s $src $dst" || ln -s "$src" "$dst"
}

mapfile -t files < <(find "$src_root" -type f ! -name '.gitkeep' -print | LC_ALL=C sort)

if [[ ${#files[@]} -eq 0 ]]; then
  echo "no files under $src_root"
  exit 0
fi

errors=0
for src in "${files[@]}"; do
  rel="${src#"$src_root"/}"
  dst="$dst_root/$rel"
  if ! link_file "$src" "$dst"; then
    errors=1
  fi
done

if [[ -f "$repo_root/AGENTS.md" ]]; then
  if ! link_file "$repo_root/AGENTS.md" "$dst_root/AGENTS.md"; then
    errors=1
  fi
else
  echo "missing: $repo_root/AGENTS.md" >&2
  errors=1
fi

exit "$errors"
