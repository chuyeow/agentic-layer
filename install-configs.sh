#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./install-configs.sh [--force] [--dry-run]

Symlink repo `configs/codex/**` into `~/.codex/**` (or `$CODEX_HOME/**`).
Copy repo `skills/**` into `~/.codex/skills/**` (or `$CODEX_HOME/skills/**`).
Copy repo `commands/*.md` into `~/.codex/skills/<name>/SKILL.md` (frontmatter filtered for Codex).
Symlink repo `commands/*.md` into `~/.claude/commands/*.md`.
Also symlink repo `AGENTS.md` into `~/.claude/CLAUDE.md`.

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
      echo "✅ ok $dst -> $src"
      return 0
    fi
    if [[ $force -eq 1 ]]; then
      move_aside "$dst"
    else
      echo "❌ conflict (symlink): $dst -> $existing (want $src)" >&2
      return 1
    fi
  elif [[ -e "$dst" ]]; then
    if [[ $force -eq 1 ]]; then
      move_aside "$dst"
    else
      echo "❌ conflict (exists): $dst" >&2
      return 1
    fi
  fi

  [[ $dry_run -eq 1 ]] && echo "ln -s $src $dst" || ln -s "$src" "$dst"
}

copy_file() {
  local src="$1"
  local dst="$2"

  mkdirp "$(dirname "$dst")"

  if [[ -L "$dst" ]]; then
    if [[ $force -eq 1 ]]; then
      move_aside "$dst"
    else
      echo "❌ conflict (symlink): $dst" >&2
      return 1
    fi
  elif [[ -f "$dst" ]]; then
    if cmp -s "$src" "$dst"; then
      echo "✅ ok $dst"
      return 0
    fi
    if [[ $force -eq 1 ]]; then
      move_aside "$dst"
    else
      echo "❌ conflict (differs): $dst" >&2
      return 1
    fi
  elif [[ -e "$dst" ]]; then
    if [[ $force -eq 1 ]]; then
      move_aside "$dst"
    else
      echo "❌ conflict (exists): $dst" >&2
      return 1
    fi
  fi

  [[ $dry_run -eq 1 ]] && echo "cp $src $dst" || cp "$src" "$dst"
}

copy_command_as_codex_skill() {
  local src="$1"
  local dst="$2"

  mkdirp "$(dirname "$dst")"

  if [[ $dry_run -eq 1 ]]; then
    echo "write $dst (from $src)"
    return 0
  fi

  local tmp
  tmp="$(mktemp)"

  awk '
    BEGIN { in_fm=0 }
    NR==1 && $0=="---" { in_fm=1; print; next }
    NR==1 { print; next }
    in_fm && $0=="---" { in_fm=0; print; next }
    in_fm && $0 ~ /^(model|argument-hint):/ { next }
    { print }
  ' "$src" >"$tmp"

  if [[ -f "$dst" ]] && cmp -s "$tmp" "$dst"; then
    echo "✅ ok $dst"
    rm -f "$tmp"
    return 0
  fi

  if [[ -e "$dst" || -L "$dst" ]]; then
    if [[ $force -eq 1 ]]; then
      move_aside "$dst"
    else
      echo "❌ conflict (exists): $dst" >&2
      rm -f "$tmp"
      return 1
    fi
  fi

  mv "$tmp" "$dst"
}

mapfile -t files < <(find "$src_root" -type f ! -name '.gitkeep' -print | LC_ALL=C sort)

errors=0
for src in "${files[@]}"; do
  rel="${src#"$src_root"/}"
  dst="$dst_root/$rel"
  if ! link_file "$src" "$dst"; then
    errors=1
  fi
done

src_skills_root="$repo_root/skills"
if [[ -d "$src_skills_root" ]]; then
  mapfile -t skill_files < <(find "$src_skills_root" -type f ! -name '.gitkeep' -print | LC_ALL=C sort)
  for src in "${skill_files[@]}"; do
    rel="${src#"$src_skills_root"/}"
    dst="$dst_root/skills/$rel"
    if ! copy_file "$src" "$dst"; then
      errors=1
    fi
  done
fi

src_commands_root="$repo_root/commands"
if [[ -d "$src_commands_root" ]]; then
  mapfile -t command_files < <(find "$src_commands_root" -maxdepth 1 -type f -name '*.md' -print | LC_ALL=C sort)

  for src in "${command_files[@]}"; do
    command_name="$(basename "${src%.md}")"
    if [[ -f "$src_skills_root/$command_name/SKILL.md" ]]; then
      echo "✅ skip $command_name (repo skill exists)"
      continue
    fi
    dst="$dst_root/skills/$command_name/SKILL.md"
    if ! copy_command_as_codex_skill "$src" "$dst"; then
      errors=1
    fi
  done

  claude_commands_root="$HOME/.claude/commands"
  mkdirp "$claude_commands_root"
  for src in "${command_files[@]}"; do
    command_name="$(basename "$src")"
    dst="$claude_commands_root/$command_name"
    if ! link_file "$src" "$dst"; then
      errors=1
    fi
  done
fi

if [[ -f "$repo_root/AGENTS.md" ]]; then
  if ! link_file "$repo_root/AGENTS.md" "$dst_root/AGENTS.md"; then
    errors=1
  fi

  if ! link_file "$repo_root/AGENTS.md" "$HOME/.claude/CLAUDE.md"; then
    errors=1
  fi
else
  echo "missing: $repo_root/AGENTS.md" >&2
  errors=1
fi

exit "$errors"
