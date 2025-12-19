#!/bin/sh

set -e

# If NODE_NAME is set, start in distributed mode
if [ -n "$NODE_NAME" ]; then
    echo "🚀 Starting Elixir in distributed mode as $NODE_NAME"
    export ELIXIR_ERL_OPTIONS="-proto_dist inet_tcp"
    # Use --sname for short names in Docker
    exec elixir --sname "$NODE_NAME" --cookie "$COOKIE" -S mix run --no-halt
else
    echo "🚀 Starting Elixir in local mode"
    exec mix run --no-halt
fi
