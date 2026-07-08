#!/usr/bin/env bash
# lock.sh — the family's advisory file lock. SOURCE this (don't execute). Defines
# with_lock; sets no shell options and runs no top-level code. This is the ONE copy
# (four byte-identical with_lock copies used to live in the skills).
#
# It is mkdir-based (atomic), steals a dead holder's lock (PID check), and cleans up
# via an EXIT trap, so a short-lived script invocation acquires once and releases
# when it exits.

# with_lock <lock_dir> — block until the lock is held, then take it. A ~5s timeout
# (50 × 0.1s) steals a presumed-dead lock so a holder that died without cleanup
# can't deadlock the family. Use around a read-modify-write of shared state.
with_lock() {
  local lock="$1" i=0 pid=""
  while ! mkdir "$lock" 2>/dev/null; do
    pid=""
    [ -f "$lock/pid" ] && pid=$(cat "$lock/pid" 2>/dev/null || true)
    if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then
      rm -rf "$lock"
      continue
    fi
    i=$((i + 1))
    [ "$i" -ge 50 ] && {
      rm -rf "$lock"
      continue
    }
    sleep 0.1
  done
  echo $$ >"$lock/pid"
  # shellcheck disable=SC2064
  trap "rm -rf '$lock'" EXIT
}
