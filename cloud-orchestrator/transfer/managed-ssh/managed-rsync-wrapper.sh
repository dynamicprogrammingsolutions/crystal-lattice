#!/usr/bin/env bash
set -euo pipefail

original="${SSH_ORIGINAL_COMMAND:-}"
case "${original}" in
  rsync\ --server*) ;;
  *)
    echo "Only rsync server mode is allowed" >&2
    exit 126
    ;;
esac

case "${original}" in
  *'..'*|*';'*|*'&'*|*'|'*|*'`'*|*'$('*|*'<'*|*'>'*)
    echo "Unsafe rsync command rejected" >&2
    exit 126
    ;;
esac

cd /transfer
exec ${original}